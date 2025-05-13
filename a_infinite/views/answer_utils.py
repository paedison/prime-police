import json
from collections import defaultdict

from django.db.models import F, Window
from django.db.models.functions import Rank
from django.urls import reverse_lazy

from .staff_utils import bulk_create_or_update
from .. import models

PROBLEM_COUNT = 40


def get_subject_vars() -> dict[str, tuple[str, str, int]]:
    return {
        '형사': ('형사법', 'subject_0', 0),
        '헌법': ('헌법', 'subject_1', 1),
        '경찰': ('경찰학', 'subject_2', 2),
        '범죄': ('범죄학', 'subject_3', 3),
        '민법': ('민법총칙', 'subject_4', 4),
        '총점': ('총점', 'sum', 5),
    }


def get_field_vars() -> dict[str, tuple[str, str, int]]:
    return {
        'subject_0': ('형사', '형사법', 0),
        'subject_1': ('헌법', '헌법', 1),
        'subject_2': ('경찰', '경찰학', 2),
        'subject_3': ('범죄', '범죄학', 3),
        'subject_4': ('민법', '민법총칙', 4),
        'sum': ('총점', '총점', 5),
    }


def get_score_unit(sub):
    police_score_unit = {
        '형사': 3, '경찰': 3, '세법': 2, '회계': 2, '정보': 2,
        '시네': 2, '행법': 1, '행학': 1, '민법': 1,
    }
    return police_score_unit.get(sub, 1.5)


def get_answer_tab(exam) -> list:
    subject_vars = get_subject_vars()
    subject_vars.pop('총점')
    answer_tab = []
    for sub, (subject, fld, idx) in subject_vars.items():
        loop_list = get_loop_list()
        answer_tab.append({
            'id': str(idx), 'title': subject, 'loop_list': loop_list,
            'url_answer_input': reverse_lazy('infinite:answer-input', args=[exam.pk, fld])
        })
    return answer_tab


def get_loop_list():
    loop_list = []
    quotient = PROBLEM_COUNT // 10
    counter = [10] * quotient
    remainder = PROBLEM_COUNT % 10
    if remainder:
        counter.append(remainder)
    loop_min = 0
    for loop_idx in range(quotient):
        loop_list.append({'counter': counter[loop_idx], 'min': loop_min})
        loop_min += 10
    return loop_list


def get_is_confirmed_data(student) -> list:
    is_confirmed_data = [True if val else False for val in student.answer_count.values()]
    all_confirmed = sum(student.answer_count.values()) == PROBLEM_COUNT * 5
    is_confirmed_data.extend([all_confirmed, all_confirmed])  # Add is_confirmed_data for '총점, 평균'
    return is_confirmed_data


def get_input_answer_data_set(request) -> dict:
    subject_vars = get_subject_vars()
    subject_vars.pop('총점')
    empty_answer_data = {fld: [0 for _ in range(PROBLEM_COUNT)] for _, (_, fld, _) in subject_vars.items()}
    answer_data_set_cookie = request.COOKIES.get('answer_data_set', '{}')
    answer_data_set = json.loads(answer_data_set_cookie) or empty_answer_data
    return answer_data_set


def get_empty_dict_stat_data(
        student: models.Student,
        is_confirmed_data: list,
        answer_data_set: dict,
        subject_vars: dict,
) -> list[dict]:
    total_answer_count = 0
    stat_data = []
    for sub, (subject, fld, fld_idx) in subject_vars.items():
        problem_count = PROBLEM_COUNT * 5 if sub == '총점' else PROBLEM_COUNT
        url_answer_input = student.exam.get_answer_input_url(fld) if sub != '총점' else ''
        answer_list = answer_data_set.get(fld)
        saved_answers = []
        if answer_list:
            saved_answers = [ans for ans in answer_list if ans]
        answer_count = max(student.answer_count.get(fld, 0), len(saved_answers))
        total_answer_count += answer_count
        time_schedule = get_time_schedule(student.exam)[sub]

        stat_data.append({
            'field': fld, 'sub': sub, 'subject': subject,
            'start_time': time_schedule[0],
            'end_time': time_schedule[1],

            'participants': 0,
            'is_confirmed': is_confirmed_data[fld_idx],
            'url_answer_input': url_answer_input,

            'problem_count': problem_count,
            'answer_count': answer_count,

            'rank': 0, 'score': 0, 'max_score': 0,
            'top_score_10': 0, 'top_score_25': 0, 'top_score_50': 0, 'avg_score': 0,
        })
    stat_data[-1]['answer_count'] = total_answer_count
    return stat_data


