from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django_htmx.http import replace_url

from a_common.constants import icon_set
from a_common.decorators import staff_required
from a_common.utils import HtmxHttpRequest, update_context_data
from a_mock import models, forms
from a_mock.utils.staff_utils import AdminListData, AdminDetailData, AdminCreateData, AdminUpdateData
from a_mock.views import result_views


class ViewConfiguration:
    menu = 'mock'
    submenu = 'staff'
    info = {'menu': menu, 'menu_self': submenu}
    menu_title = {'kor': '전국모의고사', 'eng': menu.capitalize()}
    submenu_title = {'kor': '관리자 메뉴', 'eng': submenu.capitalize()}
    url_admin = reverse_lazy(f'admin:a_mock_exam_changelist')
    url_admin_exam_list = reverse_lazy('admin:a_mock_exam_changelist')
    url_admin_problem_list = reverse_lazy('admin:a_mock_problem_changelist')
    url_list = reverse_lazy(f'mock:staff-list')
    url_exam_create = reverse_lazy('mock:staff-exam-create')


@staff_required
def list_view(request: HtmxHttpRequest):
    config = ViewConfiguration()
    list_data = AdminListData(request=request)
    context = update_context_data(
        config=config, icon_menu=icon_set.ICON_MENU['score'], icon_subject=icon_set.ICON_SUBJECT,
        exam_context=list_data.get_exam_context(), student_context=list_data.get_student_context(),
    )
    if list_data.view_type == 'student_list':
        return render(request, 'a_mock/staff_list.html#student_list', context)
    return render(request, 'a_mock/staff_list.html', context)


@staff_required
def detail_view(request: HtmxHttpRequest, pk: int):
    config = ViewConfiguration()
    exam = get_object_or_404(models.Exam, pk=pk)
    detail_data = AdminDetailData(request=request, exam=exam)

    answer_tab = detail_data.get_answer_tab()

    config.url_admin_update = reverse_lazy('mock:staff-update', args=[pk])
    config.url_statistics_print = reverse_lazy('mock:staff-statistics-print', args=[pk])
    config.url_catalog_print = reverse_lazy('mock:staff-catalog-print', args=[pk])
    config.url_answers_print = reverse_lazy('mock:staff-answers-print', args=[pk])
    config.url_export_statistics_excel = reverse_lazy('mock:staff-export-statistics-excel', args=[pk])
    config.url_export_catalog_excel = reverse_lazy('mock:staff-export-catalog-excel', args=[pk])
    config.url_export_answers_excel = reverse_lazy('mock:staff-export-answers-excel', args=[pk])
    config.url_export_statistics_pdf = reverse_lazy('mock:staff-export-statistics-pdf', args=[pk])

    context = update_context_data(
        config=config, exam=exam, answer_tab=answer_tab,
        icon_nav=icon_set.ICON_NAV, icon_search=icon_set.ICON_SEARCH,
    )

    if detail_data.view_type == 'statistics_list':
        context = update_context_data(context, **detail_data.get_admin_statistics_context())
        return render(request, 'a_mock/snippets/staff_detail_statistics.html', context)
    if detail_data.view_type == 'catalog_list':
        context = update_context_data(context, **detail_data.get_admin_catalog_context())
        return render(request, 'a_mock/snippets/staff_detail_catalog.html', context)
    if detail_data.view_type == 'student_search':
        context = update_context_data(context, **detail_data.get_admin_catalog_context(True))
        return render(request, 'a_mock/snippets/staff_detail_catalog.html', context)
    if detail_data.view_type == 'answer_list':
        answer_data = detail_data.get_admin_answer_context(True)['answer_context'][detail_data.exam_subject]
        context = update_context_data(context, answer_data=answer_data)
        return render(request, 'a_mock/snippets/staff_detail_answer.html', context)

    context = update_context_data(
        context,
        **detail_data.get_admin_statistics_context(),
        **detail_data.get_admin_catalog_context(),
        **detail_data.get_admin_answer_context(),
    )
    return render(request, 'a_mock/staff_detail.html', context)


@staff_required
def detail_student_view(request: HtmxHttpRequest, pk: int):
    student = models.Student.objects.mock_student_with_answer_count(pk=pk)
    return result_views.detail_view(request, student=student)


