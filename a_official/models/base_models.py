from django.db import models
from django.utils import timezone

from .base_settings import (
    get_current_year, year_choices, exam_choices, unit_choices, department_choices,
    TimeRemarkChoiceBase,
)


class Unit(TimeRemarkChoiceBase):
    exam = models.CharField(max_length=2, choices=exam_choices, default='경위', verbose_name='시험')
    name = models.CharField(max_length=10, choices=unit_choices, default='경위', verbose_name='모집단위')
    order = models.IntegerField(verbose_name='순서')

    class Meta:
        verbose_name = verbose_name_plural = "모집단위"
        unique_together = ['exam', 'name']
        ordering = ['order']

    def __str__(self):
        return f'[Official]Unit:{self.exam}-{self.name}'


class Department(TimeRemarkChoiceBase):
    exam = models.CharField(max_length=2, choices=exam_choices, default='경위', verbose_name='시험')
    unit = models.CharField(max_length=10, choices=unit_choices, default='경위', verbose_name='모집단위')
    name = models.CharField(max_length=10, choices=department_choices, default='일반', verbose_name='직렬')
    order = models.IntegerField(verbose_name='순서')

    class Meta:
        verbose_name = verbose_name_plural = "직렬"
        unique_together = ['exam', 'unit', 'name']
        ordering = ['order']

    def __str__(self):
        return f'[Official]Department:{self.exam}-{self.unit}-{self.name}'


class Exam(TimeRemarkChoiceBase):
    year = models.IntegerField(choices=year_choices, default=get_current_year(), verbose_name='연도')
    exam = models.CharField(max_length=2, choices=exam_choices, default='경위', verbose_name='시험')
    round = models.IntegerField(default=0, verbose_name='회차')
    answer_official = models.JSONField(default=dict, verbose_name='공식 정답')

    page_opened_at = models.DateTimeField(default=timezone.now, verbose_name='페이지 공개 일시')
    exam_started_at = models.DateTimeField(default=timezone.now, verbose_name='시험 시작 일시')
    exam_finished_at = models.DateTimeField(default=timezone.now, verbose_name='시험 종료 일시')
    answer_predict_opened_at = models.DateTimeField(default=timezone.now, verbose_name='예상 정답 공개 일시')
    answer_official_opened_at = models.DateTimeField(default=timezone.now, verbose_name='공식 정답 공개 일시')

    class Meta:
        verbose_name = verbose_name_plural = "시험"
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
