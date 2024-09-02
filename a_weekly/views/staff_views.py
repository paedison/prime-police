from django.urls import reverse_lazy

from a_common.prime_test import staff_views
from .. import forms, models


class AnswerConfiguration:
    menu = 'weekly'
    submenu = 'staff'
    info = {'menu': menu, 'menu_self': submenu}
    menu_title = {'kor': '주간모의고사', 'eng': menu.capitalize()}
    submenu_title = {'kor': '관리자 메뉴', 'eng': submenu.capitalize()}
    url_admin = reverse_lazy('admin:a_weekly_exam_changelist')
    url_admin_exam_list = reverse_lazy('admin:a_weekly_exam_changelist')
    url_admin_problem_list = reverse_lazy('admin:a_weekly_exam_changelist')
    url_list = reverse_lazy('weekly:staff-menu')
    url_exam_create = reverse_lazy('weekly:staff-exam-create')


def menu_list_view(request):
    config = AnswerConfiguration()
    return staff_views.menu_list_view(request, config)


def exam_create_view(request):
    config = AnswerConfiguration()
    return staff_views.exam_create_view(request, models, forms, config)
