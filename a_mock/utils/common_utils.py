__all__ = ['RequestData', 'ModelData', 'ExamData', 'bulk_create_or_update']

import traceback
from dataclasses import dataclass
from datetime import timedelta

import django.db.utils
from django.db import transaction

from a_common.utils import HtmxHttpRequest
from a_mock import models


@dataclass(kw_only=True)
class RequestData:
    request: HtmxHttpRequest

    def __post_init__(self):
        self.view_type = self.request.headers.get('View-Type', '')
        self.exam_year = self.request.GET.get('year', '')
        self.exam_exam = self.request.GET.get('exam', '')
        self.exam_subject = self.request.GET.get('subject', '')
        self.page_number = self.request.GET.get('page', 1)
        self.keyword = self.request.POST.get('keyword', '') or self.request.GET.get('keyword', '')
        self.student_name = self.request.GET.get('student_name', '')


@dataclass(kw_only=True)
class ModelData:
    def __post_init__(self):
        self.statistics = models.Statistics
        self.student = models.Student
        self.answer = models.Answer
        self.score = models.Score
        self.rank = models.Rank
        self.ac_all = models.AnswerCount
        self.ac_top = models.AnswerCountTopRank
        self.ac_mid = models.AnswerCountMidRank
        self.ac_low = models.AnswerCountLowRank
        self.ac_models = {'all': self.ac_all, 'top': self.ac_top, 'mid': self.ac_mid, 'low': self.ac_low}


@dataclass(kw_only=True)
class ExamData:
    exam: models.Exam

    def __post_init__(self):
        # 외부 호출 변수 정의
        self.subject_vars_sum = self.get_subject_vars()
        self.subject_vars = self.get_subject_vars()
        self.subject_vars.pop('총점')
        self.subject_fields = [fld for (_, fld, _, _) in self.subject_vars.values()]
        self.time_schedule = self.get_time_schedule()

    @staticmethod
    def get_subject_vars() -> dict[str, tuple[str, str, int, int]]:
        return {
            '형사': ('형사법', 'subject_0', 0, 40),
            '헌법': ('헌법', 'subject_1', 1, 40),
            '경찰': ('경찰학', 'subject_2', 2, 40),
            '범죄': ('범죄학', 'subject_3', 3, 40),
            '민법': ('민법총칙', 'subject_4', 4, 40),
            '총점': ('총점', 'sum', 5, 200),
        }

    @staticmethod
    def get_score_unit(sub):
        police_score_unit = {
            '형사': 3, '경찰': 3, '세법': 2, '회계': 2, '정보': 2,
            '시네': 2, '행법': 1, '행학': 1, '민법': 1,
        }
        return police_score_unit.get(sub, 1.5)

    def get_time_schedule(self) -> dict:
        start_time = self.exam.exam_started_at
        exam_1_end_time = start_time + timedelta(minutes=115)  # 1교시 시험 종료 시각
        exam_2_start_time = exam_1_end_time + timedelta(minutes=110)  # 2교시 시험 시작 시각
        finish_time = self.exam.exam_finished_at  # 3교시 시험 종료 시각
        return {
            '형사': (start_time, exam_1_end_time),
            '헌법': (start_time, exam_1_end_time),
            '경찰': (exam_2_start_time, finish_time),
            '범죄': (exam_2_start_time, finish_time),
            '민법': (exam_2_start_time, finish_time),
            '총점': (start_time, finish_time),
        }


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
