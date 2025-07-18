from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy

from a_common.constants import icon_set
from a_common.decorators import staff_required
from a_common.utils import HtmxHttpRequest, update_context_data
from a_official import models, forms
from a_official.utils.common_utils import *
from a_official.utils.predict.staff_utils import *
from a_official.views.normal_views import predict_views


class ViewConfiguration:
    menu = menu_eng = 'official_staff'
    menu_kor = '경위공채'
    submenu = submenu_eng = 'predict'
    submenu_kor = '합격예측'

    info = {'menu': menu, 'menu_self': submenu}
    icon_menu = icon_set.ICON_MENU[menu_eng]
    menu_title = {'kor': menu_kor, 'eng': menu.capitalize()}
    submenu_title = {'kor': submenu_kor, 'eng': submenu.capitalize()}

    url_admin = reverse_lazy(f'admin:a_official_problem_changelist')
    url_admin_exam_list = reverse_lazy('admin:a_official_exam_changelist')
    url_admin_problem_list = reverse_lazy('admin:a_official_problem_changelist')

    url_list = reverse_lazy('official:staff-predict-list')
    # url_problem_update = reverse_lazy('official:staff-official-update')

    url_predict_create = reverse_lazy('official:staff-predict-create')


@staff_required
def predict_list_view(request: HtmxHttpRequest):
    config = ViewConfiguration()
    list_ctx = AdminListContext(_request=request)
    context = update_context_data(config=config, predict_exam_context=list_ctx.get_predict_exam_context())

    if list_ctx.view_type == 'predict_exam_list':
        return render(request, f'a_official/staff_predict_list.html#study_category_list', context)  # noqa
    return render(request, 'a_official/staff_predict_list.html', context)


@staff_required
def predict_detail_view(request: HtmxHttpRequest, pk: int):
    config = ViewConfiguration()
    config.url_staff_predict_update = reverse_lazy('official:staff-predict-update', args=[pk])
    exam = get_object_or_404(models.Exam.objects.select_related('predict_exam'), pk=pk)

    context = update_context_data(config=config, exam=exam)

    exam_ctx = ExamContext(_exam=exam)
    redirect_ctx = RedirectContext(_request=request, _context=context)
    if exam_ctx.is_not_for_predict():
        return redirect_ctx.redirect_to_no_predict_exam()

    subject_variants = SubjectVariants(_selection='')
    request_ctx = RequestContext(_request=request)

    context = update_context_data(
        context,
        predict_exam=exam.predict_exam,
        icon_nav=icon_set.ICON_NAV,
        icon_search=icon_set.ICON_SEARCH,
        page_number=request_ctx.page_number,
        student_name=request_ctx.student_name,
        subject_vars_dict=subject_variants.subject_vars_dict,
        qs_problem=models.Problem.objects.filtered_problem_by_exam(exam),
        qs_answer_count=models.PredictAnswerCount.objects.filtered_by_exam_and_subject(exam),
    )

    problem_ctx = AdminDetailProblemContext(_request=request, _context=context)
    statistics_ctx = AdminDetailStatisticsContext(_context=context)
    catalog_ctx = AdminDetailCatalogContext(_context=context)
    answer_ctx = AdminDetailAnswerContext(_context=context)

    if request_ctx.view_type == 'problem_list':
        context = update_context_data(context, problem_context=problem_ctx.get_problem_context())
        return render(request, 'a_official/problem_list_content.html', context)

    if request_ctx.view_type == 'catalog_list':
        context = update_context_data(context, catalog_context=catalog_ctx.get_catalog_context())
        return render(request, 'a_official/snippets/staff_predict_detail_catalog.html', context)

    if request_ctx.view_type == 'student_search':
        context = update_context_data(
            context, catalog_context=catalog_ctx.get_catalog_context(for_search=True))
        return render(request, 'a_official/snippets/staff_predict_detail_catalog.html', context)

    if request_ctx.view_type == 'answer_list':
        context = update_context_data(context, answer_context=answer_ctx.get_answer_context())
        return render(request, 'a_official/snippets/staff_predict_detail_answer_analysis.html', context)

    context = update_context_data(
        context,
        problem_context=problem_ctx.get_problem_context(),
        answer_predict_context=problem_ctx.get_answer_predict_context(),
        answer_official_context=problem_ctx.get_answer_official_context(),
        statistics_context=statistics_ctx.get_statistics_context(),
        catalog_context=catalog_ctx.get_catalog_context(),
        answer_context=answer_ctx.get_answer_context(),
    )
    return render(request, 'a_official/staff_predict_detail.html', context)


