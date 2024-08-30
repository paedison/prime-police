from ckeditor_uploader.fields import RichTextUploadingField
from django.db import models
from django.urls import reverse_lazy
from django.utils import timezone

from a_common.constants import icon_set
from a_common.models import User
from a_daily.models import (
    semester_choice, circle_choice, subject_choice, round_choice, number_choice, answer_choice,
    statistics_default, semester_default, answer_default,
)


class Exam(models.Model):
    semester = models.IntegerField(choices=semester_choice, default=semester_default, verbose_name='기수')
    circle = models.IntegerField(choices=circle_choice, default=1, verbose_name='순환')
    subject = models.CharField(max_length=2, choices=subject_choice, default='형사', verbose_name='과목')
    round = models.IntegerField(choices=round_choice, default=1, verbose_name='회차')
    opened_at = models.DateTimeField(default=timezone.now, verbose_name='공개일시')
    participants = models.IntegerField(default=0, verbose_name='응시생수')
    statistics = models.JSONField(default=statistics_default, verbose_name='성적 통계')

    class Meta:
        verbose_name = verbose_name_plural = "01_시험"
        unique_together = ['semester', 'circle', 'subject', 'round']
        ordering = ['-semester', '-circle', 'subject', 'round']

    def __str__(self):
        return f'[Weekly]Exam:{self.full_reference}'

    @property
    def full_reference(self):
        return ' '.join([
            self.get_semester_display(),
            self.get_circle_display(),
            self.get_subject_display(),
            self.get_round_display(),
        ])

    @property
    def sem_cir_sub_rnd(self):
        return f'{self.semester}-{self.circle}-{self.subject}-{self.round}'

    @property
    def circle_subject_round(self):
        return f'{self.get_circle_display()}-{self.get_subject_display()}-{self.get_round_display()}'

    @property
    def is_not_opened(self):
        return timezone.now() <= self.opened_at

    @staticmethod
    def get_answer_list_url():
        return reverse_lazy('weekly:answer-list')

    def get_answer_detail_url(self):
        return reverse_lazy('weekly:answer-detail', args=[self.id])

    def get_answer_input_url(self):
        return reverse_lazy('weekly:answer-input', args=[self.id])

    def get_answer_confirm_url(self):
        return reverse_lazy('weekly:answer-confirm', args=[self.id])


class Problem(models.Model):
    semester = models.IntegerField(choices=semester_choice, default=semester_default(), verbose_name='기수')
    circle = models.IntegerField(choices=circle_choice, default=1, verbose_name='순환')
    subject = models.CharField(max_length=2, choices=subject_choice, default='형사', verbose_name='과목')
    round = models.IntegerField(choices=round_choice, default=1, verbose_name='회차')
    number = models.IntegerField(choices=number_choice, default=1, verbose_name='문제 번호')
    answer = models.IntegerField(choices=answer_choice, default=1, verbose_name='정답')
    question = models.TextField(default='', verbose_name='발문')
    data = RichTextUploadingField(config_name='problem', default='', verbose_name='문제 내용')
    opened_at = models.DateField(default=timezone.now, verbose_name='공개일')

    class Meta:
        verbose_name = verbose_name_plural = "02_문제"
        unique_together = ['semester', 'circle', 'round', 'subject', 'number']
        ordering = ['-semester', 'id']

    def __str__(self):
        return f'[Weekly]Problem(#{self.id}):{self.reference}'

    @property
    def circle_round_sub(self):
        return f'{self.circle}{self.subject}{self.round}'

    @property
    def reference(self):
        return f'{self.circle_round_sub}-{self.number:02}'

    @property
    def semester_circle_subject_round(self):
        return ' '.join([
            self.get_semester_display(),
            self.get_circle_display(),
            self.get_subject_display(),
            self.get_round_display(),
        ])

    @property
    def full_reference(self):
        return ' '.join([self.semester_circle_subject_round, self.get_number_display()])

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
        return reverse_lazy('weekly:problem-detail', args=[self.id])

    def get_like_url(self):
        return reverse_lazy('weekly:like-problem', args=[self.id])

    def get_rate_url(self):
        return reverse_lazy('weekly:rate-problem', args=[self.id])

    def get_solve_url(self):
        return reverse_lazy('weekly:solve-problem', args=[self.id])

    def get_memo_url(self):
        return reverse_lazy('weekly:memo-problem', args=[self.id])

    def get_tag_url(self):
        return reverse_lazy('weekly:tag-problem', args=[self.id])

    def get_collect_url(self):
        return reverse_lazy('weekly:collect-problem', args=[self.id])


