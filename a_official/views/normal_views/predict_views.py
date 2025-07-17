from django.contrib.auth.decorators import login_not_required
from django.shortcuts import render
from django.urls import reverse_lazy
from django.utils import timezone

from a_official import models, forms
from a_official.utils import ExamData, SubjectVariants
from a_official.utils.predict.normal_utils import *
from a_common.constants import icon_set
from a_common.utils import HtmxHttpRequest, update_context_data
from a_official.utils.predict.normal_utils import NormalRedirect, TemporaryAnswerData


class ViewConfiguration:
    current_time = timezone.now()

    menu = menu_eng = 'official'
    menu_kor = '경위공채'
    submenu = submenu_eng = 'predict'
    submenu_kor = '합격예측'

    info = {'menu': menu, 'menu_self': submenu}
    icon_menu = icon_set.ICON_MENU[menu_eng]
    menu_title = {'kor': menu_kor, 'eng': menu.capitalize()}
    submenu_title = {'kor': submenu_kor, 'eng': submenu.capitalize()}

    url_admin = reverse_lazy('admin:a_official_exam_changelist')
    url_list = reverse_lazy('official:predict-list')
    url_register = reverse_lazy('official:predict-register')


@login_not_required
def predict_list_view(request: HtmxHttpRequest):
    config = ViewConfiguration()
    list_data = NormalListData(_request=request)
    context = update_context_data(
        current_time=timezone.now(),
        config=config,
        **list_data.get_exams_context(),
        **list_data.get_login_url_context(),
    )
    return render(request, 'a_official/predict_list.html', context)


@login_not_required
def predict_detail_view(request: HtmxHttpRequest, pk: int, student=None):
    current_time = timezone.now()
    config = ViewConfiguration()
    exam = models.Exam.objects.filter(pk=pk).select_related('predict_exam').first()
    config.submenu_kor = f'{exam.get_year_display()} {config.submenu_kor}'
    context = update_context_data(current_time=current_time, config=config, exam=exam)

    exam_data = ExamData(_exam=exam)
    redirect_data = NormalRedirect(_request=request, _context=context)

    if exam_data.is_not_for_predict:
        return redirect_data.redirect_to_no_predict_exam()

    if student is None:
        student = models.PredictStudent.objects.annotated_student_for_normal_view(request.user, exam)
    if not student:
        return redirect_data.redirect_to_no_student()

    subject_variants = SubjectVariants(_selection=student.selection)
    context = update_context_data(
        context, student=student,
        time_schedule=exam_data.get_time_schedule(),
        subject_vars_dict=subject_variants.subject_vars_dict
    )

    detail_data = NormalDetailData(_request=request, _context=context)
    context = update_context_data(
        context,
        sub_title=f'{exam.get_year_display()} 합격 예측',
        predict_exam=exam.predict_exam,

        # info_student: 수험 정보
        student=student,

        # sheet_score: 성적 예측
        is_analyzing=detail_data.is_analyzing(),
        stat_data=detail_data.stat_data,

        # sheet_answer: 예상 정답 / 답안 확인
        answer_context=detail_data.get_normal_answer_context(),

        # chart: 성적 분포 차트
        stat_chart=detail_data.chart_data.get_dict_stat_chart(),
        stat_frequency=detail_data.chart_data.get_dict_stat_frequency(),
        all_confirmed=detail_data.is_confirmed_data['총점'],
    )

    # if detail_data.view_type == 'info_answer':
    #     return render(request, 'a_official/snippets/predict_update_info_answer.html', context)
    # if detail_data.view_type == 'score_all':
    #     return render(request, 'a_official/snippets/predict_update_sheet_score.html', context)
    # if detail_data.view_type == 'answer_submit':
    #     return render(request, 'a_official/snippets/predict_update_sheet_answer_submit.html', context)
    # if detail_data.view_type == 'answer_predict':
    #     return render(request, 'a_official/snippets/predict_update_sheet_answer_predict.html', context)
    return render(request, 'a_official/predict_detail.html', context)


@login_not_required
def predict_register_view(request: HtmxHttpRequest):
    config = ViewConfiguration()
    form_class = forms.PredictStudentForm
    form = form_class()
    context = update_context_data(config=config)

    redirect_data = NormalRedirect(_request=request, _context=context)
    register_data = NormalRegisterData(_request=request, _context=context, _form=form)

    if register_data.is_not_for_predict:
        return redirect_data.redirect_to_no_predict_exam()
    if register_data.has_student:
        return redirect_data.redirect_to_has_student()

    context = update_context_data(context, title=register_data.title, form=form)

    if request.method == 'POST':
        form = form_class(request.POST)
        register_data.set_form(form)
        if form.is_valid():
            return register_data.process_register(context)
        context = update_context_data(context, form=form)
    return render(request, 'a_official/predict_register.html', context)


