from django.urls import reverse_lazy
from django.views.decorators.http import require_POST

from a_common import utils
from a_common.decorators import permission_or_staff_required
from a_common.prime_views import problem_views
from .. import models, forms, filters


class ProblemConfiguration:
    menu = 'daily'
    submenu = 'problem'
    info = {'menu': menu, 'menu_self': submenu}
    menu_title = {'kor': '데일리테스트', 'eng': menu.capitalize()}
    submenu_title = {'kor': '오답 노트', 'eng': submenu.capitalize()}
    url_admin = reverse_lazy(f'admin:a_daily_problem_changelist')
    url_list = reverse_lazy(f'daily:problem-list')
    url_create_collection = reverse_lazy('daily:collection-create')


@permission_or_staff_required('a_daily.view_student', login_url='/')
def problem_list_view(request: utils.HtmxHttpRequest):
    config = ProblemConfiguration()
    return problem_views.problem_list_view(request, models, filters, config)


@permission_or_staff_required('a_daily.view_student', login_url='/')
def problem_detail_view(request: utils.HtmxHttpRequest, pk: int):
    config = ProblemConfiguration()
    return problem_views.problem_detail_view(request, pk, models, forms, config)


@require_POST
@permission_or_staff_required('a_daily.view_student', login_url='/')
def like_problem(request: utils.HtmxHttpRequest, pk: int):
    return problem_views.like_problem(request, pk, models)


@permission_or_staff_required('a_daily.view_student', login_url='/')
def rate_problem(request: utils.HtmxHttpRequest, pk: int):
    return problem_views.rate_problem(request, pk, models)


@permission_or_staff_required('a_daily.view_student', login_url='/')
def memo_problem(request: utils.HtmxHttpRequest, pk: int):
    return problem_views.memo_problem(request, pk, models, forms)


@require_POST
@permission_or_staff_required('a_daily.view_student', login_url='/')
def tag_problem(request: utils.HtmxHttpRequest, pk: int):
    return problem_views.tag_problem(request, pk, models)


@permission_or_staff_required('a_daily.view_student', login_url='/')
def collection_list_view(request: utils.HtmxHttpRequest):
    config = ProblemConfiguration()
    return problem_views.collection_list_view(request, models, config)


@permission_or_staff_required('a_daily.view_student', login_url='/')
def collection_create(request: utils.HtmxHttpRequest):
    return problem_views.collection_create(request, models, forms)


@permission_or_staff_required('a_daily.view_student', login_url='/')
def collection_detail_view(request: utils.HtmxHttpRequest, pk: int):
    return problem_views.collection_detail_view(request, pk, models, forms)


@permission_or_staff_required('a_daily.view_student', login_url='/')
def collect_problem(request: utils.HtmxHttpRequest, pk: int):
    return problem_views.collect_problem(request, pk, models)
