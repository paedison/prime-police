import io
import traceback
from collections import defaultdict
from urllib.parse import quote

import django.db.utils
import pandas as pd
from django.db import transaction
from django.db.models import Count, F, Window
from django.db.models.functions import Rank
from django.http import HttpResponse
from django.shortcuts import get_object_or_404

from a_common.prime_test import model_settings
from .. import models, utils

PROBLEM_COUNT = 40


def get_sub_list() -> list:
    return ['형사', '헌법', '경찰', '범죄', '민법']


def get_subject_list() -> list:
    return ['형사법', '헌법', '경찰학', '범죄학', '민법총칙']


def get_answer_tab() -> list:
    return [{'id': str(idx), 'title': subject} for idx, subject in enumerate(get_subject_list())]


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


def get_answer_count_models():
    return {
        'all': models.AnswerCount,
        'top': models.AnswerCountTopRank,
        'mid': models.AnswerCountMidRank,
        'low': models.AnswerCountLowRank,
    }


def get_answer_page_data(qs_answer_count, page_number, per_page=10):
    subject_vars = get_subject_vars()
    qs_answer_count_group, answers_page_obj_group, answers_page_range_group = {}, {}, {}

    for entry in qs_answer_count:
        if entry.subject not in qs_answer_count_group:
            qs_answer_count_group[entry.subject] = []
        qs_answer_count_group[entry.subject].append(entry)

    for subject, qs_answer_count in qs_answer_count_group.items():
        if subject not in answers_page_obj_group:
            answers_page_obj_group[subject] = []
            answers_page_range_group[subject] = []
        data_answers = get_data_answers(qs_answer_count, subject_vars)
        answers_page_obj_group[subject], answers_page_range_group[subject] = utils.get_paginator_data(
            data_answers, page_number, per_page)

    return answers_page_obj_group, answers_page_range_group


def get_data_answers(qs_answer_count, subject_vars):
    for qs_ac in qs_answer_count:
        sub = qs_ac.subject
        field = subject_vars[sub][1]
        ans_official = qs_ac.ans_official

        answer_official_list = []
        if ans_official > 5:
            answer_official_list = [int(digit) for digit in str(ans_official)]

        qs_ac.no = qs_ac.number
        qs_ac.ans_official = ans_official
        qs_ac.ans_official_circle = qs_ac.problem.get_answer_display
        qs_ac.ans_predict_circle = model_settings.answer_choice().get(qs_ac.ans_predict)
        qs_ac.ans_list = answer_official_list
        qs_ac.field = field

        qs_ac.rate_correct = qs_ac.get_answer_rate(ans_official)
        qs_ac.rate_correct_top = get_answer_rate_by_rank_type(qs_ac.problem, 'top', ans_official)
        qs_ac.rate_correct_mid = get_answer_rate_by_rank_type(qs_ac.problem, 'mid', ans_official)
        qs_ac.rate_correct_low = get_answer_rate_by_rank_type(qs_ac.problem, 'low', ans_official)
        if qs_ac.rate_correct_top is not None and qs_ac.rate_correct_low is not None:
            qs_ac.rate_gap = qs_ac.rate_correct_top - qs_ac.rate_correct_low

    return qs_answer_count


def get_answer_rate_by_rank_type(problem, rank_type: str, ans_official):
    attr_name = f'answer_count_{rank_type}_rank'
    if hasattr(problem, attr_name):
        return getattr(problem, attr_name).get_answer_rate(ans_official)


def update_problem_model_for_answer_official(exam, form, file) -> tuple:
    message_dict = {
        None: '에러가 발생했습니다.',
        True: '문제 정답을 업데이트했습니다.',
        False: '기존 정답 데이터와 일치합니다.',
    }
    list_update = []
    list_create = []

    if form.is_valid():
        df = pd.read_excel(file, header=0, index_col=0)
        df = df.infer_objects(copy=False)
        df.fillna(value=0, inplace=True)

        for subject, rows in df.items():
            for number, answer in rows.items():
                if answer:
                    try:
                        problem = models.Problem.objects.get(exam=exam, subject=subject[0:2], number=number)
                        if problem.answer != answer:
                            problem.answer = answer
                            list_update.append(problem)
                    except models.Problem.DoesNotExist:
                        problem = models.Problem(exam=exam, subject=subject, number=number, answer=answer)
                        list_create.append(problem)
                    except ValueError as error:
                        print(error)
        update_fields = ['answer']
        is_updated = bulk_create_or_update(models.Problem, list_create, list_update, update_fields)
    else:
        is_updated = None
        print(form)
    return is_updated, message_dict[is_updated]


