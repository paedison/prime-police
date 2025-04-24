import pandas as pd
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django_htmx.http import replace_url

from a_common.constants import icon_set
from a_common.decorators import staff_required
from a_common.utils import HtmxHttpRequest, update_context_data
from . import staff_utils, answer_views
from .. import models, utils, forms


class ViewConfiguration:
    menu = 'infinite'
    submenu = 'staff'
    info = {'menu': menu, 'menu_self': submenu}
    menu_title = {'kor': '무한반', 'eng': menu.capitalize()}
    submenu_title = {'kor': '관리자 메뉴', 'eng': submenu.capitalize()}
    url_admin = reverse_lazy(f'admin:a_infinite_exam_changelist')
    url_admin_exam_list = reverse_lazy('admin:a_infinite_exam_changelist')
    url_admin_problem_list = reverse_lazy('admin:a_infinite_problem_changelist')
    url_list = reverse_lazy(f'infinite:staff-menu')
    url_exam_create = reverse_lazy('infinite:staff-exam-create')


@staff_required
def menu_list_view(request: HtmxHttpRequest):
    view_type = request.headers.get('View-Type', '')
    page_number = request.GET.get('page', 1)

    exam_list = models.Exam.objects.infinite_qs_exam_list()
    config = ViewConfiguration()
    exam_page_obj, exam_page_range = utils.get_paginator_data(exam_list, page_number)

    student_list = models.Student.objects.infinite_qs_student_list()
    student_page_obj, student_page_range = utils.get_paginator_data(student_list, page_number)

    context = update_context_data(
        config=config,
        icon_menu=icon_set.ICON_MENU['score'],
        icon_subject=icon_set.ICON_SUBJECT,

        exam_page_obj=exam_page_obj,
        exam_page_range=exam_page_range,
        student_page_obj=student_page_obj,
        student_page_range=student_page_range,
    )
    if view_type == 'student_list':
        return render(request, 'a_infinite/staff_list.html#student_list', context)
    return render(request, 'a_infinite/staff_list.html', context)


@staff_required
def detail_view(request: HtmxHttpRequest, pk: int):
    config = ViewConfiguration()
    view_type = request.headers.get('View-Type', '')
    page_number = request.GET.get('page', '1')
    subject = request.GET.get('subject', '')
    student_name = request.GET.get('student_name', '')

    exam = get_object_or_404(models.Exam, pk=pk)
    answer_tab = staff_utils.get_answer_tab()

    config.url_admin_update = reverse_lazy('infinite:staff-update', args=[exam.id])
    config.url_statistics_print = reverse_lazy('infinite:staff-statistics-print', args=[exam.id])
    config.url_catalog_print = reverse_lazy('infinite:staff-catalog-print', args=[exam.id])
    config.url_answers_print = reverse_lazy('infinite:staff-answers-print', args=[exam.id])
    config.url_export_statistics_excel = reverse_lazy('infinite:staff-export-statistics-excel', args=[exam.id])
    config.url_export_catalog_excel = reverse_lazy('infinite:staff-export-catalog-excel', args=[exam.id])
    config.url_export_answers_excel = reverse_lazy('infinite:staff-export-answers-excel', args=[exam.id])
    config.url_export_statistics_pdf = reverse_lazy('infinite:staff-export-statistics-pdf', args=[exam.id])

    context = update_context_data(
        config=config, exam=exam, answer_tab=answer_tab,
        icon_nav=icon_set.ICON_NAV, icon_search=icon_set.ICON_SEARCH,
    )
    data_statistics = models.Statistics.objects.filter(exam=exam).order_by('id')
    student_list = models.Student.objects.infinite_qs_student_list_by_exam(exam)
    qs_answer_count = models.AnswerCount.objects.infinite_qs_answer_count_by_exam_and_subject(exam)

    if view_type == 'statistics_list':
        statistics_page_obj, statistics_page_range = utils.get_paginator_data(data_statistics, page_number)
        context = update_context_data(
            context, statistics_page_obj=statistics_page_obj, statistics_page_range=statistics_page_range)
        return render(request, 'a_infinite/snippets/staff_detail_statistics.html', context)
    if view_type == 'catalog_list':
        catalog_page_obj, catalog_page_range = utils.get_paginator_data(student_list, page_number)
        context = update_context_data(
            context, catalog_page_obj=catalog_page_obj, catalog_page_range=catalog_page_range)
        return render(request, 'a_infinite/snippets/staff_detail_catalog.html', context)
    if view_type == 'student_search':
        searched_student = student_list.filter(name=student_name)
        catalog_page_obj, catalog_page_range = utils.get_paginator_data(searched_student, page_number)
        context = update_context_data(
            context, catalog_page_obj=catalog_page_obj, catalog_page_range=catalog_page_range)
        return render(request, 'a_infinite/snippets/staff_detail_catalog.html', context)
    if view_type == 'answer_list':
        subject_vars = staff_utils.get_subject_vars()
        subject_idx = subject_vars[subject][2]
        answers_page_obj_group, answers_page_range_group = staff_utils.get_answer_page_data(
            qs_answer_count, page_number)
        context = update_context_data(
            context,
            tab=answer_tab[subject_idx],
            answers=answers_page_obj_group[subject],
            answers_page_range=answers_page_range_group[subject],
        )
        return render(request, 'a_infinite/snippets/staff_detail_answer.html', context)

    statistics_page_obj, statistics_page_range = utils.get_paginator_data(data_statistics, page_number)
    catalog_page_obj, catalog_page_range = utils.get_paginator_data(student_list, page_number)
    answers_page_obj_group, answers_page_range_group = staff_utils.get_answer_page_data(
        qs_answer_count, page_number)

    context = update_context_data(
        context,
        statistics_page_obj=statistics_page_obj, statistics_page_range=statistics_page_range,
        catalog_page_obj=catalog_page_obj, catalog_page_range=catalog_page_range,
        answers_page_obj_group=answers_page_obj_group, answers_page_range_group=answers_page_range_group,
    )
    return render(request, 'a_infinite/staff_detail.html', context)


