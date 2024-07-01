from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.utils import timezone

from a_common.constants import icon_set
from a_common.utils import HtmxHttpRequest, update_context_data
from a_predict import forms as predict_forms
from .base_info import ExamInfo


def index_view(request: HtmxHttpRequest):
    ei = ExamInfo()
    exam = ei.qs_exam.first()

    if not request.user.is_authenticated:
        return render(request, 'a_predict/index.html', {})

    student = ei.get_obj_student(request=request)
    if not student:
        return redirect('predict:student-create')

    info = {
        'menu': 'predict',
        'view_type': 'predict',
    }

    data_answer_official = ei.get_dict_data_answer_official(exam=exam)
    qs_answer_count = ei.qs_answer_count
    data_answer_rate = ei.get_dict_data_answer_rate(
        data_answer_official=data_answer_official,
        qs_answer_count=qs_answer_count,
    )

    data_answer_student, data_answer_count, data_answer_confirmed = (
        ei.get_tuple_data_answer_student(request=request, data_answer_rate=data_answer_rate)
    )
    data_answer_predict = ei.get_dict_data_answer_predict(
        data_answer_official=data_answer_official,
        qs_answer_count=qs_answer_count,
    )

    info_answer_student = ei.get_dict_info_answer_student(
        data_answer_student=data_answer_student,
        data_answer_count=data_answer_count,
        data_answer_confirmed=data_answer_confirmed,
        data_answer_official=data_answer_official,
        data_answer_predict=data_answer_predict,
    )

    stat_total_all = ei.get_dict_stat_data(student=student, statistics_type='total')
    stat_department_all = ei.get_dict_stat_data(student=student, statistics_type='department')
    stat_total_filtered = ei.get_dict_stat_data(
        student=student, statistics_type='total', exam=exam)
    stat_department_filtered = ei.get_dict_stat_data(
        student=student, statistics_type='department', exam=exam)

    context = update_context_data(
        # base info
        info=info,
        exam=exam,
        current_time=timezone.now(),

        # icons
        icon_menu=icon_set.ICON_MENU['predict'],
        icon_subject=icon_set.ICON_SUBJECT,
        icon_nav=icon_set.ICON_NAV,

        # index_info_student: 수험 정보
        student=student,
        location=ei.get_obj_location(student=student),

        # index_info_answer: 답안 제출 현황
        info_answer_student=info_answer_student,

        # index_sheet_answer: 답안 확인
        data_answer_official=data_answer_official,
        data_answer_predict=data_answer_predict,
        data_answer_student=data_answer_student,

        # index_sheet_score: 성적 예측 I [전체 데이터]
        stat_total_all=stat_total_all,
        stat_department_all=stat_department_all,

        # index_sheet_score_filtered: 성적 예측 II [정답 공개 전 데이터]
        stat_total_filtered=stat_total_filtered,
        stat_department_filtered=stat_department_filtered,
    )
    return render(request, 'a_predict/index.html', context)


@login_required
def student_create_view(request: HtmxHttpRequest):
    ei = ExamInfo()
    student = ei.get_obj_student(request=request)
    if student:
        return redirect('predict:index')

    if request.method == "POST":
        form = predict_forms.StudentForm(request.POST)
        if form.is_valid():
            student = form.save(commit=False)
            ei.create_student(student=student, request=request)
        else:
            pass
        first_sub = '헌법' if '헌법' in ei.PROBLEM_COUNT.keys() else '언어'
        return redirect('predict:answer-input', first_sub)

    else:
        form = predict_forms.StudentForm()

    units = ei.qs_unit.values_list('unit', flat=True)
    context = update_context_data(
        # base info
        info=ei.INFO,
        exam=ei.EXAM,
        current_time=timezone.now(),

        # icons
        icon_menu=icon_set.ICON_MENU['predict'],
        icon_subject=icon_set.ICON_SUBJECT,
        icon_nav=icon_set.ICON_NAV,

        # index_info_student: 수험 정보
        units=units,
        form=form,
    )

    return render(request, 'a_predict/student_create.html', context)


@login_required
def department_list(request):
    if request.method == 'POST':
        ei = ExamInfo()
        unit = request.POST.get('unit')
        departments = ei.qs_department.filter(unit=unit).values_list('department', flat=True)
        context = update_context_data(departments=departments)
        return render(request, 'a_predict/snippets/department_list.html', context)


@login_required
def answer_input_view(request, sub):
    ei = ExamInfo()

    if sub not in ei.PROBLEM_COUNT.keys():
        return redirect('predict:index')

    student = ei.get_obj_student(request=request)
    if not student:
        return redirect('predict:student-create')

    field = ei.SUBJECT_VARS[sub][1]
    is_confirmed = ei.get_obj_student_answer(request=request).answer_confirmed[field]
    if is_confirmed:
        return redirect('predict:index')

    answer_student_list = ei.get_list_answer_temp(request=request, sub=sub)

    context = update_context_data(
        info=ei.INFO, exam=ei.EXAM, sub=sub, answer_student=answer_student_list)
    return render(request, 'a_predict/answer_input.html', context)


@login_required
def answer_submit(request, sub):
    if request.method == 'POST':
        ei = ExamInfo()
        submitted_answer = ei.create_submitted_answer(request, sub)
        context = update_context_data(sub=sub, submitted_answer=submitted_answer)
        return render(request, 'a_predict/snippets/submitted_answer_form.html', context)


@login_required
def answer_confirm(request, sub):
    if request.method == 'POST':
        ei = ExamInfo()
        subject, field = ei.SUBJECT_VARS[sub]

        student_answer = ei.get_obj_student_answer(request=request)
        answer_string, is_confirmed = ei.get_tuple_answer_string_confirm(request=request, sub=sub)
        if is_confirmed:
            setattr(student_answer, field, answer_string)
            setattr(student_answer, f'{field}_confirmed', is_confirmed)
            student_answer.save()

        next_url = ei.get_str_next_url(student_answer=student_answer)

        context = update_context_data(
            header=f'{subject} 답안 제출',
            is_confirmed=is_confirmed,
            next_url=next_url,
        )
        return render(request, 'a_predict/snippets/modal_answer_confirmed.html', context)
    else:
        return redirect('predict:answer-input', sub)
