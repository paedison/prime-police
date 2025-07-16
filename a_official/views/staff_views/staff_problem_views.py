from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy

from a_official import models, forms
from a_official.utils.problem.staff_utils import *
from a_common.constants import icon_set
from a_common.decorators import staff_required
from a_common.utils import HtmxHttpRequest, update_context_data


class ViewConfiguration:
    menu = menu_eng = 'official_staff'
    menu_kor = '경위공채 관리자'
    submenu = submenu_eng = 'problem'
    submenu_kor = '기출문제'

    info = {'menu': menu, 'menu_self': submenu}
    icon_menu = icon_set.ICON_MENU[menu_eng]
    menu_title = {'kor': menu_kor, 'eng': menu.capitalize()}
    submenu_title = {'kor': submenu_kor, 'eng': submenu.capitalize()}

    url_admin = reverse_lazy('admin:a_official_exam_changelist')
    url_admin_exam_list = reverse_lazy('admin:a_official_exam_changelist')
    url_admin_problem_list = reverse_lazy('admin:a_official_problem_changelist')

    url_list = reverse_lazy('official:staff-official-list')
    url_exam_create = reverse_lazy('official:staff-official-exam-create')
    url_problem_update = reverse_lazy('official:staff-official-update')


@staff_required
def problem_list_view(request: HtmxHttpRequest):
    config = ViewConfiguration()
    list_data = AdminListData(_request=request)
    context = update_context_data(
        config=config,
        sub_title=list_data.sub_title,
        exam_form=list_data.filterset.form,
        exam_context=list_data.get_exam_context()
    )
    if list_data.view_type == 'exam_list':
        return render(request, f'a_official/staff_official_list.html#exam_list', context)  # noqa
    return render(request, 'a_official/staff_official_list.html', context)


@staff_required
def problem_detail_view(request: HtmxHttpRequest, pk: int):
    config = ViewConfiguration()
    exam = get_object_or_404(models.Exam, pk=pk)
    detail_data = AdminDetailData(_request=request, _exam=exam)
    context = update_context_data(config=config, psat=exam, problem_context=detail_data.get_problem_context())

    if detail_data.view_type == 'problem_list':
        return render(request, 'a_official/problem_list_content.html', context)

    context = update_context_data(context, answer_official_context=detail_data.get_answer_official_context())
    return render(request, 'a_official/staff_official_detail.html', context)


@staff_required
def official_exam_create_view(request: HtmxHttpRequest):
    config = ViewConfiguration()
    title = '새 시험 등록'
    context = update_context_data(config=config, title=title)

    if request.method == 'POST':
        form = forms.ExamForm(request.POST, request.FILES)
        if form.is_valid():
            create_data = AdminCreateData(form=form)
            create_data.process_post_request()
            return redirect(config.url_list)
        else:
            context = update_context_data(context, form=form)
            return render(request, 'a_official/staff_form.html', context)

    form = forms.ExamForm()
    context = update_context_data(context, form=form)
    return render(request, 'a_official/staff_form.html', context)


@staff_required
def official_exam_active_view(request: HtmxHttpRequest, pk: int):
    if request.method == 'POST':
        form = forms.ExamActiveForm(request.POST)
        if form.is_valid():
            psat = get_object_or_404(models.Exam, pk=pk)
            is_active = form.cleaned_data['is_active']
            psat.is_active = is_active
            psat.save()
    return HttpResponse('')


@staff_required
def official_update_view(request: HtmxHttpRequest):
    config = ViewConfiguration()
    title = 'PSAT 문제 업데이트'
    context = update_context_data(config=config, title=title)

    if request.method == 'POST':
        form = forms.ProblemUpdateForm(request.POST, request.FILES)
        if form.is_valid():
            year = form.cleaned_data['year']
            exam = get_object_or_404(models.Exam, year=year)
            update_data = AdminUpdateData(_request=request, _exam=exam)
            update_data.process_post_request()
            return redirect(config.url_list)
        else:
            context = update_context_data(context, form=form)
            return render(request, 'a_official/staff_form.html', context)

    form = forms.ProblemUpdateForm()
    context = update_context_data(context, form=form)
    return render(request, 'a_official/staff_form.html', context)