def prepare_exam_context(request: HtmxHttpRequest, pk: int, subject_field: str):
    config = ViewConfiguration()
    exam = models.Exam.objects.filter(pk=pk).select_related('predict_exam').first()
    config.url_detail = exam.get_predict_detail_url()
    context = update_context_data(config=config, subject_field=subject_field, exam=exam)

    exam_data = ExamData(_exam=exam)
    redirect_data = NormalRedirect(_request=request, _context=context)

    if exam_data.get_is_not_for_predict():
        return None, redirect_data.redirect_to_no_predict_exam()
    if exam_data.get_before_exam_start():
        return None, redirect_data.redirect_to_before_exam_start()

    student = models.PredictStudent.objects.annotated_student_for_normal_view(request.user, exam)
    if not student:
        return None, redirect_data.redirect_to_no_student()

    subject_variants = SubjectVariants(_selection=student.selection)
    sub, subject, fld_idx, problem_count, score_per_problem = subject_variants.get_subject_variable(subject_field)

    context = update_context_data(
        context,
        sub=sub, subject=subject, fld_idx=fld_idx,
        problem_count=problem_count, score_per_problem=score_per_problem,
        subject_vars=subject_variants.subject_vars,
        student=student,
    )
    return {
        'exam': exam,
        'context': context,
        'student': student,
        'exam_data': exam_data,
        'redirect_data': redirect_data,
    }, None


@login_not_required
def predict_answer_input_view(request: HtmxHttpRequest, pk: int, subject_field: str):
    result, redirect_response = prepare_exam_context(request, pk, subject_field)
    if redirect_response:
        return redirect_response

    temporary_answer_data = TemporaryAnswerData(_request=request, _context=result['context'])
    answer_input_data = NormalAnswerInputData(
        _request=request, _context=result['context'],
        _temporary_answer_data=temporary_answer_data
    )

    if answer_input_data.already_submitted():
        return result['redirect_data'].redirect_to_already_submitted()

    if request.method == 'POST':
        return answer_input_data.process_post_request_to_answer_input()

    context = update_context_data(
        result['context'],
        answer_student=temporary_answer_data.get_answer_student_list_for_subject(),
        url_answer_confirm=result['exam'].get_predict_answer_confirm_url(subject_field),
    )
    return render(request, 'a_official/predict_answer_input.html', context)


@login_not_required
def predict_answer_confirm_view(request: HtmxHttpRequest, pk: int, subject_field: str):
    result, redirect_response = prepare_exam_context(request, pk, subject_field)
    if redirect_response:
        return redirect_response

    temporary_answer_data = TemporaryAnswerData(_request=request, _context=result['context'])
    answer_confirm_data = NormalAnswerConfirmData(
        _request=request, _context=result['context'],
        _temporary_answer_data=temporary_answer_data,
        time_schedule=result['exam_data'].get_time_schedule()
    )
    if request.method == 'POST':
        return answer_confirm_data.process_post_request_to_answer_confirm()

    context = update_context_data(
        result['context'],
        verifying=True,
        header=answer_confirm_data.get_header(),
        url_answer_confirm=result['exam'].get_predict_answer_confirm_url(subject_field),
    )
    return render(request, 'a_official/snippets/modal_answer_confirmed.html', context)
#
#
# def predict_answer_confirm_view(request: HtmxHttpRequest, pk: int, subject_field: str):
#     result, redirect_response = prepare_exam_context(request, pk, subject_field)
#     if redirect_response:
#         return redirect_response
#
#     temporary_answer_data = TemporaryAnswerData(_request=request, _context=result['context'])
#     config = ViewConfiguration()
#     context = update_context_data(config=config)
#
#     exam = models.Exam.objects.filter(pk=pk).first()
#     redirect_data = NormalRedirect(_request=request, _context=context)
#     answer_data = NormalAnswerConfirmData(_request=request, _exam=exam, _subject_field=subject_field)
#
#     if answer_data.is_not_for_predict:
#         return redirect_data.redirect_to_no_predict_exam()
#     if answer_data.no_student:
#         return redirect_data.redirect_to_no_student()
#
#     config.url_detail = exam.get_predict_detail_url()
#     if config.current_time < exam.predict_exam.exam_started_at:
#         context = update_context_data(context, message='시험 시작 전입니다.', next_url=config.url_detail)
#         return render(request, 'a_official/redirect.html', context)
#
#     answer_data = NormalAnswerConfirmData(_request=request, _exam=exam, _subject_field=subject_field)
#     if request.method == 'POST':
#         return answer_data.process_post_request_to_answer_confirm()
#
#     context = update_context_data(
#         url_answer_confirm=exam.get_predict_answer_confirm_url(subject_field),
#         header=answer_data.get_header(), verifying=True)
#     return render(request, 'a_official/snippets/modal_answer_confirmed.html', context)
