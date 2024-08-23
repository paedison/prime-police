from datetime import date

from django.db.models import F, Max, Case, When, BooleanField, Value
from django.db.models.functions import Coalesce
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.decorators.http import require_POST

from a_common.constants import icon_set
from a_common.utils import HtmxHttpRequest, update_context_data
from .. import models, utils, forms, filters


def answer_list_view(request: HtmxHttpRequest):
    view_type = request.headers.get('View-Type', '')

    exam_circle = request.GET.get('circle', '')
    exam_round = request.GET.get('round', '')
    exam_subject = request.GET.get('subject', '')
    page = request.GET.get('page', '1')
    filterset = filters.DailyExamFilter(data=request.GET, request=request)

    info = {'menu': 'daily', 'menu_self': 'answer'}
    sub_title = utils.get_sub_title(exam_circle, exam_round, exam_subject, end_string='답안 제출 현황')

    page_obj, page_range = utils.get_page_obj_and_range(page, filterset.qs)
    for exam in page_obj:
        exam_info = {
            'semester': exam.semester,
            'circle': exam.circle,
            'subject': exam.subject,
            'round': exam.round,
        }
        student = models.Student.objects.filter(**exam_info).first()
        exam.detail_url = ''
        if student:
            exam.detail_url = reverse_lazy('daily:answer-detail', args=[exam.id])

    context = update_context_data(
        info=info, title='데일리테스트', sub_title=sub_title, form=filterset.form,
        icon_menu=icon_set.ICON_MENU['daily'],
        page_obj=page_obj, page_range=page_range,
    )
    if view_type == 'problem_list':
        template_name = 'a_daily/answer_list.html#list_content'
        return render(request, template_name, context)
    return render(request, 'a_daily/answer_list.html', context)


def answer_detail_view(request: HtmxHttpRequest, pk: int):
    # view_type = request.headers.get('View-Type', '')
    info = {'menu': 'daily', 'menu_self': 'answer'}
    exam = get_object_or_404(models.Exam, pk=pk)
    exam_info = {
        'semester': models.semester_default(),
        'circle': exam.circle,
        'subject': exam.subject,
        'round': exam.round,
    }

    student = models.Student.objects.filter(**exam_info).first()
    if not student:
        return redirect('daily:answer-list')

    sub_title = f'{exam.full_reference} - 성적 확인'
    context = update_context_data(
        info=info, title='데일리테스트', sub_title=sub_title, exam=exam, student=student,
        icon_menu=icon_set.ICON_MENU['daily'],
        icon_question=icon_set.ICON_QUESTION,
        icon_nav=icon_set.ICON_NAV,
        icon_board=icon_set.ICON_BOARD,
    )
    return render(request, 'a_daily/answer_detail.html', context)


def answer_input_view():
    pass


def answer_confirm_view():
    pass
