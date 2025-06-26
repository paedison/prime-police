from ckeditor_uploader.fields import RichTextUploadingField
from django.db import models
from django.urls import reverse_lazy
from django.utils import timezone

from a_common.constants import icon_set
from a_mock.models import queryset, abstract_models

verbose_name_prefix = '[문제은행] '


class Exam(models.Model):
    objects = queryset.ExamQuerySet().as_manager()

    year = models.IntegerField(
        choices=abstract_models.year_choice, default=abstract_models.get_next_year, verbose_name='연도')
    page_opened_at = models.DateTimeField(default=timezone.now, verbose_name='페이지 오픈 일시')
    exam_started_at = models.DateTimeField(default=timezone.now, verbose_name='시험 시작 일시')
    exam_finished_at = models.DateTimeField(default=timezone.now, verbose_name='시험 종료 일시')
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}00_시험'
        constraints = [models.UniqueConstraint(fields=['year'], name='unique_mock_exam')]

    def __str__(self):
        return self.full_reference

    @property
    def reference(self):
        return f'{self.year}전모'

    @property
    def full_reference(self):
        return f'{self.get_year_display()}도 대비 전국모의고사'

    @staticmethod
    def get_staff_menu_url():
        return reverse_lazy('mock:staff-menu')

    def get_staff_detail_url(self):
        return reverse_lazy('mock:staff-detail', args=[self.id])

    def get_staff_answer_detail_url(self):
        return reverse_lazy('mock:staff-answer-detail', args=[self.id])

    def get_staff_answer_update_url(self):
        return reverse_lazy('mock:staff-answer-update', args=[self.id])

    def is_finished(self):
        return self.exam_finished_at <= timezone.now()


class Problem(models.Model):
    objects = queryset.ProblemQuerySet().as_manager()

    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='problems')
    subject = models.CharField(
        max_length=2, choices=abstract_models.subject_choice, default='형사', verbose_name='과목')
    number = models.IntegerField(choices=abstract_models.number_choice, default=1, verbose_name='문제 번호')
    answer = models.IntegerField(choices=abstract_models.answer_choice, default=1, verbose_name='정답')
    question = models.TextField(default='', verbose_name='발문')
    data = RichTextUploadingField(config_name='problem', default='', verbose_name='문제 내용')

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}01_문제'
        ordering = ['-exam', 'id']
        constraints = [
            models.UniqueConstraint(fields=['exam', 'subject', 'number'], name='unique_mock_problem')
        ]

    def __str__(self):
        return self.reference

    @property
    def exam_name(self):
        return f'{self.exam.get_year_display()} {self.get_subject_display()}'

    @property
    def reference(self):
        return f'{self.exam.year:02}-{self.subject}-{self.number:02}'

    @property
    def semester_round_subject(self):
        return ' '.join([
            self.exam.get_year_display(),
            self.get_subject_display(),
        ])

    @property
    def full_reference(self):
        return ' '.join([self.semester_round_subject, self.get_number_display()])

    @property
    def icon(self):
        return {
            'nav': icon_set.ICON_NAV,
            'like': icon_set.ICON_LIKE,
            'rate': icon_set.ICON_RATE,
            'solve': icon_set.ICON_SOLVE,
            'memo': icon_set.ICON_MEMO,
            'tag': icon_set.ICON_TAG,
            'collection': icon_set.ICON_COLLECTION,
            'question': icon_set.ICON_QUESTION,
        }

    def get_absolute_url(self):
        return reverse_lazy('mock:problem-detail', args=[self.id])

    @staticmethod
    def get_list_url():
        return reverse_lazy('mock:problem-list')

    def get_admin_change_url(self):
        return reverse_lazy('admin:a_mock_problem_change', args=[self.id])
