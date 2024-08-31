from ckeditor.fields import RichTextField
from ckeditor_uploader.fields import RichTextUploadingField
from django.db import models
from django.urls import reverse_lazy
from django.utils import timezone
from taggit.managers import TaggableManager
from taggit.models import TaggedItemBase, TagBase

from a_common.constants import icon_set
from a_common.models import User
from a_common.model_settings import *


class ProblemTag(TagBase):
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = verbose_name_plural = "07_태그"
        db_table = 'a_daily_problem_tag'

    def __str__(self):
        return f'[Daily]ProblemTag(#{self.id}):{self.name}'


class ProblemTaggedItem(TaggedItemBase):
    tag = models.ForeignKey(ProblemTag, on_delete=models.CASCADE, related_name="tagged_items")
    content_object = models.ForeignKey('Problem', on_delete=models.CASCADE, related_name='tagged_problems')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='daily_tagged_items')
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    remarks = models.TextField(null=True, blank=True)

    class Meta:
        verbose_name = verbose_name_plural = "08_태그 문제"
        unique_together = ['tag', 'content_object', 'user']
        db_table = 'a_daily_problem_tagged_item'

    @property
    def tag_name(self):
        return self.tag.name

    def save(self, *args, **kwargs):
        message_type = kwargs.pop('message_type', 'tagged')
        self.remarks = get_remarks(message_type, self.remarks)
        super().save(*args, **kwargs)

    @property
    def reference(self):
        return self.content_object.reference


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

    tags = TaggableManager(through=ProblemTaggedItem, blank=True)

    open_users = models.ManyToManyField(User, related_name='daily_opened_problems', through='ProblemOpen')
    like_users = models.ManyToManyField(User, related_name='daily_liked_problems', through='ProblemLike')
    rate_users = models.ManyToManyField(User, related_name='daily_rated_problems', through='ProblemRate')
    solve_users = models.ManyToManyField(User, related_name='daily_solved_problems', through='ProblemSolve')
    memo_users = models.ManyToManyField(User, related_name='daily_memoed_problems', through='ProblemMemo')
    collections = models.ManyToManyField(
        'ProblemCollection', related_name='collected_problems', through='ProblemCollectionItem')

    class Meta:
        verbose_name = verbose_name_plural = "01_문제"
        unique_together = ['semester', 'circle', 'round', 'subject', 'number']
        ordering = ['-semester', 'id']

    def __str__(self):
        return f'[Daily]Problem(#{self.id}):{self.reference}'

    @property
    def exam_code(self):
        return f'{self.circle}{self.subject}{self.round}'

    @property
    def exam_name(self):
        return f'{self.get_circle_display()} {self.get_subject_display()} {self.get_round_display()}'

    @property
    def reference(self):
        return f'{self.exam_code}-{self.number:02}'

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
        return reverse_lazy('daily:problem-detail', args=[self.id])

    @staticmethod
    def get_list_url():
        return reverse_lazy('daily:problem-list')

    def get_like_url(self):
        return reverse_lazy('daily:like-problem', args=[self.id])

    def get_rate_url(self):
        return reverse_lazy('daily:rate-problem', args=[self.id])

    def get_solve_url(self):
        return reverse_lazy('daily:solve-problem', args=[self.id])

    def get_memo_url(self):
        return reverse_lazy('daily:memo-problem', args=[self.id])

    def get_tag_url(self):
        return reverse_lazy('daily:tag-problem', args=[self.id])

    def get_collect_url(self):
        return reverse_lazy('daily:collect-problem', args=[self.id])


class ProblemOpen(models.Model):
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE, related_name='opens')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='daily_opens')
    ip_address = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = verbose_name_plural = "02_확인기록"
        db_table = 'a_daily_problem_open'

    def __str__(self):
        return f'[Daily]ProblemOpen(#{self.id}):{self.problem.reference}-{self.user}'

    @property
    def reference(self):
        return self.problem.reference


class ProblemLike(models.Model):
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='daily_likes')
    is_liked = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    remarks = models.TextField(null=True, blank=True)

    class Meta:
        verbose_name = verbose_name_plural = "03_즐겨찾기"
        unique_together = ['user', 'problem']
        ordering = ['-id']
        db_table = 'a_daily_problem_like'

    def __str__(self):
        status = 'Liked' if self.is_liked else 'Unliked'
        return f'[Daily]ProblemLike(#{self.id}):{self.problem.reference}({status})-{self.user}'

    @property
    def reference(self):
        return self.problem.reference

    @property
    def semester_circle_round_subject(self):
        return self.problem.semester_circle_subject_round

    def save(self, *args, **kwargs):
        message_type = kwargs.pop('message_type', 'liked')
        self.remarks = get_remarks(message_type, self.remarks)
        super().save(*args, **kwargs)


