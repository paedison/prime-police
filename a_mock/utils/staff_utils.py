import io
from collections import defaultdict
from dataclasses import dataclass
from urllib.parse import quote

import numpy as np
import pandas as pd
from django.db.models import Count, F, Window, QuerySet
from django.db.models.functions import Rank
from django.http import HttpResponse
from django.shortcuts import get_object_or_404

from a_common.prime_test import model_settings
from a_common.utils import HtmxHttpRequest, get_paginator_context
from a_common.utils.modify_models_methods import *
from a_mock.utils.common_utils import *
from a_mock import models, forms

UPDATE_MESSAGES = {
    'student': get_update_messages('제출 답안'),
    'score': get_update_messages('점수'),
    'rank': get_update_messages('등수'),
    'statistics': get_update_messages('통계'),
    'answer_count': get_update_messages('문항분석표'),
}


@dataclass(kw_only=True)
class AdminListData:
    request: HtmxHttpRequest

    def __post_init__(self):
        request_data = RequestData(request=self.request)
        self.view_type = request_data.view_type
        self.page_number = request_data.page_number

    def get_exam_context(self):
        exam_list = models.Exam.objects.mock_qs_exam_list()
        return get_paginator_context(exam_list, self.page_number)

    def get_student_context(self):
        student_list = models.Student.objects.mock_qs_student_list()
        return get_paginator_context(student_list, self.page_number)


@dataclass(kw_only=True)
class AdminDetailData:
    request: HtmxHttpRequest
    exam: models.Exam

    def __post_init__(self):
        request_data = RequestData(request=self.request)
        self.model = ModelData()
        exam_data = ExamData(exam=self.exam)

        self._subject_vars = exam_data.subject_vars
        self._subject_vars_avg = exam_data.subject_vars_sum

        self.exam_subject = request_data.exam_subject
        self.view_type = request_data.view_type
        self.page_number = request_data.page_number
        self.student_name = request_data.student_name

    @staticmethod
    def get_answer_tab() -> list:
        return [{'id': str(idx), 'title': subject} for idx, subject in enumerate(get_subject_list())]

    def get_admin_statistics_context(self, per_page=10) -> dict:
        qs_statistics = self.model.statistics.objects.filter(exam=self.exam)
        statistics_context = get_paginator_context(qs_statistics, self.page_number, per_page)
        return {'statistics_context': statistics_context}

    def get_admin_catalog_context(self, for_search=False) -> dict:
        student_list = self.model.student.objects.mock_qs_student_list_by_exam(self.exam)
        if for_search:
            student_list = student_list.filter(name=self.student_name)
        catalog_context = get_paginator_context(student_list, self.page_number)
        return {'catalog_context': catalog_context}

    def get_admin_answer_context(self, for_pagination=False, per_page=10) -> dict:
        sub_list = [sub for sub in self._subject_vars]
        subject = self.exam_subject if for_pagination else None
        qs_answer_count = self.model.ac_all.objects.mock_qs_answer_count_by_exam_and_subject(
            exam=self.exam, subject=subject)
        qs_answer_count_group = {sub: [] for sub in sub_list}
        answer_context = {}

        for qs_ac in qs_answer_count:
            qs_answer_count_group[qs_ac.subject].append(qs_ac)

        for sub, answers in qs_answer_count_group.items():
            answer_data = self.get_admin_answer_data(answers)
            context = get_paginator_context(answer_data, self.page_number, per_page)
            context.update({
                'id': str(sub_list.index(sub)),
                'title': sub,
                'prefix': 'Answer',
                'header': 'answer_list',
                'answer_count': 4,
            })
            answer_context[sub] = context

        return {'answer_context': answer_context}

    def get_admin_answer_data(self, qs_answer_count: QuerySet) -> QuerySet:
        for qs_ac in qs_answer_count:
            sub = qs_ac.subject
            field = self._subject_vars[sub][1]
            ans_official = qs_ac.ans_official

            answer_official_list = []
            if ans_official > 5:
                answer_official_list = [int(digit) for digit in str(ans_official)]

            qs_ac.no = qs_ac.number
            qs_ac.ans_official = ans_official
            qs_ac.ans_official_circle = qs_ac.problem.get_answer_display()
            qs_ac.ans_list = answer_official_list
            qs_ac.field = field

            qs_ac.rate_correct = qs_ac.get_answer_rate(ans_official)
            qs_ac.rate_correct_top = qs_ac.problem.answer_count_top_rank.get_answer_rate(ans_official)
            qs_ac.rate_correct_mid = qs_ac.problem.answer_count_mid_rank.get_answer_rate(ans_official)
            qs_ac.rate_correct_low = qs_ac.problem.answer_count_low_rank.get_answer_rate(ans_official)
            try:
                qs_ac.rate_gap = qs_ac.rate_correct_top - qs_ac.rate_correct_low
            except TypeError:
                qs_ac.rate_gap = None

        return qs_answer_count


