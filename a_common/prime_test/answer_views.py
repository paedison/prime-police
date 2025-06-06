import json

from django.db.models import F
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django_htmx.http import reswap

from a_common import utils
from a_common.constants import icon_set


def answer_list_view(request: utils.HtmxHttpRequest, models, filters, config):
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
        template_name = 'a_common/prime_test/answer_list.html#list_content'
        return render(request, template_name, context)
    return render(request, 'a_common/prime_test/answer_list.html', context)


def answer_detail_view(request: utils.HtmxHttpRequest, pk: int, models, config):
    exam = get_object_or_404(models.Exam, pk=pk)
    exam_info = utils.get_exam_info(exam)
    student = utils.get_student(request, models, exam_info)
    if not student:
        return redirect('daily:answer-list')
    student.rank_ratio = student.get_rank_ratio(exam.participants)

    qs_problem = models.Problem.objects.filter(**exam_info).order_by('number')
    qs_answer_count = models.AnswerCount.objects.filter(**exam_info).order_by('number')
    answer_analysis = utils.get_answer_analysis(qs_problem, qs_answer_count, student)

    stat_chart = utils.get_dict_stat_chart(exam, student)
    scores = models.Student.objects.filter(score__isnull=False, **exam_info).values_list('score', flat=True)
    stat_frequency = utils.get_dict_stat_frequency(scores, student)

    context = utils.update_context_data(
        config=config, exam=exam, student=student,
        stat_chart=stat_chart, stat_frequency=stat_frequency,
        loop_list=utils.get_loop_list(qs_problem), answer_analysis=answer_analysis,
        icon_menu=icon_set.ICON_MENU['daily'], icon_question=icon_set.ICON_QUESTION,
        icon_nav=icon_set.ICON_NAV, icon_board=icon_set.ICON_BOARD,
    )
    return render(request, 'a_common/prime_test/answer_detail.html', context)


def answer_input_view(request: utils.HtmxHttpRequest, pk: int, models, config):
    menu = config.menu
    exam = get_object_or_404(models.Exam, pk=pk)
    if exam.opened_at > timezone.now():
        return redirect('daily:answer-list')
    exam_info = utils.get_exam_info(exam)
    student = utils.get_student(request, models, exam_info)
    if not student:
        models.Student.objects.create(user=request.user, **exam_info)

    problem_count = models.Problem.objects.filter(**exam_info).count()
    empty_answer_data = [0 for _ in range(problem_count)]
    answer_input = json.loads(request.COOKIES.get(f'{menu}_answer_input', '[]')) or empty_answer_data

    # answer_submit
    if request.method == 'POST':
        try:
            no = int(request.POST.get('number'))
            ans = int(request.POST.get('answer'))
        except Exception as e:
            print(e)
            return reswap(HttpResponse(''), 'none')

        answer = {'no': no, 'ans': ans}
        context = utils.update_context_data(answer=answer, exam=exam)
        response = render(request, 'a_common/prime_test/answer_button.html', context)

        if 1 <= no <= problem_count and 1 <= ans <= 4:
            answer_input[no - 1] = ans
            response.set_cookie(f'{menu}_answer_input', json.dumps(answer_input), max_age=300)
            return response
        else:
            print('Answer is not appropriate.')
            return reswap(HttpResponse(''), 'none')

    answer_student = [{'no': no, 'ans': ans} for no, ans in enumerate(answer_input, start=1)]
    context = utils.update_context_data(
        config=config, exam=exam, icon_menu=icon_set.ICON_MENU['daily'], answer_student=answer_student)
    return render(request, 'a_common/prime_test/answer_input.html', context)


def answer_confirm_view(request: utils.HtmxHttpRequest, pk: int, models, config):
    menu = config.menu
    exam = get_object_or_404(models.Exam, pk=pk)
    exam_info = utils.get_exam_info(exam)
    student = utils.get_student(request, models, exam_info)
    context = utils.update_context_data(exam=exam, header=f'답안을 제출하시겠습니까?', verifying=True)

    if request.method == 'POST':
        answer_official = models.Problem.objects.filter(**exam_info).order_by(
            'number').values_list('answer', flat=True)

        empty_answer_data = [0 for _ in range(len(answer_official))]
        answer_input = json.loads(request.COOKIES.get(f'{menu}_answer_input', '[]')) or empty_answer_data

        is_confirmed = all(answer_input) and len(answer_input) == len(answer_official)
        if is_confirmed:
            correct_cnt = sum(1 for x, y in zip(answer_official, answer_input) if x == y)
            score = round(correct_cnt * 100 / len(answer_official), 1)

            score_list = list(models.Student.objects.filter(
                score__isnull=False, **exam_info).values_list('score', flat=True)) + [score]
            stat = utils.get_statistics(score_list, score)
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
        context = utils.update_context_data(exam=exam, header=f'답안 제출', is_confirmed=is_confirmed)

    return render(request, 'a_common/prime_test/answer_confirmed_modal.html', context)


def rank_verify(_: utils.HtmxHttpRequest, pk: int, models):
    student = get_object_or_404(models.Student, pk=pk)
    exam_info = utils.get_exam_info(student)
    exam = get_object_or_404(models.Exam, **exam_info)
    score_list = models.Student.objects.filter(answer_confirmed=True, **exam_info).values_list('score', flat=True)

    stat = utils.get_statistics(score_list, student.score)
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
