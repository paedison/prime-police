from dataclasses import dataclass
from datetime import timedelta

import numpy as np
from django.core.paginator import Paginator
from django.utils import timezone

from a_common.models import User
from a_common.utils import HtmxHttpRequest
from a_official import filters, models


@dataclass(kw_only=True)
class RequestData:
    _request: HtmxHttpRequest

    def __post_init__(self):
        self.view_type = self._request.headers.get('View-Type', '')
        self.exam_year = self._request.GET.get('year', '')
        self.exam_exam = self._request.GET.get('exam', '')
        self.exam_subject = self._request.GET.get('subject', '')
        self.page_number = self._request.GET.get('page', 1)
        self.keyword = self._request.POST.get('keyword', '') or self._request.GET.get('keyword', '')
        self.student_name = self._request.GET.get('student_name', '')

    def get_filterset(self):
        problem_filter = filters.OfficialFilter if self._request.user.is_authenticated \
            else filters.AnonymousOfficialFilter
        return problem_filter(data=self._request.GET, request=self._request)

    def get_sub_title(self, end_string='기출문제') -> str:
        year = self.exam_year
        exam = self.exam_exam
        subject = self.exam_subject
        title_parts = []
        if year:
            title_parts.append(f'{year}년')
            if isinstance(year, str):
                year = int(year)

        if not year and not exam and not subject:
            title_parts.append('전체')
        else:
            title_parts.append('전체')
        sub_title = f'{" ".join(title_parts)} {end_string}'
        return sub_title


@dataclass(kw_only=True)
class ModelData:
    def __post_init__(self):
        self.exam = models.Exam
        self.problem = models.Problem

        self.predict_exam = models.PredictExam
        self.statistics = models.PredictStatistics
        self.student = models.PredictStudent
        self.answer = models.PredictAnswer
        self.score = models.PredictScore

        self.rank = models.PredictRank
        self.ac_all = models.PredictAnswerCount
        self.ac_top = models.PredictAnswerCountTopRank
        self.ac_mid = models.PredictAnswerCountMidRank
        self.ac_low = models.PredictAnswerCountLowRank
        self.ac_model_set = {'all': self.ac_all, 'top': self.ac_top, 'mid': self.ac_mid, 'low': self.ac_low}


@dataclass(kw_only=True)
class ExamData:
    _exam: models.Exam

    def __post_init__(self):
        self.subject_vars, self.subject_vars_sum, self.subject_vars_sum_first = self.get_subject_vars_all()
        self.subject_fields, self.subject_fields_sum, self.subject_fields_sum_first = self.get_subject_fields_all()
        self.sub_list = [sub for sub in self.subject_vars]

        has_predict = self.get_has_predict()
        self.predict_exam = self._exam.predict_exam if has_predict else None
        self.time_schedule = self.get_time_schedule() if has_predict else {}
        self.is_not_for_predict = self.get_is_not_for_predict()
        self.before_exam_start = self.get_before_exam_start()

    def get_exam(self):
        return self._exam

    def get_has_predict(self):
        if hasattr(self._exam, 'predict_exam'):
            return all([self._exam, self._exam.predict_exam.is_active])

    def get_is_not_for_predict(self):
        return any([
            not self._exam,
            not hasattr(self._exam, 'predict_exam'),
            not self._exam.predict_exam.is_active if hasattr(self._exam, 'predict_exam') else True,
        ])

    def get_before_exam_start(self):
        current_time = timezone.now()
        before_exam_start = True
        if not self.is_not_for_predict:
            before_exam_start = current_time < self._exam.predict_exam.exam_started_at
        return before_exam_start

    @staticmethod
    def get_subject_vars_all():
        sum_vars = {'총점': ('총점', 'sum', 5, 200, 0)}
        subject_vars = {
            '형사': ('형사법', 'subject_0', 0, 40, 3),
            '헌법': ('헌법', 'subject_1', 1, 40, 1.5),
            '경찰': ('경찰학', 'subject_2', 2, 40, 3),
            '범죄': ('범죄학', 'subject_3', 3, 40, 1.5),
            '민법': ('민법총칙', 'subject_4', 4, 40, 1),
            '행법': ('행정법', 'subject_5', 5, 40, 1),
            '행학': ('행정학', 'subject_6', 6, 40, 1),
        }
        subject_vars_sum_first = dict(sum_vars, **subject_vars)
        subject_vars_sum = dict(subject_vars, **sum_vars)
        return subject_vars, subject_vars_sum, subject_vars_sum_first

    def get_subject_fields_all(self):
        subject_fields_sum_first = [fld for (_, fld, _, _, _) in self.subject_vars_sum_first.values()]
        subject_fields_sum = [fld for (_, fld, _, _, _) in self.subject_vars_sum.values()]
        subject_fields = [fld for (_, fld, _, _, _) in self.subject_vars.values()]
        return subject_fields, subject_fields_sum, subject_fields_sum_first

    def get_time_schedule(self) -> dict:
        start_time = self.predict_exam.exam_started_at  # 시험 시작
        exam_1_end_time = start_time + timedelta(minutes=80)  # 1교시 종료
        exam_2_start_time = exam_1_end_time + timedelta(minutes=30)  # 2교시 시작
        finish_time = self.predict_exam.exam_finished_at  # 시험 종료
        return {
            '형사': (start_time, exam_1_end_time),
            '헌법': (start_time, exam_1_end_time),
            '경찰': (exam_2_start_time, finish_time),
            '범죄': (exam_2_start_time, finish_time),
            '민법': (exam_2_start_time, finish_time),
            '행법': (exam_2_start_time, finish_time),
            '행학': (exam_2_start_time, finish_time),
            '총점': (start_time, finish_time),
        }


