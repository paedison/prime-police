import json

from django.http import HttpResponse
from django.shortcuts import render
from django.urls import reverse_lazy
from django.utils import timezone
from django_htmx.http import reswap

from a_common.constants import icon_set
from a_common.decorators import permission_or_staff_required
from a_common.utils import HtmxHttpRequest, update_context_data
from . import answer_utils
from .. import models


class ViewConfiguration:
    menu = 'infinite'
    submenu = 'answer'
    info = {'menu': menu, 'menu_self': submenu}
    menu_title = {'kor': '무한반', 'eng': menu.capitalize()}
    submenu_title = {'kor': '답안 제출', 'eng': submenu.capitalize()}
    url_admin = reverse_lazy(f'admin:a_infinite_exam_changelist')
    url_list = reverse_lazy(f'infinite:answer-list')

    def __init__(self, answer_input=False):
        self.answer_input = answer_input


@permission_or_staff_required('a_weekly.view_student', login_url='/')
def list_view(request: HtmxHttpRequest):
    config = ViewConfiguration()
    current_time = timezone.now()
    qs_student = []

    student_list = {}
    if request.user.is_authenticated:
        qs_student = models.Student.objects.with_select_related().filter(user=request.user).order_by('-id')
        for qs_s in qs_student:
            student_list[qs_s.exam.round] = qs_s

    qs_exam = models.Exam.objects.order_by('-round')
    for qs_e in qs_exam:
        qs_e.student = student_list.get(qs_e.round)

    context = update_context_data(
        config=config, current_time=current_time,
        icon_menu=icon_set.ICON_MENU['daily'], students=qs_student,
        exams=qs_exam,
    )
    return render(request, 'a_infinite/answer_list.html', context)


@permission_or_staff_required('a_weekly.view_student', login_url='/')
def detail_view(request: HtmxHttpRequest, pk: int, student=None, is_for_print=False):
    config = ViewConfiguration()
    current_time = timezone.now()
    context = update_context_data(current_time=current_time, config=config)

    exam = models.Exam.objects.filter(pk=pk).first()
    if not exam:
        context = update_context_data(context, message='답안 제출 대상 시험이 아닙니다.', next_url=config.url_list)
        return render(request, 'a_infinite/redirect.html', context)
    if current_time < exam.page_opened_at:
        context = update_context_data(context, message='답안 제출 기간이 아닙니다.', next_url=config.url_list)
        return render(request, 'a_infinite/redirect.html', context)

    if student is None:
        student = models.Student.objects.infinite_qs_student_by_user_and_exam_with_answer_count(request.user, exam)
    if not student:
        student = models.Student.objects.create(exam=exam, user=request.user)
        models.Score.objects.create(student=student)
        models.Rank.objects.create(student=student)
        student = models.Student.objects.infinite_qs_student_by_user_and_exam_with_answer_count(request.user, exam)

    is_confirmed_data = answer_utils.get_is_confirmed_data(student)
    qs_student_answer = models.Answer.objects.infinite_qs_answer_by_student_with_predict_result(student)
    answer_data_set = answer_utils.get_input_answer_data_set(request)

    stat_data_total = answer_utils.get_dict_stat_data(student, is_confirmed_data, answer_data_set)
    # if current_time > exam.answer_official_opened_at:
    #     answer_utils.update_score_real(stat_data, qs_student_answer)

    stat_chart = answer_utils.get_dict_stat_chart(student, stat_data_total)
    score_frequency_list = models.Student.objects.filter(exam=exam).values_list('score__sum', flat=True)
    stat_frequency = answer_utils.get_dict_stat_frequency(student, score_frequency_list)

    data_answers = answer_utils.get_data_answers(qs_student_answer)

    context = update_context_data(
        context, exam=exam, head_title=f'{exam.get_round_display()} 성적표',
        icon_menu=icon_set.ICON_MENU['infinite'], icon_nav=icon_set.ICON_NAV,

        # tab variables for templates
        answer_tab=answer_utils.get_answer_tab(),

        # info_student: 수험 정보
        student=student,

        # sheet_score: 성적 결과
        stat_data_total=stat_data_total,

        # sheet_answer: 답안 확인
        data_answers=data_answers, is_confirmed_data=is_confirmed_data,

        # chart: 성적 분포 차트
        stat_chart=stat_chart, stat_frequency=stat_frequency, all_confirmed=is_confirmed_data[-1],
    )
    if is_for_print:
        return render(request, 'a_infinite/answer_print.html', context)
    return render(request, 'a_infinite/answer_detail.html', context)