def get_dict_stat_data(request, student: models.Student, is_confirmed_data: list):
    answer_data_set = get_input_answer_data_set(request)

    subject_vars = get_subject_vars()
    stat_data = get_empty_dict_stat_data(student, is_confirmed_data, answer_data_set, subject_vars)
    qs_answer = models.Answer.objects.infinite_qs_answer_by_student(student)
    qs_score = models.Score.objects.infinite_qs_score_by_student(student)

    participants_dict = {subject_vars[qs_a['problem__subject']][1]: qs_a['participant_count'] for qs_a in qs_answer}
    participants_dict['sum'] = participants_dict[min(participants_dict)] if participants_dict else 0
    update_dict_stat_data(student, qs_score, stat_data, participants_dict)

    return stat_data


def update_dict_stat_data(student, qs_score, stat_data: list, participants_dict: dict):
    field_vars = get_field_vars()
    scores = {fld: [] for fld in field_vars}
    for stat in stat_data:
        fld = stat['field']
        if fld in participants_dict.keys():
            participants = participants_dict.get(fld, 0)
            stat['participants'] = participants
            for qs_s in qs_score:
                fld_score = qs_s[fld]
                if fld_score is not None:
                    scores[fld].append(fld_score)

            student_score = getattr(student.score, fld)
            if scores[fld] and student_score:
                sorted_scores = sorted(scores[fld], reverse=True)

                def get_top_score(_sorted_scores, percentage):
                    if _sorted_scores:
                        threshold = max(1, int(participants * percentage))
                        return _sorted_scores[threshold - 1]

                stat.update({
                    'score': student_score,
                    'rank': sorted_scores.index(student_score) + 1,
                    'max_score': sorted_scores[0],
                    'top_score_10': get_top_score(sorted_scores, 0.10),
                    'top_score_25': get_top_score(sorted_scores, 0.25),
                    'top_score_50': get_top_score(sorted_scores, 0.50),
                    'avg_score': round(sum(sorted_scores) / participants, 1),
                })


def get_time_schedule(exam: models.Exam):
    return {
        '형사': (exam.exam_started_at, exam.exam_1_end_time),
        '헌법': (exam.exam_started_at, exam.exam_1_end_time),
        '경찰': (exam.exam_2_start_time, exam.exam_finished_at),
        '범죄': (exam.exam_2_start_time, exam.exam_finished_at),
        '민법': (exam.exam_2_start_time, exam.exam_finished_at),
        '총점': (exam.exam_started_at, exam.exam_finished_at),
    }


def get_dict_stat_chart(stat_data_total) -> dict:
    return {
        'my_score': [stat['score'] for stat in stat_data_total],
        'top_score_10': [stat['top_score_10'] for stat in stat_data_total],
        'top_score_25': [stat['top_score_25'] for stat in stat_data_total],
        'top_score_50': [stat['top_score_50'] for stat in stat_data_total],
        'max_score': [stat['max_score'] for stat in stat_data_total],
        'avg_score': [stat['avg_score'] for stat in stat_data_total],
    }


