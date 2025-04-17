from datetime import timedelta

from ckeditor_uploader.fields import RichTextUploadingField
from django.db import models
from django.urls import reverse_lazy
from django.utils import timezone
from taggit.managers import TaggableManager

from a_common.constants import icon_set
from a_common.models import User
from a_common.prime_test.model_settings import *

verbose_name_prefix = '[문제은행] '


class Exam(models.Model):
    semester = models.IntegerField(
        choices=semester_choice, default=semester_default, verbose_name='기수')
    round = models.IntegerField(choices=round_choice, default=1, verbose_name='회차')
    page_opened_at = models.DateTimeField(default=timezone.now, verbose_name='페이지 오픈 일시')
    exam_started_at = models.DateTimeField(default=timezone.now, verbose_name='시험 시작 일시')
    exam_finished_at = models.DateTimeField(default=timezone.now, verbose_name='시험 종료 일시')

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}00_시험'
        constraints = [models.UniqueConstraint(fields=['semester', 'round'], name='unique_infinite_exam')]

    def __str__(self):
        return self.full_reference

    @property
    def reference(self):
        return f'무한반-{self.get_round_display()}'

    @property
    def full_reference(self):
        return ' '.join([self.get_semester_display(), self.get_round_display()])

    @property
    def exam_1_end_time(self):
        return self.exam_started_at + timedelta(minutes=80)

    @property
    def exam_2_start_time(self):
        return self.exam_1_end_time + timedelta(minutes=20)

    @staticmethod
    def get_answer_list_url():
        return reverse_lazy('infinite:answer-list')

    def get_answer_detail_url(self):
        return reverse_lazy('infinite:answer-detail', args=[self.id])

    def get_answer_input_url(self, subject_field):
        return reverse_lazy('infinite:answer-input', args=[self.id, subject_field])

    def get_answer_confirm_url(self, subject_field):
        return reverse_lazy('infinite:answer-confirm', args=[self.id, subject_field])

    @staticmethod
    def get_staff_menu_url():
        return reverse_lazy('infinite:staff-menu')

    def get_staff_detail_url(self):
        return reverse_lazy('infinite:staff-detail', args=[self.id])

    def get_staff_answer_detail_url(self):
        return reverse_lazy('infinite:staff-answer-detail', args=[self.id])

    def get_staff_answer_update_url(self):
        return reverse_lazy('infinite:staff-answer-update', args=[self.id])


class ProblemTag(BaseProblemTag):
    class Meta(BaseProblemTag.Meta):
        db_table = 'a_infinite_problem_tag'
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}07_태그'

    def __str__(self):
        return self.name


class ProblemTaggedItem(BaseProblemTaggedItem):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='infinite_tagged_items')
    content_object = models.ForeignKey('Problem', on_delete=models.CASCADE, related_name='tagged_problems')
    tag = models.ForeignKey(ProblemTag, on_delete=models.CASCADE, related_name="tagged_items")

    class Meta(BaseProblemTaggedItem.Meta):
        db_table = 'a_infinite_problem_tagged_item'
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}08_태그 문제'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'content_object', 'tag'], name='unique_infinite_problem_tagged_item'
            )
        ]