def update_scores(qs_student):
    message_dict = {
        None: '에러가 발생했습니다.',
        True: '점수를 업데이트했습니다.',
        False: '기존 점수와 일치합니다.',
    }
    is_updated_list = [update_score_model_for_score(qs_student)]
    if None in is_updated_list:
        is_updated = None
    elif any(is_updated_list):
        is_updated = True
    else:
        is_updated = False
    return is_updated, message_dict[is_updated]


def update_score_model_for_score(qs_student):
    answer_model = models.Answer
    score_model = models.Score
    sub_list = get_sub_list()

    list_update = []
    list_create = []

    for qs_s in qs_student:
        original_score_instance, _ = score_model.objects.get_or_create(student=qs_s)

        score_list = []
        fields_not_match = []
        for idx, sub in enumerate(sub_list):
            score_unit = get_score_unit(sub)
            qs_answer = (
                answer_model.objects.filter(student=qs_s, problem__subject=sub)
                .annotate(answer_correct=F('problem__answer'), answer_student=F('answer'))
            )
            if qs_answer:
                correct_count = 0
                for qs_a in qs_answer:
                    answer_correct_list = [int(digit) for digit in str(qs_a.answer_correct)]
                    correct_count += 1 if qs_a.answer_student in answer_correct_list else 0
                score = correct_count * score_unit
                score_list.append(score)
                fields_not_match.append(getattr(original_score_instance, f'subject_{idx}') != score)

        score_sum = sum(score_list)
        fields_not_match.append(original_score_instance.sum != score_sum)

        if any(fields_not_match):
            for idx, score in enumerate(score_list):
                setattr(original_score_instance, f'subject_{idx}', score)
            original_score_instance.sum = score_sum
            list_update.append(original_score_instance)

    update_fields = ['subject_0', 'subject_1', 'subject_2', 'subject_3', 'subject_4', 'sum']
    return bulk_create_or_update(score_model, list_create, list_update, update_fields)


def update_ranks(qs_student):
    message_dict = {
        None: '에러가 발생했습니다.',
        True: '등수를 업데이트했습니다.',
        False: '기존 등수와 일치합니다.',
    }
    is_updated_list = [update_rank_model(qs_student)]
    if None in is_updated_list:
        is_updated = None
    elif any(is_updated_list):
        is_updated = True
    else:
        is_updated = False
    return is_updated, message_dict[is_updated]


def update_rank_model(qs_student):
    rank_model = models.Rank

    list_create = []
    list_update = []
    subject_count = 5

    def rank_func(field_name) -> Window:
        return Window(expression=Rank(), order_by=F(field_name).desc())

    annotate_dict = {f'rank_{idx}': rank_func(f'score__subject_{idx}') for idx in range(subject_count)}
    annotate_dict[f'rank_sum'] = rank_func('score__sum')

    for qs_s in qs_student:
        rank_list = qs_student.annotate(**annotate_dict)
        target, _ = rank_model.objects.get_or_create(student=qs_s)

        participants = rank_list.count()
        fields_not_match = [target.participants != participants]

        for row in rank_list:
            if row.id == qs_s.id:
                for idx in range(subject_count):
                    fields_not_match.append(
                        getattr(target, f'subject_{idx}') != getattr(row, f'rank_{idx}')
                    )
                fields_not_match.append(getattr(target, f'sum') != getattr(row, f'rank_sum'))

                if any(fields_not_match):
                    for idx in range(subject_count):
                        setattr(target, f'subject_{idx}', getattr(row, f'rank_{idx}'))
                    setattr(target, f'sum', getattr(row, f'rank_sum'))
                    setattr(target, f'participants', participants)
                    list_update.append(target)

    update_fields = ['subject_0', 'subject_1', 'subject_2', 'subject_3', 'subject_4', 'sum', 'participants']
    return bulk_create_or_update(rank_model, list_create, list_update, update_fields)


