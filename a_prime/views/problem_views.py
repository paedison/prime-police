from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect

from a_common import utils as common_utils
from a_common.constants import icon_set
from a_official import utils as police_utils
from a_official.models import Problem, ProblemRate, ProblemSolve, ProblemTag, ProblemTaggedItem


def get_list_variables(request: common_utils.HtmxHttpRequest):
    filterset = police_utils.get_filterset(request)
    paginator = Paginator(filterset.qs, per_page=10)
    page = int(request.GET.get('page', 1))
    elided_page_range = police_utils.get_elided_page_range(
        request, filterset, page, paginator.num_pages)
    return filterset, paginator, page, elided_page_range


def problem_list_view(request: common_utils.HtmxHttpRequest, tag=None):
    filterset, paginator, page, elided_page_range = get_list_variables(request)

    info = {'menu': 'official'}
    next_path = police_utils.get_page_added_path(request, page)['next_path']

    try:
        problems = paginator.page(page)
    except EmptyPage:
        return HttpResponse('')

    context = common_utils.update_context_data(
        info=info,
        problems=problems,
        tag=tag,
        form=filterset.form,
        next_path=next_path,
        page=page,
        elided_page_range=elided_page_range,
        show_first_page=True,
        show_next_page=False,
    )
    if request.htmx:
        if request.headers.get('Open-First-Page') != 'true':
            context = common_utils.update_context_data(
                context, show_first_page=False, show_next_page=True)
        return render(request, 'a_official/problem_list_content.html', context)
    return render(request, 'a_official/problem_list.html', context)


def problem_list_filter(request: common_utils.HtmxHttpRequest):
    filterset, paginator, page, elided_page_range = get_list_variables(request)
    context = {
        'form': filterset.form,
        'page': page,
        'elided_page_range': elided_page_range,
    }
    return render(request, 'a_official/snippets/filter_list.html', context)


def problem_detail_view(request: common_utils.HtmxHttpRequest, pk: int | None = None):
    if pk is None:
        pk_list = request.GET.getlist('pk')
        for p in pk_list:
            if str(p).isdigit():
                return redirect('official:problem-detail', p)

    queryset = Problem.objects
    problem = get_object_or_404(queryset, pk=pk)

    problem_neighbors = queryset.filter(year=problem.year, subject=problem.subject)
    # problem_likes = problem_rates = problem_solves = None
    # if request.user.is_authenticated:
    #     problem_likes = police_utils.get_customized_problems(request, ProblemLike)
    #     problem_rates = police_utils.get_customized_problems(request, ProblemRate)
    #     problem_solves = police_utils.get_customized_problems(request, ProblemSolve)

    info = {'menu': 'official'}
    context = common_utils.update_context_data(
        info=info,
        problem=problem,
        problem_neighbors=problem_neighbors,
        # problem_likes=problem_likes,
        # problem_rates=problem_rates,
        # problem_solves=problem_solves,
    )
    if request.htmx:
        return render(request, 'a_official/problem_detail_content.html', context)
    return render(request, 'a_official/problem_detail.html', context)


def get_problem(pk: int):
    return get_object_or_404(Problem, pk=pk)


@login_required
def like_problem(request: common_utils.HtmxHttpRequest, pk: int):
    problem = get_problem(pk)

    if request.method == 'POST':
        user_exists = problem.problem_like_set.filter(user=request.user).exists()
        if user_exists:
            problem.like_users.remove(request.user)
        else:
            problem.like_users.add(
                request.user, through_defaults={'is_liked': True})
        icon_like = icon_set.ICON_LIKE[f'{not user_exists}']
        like_users = problem.like_users.count()
        return HttpResponse(f'{icon_like} {like_users}')


@login_required
def rate_problem(request: common_utils.HtmxHttpRequest, pk: int):
    problem = get_problem(pk)

    if request.method == 'POST':
        rating = request.POST.get('rating')
        user_exists = problem.problem_rate_set.filter(user=request.user).exists()
        if user_exists:
            problem_rate = ProblemRate.objects.get(
                user=request.user, problem=problem)
            problem_rate.rating = rating
            problem_rate.save()
        else:
            problem.rate_users.add(
                request.user, through_defaults={'rating': rating})
        icon_rate = icon_set.ICON_RATE[f'star{rating}']
        return HttpResponse(icon_rate)

    context = {
        'problem': problem,
    }
    return render(request, 'a_official/snippets/rate_modal.html', context)


@login_required
def solve_problem(request: common_utils.HtmxHttpRequest, pk: int):
    problem = get_problem(pk)

    if request.method == 'POST':
        answer = int(request.POST.get('answer'))
        is_correct = answer == problem.answer

        user_exists = problem.problem_solve_set.filter(user=request.user).exists()
        if user_exists:
            problem_solve = ProblemSolve.objects.get(
                user=request.user, problem=problem)
            problem_solve.answer = answer
            problem_solve.is_correct = is_correct
            problem_solve.save()
        else:
            problem.solve_users.add(
                request.user,
                through_defaults={'answer': answer, 'is_correct': is_correct}
            )
        context = {
            'problem': problem,
            'icon_solve': icon_set.ICON_SOLVE[f'{is_correct}'],
            'is_correct': is_correct,
        }
        return render(request, 'a_official/snippets/solve_result.html', context)

    context = {
        'problem': problem,
    }
    return render(request, 'a_official/snippets/solve_modal.html', context)


@login_required
def tag_problem_add(request: common_utils.HtmxHttpRequest, pk: int):
    problem = get_problem(pk)

    if request.method == 'POST':
        tag = request.POST.get('tag')
        tag, created = ProblemTag.objects.get_or_create(name=tag)
        tagged_item, created = ProblemTaggedItem.objects.get_or_create(
            tag=tag, content_object=problem, user=request.user)
        if not created:
            tagged_item.is_tagged = True
            tagged_item.save(message_type='tagged')
        return HttpResponse('')


@login_required
def tag_problem_remove(request: common_utils.HtmxHttpRequest, pk: int):
    problem = get_problem(pk)

    if request.method == 'POST':
        tag = request.POST.get('tag')
        tagged_item = get_object_or_404(
            ProblemTaggedItem, tag__name=tag, content_object=problem, user=request.user)
        tagged_item.is_tagged = False
        tagged_item.save(message_type='untagged')
        return HttpResponse('')
