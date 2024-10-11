import itertools

import pandas as pd
from django.db.models import F
from django.shortcuts import render, redirect, get_object_or_404
from django_htmx.http import replace_url

from .. import utils
from ..constants import icon_set
from ..decorators import staff_required


@staff_required
def menu_list_view(request: utils.HtmxHttpRequest, models, filters, config):
    view_type = request.headers.get('View-Type', '')
    exam_circle = request.GET.get('circle', '')
    exam_round = request.GET.get('round', '')
    exam_subject = request.GET.get('subject', '')
    page = request.GET.get('page', '1')
    filterset = filters.ExamFilter(data=request.GET, request=request)

    sub_title = utils.get_sub_title(exam_circle, exam_round, exam_subject, end_string='답안 제출 현황')

    page_obj, page_range = utils.get_page_obj_and_range(page, filterset.qs)
    for exam in page_obj:
        exam_info = utils.get_exam_info(exam)
        exam.student = utils.get_student(request, models, exam_info)
    context = utils.update_context_data(
        config=config, sub_title=sub_title, form=filterset.form,
        icon_menu=icon_set.ICON_MENU['daily'], page_obj=page_obj, page_range=page_range)
    if view_type == 'exam_list':
        template_name = 'a_common/prime_test/staff_list.html#list_content'
        return render(request, template_name, context)

    return render(request, 'a_common/prime_test/staff_list.html', context)


@staff_required
def exam_create_view(request: utils.HtmxHttpRequest, models, forms, config):
    if request.method == 'POST':
        form = forms.ExamForm(request.POST, request.FILES)
        if form.is_valid():
            opened_at = form.cleaned_data['opened_at']
            exam = form.save()
            exam_info = {
                'semester': exam.semester, 'circle': exam.circle,
                'subject': exam. subject, 'round': exam.round,
            }
            answer_file = request.FILES['answer_file']
            df = pd.read_excel(answer_file, sheet_name='정답', header=0, index_col=0)

            answer_symbol = {'①': 1, '②': 2, '③': 3, '④': 4}
            keys = list(answer_symbol.keys())
            combinations = []
            for i in range(1, 6):
                combinations.extend(itertools.combinations(keys, i))

            replace_dict = {}
            for combination in combinations:
                key = ''.join(combination)
                value = int(''.join(str(answer_symbol[k]) for k in combination))
                replace_dict[key] = value

            df.replace(to_replace=replace_dict, inplace=True)
            df = df.infer_objects(copy=False)
            df.fillna(value=0, inplace=True)
            answer_list = df.get('정답')
            for number, answer in answer_list.items():
                models.Problem.objects.get_or_create(number=number, answer=answer, opened_at=opened_at, **exam_info)

            response = redirect('daily:staff-menu')
            return replace_url(response, config.url_list)
        else:
            context = utils.update_context_data(config=config, form=form)
            return render(request, 'a_common/prime_test/staff_exam_create.html', context)

    form = forms.ExamForm()
    context = utils.update_context_data(config=config, form=form)
    return render(request, 'a_common/prime_test/staff_exam_create.html', context)


@staff_required
def answer_update_view(request: utils.HtmxHttpRequest, pk: int, models):
    exam = get_object_or_404(models.Exam, pk=pk)
    exam_info = utils.get_exam_info(exam)
    rank_list = ['all_rank', 'top_rank', 'mid_rank', 'low_rank']

    answer_lists_by_rank = utils.get_answer_lists_by_rank(models, exam_info, rank_list, exam)
    answer_count = utils.get_answer_count_list(models, exam_info, rank_list, answer_lists_by_rank)

    answer_message = utils.update_answer_count_model(models, exam_info, answer_count)
    score_message = utils.update_student_model_for_score(models, exam_info)
    rank_message = utils.update_student_model_for_rank(models, exam, exam_info)
    messages = [answer_message, score_message, rank_message]

    context = utils.update_context_data(header='통계 업데이트', messages=messages)
    return render(request, 'a_common/prime_test/staff_update_modal.html', context)


@staff_required
def answer_detail_view(request: utils.HtmxHttpRequest, pk: int, models, config):
    view_type = request.headers.get('View-Type', '')
    page = request.GET.get('page', '1')
    exam = get_object_or_404(models.Exam, pk=pk)
    exam_info = utils.get_exam_info(exam)
    context = utils.update_context_data(config=config, exam=exam)

    def get_context_for_student_catalog():
        qs_student = models.Student.objects.filter(rank__isnull=False, **exam_info).order_by('rank').annotate(
            student_name=F('user__name'), student_id=F('user__prime_id'))
        return utils.get_page_obj_and_range(page, qs_student, 20)

    def get_context_for_problem_statistics():
        answer_official = models.Problem.objects.filter(**exam_info).order_by('number').values(no=F('number'), ans=F('answer'))
        qs_answer_count = utils.get_qs_answer_count_for_staff_answer_detail(models, exam_info, answer_official)
        return utils.get_page_obj_and_range(page, qs_answer_count, 20)

    if view_type == 'student_catalog':
        page_obj_student, page_range_student = get_context_for_student_catalog()
        context = utils.update_context_data(context, page_obj_student=page_obj_student, page_range_student=page_range_student)
        template_name = 'a_common/prime_test/staff_answer_detail.html#student_catalog'
        return render(request, template_name, context)

    if view_type == 'problem_statistics':
        page_obj_problem, page_range_problem = get_context_for_problem_statistics()
        context = utils.update_context_data(context, page_obj_problem=page_obj_problem, page_range_problem=page_range_problem)
        template_name = 'a_common/prime_test/staff_answer_detail.html#problem_statistics'
        return render(request, template_name, context)

    page_obj_student, page_range_student = get_context_for_student_catalog()
    page_obj_problem, page_range_problem = get_context_for_problem_statistics()
    score_points = utils.get_score_points(models, exam_info)
    score_colors = ['white' for _ in score_points.keys()]

    context = utils.update_context_data(
        config=config, exam=exam,
        page_obj_student=page_obj_student, page_range_student=page_range_student,
        page_obj_problem=page_obj_problem, page_range_problem=page_range_problem,
        score_points=score_points, score_colors=score_colors,
        icon_menu=icon_set.ICON_MENU['daily'], icon_question=icon_set.ICON_QUESTION,
        icon_nav=icon_set.ICON_NAV, icon_board=icon_set.ICON_BOARD,
    )
    return render(request, 'a_common/prime_test/staff_answer_detail.html', context)