@staff_required
def detail_student_print_view(request: HtmxHttpRequest, pk: int):
    student = models.Student.objects.mock_student_with_answer_count(pk=pk)
    return result_views.detail_view(request, student, True)


@staff_required
def exam_create_view(request: HtmxHttpRequest):
    config = ViewConfiguration()
    title = '전국모의고사 등록'
    context = update_context_data(config=config, title=title)

    if request.method == 'POST':
        form = forms.ExamForm(request.POST, request.FILES)
        if form.is_valid():
            create_data = AdminCreateData(request=request, form=form)
            create_data.process_post_request()
            response = redirect(config.url_list)
            return replace_url(response, config.url_list)
        else:
            context = update_context_data(context, form=form)
            return render(request, 'a_common/prime_test/staff_exam_create.html', context)

    form = forms.ExamForm()
    context = update_context_data(context, form=form)
    return render(request, 'a_common/prime_test/staff_exam_create.html', context)


@staff_required
def update_view(request: HtmxHttpRequest, pk: int):
    exam = get_object_or_404(models.Exam, pk=pk)
    context = update_context_data(next_url=exam.get_staff_detail_url())
    update_data = AdminUpdateData(request=request, exam=exam)

    if update_data.view_type == 'answer_official':
        is_updated, message = update_data.update_problem_model_for_answer_official()
        context = update_context_data(context, header='정답 업데이트', is_updated=is_updated, message=message)

    if update_data.view_type == 'answer_student':
        is_updated, message = update_data.update_answer_student()
        context = update_context_data(context, header='제출 답안 업데이트', is_updated=is_updated, message=message)

    if update_data.view_type == 'score':
        is_updated, message = update_data.update_scores()
        context = update_context_data(context, header='점수 업데이트', is_updated=is_updated, message=message)

    if update_data.view_type == 'rank':
        is_updated, message = update_data.update_ranks()
        context = update_context_data(context, header='등수 업데이트', is_updated=is_updated, message=message)

    if update_data.view_type == 'statistics':
        is_updated, message = update_data.update_statistics()
        context = update_context_data(context, header='통계 업데이트', is_updated=is_updated, message=message)

    if update_data.view_type == 'answer_count':
        is_updated, message = update_data.update_answer_counts()
        context = update_context_data(context, header='문항분석표 업데이트', is_updated=is_updated, message=message)

    return render(request, 'a_mock/snippets/staff_modal_update.html', context)


@staff_required
def statistics_print_view(request: HtmxHttpRequest, pk: int):
    exam = get_object_or_404(models.Exam, pk=pk)
    data_statistics = staff_utils.get_data_statistics(exam)
    context = update_context_data(exam=exam, data_statistics=data_statistics)
    return render(request, 'a_mock/staff_print_statistics.html', context)


@staff_required
def catalog_print_view(request: HtmxHttpRequest, pk: int):
    exam = get_object_or_404(models.Exam, pk=pk)
    student_list = models.Student.objects.mock_qs_student_list_by_exam(exam)
    context = update_context_data(exam=exam, student_list=student_list)
    return render(request, 'a_mock/staff_print_catalog.html', context)


@staff_required
def answers_print_view(request: HtmxHttpRequest, pk: int):
    exam = get_object_or_404(models.Exam, pk=pk)
    qs_answer_count = models.AnswerCount.objects.mock_qs_answer_count_by_exam_and_subject(exam)
    answers_page_obj_group, answers_page_range_group = (
        staff_utils.get_answer_page_data(qs_answer_count, 1, 1000))
    context = update_context_data(exam=exam, answers_page_obj_group=answers_page_obj_group)
    return render(request, 'a_mock/staff_print_answers.html', context)


@staff_required
def export_statistics_excel_view(_: HtmxHttpRequest, pk: int):
    exam = get_object_or_404(models.Exam, pk=pk)
    return staff_utils.get_statistics_response(exam)


@staff_required
def export_catalog_excel_view(_: HtmxHttpRequest, pk: int):
    exam = get_object_or_404(models.Exam, pk=pk)
    return staff_utils.get_catalog_response(exam)


@staff_required
def export_answers_excel_view(_: HtmxHttpRequest, pk: int):
    exam = get_object_or_404(models.Exam, pk=pk)
    return staff_utils.get_answer_response(exam)