def print_view(request: HtmxHttpRequest, pk: int, student=None):
    return detail_view(request, pk, student, True)


@permission_or_staff_required('a_weekly.view_student', login_url='/')
def answer_input_view(request: HtmxHttpRequest, pk: int, subject_field: str):
    config = ViewConfiguration()
    current_time = timezone.now()
    exam = models.Exam.objects.filter(pk=pk).first()
    # if not exam or not exam.is_active:
    #     return redirect('prime:predict-list')

    config.url_detail = exam.get_answer_detail_url()
    student = models.Student.objects.infinite_qs_student_by_user_and_exam_with_answer_count(request.user, exam)
    sub, subject, field_idx = answer_utils.get_field_vars()[subject_field]

    # time_schedule = answer_utils.get_time_schedule(exam).get(sub)
    # if current_time < time_schedule[0]:
    #     return redirect('prime:predict-detail', pk=pk)

    answer_data_set = answer_utils.get_input_answer_data_set(request)
    answer_data = answer_data_set[subject_field]

    # answer_submit
    if request.method == 'POST':
        try:
            no = int(request.POST.get('number'))
            ans = int(request.POST.get('answer'))
        except Exception as e:
            print(e)
            return reswap(HttpResponse(''), 'none')

        answer_temporary = {'no': no, 'ans': ans}
        context = update_context_data(subject=subject, answer=answer_temporary, exam=exam)
        response = render(request, 'a_infinite/snippets/answer_button.html', context)

        if 1 <= no <= answer_utils.PROBLEM_COUNT and 1 <= ans <= 5:
            answer_data[no - 1] = ans
            response.set_cookie('answer_data_set', json.dumps(answer_data_set), max_age=3600)
            return response
        else:
            print('Answer is not appropriate.')
            return reswap(HttpResponse(''), 'none')

    answer_student = [
        {'no': no, 'ans': ans} for no, ans in enumerate(answer_data, start=1)
    ]
    context = update_context_data(
        leet=exam, config=config, subject=subject,
        student=student, answer_student=answer_student,
        url_answer_confirm=exam.get_answer_confirm_url(subject_field),
    )
    return render(request, 'a_infinite/answer_input.html', context)


@permission_or_staff_required('a_weekly.view_student', login_url='/')
def answer_confirm_view(request: HtmxHttpRequest, pk: int, subject_field: str):
    exam = models.Exam.objects.filter(pk=pk).first()
    # if not exam or not exam.is_active:
    #     return redirect('prime:predict-list')

    student = models.Student.objects.infinite_qs_student_by_user_and_exam_with_answer_count(request.user, exam)
    sub, subject, field_idx = answer_utils.get_field_vars()[subject_field]

    if request.method == 'POST':
        answer_data_set = answer_utils.get_input_answer_data_set(request)
        answer_data = answer_data_set[subject_field]

        is_confirmed = all(answer_data)
        if is_confirmed:
            answer_utils.create_confirmed_answers(student, sub, answer_data)  # Answer 모델에 추가
            answer_utils.update_answer_count_after_confirm(exam, sub, answer_data)  # AnswerCount 모델 수정
            answer_utils.update_score_after_confirm(student, sub)  # Score 모델 수정

            qs_student = models.Student.objects.filter(exam=exam)
            answer_utils.update_rank_after_confirm(qs_student, student, subject_field)  # Rank 모델 수정
            answer_utils.update_statistics_after_confirm(student, subject_field)  # Statistics 모델 수정

        # Load student instance after save
        student = models.Student.objects.infinite_qs_student_by_user_and_exam_with_answer_count(request.user, exam)
        next_url = answer_utils.get_next_url_for_answer_input(student)

        context = update_context_data(header=f'{subject} 답안 제출', is_confirmed=is_confirmed, next_url=next_url)
        return render(request, 'a_infinite/snippets/modal_answer_confirmed.html', context)

    context = update_context_data(
        url_answer_confirm=exam.get_answer_confirm_url(subject_field),
        header=f'{subject} 답안을 제출하시겠습니까?', verifying=True)
    return render(request, 'a_infinite/snippets/modal_answer_confirmed.html', context)
