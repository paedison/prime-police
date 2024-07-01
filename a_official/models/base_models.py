from django.db import models
from django.utils import timezone

from .base_settings import (
    get_current_year, year_choices, exam_choices, unit_choices, department_choices,
    TimeRemarkChoiceBase,
)


class Unit(TimeRemarkChoiceBase):
    exam = models.CharField(max_length=2, choices=exam_choices, default='경위')
    name = models.CharField(max_length=10, choices=unit_choices, default='경위')
    order = models.IntegerField()

    class Meta:
        unique_together = ['exam', 'name']
        ordering = ['order']

    def __str__(self):
        return f'[Official]Unit:{self.exam}-{self.name}'


class Department(TimeRemarkChoiceBase):
    exam = models.CharField(max_length=2, choices=exam_choices, default='경위')
    unit = models.CharField(max_length=10, choices=unit_choices, default='경위')
    name = models.CharField(max_length=10, choices=department_choices, default='일반')
    order = models.IntegerField()

    class Meta:
        unique_together = ['exam', 'unit', 'name']
        ordering = ['order']

    def __str__(self):
        return f'[Official]Department:{self.exam}-{self.unit}-{self.name}'


class Exam(TimeRemarkChoiceBase):
    year = models.IntegerField(choices=year_choices, default=get_current_year())
    exam = models.CharField(max_length=2, choices=exam_choices, default='경위')
    round = models.IntegerField(default=0)
    answer_official = models.JSONField(default=dict)

    page_opened_at = models.DateTimeField(default=timezone.now)
    exam_started_at = models.DateTimeField(default=timezone.now)
    exam_finished_at = models.DateTimeField(default=timezone.now)
    answer_predict_opened_at = models.DateTimeField(default=timezone.now)
    answer_official_opened_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ['year', 'exam', 'round']

    def __str__(self):
        return f'[Official]Exam:{self.reference}'

    @property
    def reference(self):
        return f'{self.year}{self.exam}{self.round}'

    @property
    def is_not_page_open(self):
        return timezone.now() <= self.page_opened_at

    @property
    def is_not_finished(self):
        return self.page_opened_at < timezone.now() <= self.exam_finished_at

    @property
    def is_collecting_answer(self):
        return self.exam_finished_at < timezone.now() <= self.answer_predict_opened_at

    @property
    def is_answer_predict_opened(self):
        return self.answer_predict_opened_at < timezone.now() <= self.answer_official_opened_at

    @property
    def is_answer_official_opened(self):
        return self.answer_official_opened_at <= timezone.now()
