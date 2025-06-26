from datetime import datetime

from django.contrib.auth.decorators import login_not_required
from django.shortcuts import render, get_object_or_404
from django.urls import reverse_lazy
from django_htmx.http import retarget

from a_common.constants import icon_set
from a_common.utils import HtmxHttpRequest, update_context_data
from a_mock import models, forms
from a_mock.utils.result_utils import ResultDetailData


class ViewConfiguration:
    menu = 'mock'
    submenu = 'result'
    info = {'menu': menu, 'menu_self': submenu}
    menu_title = {'kor': '전국모의고사', 'eng': menu.capitalize()}
    submenu_title = {'kor': '성적 확인', 'eng': submenu.capitalize()}
    url_admin = reverse_lazy(f'admin:a_mock_exam_changelist')
    url_list = reverse_lazy(f'mock:index')


@login_not_required
def index_view(request: HtmxHttpRequest):
    config = ViewConfiguration()
    exam = get_object_or_404(models.Exam, year=datetime.now().year+1)
    context = update_context_data(icon_menu=icon_set.ICON_MENU['mock'], config=config, exam=exam)

    form_class = forms.StudentForm
    if request.method == "POST":
        form = form_class(request.POST)
        if form.is_valid():
            serial = form.cleaned_data['serial']
            name = form.cleaned_data['name']
            password = form.cleaned_data['password']
            student = models.Student.objects.filter(
                exam=exam, serial=serial, name=name, password=password).first()
            if student:
                response = detail_view(request, student)
                return retarget(response, '#main')
            else:
                context = update_context_data(context, form=form, no_student=True)
                response = render(request, 'a_mock/snippets/create_info_student.html', context)
                return retarget(response, '#infoStudent')
        else:
            context = update_context_data(context, form=form)
            response = render(request, 'a_mock/snippets/create_info_student.html', context)
            return retarget(response, '#infoStudent')
    else:
        context = update_context_data(context, form=form_class())
        return render(request, 'a_mock/index.html', context)


@login_not_required
def detail_view(request: HtmxHttpRequest, student: models.Student, is_for_print=False):
    config = ViewConfiguration()
    detail_data = ResultDetailData(request=request, student=student)

    context = update_context_data(
        config=config, exam=student.exam,
        icon_menu=icon_set.ICON_MENU['mock'], icon_nav=icon_set.ICON_NAV,

        student=student,
        **detail_data.get_stat_data_context(),
        **detail_data.get_answer_context(),

        # chart: 성적 분포 차트
        stat_chart=detail_data.chart_data.get_dict_stat_chart(),
        stat_frequency=detail_data.chart_data.get_dict_stat_frequency(),
    )
    if is_for_print:
        return render(request, 'a_mock/result_print.html', context)
    return render(request, 'a_mock/result_detail.html', context)
