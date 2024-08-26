import json
from datetime import date

from django.db.models import F, Max, Case, When, BooleanField, Value
from django.db.models.functions import Coalesce
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.decorators.http import require_POST
from django_htmx.http import reswap

from a_common.constants import icon_set
from a_common.decorators import permission_or_staff_required
from a_common.utils import HtmxHttpRequest, update_context_data
from .. import models, utils, forms, filters


@permission_or_staff_required('a_daily.view_student', login_url='/')
def answer_list_view(request: HtmxHttpRequest):
    view_type = request.headers.get('View-Type', '')

    exam_circle = request.GET.get('circle', '')
    exam_round = request.GET.get('round', '')
    exam_subject = request.GET.get('subject', '')
    page = request.GET.get('page', '1')
    filterset = filters.DailyExamFilter(data=request.GET, request=request)

    info = {'menu': 'daily', 'menu_self': 'answer'}
    sub_title = utils.get_sub_title(exam_circle, exam_round, exam_subject, end_string='답안 제출 현황')

    page_obj, page_range = utils.get_page_obj_and_range(page, filterset.qs)
    for exam in page_obj:
        exam_info = get_exam_info(exam)
        exam.student = get_student(request, exam_info)

    context = update_context_data(
        info=info, title='데일리테스트', sub_title=sub_title, form=filterset.form,
        icon_menu=icon_set.ICON_MENU['daily'],
        page_obj=page_obj, page_range=page_range,
    )
    if view_type == 'problem_list':
        template_name = 'a_daily/answer_list.html#list_content'
        return render(request, template_name, context)
    return render(request, 'a_daily/answer_list.html', context)


@permission_or_staff_required('a_daily.view_student', login_url='/')
def answer_detail_view(request: HtmxHttpRequest, pk: int):
    # view_type = request.headers.get('View-Type', '')
    info = {'menu': 'daily', 'menu_self': 'answer'}
    exam = get_object_or_404(models.Exam, pk=pk)
    exam_info = get_exam_info(exam)
    student = get_student(request, exam_info)
    if not student:
        return redirect('daily:answer-list')
    student.rank_ratio = student.get_rank_ratio(exam.participants)

    answer_official = [{'no': no, 'ans': ans} for no, ans in enumerate(exam.answer_official, start=1)]
    answer_student = [{'no': no, 'ans': ans} for no, ans in enumerate(student.answer_student, start=1)]

    qs_answer_count = models.AnswerCount.objects.filter(**exam_info).order_by('number')
    for idx, answer_count in enumerate(qs_answer_count):
        ans_official = exam.answer_official[idx]
        ans_student = student.answer_student[idx]
        if 1 <= ans_official <= 5:
            rate_correct = getattr(answer_count, f'rate_{ans_official}')
        else:
            ans_official_list = [int(ans) for ans in str(ans_official)]
            rate_correct = sum(getattr(answer_count, f'rate_{ans}') for ans in ans_official_list)
        answer_official[idx]['rate_correct'] = rate_correct
        answer_student[idx]['rate_selection'] = getattr(answer_count, f'rate_{ans_student}')
        answer_student[idx]['result'] = ans_student == ans_official

    context = update_context_data(
        info=info, title='데일리테스트', sub_title='성적 확인', exam=exam, student=student,
        answer_official=answer_official, answer_student=answer_student,
        icon_menu=icon_set.ICON_MENU['daily'],
        icon_question=icon_set.ICON_QUESTION,
        icon_nav=icon_set.ICON_NAV,
        icon_board=icon_set.ICON_BOARD,
    )
    return render(request, 'a_daily/answer_detail.html', context)


@permission_or_staff_required('a_daily.view_student', login_url='/')
def answer_input_view(request: HtmxHttpRequest, pk: int):
    info = {'menu': 'daily', 'menu_self': 'answer'}
    exam = get_object_or_404(models.Exam, pk=pk)
    exam_info = get_exam_info(exam)
    student = get_student(request, exam_info)
    if not student:
        models.Student.objects.create(user=request.user, **exam_info)
    empty_answer_data = [0 for _ in range(len(exam.answer_official))]
    answer_input = json.loads(request.COOKIES.get('answer_input', '[]')) or empty_answer_data

    # answer_submit
    if request.method == 'POST':
        try:
            no = int(request.POST.get('number'))
            ans = int(request.POST.get('answer'))
        except Exception as e:
            print(e)
            return reswap(HttpResponse(''), 'none')

        answer = {'no': no, 'ans': ans}
        context = update_context_data(answer=answer, exam=exam)
        response = render(request, 'a_daily/snippets/answer_button.html', context)

        if 1 <= no <= len(exam.answer_official) and 1 <= ans <= 4:
            answer_input[no - 1] = ans
            response.set_cookie('answer_input', json.dumps(answer_input), max_age=300)
            return response
        else:
            print('Answer is not appropriate.')
            return reswap(HttpResponse(''), 'none')

    answer_student = [{'no': no, 'ans': ans} for no, ans in enumerate(answer_input, start=1)]
    context = update_context_data(
        info=info, exam=exam, title='데일리테스트', sub_title='답안 제출',
        icon_menu=icon_set.ICON_MENU['daily'], answer_student=answer_student)
    return render(request, 'a_daily/answer_input.html', context)


