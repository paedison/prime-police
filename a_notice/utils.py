from django.core.paginator import Paginator

from . import models


def get_filtered_queryset(request, top_fixed: bool = False):
    """ Get filtered queryset for list view. """
    fq = models.Post.objects.filter(top_fixed=top_fixed)
    if not request.user.is_authenticated or not request.user.is_staff:
        fq = fq.filter(is_hidden=False)
    return fq


def get_paginator_info(request) -> tuple:
    """ Get paginator, elided page range for list view. """
    queryset = get_filtered_queryset(request)
    page_number = request.GET.get('page', '1')
    paginator = Paginator(queryset, 10)
    page_obj = paginator.get_page(page_number)
    page_range = paginator.get_elided_page_range(number=page_number, on_each_side=3, on_ends=1)
    return page_obj, page_range