def frequency_table_by_bin(scores, bin_size=10, target_score=None):
    freq = defaultdict(int)

    for score in scores:
        bin_start = int((score // bin_size) * bin_size)
        bin_end = bin_start + bin_size
        bin_label = f'{bin_start}~{bin_end}'
        freq[bin_label] += 1

    # bin_start 기준으로 정렬
    sorted_freq = dict(sorted(freq.items(), key=lambda x: int(x[0].split('~')[0])))

    # 특정 점수의 구간 구하기
    target_bin = None
    if target_score is not None:
        bin_start = int((target_score // bin_size) * bin_size)
        bin_end = bin_start + bin_size
        target_bin = f'{bin_start}~{bin_end}'

    return sorted_freq, target_bin


def get_dict_stat_frequency(student) -> dict:
    score_frequency_list = models.Student.objects.filter(exam=student.exam).values_list('score__sum', flat=True)
    scores = [round(score, 1) for score in score_frequency_list]
    sorted_freq, target_bin = frequency_table_by_bin(scores, target_score=student.score.sum)

    score_label = []
    score_data = []
    score_color = []
    for key, val in sorted_freq.items():
        score_label.append(key)
        score_data.append(val)
        color = 'rgba(255, 99, 132, 0.5)' if key == target_bin else 'rgba(54, 162, 235, 0.5)'
        score_color.append(color)

    return {'score_data': score_data, 'score_label': score_label, 'score_color': score_color}


def get_data_answers(qs_student_answer):
    subject_vars = get_subject_vars()
    subject_vars.pop('총점')
    data_answers = [[] for _ in subject_vars]

    for qs_sa in qs_student_answer:
        sub = qs_sa.problem.subject
        subject, field, idx = subject_vars[sub]

        ans_official = qs_sa.problem.answer
        ans_student = qs_sa.answer
        ans_predict = qs_sa.problem.answer_count.answer_predict

        qs_sa.field = field
        qs_sa.subject = subject
        qs_sa.no = qs_sa.problem.number

        qs_sa.ans_official = ans_official
        qs_sa.ans_official_circle = qs_sa.problem.get_answer_display()

        qs_sa.ans_student = ans_student
        qs_sa.ans_student_circle = qs_sa.get_answer_display()

        qs_sa.ans_predict = ans_predict
        qs_sa.rate_accuracy = qs_sa.problem.answer_count.get_answer_predict_rate()

        qs_sa.rate_correct = qs_sa.problem.answer_count.get_answer_rate(ans_official)
        qs_sa.rate_correct_top = get_answer_rate_by_rank_type(qs_sa.problem, 'top', ans_official)
        qs_sa.rate_correct_mid = get_answer_rate_by_rank_type(qs_sa.problem, 'mid', ans_official)
        qs_sa.rate_correct_low = get_answer_rate_by_rank_type(qs_sa.problem, 'low', ans_official)

        qs_sa.rate_selection = qs_sa.problem.answer_count.get_answer_rate(ans_student)
        qs_sa.rate_selection_top = get_answer_rate_by_rank_type(qs_sa.problem, 'top', ans_student)
        qs_sa.rate_selection_mid = get_answer_rate_by_rank_type(qs_sa.problem, 'mid', ans_student)
        qs_sa.rate_selection_low = get_answer_rate_by_rank_type(qs_sa.problem, 'low', ans_student)

        data_answers[idx].append(qs_sa)
    return data_answers


def get_answer_rate_by_rank_type(problem, rank_type: str, ans_official):
    attr_name = f'answer_count_{rank_type}_rank'
    if hasattr(problem, attr_name):
        return getattr(problem, attr_name).get_answer_rate(ans_official)


def create_confirmed_answers(student, sub, answer_data):
    list_create = []
    for no, ans in enumerate(answer_data, start=1):
        problem = models.Problem.objects.get(exam=student.exam, subject=sub, number=no)
        list_create.append(models.Answer(student=student, problem=problem, answer=ans))
    bulk_create_or_update(models.Answer, list_create, [], [])


def update_answer_count_after_confirm(exam, sub, answer_data):
    qs_answer_count = models.AnswerCount.objects.infinite_qs_answer_count_by_exam(exam).filter(sub=sub)
    for qs_ac in qs_answer_count:
        ans_student = answer_data[qs_ac.problem.number - 1]
        count_number = getattr(qs_ac, f'count_{ans_student}')
        count_sum = getattr(qs_ac, f'count_{ans_student}')
        setattr(qs_ac, f'count_{ans_student}', count_number + 1)
        setattr(qs_ac, f'count_sum', count_sum + 1)
        qs_ac.save()


def update_score_after_confirm(student: models.Student, sub: str):
    score_field = get_subject_vars()[sub][1]
    score_unit = get_score_unit(sub)
    qs_student_answer = models.Answer.objects.infinite_qs_answer_by_student_with_predict_result(student)

    correct_count = qs_student_answer.filter(problem__subject=sub, real_result=True).count()
    setattr(student.score, score_field, correct_count * score_unit)
    student.score.save()


def update_rank_after_confirm(qs_student, student, subject_field: str):
    def rank_func(field_name) -> Window:
        return Window(expression=Rank(), order_by=F(field_name).desc())

    rank_list = qs_student.annotate(**{
        f'rank_{subject_field}': rank_func(f'score__{subject_field}'),
        'rank_sum': rank_func(f'score__sum')
    })
    participants = rank_list.count()

    target_rank, _ = models.Rank.objects.get_or_create(student=student)
    fields_not_match = [target_rank.participants != participants]

    for entry in rank_list:
        if entry.id == student.id:
            rank_for_field = getattr(entry, f'rank_{subject_field}')
            rank_for_sum = getattr(entry, f'rank_sum')
            fields_not_match.append(getattr(target_rank, subject_field) != rank_for_field)
            fields_not_match.append(target_rank.sum != entry.rank_sum)

            if any(fields_not_match):
                target_rank.participants = participants
                setattr(target_rank, subject_field, rank_for_field)
                setattr(target_rank, 'sum', rank_for_sum)
                target_rank.save()


def update_statistics_after_confirm(student, subject_field):
    stat, _ = models.Statistics.objects.get_or_create(exam=student.exam)
    getattr(stat, subject_field)['participants'] += 1

    answer_student_counts = models.Answer.objects.filter(student=student).count()
    if answer_student_counts == PROBLEM_COUNT * 5:
        stat.sum['participants'] += 1
    stat.save()


def get_next_url_for_answer_input(student: models.Student):
    subject_vars = get_subject_vars()
    subject_vars.pop('총점')
    for _, (_, subject_field, _) in subject_vars.items():
        if student.answer_count[subject_field] == 0:
            return student.exam.get_answer_input_url(subject_field)
    return student.exam.get_answer_detail_url()