@staff_required
def detail_student_view(request: HtmxHttpRequest, pk: int):
    student = models.Student.objects.infinite_student_with_answer_count(pk=pk)
    return answer_views.detail_view(request, student.exam.pk, student=student)


@staff_required
def detail_student_print_view(request: HtmxHttpRequest, pk: int):
    student = models.Student.objects.infinite_student_with_answer_count(pk=pk)
    return answer_views.print_view(request, student.exam.pk, student=student)


@staff_required
def update_view(request: HtmxHttpRequest, pk: int):
    view_type = request.headers.get('View-Type', '')
    exam = get_object_or_404(models.Exam, pk=pk)

    context = update_context_data(next_url=exam.get_staff_detail_url())
    qs_student = models.Student.objects.filter(exam=exam).order_by('id')
    upload_form = forms.UploadFileForm(request.POST, request.FILES)

    if view_type == 'answer_official':
        file = request.FILES.get('file')
        is_updated, message = staff_utils.update_problem_model_for_answer_official(exam, upload_form, file)
        context = update_context_data(context, header='정답 업데이트', is_updated=is_updated, message=message)

    if view_type == 'score':
        is_updated, message = staff_utils.update_scores(qs_student)
        context = update_context_data(context, header='점수 업데이트', is_updated=is_updated, message=message)

    if view_type == 'rank':
        is_updated, message = staff_utils.update_ranks(qs_student)
        context = update_context_data(context, header='등수 업데이트', is_updated=is_updated, message=message)

    if view_type == 'statistics':
        is_updated, message = staff_utils.update_statistics(exam)
        context = update_context_data(context, header='통계 업데이트', is_updated=is_updated, message=message)

    if view_type == 'answer_count':
        is_updated, message = staff_utils.update_answer_counts(exam)
        context = update_context_data(context, header='문항분석표 업데이트', is_updated=is_updated, message=message)

    return render(request, 'a_infinite/snippets/staff_modal_update.html', context)


@staff_required
def exam_create_view(request: HtmxHttpRequest):
    config = ViewConfiguration()
    if request.method == 'POST':
        form = forms.ExamForm(request.POST, request.FILES)
        if form.is_valid():
            semester = form.cleaned_data['semester']
            exam_round = form.cleaned_data['round']

            try:
                exam = models.Exam.objects.get(semester=semester, round=exam_round)
                exam.page_opened_at = form.cleaned_data['page_opened_at']
                exam.exam_started_at = form.cleaned_data['exam_started_at']
                exam.exam_finished_at = form.cleaned_data['exam_finished_at']
                exam.save()
            except models.Exam.DoesNotExist:
                exam = form.save()

            answer_file = request.FILES['answer_file']
            df = pd.read_excel(answer_file, header=0, index_col=0)
            df = df.infer_objects(copy=False)

            staff_utils.create_default_problems(exam, df)
            staff_utils.create_default_statistics(exam)

            problems = models.Problem.objects.filter(exam=exam).order_by('id')
            staff_utils.create_default_answer_counts(problems)

            response = redirect(config.url_list)
            return replace_url(response, config.url_list)
        else:
            context = update_context_data(config=config, form=form)
            return render(request, 'a_common/prime_test/staff_exam_create.html', context)

    form = forms.ExamForm()
    context = update_context_data(config=config, form=form)
    return render(request, 'a_common/prime_test/staff_exam_create.html', context)


@staff_required
def statistics_print_view(request: HtmxHttpRequest, pk: int):
    exam = get_object_or_404(models.Exam, pk=pk)
    data_statistics = staff_utils.get_data_statistics(exam)
    context = update_context_data(exam=exam, data_statistics=data_statistics)
    return render(request, 'a_infinite/staff_print_statistics.html', context)


@staff_required
def catalog_print_view(request: HtmxHttpRequest, pk: int):
    exam = get_object_or_404(models.Exam, pk=pk)
    student_list = models.Student.objects.infinite_qs_student_list_by_exam(exam)
    context = update_context_data(exam=exam, student_list=student_list)
    return render(request, 'a_infinite/staff_print_catalog.html', context)


@staff_required
def answers_print_view(request: HtmxHttpRequest, pk: int):
    exam = get_object_or_404(models.Exam, pk=pk)
    qs_answer_count = models.AnswerCount.objects.infinite_qs_answer_count_by_exam_and_subject(exam)
    answers_page_obj_group, answers_page_range_group = (
        staff_utils.get_answer_page_data(qs_answer_count, 1, 1000))
    context = update_context_data(exam=exam, answers_page_obj_group=answers_page_obj_group)
    return render(request, 'a_infinite/staff_print_answers.html', context)


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