@staff_required
def predict_create_view(request: HtmxHttpRequest):
    config = ViewConfiguration()
    title = '합격 예측 새 시험 등록'
    context = update_context_data(config=config, title=title)

    if request.method == 'POST':
        form = forms.PredictExamForm(request.POST, request.FILES)
        context = update_context_data(context, form=form)
        if form.is_valid():
            return AdminCreateContext(_context=context).process_post_request()
        return render(request, 'a_official/staff_form.html', context)

    form = forms.PredictExamForm()
    context = update_context_data(context, form=form)
    return render(request, 'a_official/staff_form.html', context)


@staff_required
def predict_update_view(request: HtmxHttpRequest, pk: int):
    exam = get_object_or_404(models.Exam.objects.select_related('predict_exam'), pk=pk)
    subject_variants = SubjectVariants(_selection='')
    context = update_context_data(
        exam=exam,
        next_url=exam.get_staff_predict_detail_url(),
        subject_vars_dict=subject_variants.get_subject_vars_dict(),
        subject_fields_dict=subject_variants.get_subject_fields_dict(),
    )

    view_type = request.headers.get('View-Type', '')
    if view_type == 'answer_official':
        answer_official_ctx = AdminUpdateAnswerOfficialContext(_request=request, _context=context)
        is_updated, message = answer_official_ctx.update_problem_model_for_answer_official()
        context = update_context_data(context, header='정답 업데이트', is_updated=is_updated, message=message)

    if view_type == 'score':
        is_updated, message = AdminUpdateScoreContext(_context=context).update_scores()
        context = update_context_data(context, header='점수 업데이트', is_updated=is_updated, message=message)

    if view_type == 'rank':
        is_updated, message = AdminUpdateRankContext(_context=context).update_ranks()
        context = update_context_data(context, header='등수 업데이트', is_updated=is_updated, message=message)

    if view_type == 'statistics':
        is_updated, message = AdminUpdateStatisticsContext(_context=context).update_statistics()
        context = update_context_data(context, header='통계 업데이트', is_updated=is_updated, message=message)

    if view_type == 'answer_count':
        is_updated, message = AdminUpdateAnswerCountContext(_context=context).update_answer_counts()
        context = update_context_data(context, header='문항분석표 업데이트', is_updated=is_updated, message=message)

    return render(request, 'a_official/snippets/staff_modal_predict_update.html', context)


@staff_required
def predict_student_detail_view(request: HtmxHttpRequest, pk: int):
    student: models.PredictStudent = models.PredictStudent.objects.filter(pk=pk).first()
    if student:
        student = models.PredictStudent.objects.exam_student_with_answer_count(student.user, student.exam)
        return predict_views.predict_detail_view(request, student.exam.id, student=student)
    return redirect('official:staff-predict-list')


@staff_required
def predict_statistics_print(request: HtmxHttpRequest, pk: int):
    exam = get_object_or_404(models.Exam, pk=pk)
    subject_variants = SubjectVariants(_selection='')
    context = update_context_data(exam=exam, subject_vars_dict=subject_variants.subject_vars_dict)
    statistics_ctx = AdminDetailStatisticsContext(_context=context)
    context = update_context_data(exam=exam, **statistics_ctx.get_statistics_context())
    return render(request, 'a_official/staff_print_statistics.html', context)


@staff_required
def predict_catalog_print(request: HtmxHttpRequest, pk: int):
    exam = get_object_or_404(models.Exam, pk=pk)
    student_list = models.PredictStudent.objects.filtered_student_by_exam(exam)
    context = update_context_data(exam=exam, student_list=student_list)
    return render(request, 'a_official/staff_print_catalog.html', context)


@staff_required
def predict_answer_print(request: HtmxHttpRequest, pk: int):
    exam = get_object_or_404(models.Exam, pk=pk)
    request_ctx = RequestContext(_request=request)
    subject_variants = SubjectVariants(_selection='')
    context = update_context_data(
        exam=exam, page_number=request_ctx.page_number,
        subject_vars_dict=subject_variants.subject_vars_dict
    )
    answer_ctx = AdminDetailAnswerContext(_context=context)
    context = update_context_data(exam=exam, answer_context=answer_ctx.get_answer_context(per_page=1000))
    return render(request, 'a_official/staff_print_answers.html', context)


@staff_required
def predict_statistics_excel(_: HtmxHttpRequest, pk: int):
    exam = get_object_or_404(models.Exam, pk=pk)
    return AdminExportExcelContext(_exam=exam).get_statistics_response()


@staff_required
def predict_catalog_excel(_: HtmxHttpRequest, pk: int):
    exam = get_object_or_404(models.Exam, pk=pk)
    return AdminExportExcelContext(_exam=exam).get_catalog_response()


@staff_required
def predict_answer_excel(_: HtmxHttpRequest, pk: int):
    exam = get_object_or_404(models.Exam, pk=pk)
    return AdminExportExcelContext(_exam=exam).get_answer_response()