class Problem(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='problems')
    subject = models.CharField(max_length=2, choices=infinite_subject_choice, default='형사', verbose_name='과목')
    number = models.IntegerField(choices=number_choice, default=1, verbose_name='문제 번호')
    answer = models.IntegerField(choices=answer_choice, default=1, verbose_name='정답')
    question = models.TextField(default='', verbose_name='발문')
    data = RichTextUploadingField(config_name='problem', default='', verbose_name='문제 내용')

    tags = TaggableManager(through=ProblemTaggedItem, blank=True)

    open_users = models.ManyToManyField(User, related_name='infinite_opened_problems', through='ProblemOpen')
    like_users = models.ManyToManyField(User, related_name='infinite_liked_problems', through='ProblemLike')
    rate_users = models.ManyToManyField(User, related_name='infinite_rated_problems', through='ProblemRate')
    solve_users = models.ManyToManyField(User, related_name='infinite_solved_problems', through='ProblemSolve')
    memo_users = models.ManyToManyField(User, related_name='infinite_memoed_problems', through='ProblemMemo')
    collections = models.ManyToManyField(
        'ProblemCollection', related_name='collected_problems', through='ProblemCollectionItem')

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}01_문제'
        ordering = ['-exam', 'id']
        constraints = [
            models.UniqueConstraint(fields=['exam', 'subject', 'number'], name='unique_infinite_problem')
        ]

    def __str__(self):
        return self.reference

    @property
    def exam_name(self):
        return f'{self.exam.get_round_display()} {self.get_subject_display()}'

    @property
    def reference(self):
        return f'{self.exam.round:02}-{self.subject}-{self.number:02}'

    @property
    def semester_round_subject(self):
        return ' '.join([
            self.exam.get_semester_display(),
            self.exam.get_round_display(),
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
        return reverse_lazy('infinite:problem-detail', args=[self.id])

    @staticmethod
    def get_list_url():
        return reverse_lazy('infinite:problem-list')

    def get_like_url(self):
        return reverse_lazy('infinite:like-problem', args=[self.id])

    def get_rate_url(self):
        return reverse_lazy('infinite:rate-problem', args=[self.id])

    def get_solve_url(self):
        return reverse_lazy('infinite:solve-problem', args=[self.id])

    def get_memo_url(self):
        return reverse_lazy('infinite:memo-problem', args=[self.id])

    def get_tag_url(self):
        return reverse_lazy('infinite:tag-problem', args=[self.id])

    def get_collect_url(self):
        return reverse_lazy('infinite:collect-problem', args=[self.id])

    def get_admin_change_url(self):
        return reverse_lazy('admin:a_infinite_problem_change', args=[self.id])


class ProblemOpen(BaseProblemOpen):
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE, related_name='opens')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='infinite_opens')

    class Meta(BaseProblemOpen.Meta):
        db_table = 'a_infinite_problem_open'
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}02_확인기록'

    def __str__(self):
        return f'{self.problem.reference}-{self.user}'


class ProblemLike(BaseProblemLike):
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='infinite_likes')

    class Meta(BaseProblemLike.Meta):
        db_table = 'a_infinite_problem_like'
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}03_즐겨찾기'

    def __str__(self):
        status = 'Liked' if self.is_liked else 'Unliked'
        return f'{self.problem.reference}({status})-{self.user}'


class ProblemRate(BaseProblemRate):
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE, related_name='rates')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='infinite_rates')

    class Meta(BaseProblemRate.Meta):
        db_table = 'a_infinite_problem_rate'
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}04_난이도'

    def __str__(self):
        return f'{self.problem.reference}({self.rating})-{self.user}'


class ProblemSolve(BaseProblemSolve):
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE, related_name='solves')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='infinite_solves')

    class Meta(BaseProblemSolve.Meta):
        db_table = 'a_infinite_problem_solve'
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}05_정답확인'

    def __str__(self):
        status = 'Correct' if self.is_correct else 'Wrong'
        return f'{self.problem.reference}({status})-{self.user}'


class ProblemMemo(BaseProblemMemo):
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE, related_name='memos')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='infinite_memos')

    class Meta(BaseProblemMemo.Meta):
        db_table = 'a_infinite_problem_memo'
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}06_메모'

    def __str__(self):
        return f'{self.problem.reference}-{self.user}'


class ProblemCollection(BaseProblemCollection):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='infinite_collections')

    class Meta(BaseProblemCollection.Meta):
        db_table = 'a_infinite_problem_collection'
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}09_컬렉션'

    def __str__(self):
        return f'{self.title}-{self.user}'

    def get_detail_url(self):
        return reverse_lazy('infinite:collection-detail', args=[self.id])


class ProblemCollectionItem(BaseProblemCollectionItem):
    collection = models.ForeignKey(ProblemCollection, on_delete=models.CASCADE, related_name='collected_items')
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE, related_name='collected_problems')

    class Meta(BaseProblemCollectionItem.Meta):
        db_table = 'a_infinite_problem_collection_item'
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}10_컬렉션 문제'

    def __str__(self):
        return f'{self.collection.title}-{self.problem.reference}'