def get_data_statistics(exam):
    field_vars = get_field_vars()
    student_model = models.Student

    data_statistics = [{'participants': 0}]
    score_list = {'전체': {fld: [] for fld in field_vars}}

    qs_students = (
        student_model.objects.filter(exam=exam).select_related('exam', 'score', 'rank')
        .annotate(
            subject_0=F('score__subject_0'),
            subject_1=F('score__subject_1'),
            subject_2=F('score__subject_2'),
            subject_3=F('score__subject_3'),
            subject_4=F('score__subject_4'),
            sum=F('score__sum'),
        )
    )
    for qs_s in qs_students:
        for fld in field_vars:
            score = getattr(qs_s, fld)
            if score is not None:
                score_list['전체'][fld].append(score)

    update_data_statistics(data_statistics, score_list, field_vars)
    return data_statistics


def update_data_statistics(data_statistics, score_list, field_vars):
    for _, score_dict in score_list.items():
        for fld, scores in score_dict.items():
            sub = field_vars[fld][0]
            subject = field_vars[fld][1]
            participants = len(scores)
            sorted_scores = sorted(scores, reverse=True)

            def get_top_score(percentage):
                if sorted_scores:
                    threshold = max(1, int(participants * percentage))
                    return sorted_scores[threshold - 1]

            data_statistics[0][fld] = {
                'field': fld,
                'is_confirmed': True,
                'sub': sub,
                'subject': subject,
                'participants': participants,
                'max': sorted_scores[0] if sorted_scores else None,
                't10': get_top_score(0.10),
                't25': get_top_score(0.25),
                't50': get_top_score(0.50),
                'avg': round(sum(scores) / participants, 1) if sorted_scores else None,
            }


def update_statistics(exam):
    message_dict = {
        None: '에러가 발생했습니다.',
        True: '통계를 업데이트했습니다.',
        False: '기존 통계와 일치합니다.',
    }
    data_statistics = get_data_statistics(exam)
    is_updated_list = [update_statistics_model(exam, data_statistics, models.Statistics)]
    if None in is_updated_list:
        is_updated = None
    elif any(is_updated_list):
        is_updated = True
    else:
        is_updated = False
    return is_updated, message_dict[is_updated]


def update_statistics_model(exam, data_statistics, statistics_model):
    field_vars = get_field_vars()
    list_update = []
    list_create = []

    for data_stat in data_statistics:
        stat_dict = {}
        for fld, (_, subject, _) in field_vars.items():
            stat_dict.update({
                fld: {
                    'subject': subject,
                    'participants': data_stat[fld]['participants'],
                    'max': data_stat[fld]['max'],
                    't10': data_stat[fld]['t10'],
                    't25': data_stat[fld]['t25'],
                    't50': data_stat[fld]['t50'],
                    'avg': data_stat[fld]['avg'],
                }
            })

        try:
            new_query = statistics_model.objects.get(exam=exam)
            fields_not_match = any(getattr(new_query, fld) != val for fld, val in stat_dict.items())
            if fields_not_match:
                for fld, val in stat_dict.items():
                    setattr(new_query, fld, val)
                list_update.append(new_query)
        except statistics_model.DoesNotExist:
            list_create.append(statistics_model(exam=exam, **stat_dict))
    update_fields = []
    update_fields.extend([f'{key}' for key in field_vars])
    return bulk_create_or_update(statistics_model, list_create, list_update, update_fields)


def update_answer_counts(exam):
    message_dict = {
        None: '에러가 발생했습니다.',
        True: '문항 분석표를 업데이트했습니다.',
        False: '기존 문항 분석표와 일치합니다.',
    }
    answer_count_models = get_answer_count_models()
    is_updated_list = [
        update_answer_count_model(exam, answer_count_models, 'all'),
        update_answer_count_model(exam, answer_count_models, 'top'),
        update_answer_count_model(exam, answer_count_models, 'mid'),
        update_answer_count_model(exam, answer_count_models, 'low'),
    ]
    if None in is_updated_list:
        is_updated = None
    elif any(is_updated_list):
        is_updated = True
    else:
        is_updated = False
    return is_updated, message_dict[is_updated]


