from bs4 import BeautifulSoup as bs
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_POST

from a_common.constants import icon_set
from a_common.utils import HtmxHttpRequest, update_context_data
from . import models, forms, utils, filters


def problem_list_view(request: HtmxHttpRequest, tag=None):
    view_type = request.headers.get('View-Type', '')
    page = int(request.GET.get('page', 1))
    if request.user.is_authenticated:
        filterset = filters.OfficialListFilter(data=request.GET, request=request)
    else:
        filterset = filters.AnonymousOfficialListFilter(data=request.GET, request=request)

    problems, page_range = utils.get_page_obj_and_range(page, filterset.qs)
    if not problems:
        return HttpResponse('')

    info = {'menu': 'official'}
    curr_path = request.get_full_path()
    if 'page=' not in curr_path:
        curr_path += '&page=1' if '?' in curr_path else '?page=1'
    next_path = curr_path.replace(f'page={page}', f'page={page + 1}')

    custom_data = utils.get_custom_data(request.user)

    context = update_context_data(
        info=info,
        tag=tag, form=filterset.form, next_path=next_path,
        problems=problems, page=page, page_range=page_range,
        custom_data=custom_data,
    )
    if view_type == 'list_next_page':
        return render(request, 'a_official/problem_list_content.html#next_page', context)
    return render(request, 'a_official/problem_list.html', context)


def problem_detail_view(request: HtmxHttpRequest, pk: int | None = None):
    if pk is None:
        pk_list = request.GET.getlist('pk')
        for p in pk_list:
            if str(p).isdigit():
                return redirect('official:problem-detail', p)

    problem = get_object_or_404(models.Problem, pk=pk)
    problem_neighbors = models.Problem.objects.filter(year=problem.year, subject=problem.subject)
    custom_data = utils.get_custom_data(request.user)
    problem_likes = custom_data['like']
    problem_rates = custom_data['rate']
    problem_solves = custom_data['solve']

    info = {'menu': 'official'}
    context = update_context_data(
        info=info, problem=problem,
        problem_neighbors=problem_neighbors,
        problem_likes=problem_likes,
        problem_rates=problem_rates,
        problem_solves=problem_solves,
        custom_data=custom_data,
    )
    if request.htmx:
        return render(request, 'a_official/problem_detail_content.html', context)
    return render(request, 'a_official/problem_detail.html', context)


@login_required
@require_POST
def like_problem(request: HtmxHttpRequest, pk: int):
    problem = get_object_or_404(models.Problem, pk=pk)

    try:
        problem_like = models.ProblemLike.objects.get(user=request.user, problem=problem)
        is_liked = not problem_like.is_liked
        problem_like.is_liked = is_liked
        message_type = 'liked' if is_liked else 'unliked'
        problem_like.save(message_type=message_type)
    except models.ProblemLike.DoesNotExist:
        models.ProblemLike.objects.create(user=request.user, problem=problem)
        is_liked = True
    icon_like = icon_set.ICON_LIKE[f'{is_liked}']
    like_users = models.ProblemLike.objects.filter(problem=problem, is_liked=True).count()
    return HttpResponse(f'{icon_like} {like_users}')


@login_required
def rate_problem(request: HtmxHttpRequest, pk: int):
    problem = get_object_or_404(models.Problem, pk=pk)

    if request.method == 'POST':
        rating = request.POST.get('rating')
        try:
            problem_rate = models.ProblemRate.objects.get(user=request.user, problem=problem)
            problem_rate.rating = rating
            problem_rate.save()
        except models.ProblemRate.DoesNotExist:
            models.ProblemRate.objects.create(user=request.user, problem=problem, rating=rating)
        icon_rate = icon_set.ICON_RATE[f'star{rating}']
        return HttpResponse(icon_rate)

    context = update_context_data(problem=problem)
    return render(request, 'a_official/snippets/rate_modal.html', context)


@login_required
def solve_problem(request: HtmxHttpRequest, pk: int):
    problem = get_object_or_404(models.Problem, pk=pk)

    if request.method == 'POST':
        answer = int(request.POST.get('answer'))
        is_correct = answer == problem.answer
        try:
            problem_solve = models.ProblemSolve.objects.get(user=request.user, problem=problem)
            problem_solve.answer = answer
            problem_solve.is_correct = is_correct
            problem_solve.save()
        except models.ProblemSolve.DoesNotExist:
            models.ProblemSolve.objects.create(user=request.user, problem=problem, answer=answer)
        icon_solve = icon_set.ICON_SOLVE[f'{is_correct}']

        context = update_context_data(problem=problem, icon_solve=icon_solve, is_correct=is_correct)
        return render(request, 'a_official/snippets/solve_result.html', context)

    context = update_context_data(problem=problem)
    return render(request, 'a_official/snippets/solve_modal.html', context)


@require_POST
@login_required
def tag_problem(request: HtmxHttpRequest, pk: int):
    view_type = request.headers.get('View-Type', '')
    problem = get_object_or_404(models.Problem, pk=pk)
    name = request.POST.get('tag')

    if view_type == 'add':
        tag, _ = models.ProblemTag.objects.get_or_create(name=name)
        models.ProblemTaggedItem.objects.get_or_create(
            tag=tag, content_object=problem, user=request.user)
        return HttpResponse('')

    if view_type == 'remove':
        tagged_problem = get_object_or_404(
            models.ProblemTaggedItem, tag__name=name, content_object=problem, user=request.user)
        tagged_problem.active = False
        tagged_problem.save(message_type='untagged')
        return HttpResponse('')


@login_required
def comment_problem_create(request: HtmxHttpRequest, pk: int):
    problem = get_object_or_404(models.Problem, pk=pk)
    reply_form = forms.ProblemCommentForm()

    if request.method == 'POST':
        form = forms.ProblemCommentForm(request.POST)
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
    comment = get_object_or_404(models.ProblemComment, pk=pk)
    if request.method == 'POST':
        form = forms.ProblemCommentForm(request.POST, instance=comment)
        if form.is_valid():
            form.save()
            return redirect('problemcomment-list')
    else:
        form = forms.ProblemCommentForm(instance=comment)
    return render(request, 'problemcomment_form.html', {'form': form})


@login_required
def comment_problem_delete(request: HtmxHttpRequest, pk: int):
    comment = get_object_or_404(models.ProblemComment, pk=pk)
    if request.method == 'POST':
        comment.delete()
        return redirect('problemcomment-list')
    return render(request, 'problemcomment_confirm_delete.html', {'comment': comment})