@dataclass(kw_only=True)
class AdminCreateData:
    request: HtmxHttpRequest
    form: forms.ExamForm

    def __post_init__(self):
        self.model = ModelData()
        self.year = self.form.cleaned_data['year']
        self.answer_file = self.request.FILES['answer_file']

    def process_post_request(self):
        try:
            exam = models.Exam.objects.get(year=self.year)
            exam.is_active = True
            exam.page_opened_at = self.form.cleaned_data['page_opened_at']
            exam.exam_started_at = self.form.cleaned_data['exam_started_at']
            exam.exam_finished_at = self.form.cleaned_data['exam_finished_at']
            exam.save()
        except models.Exam.DoesNotExist:
            exam = self.form.save()

        self.create_default_problems(exam)
        self.create_default_statistics(exam)
        self.create_default_answer_counts(exam)

    def create_default_problems(self, exam):
        df = pd.read_excel(self.answer_file, header=0, index_col=0)
        df = df.infer_objects(copy=False)

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

    def create_default_statistics(self, exam):
        model = self.model.statistics
        if model:
            statistics, _ = model.objects.get_or_create(exam=exam)
            field_list = ['subject_0', 'subject_1', 'subject_2', 'subject_3', 'subject_4', 'sum']
            for field_name in field_list:
                field_value = getattr(statistics, field_name)
                field_value['subject'] = model._meta.get_field(field_name).verbose_name
                setattr(statistics, field_name, field_value)
            statistics.save()

    def create_default_answer_counts(self, exam):
        problems = models.Problem.objects.filter(exam=exam).order_by('id')
        for rank_type, model in self.model.ac_models.items():
            list_create = []
            if model:
                for problem in problems:
                    try:
                        model.objects.get(problem=problem)
                    except model.DoesNotExist:
                        list_create.append(model(problem=problem))
            bulk_create_or_update(model, list_create, [], [])