def update_answer_count_model(exam, answer_count_models, rank_type='all'):
    answer_count_model = answer_count_models[rank_type]

    list_update = []
    list_create = []

    lookup_field = f'student__rank__sum'
    top_rank_threshold = 0.27
    mid_rank_threshold = 0.73
    participants_function = F(f'student__rank__participants')

    lookup_exp = {}
    if rank_type == 'top':
        lookup_exp[f'{lookup_field}__lte'] = participants_function * top_rank_threshold
    elif rank_type == 'mid':
        lookup_exp[f'{lookup_field}__gt'] = participants_function * top_rank_threshold
        lookup_exp[f'{lookup_field}__lte'] = participants_function * mid_rank_threshold
    elif rank_type == 'low':
        lookup_exp[f'{lookup_field}__gt'] = participants_function * mid_rank_threshold

    answer_distribution = (
        models.Answer.objects.filter(problem__exam=exam, **lookup_exp)
        .select_related('student', 'student__rank')
        .values('problem_id', 'answer')
        .annotate(count=Count('id')).order_by('problem_id', 'answer')
    )
    organized_distribution = defaultdict(lambda: {i: 0 for i in range(6)})

    for entry in answer_distribution:
        problem_id = entry['problem_id']
        answer = entry['answer']
        count = entry['count']
        organized_distribution[problem_id][answer] = count

    count_fields = [
        'count_0', 'count_1', 'count_2', 'count_3', 'count_4', 'count_multiple',
    ]
    for problem_id, answers_original in organized_distribution.items():
        answers = {'count_multiple': 0}
        for answer, count in answers_original.items():
            if answer <= 4:
                answers[f'count_{answer}'] = count
            else:
                answers['count_multiple'] = count
        answers['count_sum'] = sum(answers[fld] for fld in count_fields)

        try:
            new_query = answer_count_model.objects.get(problem_id=problem_id)
            fields_not_match = any(getattr(new_query, fld) != val for fld, val in answers.items())
            if fields_not_match:
                for fld, val in answers.items():
                    setattr(new_query, fld, val)
                list_update.append(new_query)
        except answer_count_model.DoesNotExist:
            list_create.append(answer_count_model(problem_id=problem_id, **answers))
    update_fields = [
        'problem_id', 'count_0', 'count_1', 'count_2', 'count_3', 'count_4',
        'count_multiple', 'count_sum',
    ]
    return bulk_create_or_update(answer_count_model, list_create, list_update, update_fields)


def create_default_problems(exam, df: pd.DataFrame):
    list_update = []
    list_create = []
    for subject, answer_data in df.items():
        for number, answer in zip(answer_data.index, answer_data.values):
            problem_info = {'exam': exam, 'subject': subject, 'number': number}
            try:
                problem = models.Problem.objects.get(**problem_info)
                if problem.answer != answer:
                    list_update.append(models.Problem(**problem_info, answer=answer))
            except models.Problem.DoesNotExist:
                list_create.append(models.Problem(**problem_info, answer=answer))
    bulk_create_or_update(models.Problem, list_create, list_update, ['answer'])


def create_default_statistics(exam):
    model = models.Statistics
    if model:
        statistics, _ = model.objects.get_or_create(exam=exam)
        field_list = ['subject_0', 'subject_1', 'subject_2', 'subject_3', 'subject_4', 'sum']
        for field_name in field_list:
            field_value = getattr(statistics, field_name)
            field_value['subject'] = model._meta.get_field(field_name).verbose_name
            setattr(statistics, field_name, field_value)
        statistics.save()


def create_default_answer_counts(problems):
    answer_count_models = get_answer_count_models()
    for rank_type, model in answer_count_models.items():
        list_create = []
        if model:
            for problem in problems:
                try:
                    model.objects.get(problem=problem)
                except model.DoesNotExist:
                    list_create.append(model(problem=problem))
        bulk_create_or_update(model, list_create, [], [])


