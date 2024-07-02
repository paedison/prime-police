from bs4 import BeautifulSoup as bs

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_POST

from a_common.constants.icon_set import ICON_LIKE, ICON_RATE, ICON_SOLVE
from a_common.utils import HtmxHttpRequest, update_context_data
from a_official.forms import ProblemCommentForm
from a_official.models import (
    Problem, ProblemRate, ProblemSolve, ProblemTag, ProblemTaggedItem, ProblemLike, ProblemComment
)
from a_official.utils import get_filterset, get_elided_page_range, get_page_added_path, get_customized_problems


def get_list_variables(request: HtmxHttpRequest):
    filterset = get_filterset(request)
    paginator = Paginator(filterset.qs, per_page=10)
    page = int(request.GET.get('page', 1))
    elided_page_range = get_elided_page_range(request, filterset, page, paginator.num_pages)
    return filterset, paginator, page, elided_page_range


def problem_list_view(request: HtmxHttpRequest, tag=None):
    filterset, paginator, page, elided_page_range = get_list_variables(request)

    info = {'menu': 'official'}
    next_path = get_page_added_path(request, page)['next_path']

    try:
        problems = paginator.page(page)
    except EmptyPage:
        return HttpResponse('')

    context = update_context_data(
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
            context = update_context_data(context, show_first_page=False, show_next_page=True)
        return render(request, 'a_official/problem_list_content.html', context)
    return render(request, 'a_official/problem_list.html', context)


def problem_list_filter(request: HtmxHttpRequest):
    filterset, paginator, page, elided_page_range = get_list_variables(request)
    context = update_context_data(form=filterset.form, page=page, elided_page_range=elided_page_range)
    return render(request, 'a_official/snippets/filter_list.html', context)


def problem_detail_view(request: HtmxHttpRequest, pk: int | None = None):
    if pk is None:
        pk_list = request.GET.getlist('pk')
        for p in pk_list:
            if str(p).isdigit():
                return redirect('official:problem-detail', p)

    queryset = Problem.objects
    problem = get_object_or_404(queryset, pk=pk)

    problem_neighbors = queryset.filter(year=problem.year, subject=problem.subject)
    problem_likes = problem_rates = problem_solves = None
    if request.user.is_authenticated:
        problem_likes = get_customized_problems(request, ProblemLike).filter(is_liked=True)
        problem_rates = get_customized_problems(request, ProblemRate)
        problem_solves = get_customized_problems(request, ProblemSolve)

    info = {'menu': 'official'}
    context = update_context_data(
        info=info,
        problem=problem,
        problem_neighbors=problem_neighbors,
        problem_likes=problem_likes,
        problem_rates=problem_rates,
        problem_solves=problem_solves,
    )
    if request.htmx:
        return render(request, 'a_official/problem_detail_content.html', context)
    return render(request, 'a_official/problem_detail.html', context)


def get_problem(pk: int):
    return get_object_or_404(Problem, pk=pk)


@login_required
@require_POST
def like_problem(request: HtmxHttpRequest, pk: int):
    problem = get_problem(pk)

    problem_like, created = ProblemLike.objects.get_or_create(user=request.user, problem=problem)
    is_liked = True
    message_type = 'liked'
    if not created:
        is_liked = not problem_like.is_liked
        message_type = 'liked' if is_liked else 'unliked'
        problem_like.is_liked = is_liked
    problem_like.save(message_type=message_type)

    icon_like = ICON_LIKE[f'{is_liked}']
    like_users = ProblemLike.objects.filter(problem=problem, is_liked=True).count()
    return HttpResponse(f'{icon_like} {like_users}')


@login_required
def rate_problem(request: HtmxHttpRequest, pk: int):
    problem = get_problem(pk)

    if request.method == 'POST':
        rating = request.POST.get('rating')
        problem_rate, created = ProblemRate.objects.get_or_create(user=request.user, problem=problem)
        problem_rate.rating = rating
        problem_rate.save(message_type='rated')
        icon_rate = ICON_RATE[f'star{rating}']
        return HttpResponse(icon_rate)

    context = update_context_data(problem=problem)
    return render(request, 'a_official/snippets/rate_modal.html', context)


@login_required
def solve_problem(request: HtmxHttpRequest, pk: int):
    problem = get_problem(pk)

    if request.method == 'POST':
        answer = int(request.POST.get('answer'))
        is_correct = answer == problem.answer
        problem_solve, created = ProblemSolve.objects.get_or_create(user=request.user, problem=problem)
        problem_solve.answer = answer
        problem_solve.is_correct = is_correct
        message_type = 'correct' if is_correct else 'wrong'
        problem_solve.save(message_type=message_type)
        icon_solve = ICON_SOLVE[f'{is_correct}']

        context = update_context_data(problem=problem, icon_solve=icon_solve, is_correct=is_correct)
        return render(request, 'a_official/snippets/solve_result.html', context)

    context = update_context_data(problem=problem)
    return render(request, 'a_official/snippets/solve_modal.html', context)


@login_required
@require_POST
def tag_problem_create(request: HtmxHttpRequest, pk: int):
    problem = get_problem(pk)
    tag_name = request.POST.get('tag')
    tag, created = ProblemTag.objects.get_or_create(name=tag_name)
    tagged_item, created = ProblemTaggedItem.objects.get_or_create(
        tag=tag, content_object=problem, user=request.user)
    if not created:
        tagged_item.is_tagged = True
    tagged_item.save(message_type='tagged')
    return HttpResponse('')


@login_required
@require_POST
def tag_problem_remove(request: HtmxHttpRequest, pk: int):
    problem = get_problem(pk)
    tag = request.POST.get('tag')
    tagged_item = get_object_or_404(
        ProblemTaggedItem, tag__name=tag, content_object=problem, user=request.user)
    tagged_item.is_tagged = False
    tagged_item.save(message_type='untagged')
    return HttpResponse('')


@login_required
def comment_problem_create(request: HtmxHttpRequest, pk: int):
    problem = get_problem(pk)
    reply_form = ProblemCommentForm()

    if request.method == 'POST':
        form = ProblemCommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)

            content = form.cleaned_data['content']
            soup = bs(content, 'html.parser')
            title = soup.get_text()[:20]

            comment.problem = problem
            comment.user = request.user
            comment.title = title
            comment.save()
            context = {
                'comment': comment,
                'problem': problem,
                'reply_form': reply_form,
            }
            return render(request, 'a_official/snippets/comment.html', context)


@login_required
def comment_problem_update(request: HtmxHttpRequest, pk: int):
    comment = get_object_or_404(ProblemComment, pk=pk)
    if request.method == 'POST':
        form = ProblemCommentForm(request.POST, instance=comment)
        if form.is_valid():
            form.save()
            return redirect('problemcomment-list')
    else:
        form = ProblemCommentForm(instance=comment)
    return render(request, 'problemcomment_form.html', {'form': form})


@login_required
def comment_problem_delete(request: HtmxHttpRequest, pk: int):
    comment = get_object_or_404(ProblemComment, pk=pk)
    if request.method == 'POST':
        comment.delete()
        return redirect('problemcomment-list')
    return render(request, 'problemcomment_confirm_delete.html', {'comment': comment})