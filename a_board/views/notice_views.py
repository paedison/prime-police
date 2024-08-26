from django.contrib.auth.decorators import login_not_required
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.decorators.http import require_POST
from django_htmx.http import retarget, reswap

from a_common.constants import icon_set
from a_common.utils import update_context_data, HtmxHttpRequest
from .. import models, utils, forms


class NoticeConfiguration:
    menu = 'notice'
    info = {'menu': menu}
    title = {'kor': '공지사항', 'eng': menu.capitalize()}
    list_page_url = {
        'admin': reverse_lazy(f'admin:a_board_{menu}_changelist'),
        'current': reverse_lazy(f'board:{menu}-list'),
        'create': reverse_lazy(f'admin:a_board_{menu}_add'),
    }
    detail_page_url = {
        'create': reverse_lazy(f'admin:a_board_{menu}_add'),
    }


def get_queryset(request):
    queryset = models.Notice.objects.prefetch_related('post_comments')
    if not request.user.is_authenticated or not request.user.is_staff:
        queryset = queryset.filter(is_hidden=False)
    return queryset


@login_not_required
def list_view(request: HtmxHttpRequest):
    config = NoticeConfiguration()
    view_type = request.headers.get('View-Type', '')
    page_number = request.GET.get('page', '1')
    queryset = get_queryset(request)
    page_obj, page_range = utils.get_paginator_info(queryset, page_number)
    top_fixed = utils.get_filtered_queryset(request, top_fixed=True)
    context = update_context_data(
        info=config.info, title=config.title, page_url=config.list_page_url,
        view_type=view_type,
        icon_menu=icon_set.ICON_MENU['notice'], icon_board=icon_set.ICON_BOARD,
        page_obj=page_obj, page_range=page_range, top_fixed=top_fixed,
    )
    if view_type == 'pagination':
        return render(request, 'a_board/post_list_content.html', context)
    return render(request, 'a_board/post_list.html', context)


@login_not_required
def detail_view(request: HtmxHttpRequest, pk: int):
    config = NoticeConfiguration()
    view_type = request.headers.get('View-Type', '')
    queryset = get_queryset(request)
    post = get_object_or_404(queryset, pk=pk)
    prev_post, next_post = utils.get_prev_next_post(queryset, post)
    comments = models.NoticeComment.objects.filter(post=post)
    context = update_context_data(
        info=config.info, view_type=view_type, title=config.title,
        icon_menu=icon_set.ICON_MENU['notice'], icon_board=icon_set.ICON_BOARD,
        post=post, prev_post=prev_post, next_post=next_post, comments=comments)
    return render(request, 'a_board/post_detail.html', context)


def create_view(request: HtmxHttpRequest):
    config = NoticeConfiguration()
    context = update_context_data(
        info=config.info, icon_menu=icon_set.ICON_MENU['notice'],
        icon_board=icon_set.ICON_BOARD)
    if request.method == 'POST':
        form = forms.NoticeForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.user = request.user
            post.save()
            return redirect('notice:detail', pk=post.id)
    form = forms.NoticeForm()
    post_url = reverse_lazy('notice:create')
    context = update_context_data(
        context, form=form, sub_title='공지사항 작성',
        post_url=post_url, message='입력')
    return render(request, 'a_board/post_create.html', context)


def update_view(request: HtmxHttpRequest, pk: int):
    config = NoticeConfiguration()
    instance = get_object_or_404(models.Notice, pk=pk)
    context = update_context_data(
        info=config.info, icon_menu=icon_set.ICON_MENU['notice'],
        icon_board=icon_set.ICON_BOARD)
    if request.method == 'POST':
        form = forms.NoticeForm(request.POST, instance=instance)
        if form.is_valid():
            notice = form.save()
            return redirect('notice:detail', pk=notice.id)
    form = forms.NoticeForm(instance=instance)
    context = update_context_data(
        context, form=form, sub_title='공지사항 수정',
        post_url=instance.get_update_url(), message='수정')
    return render(request, 'a_board/post_create.html', context)


@require_POST
def delete_view(_, pk: int):
    instance = get_object_or_404(models.Notice, pk=pk)
    instance.delete()
    return redirect('notice:base')


def comment_list_view(request: HtmxHttpRequest):
    post_id = request.GET.get('post_id')
    post = get_object_or_404(models.Notice, pk=post_id)
    comments = models.NoticeComment.objects.filter(post=post)

    order_type = request.GET.get('order_type')
    if order_type == 'oldest':
        comments = comments.order_by('created_at')
    if order_type == 'newest':
        comments = comments.order_by('-created_at')

    context = update_context_data(post=post, comments=comments, order_type=order_type)
    return render(request, 'a_board/comment_container.html', context)


def comment_create_view(request: HtmxHttpRequest):
    form = forms.NoticeCommentCreateForm()

    if request.method == 'POST':
        form = forms.NoticeCommentCreateForm(data=request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.user = request.user
            comment.post = form.cleaned_data['post']
            comment.save()
            context = update_context_data(comment=comment, make_form_blank=True)
            return render(request, 'a_board/snippets/comment_item.html', context)
        else:
            context = update_context_data(form=form)
            response = render(request, 'a_board/snippets/comment_form.html', context)
            return reswap(retarget(response, '#commentForm'), 'innerHTML swap:0.25s')

    context = update_context_data(form=form)
    return render(request, 'a_board/snippets/comment_form.html', context)


def comment_update_view(request: HtmxHttpRequest, pk: int):
    instance = get_object_or_404(models.NoticeComment, pk=pk)

    if request.method == 'POST':
        form = forms.NoticeCommentUpdateForm(data=request.POST, instance=instance)
        if form.is_valid():
            form.save()
            context = update_context_data(comment=instance)
            return render(request, 'a_board/snippets/comment_item_content.html', context)
        else:
            context = update_context_data(form=form, comment=instance)
            return render(request, 'a_board/snippets/comment_form.html', context)

    form = forms.NoticeCommentUpdateForm(instance=instance)
    context = update_context_data(form=form, comment=instance)
    return render(request, 'a_board/snippets/comment_form.html', context)


@require_POST
def comment_delete_view(_, pk: int):
    comment = get_object_or_404(models.NoticeComment, pk=pk)
    post_id = comment.post_id
    url = f"{reverse_lazy('board:notice-comment-list')}?post_id={post_id}"
    comment.delete()
    return redirect(url)