@dataclass(kw_only=True)
class SubjectVariants:
    _selection: str

    def __post_init__(self):
        self.subject_vars, self.subject_vars_sum, self.subject_vars_sum_first = self.get_subject_vars_all()
        self.subject_fields, self.subject_fields_sum, self.subject_fields_sum_first = self.get_subject_fields_all()
        self.sub_list = [sub for sub in self.subject_vars]
        self.subject_vars_dict = {
            'base': self.subject_vars,
            'sum_last': self.subject_vars_sum,
            'sum_first': self.subject_vars_sum_first
        }

    def get_subject_vars_all(self):
        sum_vars = {'총점': ('총점', 'sum', 5, 200, 0)}
        subject_vars = {
            '형사': ('형사법', 'subject_0', 0, 40, 3),
            '헌법': ('헌법', 'subject_1', 1, 40, 1.5),
            '경찰': ('경찰학', 'subject_2', 2, 40, 3),
            '범죄': ('범죄학', 'subject_3', 3, 40, 1.5),
            '민법': ('민법총칙', 'subject_4', 4, 40, 1),
            '행법': ('행정법', 'subject_5', 5, 40, 1),
            '행학': ('행정학', 'subject_6', 6, 40, 1),
        }
        subject_vars_sum_first = dict(sum_vars, **subject_vars)
        subject_vars_sum = dict(subject_vars, **sum_vars)

        selection_sub_list = ['민법', '행법', '행학']
        if self._selection:
            selection_sub_list.remove(self._selection)
            for sub in selection_sub_list:
                subject_vars.pop(sub)
                subject_vars_sum.pop(sub)
                subject_vars_sum_first.pop(sub)
        return subject_vars, subject_vars_sum, subject_vars_sum_first

    def get_subject_fields_all(self):
        subject_fields_sum_first = [fld for (_, fld, _, _, _) in self.subject_vars_sum_first.values()]
        subject_fields_sum = [fld for (_, fld, _, _, _) in self.subject_vars_sum.values()]
        subject_fields = [fld for (_, fld, _, _, _) in self.subject_vars.values()]
        return subject_fields, subject_fields_sum, subject_fields_sum_first

    def get_subject_variable(self, subject_field) -> tuple[str, str, int, int, float]:
        for sub, (subject, fld, field_idx, problem_count, score_per_problem) in self.subject_vars.items():
            if subject_field == fld:
                return sub, subject, field_idx, problem_count, score_per_problem

    def get_subject_vars_dict(self):
        return {
            'base': self.subject_vars,
            'sum_last': self.subject_vars_sum,
            'sum_first': self.subject_vars_sum_first
        }

    def get_subject_fields_dict(self):
        return {
            'base': self.subject_fields,
            'sum_last': self.subject_fields_sum,
            'sum_first': self.subject_fields_sum_first
        }


