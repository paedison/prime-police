from django.urls import reverse_lazy

from a_common import utils
from a_common.decorators import permission_or_staff_required
from a_common.prime_views import answer_views
from .. import models, filters


class AnswerConfiguration:
    menu = 'weekly'
    submenu = 'answer'
    info = {'menu': menu, 'menu_self': submenu}
    menu_title = {'kor': '주간모의고사', 'eng': menu.capitalize()}
    submenu_title = {'kor': '답안 제출', 'eng': submenu.capitalize()}
    url_admin = reverse_lazy(f'admin:a_weekly_exam_changelist')
    url_list = reverse_lazy(f'weekly:answer-list')


@permission_or_staff_required('a_weekly.view_student', login_url='/')
def answer_list_view(request: utils.HtmxHttpRequest):
    config = AnswerConfiguration()
    return answer_views.answer_list_view(request, models, filters, config)


@permission_or_staff_required('a_weekly.view_student', login_url='/')
def answer_detail_view(request: utils.HtmxHttpRequest, pk: int):
    config = AnswerConfiguration()
    return answer_views.answer_detail_view(request, pk, models, config)


@permission_or_staff_required('a_weekly.view_student', login_url='/')
def answer_input_view(request: utils.HtmxHttpRequest, pk: int):
    config = AnswerConfiguration()
    return answer_views.answer_input_view(request, pk, models, config)


@permission_or_staff_required('a_weekly.view_student', login_url='/')
def answer_confirm_view(request: utils.HtmxHttpRequest, pk: int):
    config = AnswerConfiguration()
    return answer_views.answer_confirm_view(request, pk, models, config)


@permission_or_staff_required('a_weekly.view_student', login_url='/')
def rank_verify(request: utils.HtmxHttpRequest, pk: int):
    return answer_views.rank_verify(request, pk, models)
