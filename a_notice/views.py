from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.decorators.http import require_POST

from a_common.constants import icon_set
from a_common.utils import update_context_data, HtmxHttpRequest
from a_notice import models, utils, forms


def get_queryset(request):
    queryset = models.Post.objects.prefetch_related('post_comments')
    if not request.user.is_authenticated or not request.user.is_staff:
        queryset = queryset.filter(is_hidden=False)
    return queryset


def list_view(request: HtmxHttpRequest):
    info = {'menu': 'notice'}
    view_type = request.headers.get('View-Type', '')
    page_number = request.GET.get('page', '1')
    queryset = get_queryset(request)
    page_obj, page_range = utils.get_paginator_info(queryset, page_number)
    top_fixed = utils.get_filtered_queryset(request, top_fixed=True)
    context = update_context_data(
        info=info, view_type=view_type,
        icon_menu=icon_set.ICON_MENU['notice'],
        icon_board=icon_set.ICON_BOARD,
        page_obj=page_obj, page_range=page_range, top_fixed=top_fixed,
    )
    if view_type == 'notice_list':
        return render(request, 'a_notice/post_list_content.html', context)
    return render(request, 'a_notice/post_list.html', context)


def detail_view(request: HtmxHttpRequest, pk: int):
    view_type = request.headers.get('View-Type', '')
    info = {'menu': 'notice'}
    queryset = get_queryset(request)
    post = get_object_or_404(queryset, pk=pk)
    prev_post, next_post = utils.get_prev_next_post(queryset, post)
    context = update_context_data(
        info=info, view_type=view_type,
        icon_menu=icon_set.ICON_MENU['notice'], icon_board=icon_set.ICON_BOARD,
        post=post, prev_post=prev_post, next_post=next_post)
    return render(request, 'a_notice/post_detail.html', context)


def create_view(request: HtmxHttpRequest):
    info = {'menu': 'notice'}
    context = update_context_data(
        info=info, icon_menu=icon_set.ICON_MENU['notice'],
        icon_board=icon_set.ICON_BOARD)
    if request.method == 'POST':
        form = forms.PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.user = request.user
            post.save()
            return redirect('notice:detail', pk=post.id)
    form = forms.PostForm()
    post_url = reverse_lazy('notice:create')
    context = update_context_data(
        context, form=form, sub_title='공지사항 작성',
        post_url=post_url, message='입력')
    return render(request, 'a_notice/post_create.html', context)


def update_view(request: HtmxHttpRequest, pk: int):
    info = {'menu': 'notice'}
    instance = get_object_or_404(models.Post, pk=pk)
    context = update_context_data(
        info=info, icon_menu=icon_set.ICON_MENU['notice'],
        icon_board=icon_set.ICON_BOARD)
    if request.method == 'POST':
        form = forms.PostForm(request.POST, instance=instance)
        if form.is_valid():
            notice = form.save()
            return redirect('notice:detail', pk=notice.id)
    form = forms.PostForm(instance=instance)
    context = update_context_data(
        context, form=form, sub_title='공지사항 수정',
        post_url=instance.get_update_url(), message='수정')
    return render(request, 'a_notice/post_create.html', context)


@require_POST
def delete_view(request: HtmxHttpRequest, pk: int):
    instance = get_object_or_404(models.Post, pk=pk)
    instance.delete()
    return redirect('notice:base')


def comment_list_view(request: HtmxHttpRequest):
    pass


def comment_create_view(request: HtmxHttpRequest):
    pass


def comment_update_view(request: HtmxHttpRequest):
    pass


def comment_delete_view(request: HtmxHttpRequest):
    pass