@dataclass(kw_only=True)
class AdminUpdateData:
    request: HtmxHttpRequest
    exam: models.Exam

    def __post_init__(self):
        request_data = RequestData(request=self.request)
        self.exam_data = ExamData(exam=self.exam)
        self.model = ModelData()

        self._answer_file = self.request.FILES.get('file')
        self._subject_vars = self.exam_data.subject_vars
        self._subject_vars_sum = self.exam_data.subject_vars_sum
        self._sub_list = [sub for sub in self._subject_vars]
        self._qs_student = self.model.student.objects.filter(exam=self.exam).order_by('id')

        self.view_type = request_data.view_type

    def update_problem_model_for_answer_official(self):
        message_dict = {
            None: '에러가 발생했습니다.',
            True: '정답을 업데이트했습니다.',
            False: '기존 정답과 일치합니다.',
        }
        list_create, list_update = [], []

        form = forms.UploadFileForm(self.request.POST, self.request.FILES)
        file = self.request.FILES.get('file')

        if form.is_valid():
            df = pd.read_excel(file, header=0, index_col=0)
            df = df.infer_objects(copy=False)
            df.fillna(value=0, inplace=True)

            for subject, rows in df.items():
                for number, answer in rows.items():
                    if answer:
                        try:
                            problem = models.Problem.objects.get(exam=self.exam, subject=subject[0:2], number=number)
                            if problem.answer != answer:
                                problem.answer = answer
                                list_update.append(problem)
                        except models.Problem.DoesNotExist:
                            problem = models.Problem(exam=self.exam, subject=subject, number=number, answer=answer)
                            list_create.append(problem)
                        except ValueError as error:
                            print(error)
            update_fields = ['answer']
            print(list_create)
            print(list_update)
            is_updated = bulk_create_or_update(models.Problem, list_create, list_update, update_fields)
        else:
            is_updated = None
            print(form)
        return is_updated, message_dict[is_updated]

    @with_update_message(UPDATE_MESSAGES['score'])
    def update_answer_student(self):
        return [self.update_models_for_answer_student()]

    @with_update_message(UPDATE_MESSAGES['score'])
    def update_scores(self):
        return [self.update_score_model()]

    @with_update_message(UPDATE_MESSAGES['rank'])
    def update_ranks(self):
        return [self.update_rank_model(self.model.rank)]

    @with_update_message(UPDATE_MESSAGES['statistics'])
    def update_statistics(self):
        return [self.update_statistics_model()]

    @with_update_message(UPDATE_MESSAGES['answer_count'])
    def update_answer_counts(self):
        return [
            self.update_answer_count_model(self.model.ac_all),
            self.update_answer_count_model(self.model.ac_top),
            self.update_answer_count_model(self.model.ac_mid),
            self.update_answer_count_model(self.model.ac_low),
        ]

    def update_models_for_answer_student(self):
        student_model = self.model.student
        answer_model = self.model.answer

        qs_problem = models.Problem.objects.get_qs_problem(exam=self.exam)
        qs_problem_dict = {(qs_p.subject, qs_p.number): qs_p for qs_p in qs_problem}

        qs_student = student_model.objects.filter(exam=self.exam)
        qs_student_dict = {qs_s.serial: qs_s for qs_s in qs_student}

        label_name = ('이름', 'Unnamed: 1_level_1')
        label_password = ('비밀번호', 'Unnamed: 2_level_1')

        df = pd.read_excel(
            self._answer_file, sheet_name='문항별 표기', header=[0, 1], index_col=0, dtype={label_password: str})
        df = df.infer_objects(copy=False)
        df.fillna(value={label_name: '', label_password: '0000'}, inplace=True)

        is_updated_list = []
        for serial, row in df.iterrows():
            list_update = []
            list_create = []
            student_info = {'name': row[label_name], 'password': row[label_password]}

            student = qs_student_dict.get(str(serial))
            if student is None:
                student = student_model.objects.create(exam=self.exam, serial=serial, **student_info)
            else:
                fields_not_match = any(str(getattr(student, fld)) != val for fld, val in student_info.items())
                if fields_not_match:
                    for fld, val in student_info.items():
                        setattr(student, fld, val)
                    student.save()

            qs_answer = answer_model.objects.mock_qs_answer_with_sub_number(student)
            qs_answer_dict = {(qs_a.sub, qs_a.number): qs_a for qs_a in qs_answer}

            for sub, (subject, _, idx, problem_count) in self._subject_vars.items():
                for number in range(1, problem_count + 1):
                    answer = row[(subject, number)] if not np.isnan(row[(subject, number)]) else 0
                    student_answer = qs_answer_dict.get((sub, number))

                    if student_answer and student_answer.answer != answer:
                        student_answer.answer = answer
                        list_update.append(student_answer)

                    if student_answer is None:
                        problem = qs_problem_dict.get((sub, number))
                        list_create.append(answer_model(student=student, problem=problem, answer=answer))

            update_fields = ['answer']
            is_updated_list.append(bulk_create_or_update(answer_model, list_create, list_update, update_fields))
        return is_updated_list

    @with_bulk_create_or_update()
    def update_score_model(self):
        list_create, list_update = [], []

        for student in self._qs_student:
            original_score_instance, _ = self.model.score.objects.get_or_create(student=student)

            score_list = []
            fields_not_match = []
            for idx, sub in enumerate(self._sub_list):
                score_unit = self.exam_data.get_score_unit(sub)
                qs_answer = (
                    self.model.answer.objects.filter(student=student, problem__subject=sub)
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
        return self.model.score, list_create, list_update, update_fields

    @with_bulk_create_or_update()
    def update_rank_model(self, rank_model):
        list_create = []
        list_update = []
        subject_count = 5

        def rank_func(field_name) -> Window:
            return Window(expression=Rank(), order_by=F(field_name).desc())

        annotate_dict = {f'rank_{idx}': rank_func(f'score__subject_{idx}') for idx in range(subject_count)}
        annotate_dict[f'rank_sum'] = rank_func('score__sum')

        for qs_s in self._qs_student:
            rank_list = self._qs_student.annotate(**annotate_dict)
            target, _ = rank_model.objects.get_or_create(student=qs_s)

            participants = rank_list.count()
            fields_not_match = [target.participants != participants]

            for row in rank_list:
                if row.id == qs_s.id:
                    for idx in range(subject_count):
                        fields_not_match.append(getattr(target, f'subject_{idx}') != getattr(row, f'rank_{idx}'))
                    fields_not_match.append(getattr(target, f'sum') != getattr(row, f'rank_sum'))

                    if any(fields_not_match):
                        for idx in range(subject_count):
                            setattr(target, f'subject_{idx}', getattr(row, f'rank_{idx}'))
                        setattr(target, f'sum', getattr(row, f'rank_sum'))
                        setattr(target, f'participants', participants)
                        list_update.append(target)

        update_fields = ['subject_0', 'subject_1', 'subject_2', 'subject_3', 'subject_4', 'sum', 'participants']
        return rank_model, list_create, list_update, update_fields

    @with_bulk_create_or_update()
    def update_statistics_model(self):
        data_statistics = self.get_statistics_data()
        statistics_model = self.model.statistics
        list_update = []
        list_create = []

        stat_dict = {}
        for (subject, fld, _, _) in self._subject_vars_sum.values():
            stat_dict.update({
                fld: {
                    'subject': subject,
                    'participants': data_statistics[fld]['participants'],
                    'max': data_statistics[fld]['max'],
                    't10': data_statistics[fld]['t10'],
                    't25': data_statistics[fld]['t25'],
                    't50': data_statistics[fld]['t50'],
                    'avg': data_statistics[fld]['avg'],
                }
            })

        try:
            new_query = statistics_model.objects.get(exam=self.exam)
            fields_not_match = any(getattr(new_query, fld) != val for fld, val in stat_dict.items())
            if fields_not_match:
                for fld, val in stat_dict.items():
                    setattr(new_query, fld, val)
                list_update.append(new_query)
        except statistics_model.DoesNotExist:
            list_create.append(statistics_model(psat=self.exam, **stat_dict))
        update_fields = ['subject_0', 'subject_1', 'subject_2', 'subject_3', 'subject_4', 'sum']
        return statistics_model, list_create, list_update, update_fields

    def get_statistics_data(self) -> dict:
        data_statistics = {}
        score_dict = {sub: [] for sub in self._subject_vars_sum}

        qs_students = (
            self.model.student.objects.filter(exam=self.exam).select_related('exam', 'score', 'rank')
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
            for sub, (_, fld, _, _) in self._subject_vars_sum.items():
                score = getattr(qs_s, fld)
                if score is not None:
                    score_dict[sub].append(score)

        self.update_statistics_data(data_statistics, score_dict)
        return data_statistics

    def update_statistics_data(self, data_statistics: dict, score_dict: dict) -> None:
        for sub, scores in score_dict.items():
            subject, fld, _, _ = self._subject_vars_sum[sub]
            participants = len(scores)
            sorted_scores = sorted(scores, reverse=True)

            def get_top_score(percentage):
                if sorted_scores:
                    threshold = max(1, int(participants * percentage))
                    return sorted_scores[threshold - 1]

            data_statistics[fld] = {
                'field': fld,
                'sub': sub,
                'subject': subject,
                'participants': participants,
                'max': sorted_scores[0] if sorted_scores else None,
                't10': get_top_score(0.10),
                't25': get_top_score(0.25),
                't50': get_top_score(0.50),
                'avg': round(sum(scores) / participants, 1) if sorted_scores else None,
            }

    @with_bulk_create_or_update()
    def update_answer_count_model(self, ac_model):
        list_update = []
        list_create = []

        lookup_field = f'student__rank__sum'
        top_rank_threshold = 0.27
        mid_rank_threshold = 0.73
        participants_function = F(f'student__rank__participants')

        lookup_exp = {}
        if ac_model == self.model.ac_top:
            lookup_exp[f'{lookup_field}__lte'] = participants_function * top_rank_threshold
        elif ac_model == self.model.ac_mid:
            lookup_exp[f'{lookup_field}__gt'] = participants_function * top_rank_threshold
            lookup_exp[f'{lookup_field}__lte'] = participants_function * mid_rank_threshold
        elif ac_model == self.model.ac_low:
            lookup_exp[f'{lookup_field}__gt'] = participants_function * mid_rank_threshold

        qs_answer = (
            self.model.answer.objects.filter(problem__exam=self.exam, **lookup_exp)
            .select_related('student', 'student__rank')
            .values('problem_id', 'answer')
            .annotate(count=Count('id')).order_by('problem_id', 'answer')
        )
        answer_distribution_dict = defaultdict(lambda: {i: 0 for i in range(6)})
        for qs_a in qs_answer:
            problem_id = qs_a['problem_id']
            answer = qs_a['answer']
            count = qs_a['count']
            answer_distribution_dict[problem_id][answer] = count

        count_fields = ['count_0', 'count_1', 'count_2', 'count_3', 'count_4', 'count_multiple']
        for problem_id, answer_distribution in answer_distribution_dict.items():
            answers = {'count_multiple': 0}
            for ans, cnt in answer_distribution.items():
                if ans <= 4:
                    answers[f'count_{ans}'] = cnt
                else:
                    answers['count_multiple'] = cnt
            answers['count_sum'] = sum(answers[fld] for fld in count_fields)

            try:
                new_query = ac_model.objects.get(problem_id=problem_id)
                fields_not_match = any(getattr(new_query, fld) != val for fld, val in answers.items())
                if fields_not_match:
                    for fld, val in answers.items():
                        setattr(new_query, fld, val)
                    list_update.append(new_query)
            except ac_model.DoesNotExist:
                list_create.append(ac_model(problem_id=problem_id, **answers))
        update_fields = [
            'problem_id', 'count_0', 'count_1', 'count_2', 'count_3', 'count_4',
            'count_multiple', 'count_sum',
        ]
        return ac_model, list_create, list_update, update_fields


def get_sub_list() -> list:
    return ['형사', '헌법', '경찰', '범죄', '민법']


def get_subject_list() -> list:
    return ['형사법', '헌법', '경찰학', '범죄학', '민법총칙']




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
        answers_page_obj_group[subject], answers_page_range_group[subject] = get_paginator_data(
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
