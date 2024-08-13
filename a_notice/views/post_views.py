from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, get_object_or_404

from a_common.constants import icon_set
from a_common.utils import update_context_data, HtmxHttpRequest
from a_notice import models, utils
from a_notice.views import viewmixins


def get_queryset(request):
    queryset = models.Post.objects.all()
    if not request.user.is_authenticated or not request.user.is_staff:
        queryset = queryset.filter(is_hidden=False)
    return queryset


def list_view(request: HtmxHttpRequest):
    info = {'menu': 'notice'}
    page_number = request.GET.get('page', '1')
    queryset = get_queryset(request)
    page_obj, page_range = utils.get_paginator_info(queryset, page_number)
    top_fixed = utils.get_filtered_queryset(request, top_fixed=True)
    context = update_context_data(
        info=info,
        icon_menu=icon_set.ICON_MENU['notice'],
        icon_board=icon_set.ICON_BOARD,
        page_obj=page_obj,
        page_range=page_range,
        top_fixed=top_fixed,
    )
    return render(request, 'a_notice/post_list.html', context)


def detail_view(request: HtmxHttpRequest, pk: int):
    view_type = request.headers.get('View-Type', '')
    info = {'menu': 'notice'}
    queryset = get_queryset(request)
    post = get_object_or_404(queryset, pk=pk)
    prev_post, next_post = utils.get_prev_next_post(queryset, post)
    context = update_context_data(
        info=info,
        icon_menu=icon_set.ICON_MENU['notice'],
        icon_board=icon_set.ICON_BOARD,
        post=post, prev_post=prev_post, next_post=next_post,
    )
    return render(request, 'a_notice/post_detail.html', context)


class PostCreateView(
    LoginRequiredMixin,
    viewmixins.PostViewMixin,
    # vanilla.CreateView,
):
    view_type = 'post_create'

    def get_template_names(self):
        htmx_template = {
            'False': self.templates['create_template'],
            'True': self.templates['create_main_template'],
        }
        return htmx_template[f'{bool(self.request.htmx)}']

    def get_success_url(self):
        return self.get_detail_url()

    def get_context_data(self, **kwargs):
        self.get_properties()

        context = super().get_context_data(**kwargs)
        context.update({
            'info': self.info,
            'icon': self.base_icon,
        })
        return context


class PostUpdateView(
    LoginRequiredMixin,
    viewmixins.PostViewMixin,
    # vanilla.UpdateView,
):
    view_type = 'post_update'

    def get_template_names(self):
        htmx_template = {
            'False': self.templates['create_template'],
            'True': self.templates['create_main_template'],
        }
        return htmx_template[f'{bool(self.request.htmx)}']

    def get_success_url(self):
        return self.get_detail_url()

    def get_context_data(self, **kwargs):
        self.get_properties()

        context = super().get_context_data(**kwargs)
        context.update({
            'info': self.info,
            'icon': self.base_icon,
            'post_update_url': self.urls['post_update_url']
        })
        return context


class PostDeleteView(
    LoginRequiredMixin,
    viewmixins.PostViewMixin,
    # vanilla.DeleteView,
):
    view_type = 'post_delete'

    def get_success_url(self):
        return self.get_list_url()


create_view = PostCreateView
update_view = PostUpdateView
delete_view = PostDeleteView