def bulk_create_or_update(model, list_create, list_update, update_fields):
    model_name = model._meta.model_name
    try:
        with transaction.atomic():
            if list_create:
                model.objects.bulk_create(list_create)
                message = f'Successfully created {len(list_create)} {model_name} instances.'
                is_updated = True
            elif list_update:
                model.objects.bulk_update(list_update, list(update_fields))
                message = f'Successfully updated {len(list_update)} {model_name} instances.'
                is_updated = True
            else:
                message = f'No changes were made to {model_name} instances.'
                is_updated = False
    except django.db.utils.IntegrityError:
        traceback_message = traceback.format_exc()
        print(traceback_message)
        message = f'Error occurred.'
        is_updated = None
    print(message)
    return is_updated


def get_statistics_response(exam):
    field_vars = get_field_vars()
    qs_statistics = get_object_or_404(models.Statistics, exam=exam)
    data_statistics = []
    for fld in field_vars:
        data_statistics.append(getattr(qs_statistics, fld))
    df = pd.DataFrame(data_statistics)

    filename = f'무한반_{exam.get_round_display()}_성적통계.xlsx'
    column_label = [
        ('과목',), ('응시생 수',), ('최고 점수',), ('상위 10%',), ('상위 25%',), ('상위 50%',), ('평균',)
    ]

    return get_response_for_excel_file(df, [], column_label, filename)


def get_catalog_response(exam):
    student_list = models.Student.objects.infinite_qs_student_list_by_exam(exam)
    df = pd.DataFrame.from_records(student_list.values())
    df['created_at'] = df['created_at'].dt.tz_convert('Asia/Seoul').dt.tz_localize(None)
    df['latest_answer_time'] = df['latest_answer_time'].dt.tz_convert('Asia/Seoul').dt.tz_localize(None)

    filename = f'무한반_{exam.get_round_display()}_성적일람표.xlsx'
    column_label = [
        ('ID', ''), ('등록일시', ''), ('Exam ID', ''), ('User ID', ''), ('이름', ''),
        ('최종답안 등록일시', ''), ('제출 답안수', ''), ('참여자 수', ''),
    ]
    field_vars = get_field_vars()
    for _, (_, subject, _) in field_vars.items():
        column_label.extend([
            (subject, '점수'),
            (subject, '등수'),
        ])
    return get_response_for_excel_file(df, [], column_label, filename)


def get_answer_response(exam):
    qs_answer_count = models.AnswerCount.objects.infinite_qs_answer_count_by_exam_and_subject(exam)
    df = pd.DataFrame.from_records(qs_answer_count.values())

    def move_column(col_name: str, loc: int):
        col = df.pop(col_name)
        df.insert(loc, col_name, col)

    move_column('problem_id', 1)
    move_column('subject', 2)
    move_column('number', 3)
    move_column('ans_official', 4)
    move_column('ans_predict', 5)

    filename = f'무한반_{exam.get_round_display()}_문항분석표.xlsx'
    drop_columns = [
        'answer_predict', 'count_1', 'count_2', 'count_3', 'count_4', 'count_0', 'count_multiple', 'count_sum',
    ]

    column_label = [
        ('ID', '', ''), ('문제 ID', '', ''), ('과목', '', ''),
        ('번호', '', ''), ('정답', '', ''), ('예상 정답', '', ''),
    ]
    top_field = ['전체 데이터']
    for top in top_field:
        for mid in ['전체', '상위권', '중위권', '하위권']:
            column_label.extend([
                (top, mid, '①'), (top, mid, '②'), (top, mid, '③'), (top, mid, '④'), (top, mid, '합계'),
            ])

    return get_response_for_excel_file(df, drop_columns, column_label, filename)


def get_response_for_excel_file(df, drop_columns, column_label, filename):
    df.drop(columns=drop_columns, inplace=True)
    df.columns = pd.MultiIndex.from_tuples(column_label)
    df.reset_index(inplace=True)

    excel_data = io.BytesIO()
    df.to_excel(excel_data, engine='xlsxwriter')

    response = HttpResponse(
        excel_data.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename={quote(filename)}'

    return response
