from django.core.paginator import Paginator, EmptyPage

from a_common.models import User
from a_common.utils import HtmxHttpRequest
from . import models
from .filters import AnonymousOfficialListFilter, OfficialListFilter


def get_filterset(request: HtmxHttpRequest):
    logged_in = request.user.is_authenticated
    list_filter = OfficialListFilter if logged_in else AnonymousOfficialListFilter
    return list_filter(data=request.GET, request=request)


def get_page_added_path(request: HtmxHttpRequest, page: int):
    curr_path = request.get_full_path()
    if 'page=' not in curr_path:
        curr_path += '&page=1' if '?' in curr_path else '?page=1'
    next_path = curr_path.replace(f'page={page}', f'page={page + 1}')
    return {
        'curr_path': curr_path,
        'next_path': next_path,
    }


def get_elided_page_range(
        request, filterset=None, number=None, num_pages=None,
        *, on_each_side=5, on_ends=1
):
    if filterset is None:
        filterset = get_filterset(request)
    if number is None:
        number = int(request.GET.get('page', 1))
    if num_pages is None:
        num_pages = filterset.qs.count() // 10 + 1
    page_range = range(1, num_pages + 1)

    _ellipsis = "…"
    if num_pages <= (on_each_side + on_ends) * 2:
        yield from page_range
        return

    if number > (1 + on_each_side + on_ends) + 1:
        yield from range(1, on_ends + 1)
        yield _ellipsis
        yield from range(number - on_each_side, number + 1)
    else:
        yield from range(1, number + 1)

    if number < (num_pages - on_each_side - on_ends) - 1:
        yield from range(number + 1, number + on_each_side + 1)
        yield _ellipsis
        yield from range(num_pages - on_ends + 1, num_pages + 1)
    else:
        yield from range(number + 1, num_pages + 1)


def get_customized_problems(request, model):
    return model.objects.select_related('problem', 'user').filter(user=request.user)


def get_page_obj_and_range(page_number, page_data, per_page=10):
    paginator = Paginator(page_data, per_page)
    try:
        page_obj = paginator.page(page_number)
        page_range = paginator.get_elided_page_range(number=page_number, on_each_side=3, on_ends=1)
        return page_obj, page_range
    except TypeError:
        return None, None
    except EmptyPage:
        return None, None


def get_custom_data(user: User) -> dict:
    return {
        'like': models.ProblemLike.objects.filter(user=user).values_list('problem_id', 'is_liked'),
        'rate': models.ProblemRate.objects.filter(user=user).values_list('problem_id', 'rating'),
        'solve': models.ProblemSolve.objects.filter(user=user).values_list('problem_id', 'is_correct'),
        'memo': models.ProblemMemo.objects.filter(user=user).values_list('problem_id'),
        'tag': models.ProblemTaggedItem.objects.filter(user=user).values_list('content_object_id'),
        'collection': models.ProblemCollectionItem.objects.filter(collection__user=user).values_list('problem_id'),
    }
