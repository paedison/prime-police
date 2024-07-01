from django.db import models

from a_common.models import User
from .base_settings import (
    get_current_year, year_choices, exam_choices, subject_choices, number_choices,
    TimeRemarkChoiceBase, TimeChoiceBase, unit_choices, department_choices,
)


class PredictStudent(TimeRemarkChoiceBase):
    year = models.IntegerField(choices=year_choices, default=get_current_year())
    exam = models.CharField(max_length=2, choices=exam_choices, default='경위')
    round = models.IntegerField(default=0)

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='official_predict_students')
    name = models.CharField(max_length=20)
    serial = models.CharField(max_length=10)
    unit = models.CharField(max_length=10, choices=unit_choices, default='경위')
    department = models.CharField(max_length=10, choices=department_choices, default='일반')

    password = models.IntegerField()
    prime_id = models.CharField(max_length=15, blank=True, null=True)

    answer = models.JSONField(default=dict)
    answer_count = models.JSONField(default=dict)
    answer_confirmed = models.JSONField(default=dict)
    answer_all_confirmed_at = models.DateTimeField(null=True, blank=True)

    score = models.JSONField(default=dict)
    rank_total = models.JSONField(default=dict)
    rank_department = models.JSONField(default=dict)
    participants_total = models.JSONField(default=dict)
    participants_department = models.JSONField(default=dict)

    class Meta:
        verbose_name = "성적예측 수험정보"
        verbose_name_plural = "성적예측 수험정보"
        unique_together = ['year', 'exam', 'round', 'user']
        db_table = 'a_official_predict_student'

    def __str__(self):
        return f'{self.reference}({self.student_info})'

    @property
    def reference(self):
        return f'{self.year}{self.exam}{self.round}'

    @property
    def student_info(self):
        return {self.serial}-{self.name}


class PredictAnswerRecord(TimeRemarkChoiceBase):
    student = models.ForeignKey(PredictStudent, on_delete=models.CASCADE, related_name='answer_records')
    subject = models.CharField(max_length=2, choices=subject_choices)
    number = models.IntegerField(choices=number_choices, default=1)
    answer = models.IntegerField(default=0)

    class Meta:
        verbose_name = "성적예측 답안 제출"
        verbose_name_plural = "성적예측 답안 제출"
        unique_together = ['student', 'subject', 'number']
        db_table = 'a_official_predict_answer_record'

    def __str__(self):
        return f'prime_answer_record_{self.student.reference}-{self.number}({self.student.student_info})'


class PredictAnswerCount(TimeChoiceBase):
    year = models.IntegerField(choices=year_choices, default=get_current_year())
    exam = models.CharField(max_length=2, choices=exam_choices)
    round = models.IntegerField(default=0)

    subject = models.CharField(max_length=2, choices=subject_choices)
    number = models.IntegerField()
    answer = models.IntegerField(null=True, blank=True)

    count_1 = models.IntegerField(default=0)
    count_2 = models.IntegerField(default=0)
    count_3 = models.IntegerField(default=0)
    count_4 = models.IntegerField(default=0)
    count_5 = models.IntegerField(default=0)
    count_0 = models.IntegerField(default=0)
    count_None = models.IntegerField(default=0)

    class Meta:
        verbose_name = "성적예측 답안 개수"
        verbose_name_plural = "성적예측 답안 개수"
        unique_together = ['year', 'exam', 'round', 'subject', 'number']
        db_table = 'a_official_predict_answer_count'

    def __str__(self):
        return f'prime_answer_count_{self.reference}-{self.subject}{self.number}'

    @property
    def reference(self):
        return f'{self.year}{self.exam}{self.round}'

    @property
    def count_total(self):
        counts = [
            self.count_1, self.count_2, self.count_3, self.count_4, self.count_5,
            self.count_0, self.count_None,
        ]
        return sum(filter(None, counts))

    def get_rate(self, answer: int | None):
        if self.count_total != 0:
            return getattr(self, f'count_{answer}') / self.count_total * 100

    @property
    def rate_0(self):
        return self.get_rate(0)

    @property
    def rate_1(self):
        return self.get_rate(1)

    @property
    def rate_2(self):
        return self.get_rate(2)

    @property
    def rate_3(self):
        return self.get_rate(3)

    @property
    def rate_4(self):
        return self.get_rate(4)

    @property
    def rate_5(self):
        return self.get_rate(5)

    @property
    def rate_None(self):
        return self.get_rate(None)
