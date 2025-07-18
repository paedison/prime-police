from django.contrib.auth.decorators import login_not_required
from django.shortcuts import render, get_object_or_404
from django.urls import reverse_lazy
from django.utils import timezone

from a_common.constants import icon_set
from a_common.utils import HtmxHttpRequest, update_context_data
from a_official import models, forms
from a_official.utils.common_utils import *
from a_official.utils.predict.normal_utils import *


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
    list_ctx = NormalListContext(_request=request)
    context = update_context_data(
        current_time=timezone.now(),
        config=config,
        exams=list_ctx.get_qs_exams(),
        login_url=list_ctx.get_login_url(),
    )
    return render(request, 'a_official/predict_list.html', context)


def predict_detail_view(request: HtmxHttpRequest, pk: int, student=None):
    current_time = timezone.now()
    config = ViewConfiguration()
    exam = get_object_or_404(models.Exam.objects.select_related('predict_exam'), pk=pk)
    config.submenu_kor = f'{exam.get_year_display()} {config.submenu_kor}'

    context = update_context_data(
        current_time=current_time, config=config, exam=exam,
        sub_title=f'{exam.get_year_display()} 합격 예측',
    )

    exam_ctx = ExamContext(_exam=exam)
    redirect_ctx = RedirectContext(_request=request, _context=context)

    if not request.user.is_staff and exam_ctx.is_not_for_predict():
        return redirect_ctx.redirect_to_no_predict_exam()

    if student is None:
        student = models.PredictStudent.objects.annotated_student_for_normal_view(request.user, exam)
    if not student:
        return redirect_ctx.redirect_to_no_student()
    qs_student_answer = models.PredictAnswer.objects.filtered_by_exam_student(student)

    subject_variants = SubjectVariants(_selection=student.selection)
    context = update_context_data(
        context,
        student=student,
        predict_exam=exam.predict_exam,
        time_schedule=exam_ctx.get_time_schedule(),
        subject_vars=subject_variants.subject_vars,
        subject_vars_dict=subject_variants.subject_vars_dict,
        qs_student_answer=qs_student_answer,
    )

    temporary_answer_ctx = TemporaryAnswerContext(_request=request, _context=context)
    context = update_context_data(context, total_answer_set=temporary_answer_ctx.get_total_answer_set())

    answer_ctx = NormalDetailAnswerContext(_request=request, _context=context)
    is_confirmed_data = answer_ctx.is_confirmed_data
    context = update_context_data(context, is_confirmed_data=is_confirmed_data)

    statistics_ctx = NormalDetailStatisticsContext(_request=request, _context=context)
    stat_data = statistics_ctx.get_stat_data()

    chart_ctx = ChartContext(_stat_data=stat_data, _student=student)

    context = update_context_data(
        context,

        # sheet_score: 성적 예측
        is_analyzing=answer_ctx.is_analyzing(),
        stat_data=stat_data,

        # sheet_answer: 예상 정답 / 답안 확인
        answer_context=answer_ctx.get_normal_answer_context(),

        # chart: 성적 분포 차트
        stat_chart=chart_ctx.get_dict_stat_chart(),
        stat_frequency=chart_ctx.get_dict_stat_frequency(),
        all_confirmed=is_confirmed_data['총점'],
    )

    return render(request, 'a_official/predict_detail.html', context)


def predict_register_view(request: HtmxHttpRequest):
    config = ViewConfiguration()
    exam = get_object_or_404(models.Exam.objects.select_related('predict_exam'), year=2026)  # Queryset
    context = update_context_data(config=config, exam=exam)

    exam_ctx = ExamContext(_exam=exam)
    redirect_ctx = RedirectContext(_request=request, _context=context)

    # Redirect page
    if exam_ctx.is_not_for_predict():
        return redirect_ctx.redirect_to_no_predict_exam()

    student = models.PredictStudent.objects.filter(user=request.user, exam=exam)
    if student:
        return redirect_ctx.redirect_to_has_student()

    # Process register
    form = forms.PredictStudentForm()
    context = update_context_data(context, title=f'{exam.full_reference} 합격예측 수험정보 등록', form=form)

    if request.method == 'POST':
        form = forms.PredictStudentForm(request.POST)
        context = update_context_data(context, form=form)
        if form.is_valid():
            return NormalRegisterContext(_request=request, _context=context).process_register()
    return render(request, 'a_official/predict_register.html', context)


def predict_answer_input_view(request: HtmxHttpRequest, pk: int, subject_field: str):
    context, redirect_ctx, redirect_response = prepare_exam_context(request, pk, subject_field)
    if redirect_response:
        return redirect_response

    answer_input_ctx = NormalAnswerInputContext(_request=request, _context=context)
    if answer_input_ctx.already_submitted():
        return redirect_ctx.redirect_to_already_submitted()

    if request.method == 'POST':
        return answer_input_ctx.process_post_request_to_answer_input()

    return render(request, 'a_official/predict_answer_input.html', context)


def predict_answer_confirm_view(request: HtmxHttpRequest, pk: int, subject_field: str):
    context, _, redirect_response = prepare_exam_context(request, pk, subject_field)
    if redirect_response:
        return redirect_response

    answer_confirm_ctx = NormalAnswerConfirmContext(_request=request, _context=context)
    if request.method == 'POST':
        return answer_confirm_ctx.process_post_request_to_answer_confirm()

    context = update_context_data(context, verifying=True, header=answer_confirm_ctx.get_header())
    return render(request, 'a_official/snippets/modal_answer_confirmed.html', context)


def prepare_exam_context(request: HtmxHttpRequest, pk: int, subject_field: str):
    config = ViewConfiguration()
    exam = models.Exam.objects.filter(pk=pk).select_related('predict_exam').first()
    config.url_detail = exam.get_predict_detail_url()
    url_answer_confirm = exam.get_predict_answer_confirm_url(subject_field)

    context = update_context_data(
        config=config, subject_field=subject_field, exam=exam, url_answer_confirm=url_answer_confirm)

    exam_ctx = ExamContext(_exam=exam)
    redirect_ctx = RedirectContext(_request=request, _context=context)

    if exam_ctx.is_not_for_predict():
        return None, None, redirect_ctx.redirect_to_no_predict_exam()
    if exam_ctx.get_before_exam_start():
        return None, None, redirect_ctx.redirect_to_before_exam_start()

    student = models.PredictStudent.objects.annotated_student_for_normal_view(request.user, exam)
    if not student:
        return None, None, redirect_ctx.redirect_to_no_student()

    subject_variants = SubjectVariants(_selection=student.selection)
    sub, subject, fld_idx, problem_count, score_per_problem = subject_variants.get_subject_variable(subject_field)

    context = update_context_data(
        context,
        subject_vars=subject_variants.subject_vars,
        sub=sub, subject=subject, fld_idx=fld_idx,
        problem_count=problem_count, score_per_problem=score_per_problem,
        student=student,
    )
    temporary_answer_ctx = TemporaryAnswerContext(_request=request, _context=context)
    context = update_context_data(
        context,
        total_answer_set=temporary_answer_ctx.get_total_answer_set(),
        answer_student_list=temporary_answer_ctx.get_answer_student_list_for_subject(),
        answer_student=temporary_answer_ctx.get_answer_student_for_subject(),
    )
    return context, redirect_ctx, None