class ProblemRate(models.Model):
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE, related_name='rates')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='daily_rates')
    rating = models.IntegerField(choices=rating_choice, default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    remarks = models.TextField(null=True, blank=True)

    class Meta:
        verbose_name = verbose_name_plural = "04_난이도"
        unique_together = ['user', 'problem']
        ordering = ['-id']
        db_table = 'a_daily_problem_rate'

    def __str__(self):
        return f'[Daily]ProblemRate(#{self.id}):{self.problem.reference}({self.rating})-{self.user}'

    @property
    def reference(self):
        return self.problem.reference

    @property
    def semester_circle_round_subject(self):
        return self.problem.semester_circle_subject_round

    def save(self, *args, **kwargs):
        message_type = f'rated({self.rating})'
        self.remarks = get_remarks(message_type, self.remarks)
        super().save(*args, **kwargs)


class ProblemSolve(models.Model):
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE, related_name='solves')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='daily_solves')
    answer = models.IntegerField(choices=answer_choice, default=1)
    is_correct = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    remarks = models.TextField(null=True, blank=True)

    class Meta:
        verbose_name = verbose_name_plural = "05_정답확인"
        unique_together = ['user', 'problem']
        ordering = ['-id']
        db_table = 'a_daily_problem_solve'

    def __str__(self):
        status = 'Correct' if self.is_correct else 'Wrong'
        return f'[Daily]ProblemSolve(#{self.id}):{self.problem.reference}({status})-{self.user}'

    @property
    def reference(self):
        return self.problem.reference

    @property
    def semester_circle_round_subject(self):
        return self.problem.semester_circle_subject_round

    def save(self, *args, **kwargs):
        message_type = 'correct' if self.is_correct else 'wrong'
        message_type = f'{message_type}({self.answer})'
        self.remarks = get_remarks(message_type, self.remarks)
        super().save(*args, **kwargs)


class ProblemMemo(models.Model):
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE, related_name='memos')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='daily_memos')
    content = RichTextField(config_name='minimal', default='')
    created_at = models.DateTimeField(auto_now_add=True)
    remarks = models.TextField(null=True, blank=True)

    class Meta:
        verbose_name = verbose_name_plural = "06_메모"
        unique_together = ['user', 'problem']
        ordering = ['-id']
        db_table = 'a_daily_problem_memo'

    def __str__(self):
        return f'[Daily]ProblemMemo(#{self.id}):{self.problem.reference}-{self.user}'

    @property
    def reference(self):
        return self.problem.reference

    @property
    def semester_circle_round_subject(self):
        return self.problem.semester_circle_subject_round


class ProblemCollection(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='daily_collections')
    title = models.CharField(max_length=20)
    order = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = verbose_name_plural = "09_컬렉션"
        unique_together = ['user', 'title']
        ordering = ['user', 'order']
        db_table = 'a_daily_problem_collection'

    def __str__(self):
        return f'[Daily]ProblemCollection(#{self.id}):{self.title}-{self.user}'

    def get_detail_url(self):
        return reverse_lazy('daily:collection-detail', args=[self.id])


class ProblemCollectionItem(models.Model):
    collection = models.ForeignKey(ProblemCollection, on_delete=models.CASCADE, related_name='collected_items')
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE, related_name='collected_problems')
    order = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = verbose_name_plural = "10_컬렉션 문제"
        unique_together = ['collection', 'problem']
        ordering = ['collection__user', 'collection', 'order']
        db_table = 'a_daily_problem_collection_item'

    def __str__(self):
        return f'[Daily]ProblemCollectionItem(#{self.id}):{self.collection.title}-{self.problem.reference}'

    @property
    def collect_title(self):
        return self.collection.title

    @property
    def reference(self):
        return self.problem.reference

    @property
    def semester_circle_round_subject(self):
        return self.problem.semester_circle_subject_round


class Exam(models.Model):
    semester = models.IntegerField(choices=semester_choice, default=semester_default, verbose_name='기수')
    circle = models.IntegerField(choices=circle_choice, default=1, verbose_name='순환')
    subject = models.CharField(max_length=2, choices=subject_choice, default='형사', verbose_name='과목')
    round = models.IntegerField(choices=round_choice, default=1, verbose_name='회차')
    opened_at = models.DateTimeField(default=timezone.now, verbose_name='공개일시')
    participants = models.IntegerField(default=0, verbose_name='응시생수')
    statistics = models.JSONField(default=statistics_default, verbose_name='성적 통계')

    class Meta:
        verbose_name = verbose_name_plural = "11_시험"
        unique_together = ['semester', 'circle', 'subject', 'round']
        ordering = ['-semester', '-circle', 'subject', 'round']

    def __str__(self):
        return f'[Daily]Exam:{self.full_reference}'

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
    def reference(self):
        return f'{self.get_circle_display()}-{self.get_subject_display()}-{self.get_round_display()}'

    @property
    def is_not_opened(self):
        return timezone.now() <= self.opened_at

    @staticmethod
    def get_answer_list_url():
        return reverse_lazy('daily:answer-list')

    def get_answer_detail_url(self):
        return reverse_lazy('daily:answer-detail', args=[self.id])

    def get_answer_input_url(self):
        return reverse_lazy('daily:answer-input', args=[self.id])

    def get_answer_confirm_url(self):
        return reverse_lazy('daily:answer-confirm', args=[self.id])


class Student(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성일시')
    user = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL, related_name='daily_students')
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
        verbose_name = verbose_name_plural = "12_수험정보"
        unique_together = ['user', 'semester', 'circle', 'subject', 'round']
        ordering = ['-semester', '-circle', 'subject', 'round']

    def __str__(self):
        return f'[Daily]Student:{self.user.name}_{self.full_reference}'

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
        return reverse_lazy('daily:answer-detail', args=[self.id])

    def get_rank_verify_url(self):
        return reverse_lazy('daily:rank-verify', args=[self.id])

    def get_rank_ratio(self, participants: int):
        if participants:
            return round(self.rank * 100 / participants, 1)


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
        verbose_name = verbose_name_plural = "13_답안개수"
        unique_together = ['semester', 'circle', 'subject', 'round', 'number']
        db_table = 'a_daily_answer_count'

    def __str__(self):
        return f'[Daily]AnswerCount:{self.full_reference} {self.number:02}번'

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