class AnswerCount(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성 일시')
    semester = models.IntegerField(choices=semester_choice, default=semester_default, verbose_name='기수')
    circle = models.IntegerField(choices=circle_choice, default=1, verbose_name='순환')
    subject = models.CharField(max_length=2, choices=subject_choice, default='형사', verbose_name='과목')
    round = models.IntegerField(choices=round_choice, default=1, verbose_name='회차')
    number = models.IntegerField(default=1, verbose_name="번호")

    count_1 = models.IntegerField(default=0, verbose_name='①')
    count_2 = models.IntegerField(default=0, verbose_name='②')
    count_3 = models.IntegerField(default=0, verbose_name='③')
    count_4 = models.IntegerField(default=0, verbose_name='④')
    count_0 = models.IntegerField(default=0, verbose_name='미표기')
    count_multiple = models.IntegerField(default=0, verbose_name='중복표기')
    count_total = models.IntegerField(default=0, verbose_name='총계')
    data = models.JSONField(default=dict, verbose_name='전체')

    class Meta:
        verbose_name = verbose_name_plural = "03_답안개수"
        unique_together = ['semester', 'circle', 'subject', 'round', 'number']

    def __str__(self):
        return f'[Weekly]AnswerCount:{self.full_reference} {self.number:02}번'

    @property
    def full_reference(self):
        return ' '.join([
            self.get_semester_display(),
            self.get_circle_display(),
            self.get_subject_display(),
            self.get_round_display(),
            self.number, '번'
        ])

    def get_rate(self, answer: int | str) -> float:
        count = getattr(self, f'count_{answer}', 0)
        rate = round(count / self.count_total * 100, 1) if self.count_total else 0
        return rate

    @property
    def rate_1(self): return self.get_rate(1)

    @property
    def rate_2(self): return self.get_rate(2)

    @property
    def rate_3(self): return self.get_rate(3)

    @property
    def rate_4(self): return self.get_rate(4)

    @property
    def rate_0(self): return self.get_rate(0)

    @property
    def rate_multiple(self): return self.get_rate('multiple')


class Student(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성일시')
    user = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL, related_name='weekly_students')
    semester = models.IntegerField(choices=semester_choice, default=semester_default, verbose_name='기수')
    circle = models.IntegerField(choices=circle_choice, default=1, verbose_name='순환')
    subject = models.CharField(max_length=2, choices=subject_choice, default='형사', verbose_name='과목')
    round = models.IntegerField(choices=round_choice, default=1, verbose_name='회차')
    answer_student = models.JSONField(default=answer_default, verbose_name='제출 답안')
    answer_confirmed = models.BooleanField(default=False, verbose_name='답안 확정')
    score = models.IntegerField(null=True, blank=True, verbose_name='점수')
    rank = models.IntegerField(null=True, blank=True, verbose_name='등수')
    remarks = models.TextField(null=True, blank=True, verbose_name='주석')

    class Meta:
        verbose_name = verbose_name_plural = "04_수험정보"
        unique_together = ['user', 'semester', 'circle', 'subject', 'round']
        ordering = ['-semester', '-circle', 'subject', 'round']

    def __str__(self):
        return f'[Weekly]Student:{self.user.name}_{self.full_reference}'

    @property
    def full_reference(self):
        return ' '.join([
            self.get_semester_display(),
            self.get_circle_display(),
            self.get_subject_display(),
            self.get_round_display(),
        ])

    def get_answer_count(self):
        return len([ans for ans in self.answer_student if ans])

    def get_absolute_url(self):
        return reverse_lazy('weekly:answer-detail', args=[self.id])

    def get_rank_verify_url(self):
        return reverse_lazy('weekly:rank-verify', args=[self.id])

    def get_rank_ratio(self, participants: int):
        if participants:
            return round(self.rank * 100 / participants, 1)