@permission_or_staff_required('a_daily.view_student', login_url='/')
def answer_confirm_view(request: HtmxHttpRequest, pk: int):
    exam = get_object_or_404(models.Exam, pk=pk)
    exam_info = get_exam_info(exam)
    student = get_student(request, exam_info)
    context = update_context_data(exam=exam, header=f'답안을 제출하시겠습니까?', verifying=True)

    if request.method == 'POST':
        empty_answer_data = [0 for _ in range(len(exam.answer_official))]
        answer_input = json.loads(request.COOKIES.get('answer_input', '[]')) or empty_answer_data

        is_confirmed = all(answer_input) and len(answer_input) == len(exam.answer_official)
        if is_confirmed:
            correct_cnt = sum(1 for x, y in zip(exam.answer_official, answer_input) if x == y)
            score = round(correct_cnt * 100 / len(exam.answer_official), 1)

            score_list = list(models.Student.objects.filter(
                score__isnull=False, **exam_info).values_list('score', flat=True)) + [score]
            stat = get_statistics(score_list, score)
            rank = stat.pop('rank')
            participants = stat.pop('participants')

            student.answer_student = answer_input
            student.answer_confirmed = True
            student.score = score
            student.rank = rank
            student.save()

            exam.participants = participants
            exam.statistics = stat
            exam.save()

            for no, ans in enumerate(answer_input, start=1):
                answer_count, _ = models.AnswerCount.objects.get_or_create(number=no, **exam_info)
                setattr(answer_count, f'count_{ans}', F(f'count_{ans}') + 1)
                setattr(answer_count, f'count_total', F(f'count_total') + 1)
                answer_count.save()
        context = update_context_data(exam=exam, header=f'답안 제출', is_confirmed=is_confirmed)

    return render(request, 'a_daily/snippets/answer_confirmed_modal.html', context)


@permission_or_staff_required('a_daily.view_student', login_url='/')
def rank_verify(_: HtmxHttpRequest, pk: int):
    student = get_object_or_404(models.Student, pk=pk)
    exam_info = get_exam_info(student)
    exam = get_object_or_404(models.Exam, **exam_info)
    score_list = models.Student.objects.filter(score__isnull=False, **exam_info).values_list('score', flat=True)

    stat = get_statistics(score_list, student.score)
    rank = stat.pop('rank')
    participants = stat.pop('participants')

    if rank:
        student.rank = rank
        student.save()

    exam.participants = participants
    exam.statistics = stat
    exam.save()

    student.refresh_from_db()
    rank_ratio = student.get_rank_ratio(exam.participants)
    return HttpResponse(f'{student.rank}등({rank_ratio}%)')


def get_exam_info(instance: models.Exam | models.Student):
    return {
        'semester': models.semester_default(), 'circle': instance.circle,
        'subject': instance.subject, 'round': instance.round}


def get_student(request: HtmxHttpRequest, exam_info: dict):
    return models.Student.objects.filter(user=request.user, **exam_info).first()


def get_statistics(score_list: list, score: float) -> dict:
    participants = len(score_list)
    sorted_scores = sorted(score_list, reverse=True)
    try:
        rank = sorted_scores.index(score) + 1
        max_score = round(sorted_scores[0], 1)
        top_10_threshold = max(1, int(participants * 0.1))
        top_20_threshold = max(1, int(participants * 0.2))
        top_score_10 = round(sorted_scores[top_10_threshold - 1], 1)
        top_score_20 = round(sorted_scores[top_20_threshold - 1], 1)
        avg_score = round(sum(score_list) / participants if participants else 0, 1)
    except ValueError:
        rank = max_score = top_score_10 = top_score_20 = avg_score = None
    return {
        'participants': participants, 'rank': rank,
        'max': max_score, 't10': top_score_10, 't20': top_score_20, 'avg': avg_score,
    }