def get_prev_next_obj(pk, custom_data) -> tuple:
    custom_list = list(custom_data.values_list('id', flat=True))
    prev_obj = next_obj = None
    last_id = len(custom_list) - 1
    try:
        q = custom_list.index(pk)
        if q != 0:
            prev_obj = custom_data[q - 1]
        if q != last_id:
            next_obj = custom_data[q + 1]
        return prev_obj, next_obj
    except ValueError:
        return None, None


def get_stat_from_scores(scores: np.array):
    _max = _t10 = _t25 = _t50 = _avg = 0
    if scores.any():
        _max = round(float(np.max(scores)), 1)
        _t10 = round(float(np.percentile(scores, 90)), 1)
        _t25 = round(float(np.percentile(scores, 75)), 1)
        _t50 = round(float(np.percentile(scores, 50)), 1)
        _avg = round(float(np.mean(scores)), 1)
    return {'max': _max, 't10': _t10, 't25': _t25, 't50': _t50, 'avg': _avg}


def get_page_obj_and_range(page_number, page_data, per_page=10):
    paginator = Paginator(page_data, per_page)
    page_obj = paginator.page(page_number)
    page_range = paginator.get_elided_page_range(number=page_number, on_each_side=3, on_ends=1)
    return page_obj, page_range


def get_sub_title(exam_year, exam_subject, end_string='기출문제') -> str:
    title_parts = []
    if exam_year:
        title_parts.append(f'{exam_year}년')

    if exam_subject:
        title_parts.append(models.choices.subject_choice()[exam_subject])

    if not exam_year and not exam_subject:
        title_parts.append('전체')
    sub_title = f'{" ".join(title_parts)} {end_string}'
    return sub_title


def get_prev_next_prob(pk, custom_data) -> tuple:
    custom_list = list(custom_data.values_list('id', flat=True))
    prev_prob = next_prob = None
    if custom_list:
        last_id = len(custom_list) - 1
        q = custom_list.index(pk)
        if q != 0:
            prev_prob = custom_data[q - 1]
        if q != last_id:
            next_prob = custom_data[q + 1]
    return prev_prob, next_prob


def get_list_data(custom_data) -> list:
    organized_dict = {}
    organized_list = []
    for prob in custom_data:
        key = f'{prob.year}{prob.subject}'
        if key not in organized_dict:
            organized_dict[key] = []
        organized_dict[key].append(prob)

    for key, items in organized_dict.items():
        num_empty_instances = 5 - (len(items) % 5)
        if num_empty_instances < 5:
            items.extend([None] * num_empty_instances)
        for i in range(0, len(items), 5):
            row = items[i:i+5]
            organized_list.extend(row)
    return organized_list


def get_custom_data(user: User) -> dict:
    if user.is_authenticated:
        return {
            'like': models.ProblemLike.objects.filter(user=user).select_related('user', 'problem'),
            'rate': models.ProblemRate.objects.filter(user=user).select_related('user', 'problem'),
            'solve': models.ProblemSolve.objects.filter(user=user).select_related('user', 'problem'),
            'memo': models.ProblemMemo.objects.filter(user=user).select_related('user', 'problem'),
            'tag': models.ProblemTaggedItem.objects.filter(
                user=user, active=True).select_related('user', 'content_object'),
            'collection': models.ProblemCollectionItem.objects.filter(
                collection__user=user).select_related('collection__user', 'problem'),
        }
    return {'like': [], 'rate': [], 'solve': [], 'memo': [], 'tag': [], 'collection': []}
