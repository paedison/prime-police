from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy

from a_official import models, forms
from a_official.utils import RequestData, SubjectVariants
from a_official.utils.predict.staff_utils import *
from a_official.views.normal_views import predict_views
from a_common.constants import icon_set
from a_common.decorators import staff_required
from a_common.utils import HtmxHttpRequest, update_context_data


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
    list_data = AdminListContext(_request=request)
    context = update_context_data(config=config, predict_exam_context=list_data.get_predict_exam_context())

    if list_data.view_type == 'predict_exam_list':
        return render(request, f'a_official/staff_predict_list.html#study_category_list', context)  # noqa
    return render(request, 'a_official/staff_predict_list.html', context)


@staff_required
def predict_detail_view(request: HtmxHttpRequest, pk: int):
    config = ViewConfiguration()
    exam = models.Exam.objects.filter(pk=pk).select_related('predict_exam').first()
    request_data = RequestData(_request=request)
    subject_variants = SubjectVariants(_selection='')
    context = update_context_data(
        config=config, exam=exam,
        page_number=request_data.page_number,
        student_name=request_data.student_name,
        subject_vars_dict=subject_variants.subject_vars_dict,
    )

    detail_data = AdminDetailContext(_request=request, _context=context)
    if request_data.view_type == 'problem_list':
        context = update_context_data(context, **detail_data.get_problem_context())
        return render(request, 'a_official/problem_list_content.html', context)

    config.url_staff_predict_update = reverse_lazy('official:staff-predict-update', args=[pk])
    context = update_context_data(
        context, predict_exam=exam.predict_exam, icon_nav=icon_set.ICON_NAV, icon_search=icon_set.ICON_SEARCH)

    if request_data.view_type == 'catalog_list':
        catalog_context = AdminDetailCatalogContext(_context=context)
        context = update_context_data(context, **catalog_context.get_admin_catalog_context())
        return render(request, 'a_official/snippets/staff_predict_detail_catalog.html', context)
    if request_data.view_type == 'student_search':
        catalog_context = AdminDetailCatalogContext(_context=context)
        context = update_context_data(context, **catalog_context.get_admin_catalog_context(for_search=True))
        return render(request, 'a_official/snippets/staff_predict_detail_catalog.html', context)
    if request_data.view_type == 'answer_list':
        answer_context = AdminDetailAnswerContext(_context=context)
        context = update_context_data(context, **answer_context.get_admin_answer_context())
        return render(request, 'a_official/snippets/staff_predict_detail_answer_analysis.html', context)

    statistics_context = AdminDetailStatisticsContext(_context=context)
    catalog_context = AdminDetailCatalogContext(_context=context)
    answer_context = AdminDetailAnswerContext(_context=context)

    context = update_context_data(
        context,
        **statistics_context.get_admin_statistics_context(),
        **catalog_context.get_admin_catalog_context(),
        **answer_context.get_admin_answer_context(),
        **detail_data.get_answer_predict_context(),
        **detail_data.get_answer_official_context(),
        **detail_data.get_problem_context(),
    )
    return render(request, 'a_official/staff_predict_detail.html', context)


@staff_required
def predict_create_view(request: HtmxHttpRequest):
    config = ViewConfiguration()
    title = '합격 예측 새 시험 등록'
    context = update_context_data(config=config, title=title)

    if request.method == 'POST':
        form = forms.PredictExamForm(request.POST, request.FILES)
        if form.is_valid():
            create_data = AdminCreateData(_form=form)
            create_data.process_post_request()
            return redirect(config.url_list)
        else:
            context = update_context_data(context, form=form)
            return render(request, 'a_official/staff_form.html', context)

    form = forms.PredictExamForm()
    context = update_context_data(context, form=form)
    return render(request, 'a_official/staff_form.html', context)


@staff_required
def predict_update_view(request: HtmxHttpRequest, pk: int):
    exam = get_object_or_404(models.Exam, pk=pk)
    request_data = RequestData(_request=request)
    subject_variants = SubjectVariants(_selection='')
    context = update_context_data(
        exam=exam,
        next_url=exam.get_staff_predict_detail_url(),
        subject_vars_dict=subject_variants.get_subject_vars_dict(),
        subject_fields_dict=subject_variants.get_subject_fields_dict(),
    )

    if request_data.view_type == 'answer_official':
        answer_official_context = AdminUpdateAnswerOfficialContext(_request=request, _exam=exam)
        is_updated, message = answer_official_context.update_problem_model_for_answer_official()
        context = update_context_data(context, header='정답 업데이트', is_updated=is_updated, message=message)

    if request_data.view_type == 'score':
        score_context = AdminUpdateScoreContext(_context=context)
        is_updated, message = score_context.update_scores()
        context = update_context_data(context, header='점수 업데이트', is_updated=is_updated, message=message)

    if request_data.view_type == 'rank':
        rank_context = AdminUpdateRankContext(_context=context)
        is_updated, message = rank_context.update_ranks()
        context = update_context_data(context, header='등수 업데이트', is_updated=is_updated, message=message)

    if request_data.view_type == 'statistics':
        statistics_context = AdminUpdateStatisticsContext(_context=context)
        is_updated, message = statistics_context.update_statistics()
        context = update_context_data(context, header='통계 업데이트', is_updated=is_updated, message=message)

    if request_data.view_type == 'answer_count':
        answer_count_context = AdminUpdateAnswerCountContext(_context=context)
        is_updated, message = answer_count_context.update_answer_counts()
        context = update_context_data(context, header='문항분석표 업데이트', is_updated=is_updated, message=message)

    return render(request, 'a_official/snippets/staff_modal_predict_update.html', context)


@staff_required
def predict_student_detail_view(request: HtmxHttpRequest, pk: int):
    student: models.PredictStudent = models.PredictStudent.objects.filter(pk=pk).first()
    if student:
        student = models.PredictStudent.objects.exam_student_with_answer_count(student.user, student.exam)
        return predict_views.predict_detail_view(request, student.exam.id, student=student)
    return redirect('exam:admin-predict-list')


@staff_required
def predict_statistics_print(request: HtmxHttpRequest, pk: int):
    exam = get_object_or_404(models.Exam, pk=pk)
    detail_data = AdminDetailContext(_request=request, _exam=exam)
    context = update_context_data(exam=exam, **detail_data.get_admin_statistics_context(200))
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
    detail_data = AdminDetailContext(_request=request, _exam=exam)
    context = update_context_data(exam=exam, **detail_data.answer.get_admin_answer_context(per_page=1000))
    return render(request, 'a_official/staff_print_answers.html', context)


@staff_required
def predict_statistics_excel(_: HtmxHttpRequest, pk: int):
    exam = get_object_or_404(models.Exam, pk=pk)
    return AdminExportExcelData(_exam=exam).get_statistics_response()


@staff_required
def predict_prime_id_excel(_: HtmxHttpRequest, pk: int):
    exam = get_object_or_404(models.Exam, pk=pk)
    return AdminExportExcelData(_exam=exam).get_prime_id_response()


@staff_required
def predict_catalog_excel(_: HtmxHttpRequest, pk: int):
    exam = get_object_or_404(models.Exam, pk=pk)
    return AdminExportExcelData(_exam=exam).get_catalog_response()


@staff_required
def predict_answer_excel(_: HtmxHttpRequest, pk: int):
    exam = get_object_or_404(models.Exam, pk=pk)
    return AdminExportExcelData(_exam=exam).get_answer_response()
