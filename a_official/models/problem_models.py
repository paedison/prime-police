from ckeditor.fields import RichTextField
from ckeditor_uploader.fields import RichTextUploadingField
from django.db import models
from django.urls import reverse
from taggit.managers import TaggableManager
from taggit.models import TaggedItemBase, TagBase

from a_common.constants import icon_set
from a_common.models import User
from .base_settings import (
    TimeRemarkBase, get_current_year, year_choices,
    exam_choices, subject_choices, number_choices,
    answer_choices, rating_choices,
)


class Problem(TimeRemarkBase):
    year = models.IntegerField(choices=year_choices, default=get_current_year())
    exam = models.CharField(max_length=10, choices=exam_choices, default='경위')
    subject = models.CharField(max_length=10, choices=subject_choices, default='형사')
    number = models.IntegerField(choices=number_choices, default=1)
    answer = models.IntegerField(choices=answer_choices, default=1)
    question = models.TextField()
    data = RichTextUploadingField(config_name='problem')

    tags = TaggableManager(through='ProblemTaggedItem', blank=True)

    open_users = models.ManyToManyField(
        User, related_name='official_opened_problems', through='ProblemOpen')
    like_users = models.ManyToManyField(
        User, related_name='official_liked_problems', through='ProblemLike')
    rate_users = models.ManyToManyField(
        User, related_name='official_rated_problems', through='ProblemRate')
    solve_users = models.ManyToManyField(
        User, related_name='official_solved_problems', through='ProblemSolve')
    memo_users = models.ManyToManyField(
        User, related_name='official_memoed_problems', through='ProblemMemo')
    comment_users = models.ManyToManyField(
        User, related_name='official_commented_problems', through='ProblemComment')
    collections = models.ManyToManyField(
        'ProblemCollect', related_name='collected_problems', through='ProblemCollectedItem')

    class Meta:
        verbose_name = verbose_name_plural = "기출문제"
        unique_together = ['year', 'exam', 'subject', 'number']
        ordering = ['-year', 'id']

    def __str__(self):
        return f'[Official]Problem:{self.reference}(id:{self.id})'

    @staticmethod
    def get_year_choices(): return year_choices()

    @staticmethod
    def get_exam_choices(): return exam_choices()

    @staticmethod
    def get_subject_choices(): return subject_choices()

    @staticmethod
    def get_number_choices(): return number_choices()

    @staticmethod
    def get_answer_choices(): return answer_choices()

    def get_absolute_url(self): return reverse('official:problem-detail', args=[self.id])

    def get_like_url(self): return reverse('official:like-problem', args=[self.id])

    def get_rate_url(self): return reverse('official:rate-problem', args=[self.id])

    def get_solve_url(self): return reverse('official:solve-problem', args=[self.id])

    def get_tag_create_url(self): return reverse('official:tag-problem-create', args=[self.id])

    def get_tag_remove_url(self): return reverse('official:tag-problem-remove', args=[self.id])

    @property
    def year_ex_sub(self): return f'{self.year}{self.exam}{self.subject}'

    @property
    def reference(self): return f'{self.year}{self.subject}{self.number:02}'

    @property
    def full_reference(self):
        return ' '.join([
            self.get_year_display(),
            self.get_exam_display(),
            self.get_subject_display(),
            self.get_number_display(),
        ])

    @property
    def department(self):
        for category, subjects in subject_choices().items():
            for subject in subjects.keys():
                if subject == self.subject:
                    return category.split(' ')[0]

    @property
    def bg_color(self):
        bg_color_dict = {
            '전체': 'bg_heonbeob',
            '일반': 'bg_eoneo',
            '세무회계': 'bg_jaryo',
            '사이버': 'bg_sanghwang',
        }
        return bg_color_dict[self.department]

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


class ProblemOpen(TimeRemarkBase):
    problem = models.ForeignKey(
        Problem, on_delete=models.CASCADE, related_name='problem_open_set')
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='official_problem_open_set')
    ip_address = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = verbose_name_plural = "기출문제 확인 기록"
        db_table = 'a_official_problem_open'

    def __str__(self): return f'[Official]ProblemOpen:{self.problem.reference}-{self.user.username}'


class ProblemLike(TimeRemarkBase):
    problem = models.ForeignKey(
        Problem, on_delete=models.CASCADE, related_name='problem_like_set')
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='official_problem_like_set')
    is_liked = models.BooleanField(default=True)

    class Meta:
        verbose_name = verbose_name_plural = "기출문제 즐겨찾기"
        unique_together = ['problem', 'user']
        db_table = 'a_official_problem_like'

    def __str__(self): return f'[Official]ProblemLike:{self.problem.reference}-{self.user.username}'


class ProblemRate(TimeRemarkBase):
    problem = models.ForeignKey(
        Problem, on_delete=models.CASCADE, related_name='problem_rate_set')
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='official_problem_rate_set')
    rating = models.IntegerField(choices=rating_choices)

    class Meta:
        verbose_name = verbose_name_plural = "기출문제 난이도"
        unique_together = ['problem', 'user']
        db_table = 'a_official_problem_rate'

    def __str__(self):
        return (f'[Official]ProblemRate:{self.problem.reference}-{self.user.username}'
                f'(rating:{self.rating})')

    @staticmethod
    def get_rating_choices(): return rating_choices()


class ProblemSolve(TimeRemarkBase):
    problem = models.ForeignKey(
        Problem, on_delete=models.CASCADE, related_name='problem_solve_set')
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='official_problem_solve_set')
    answer = models.IntegerField(choices=answer_choices)
    is_correct = models.BooleanField()

    class Meta:
        verbose_name = verbose_name_plural = "기출문제 정답확인"
        unique_together = ['problem', 'user']
        db_table = 'a_official_problem_solve'

    def __str__(self):
        result = 'O' if self.is_correct else 'X'
        return (f'[Official]ProblemSolve:{self.problem.reference}-{self.user.username}'
                f'(answer:{self.answer},result:{result})')

    @staticmethod
    def get_answer_choices(): return answer_choices()


class ProblemMemo(TimeRemarkBase):
    problem = models.ForeignKey(
        Problem, on_delete=models.CASCADE, related_name='problem_memo_set')
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='official_problem_memo_set')
    memo = RichTextField(config_name='minimal')

    class Meta:
        verbose_name = verbose_name_plural = "기출문제 메모"
        unique_together = ['problem', 'user']
        db_table = 'a_official_problem_memo'

    def __str__(self):
        return f'[Official]ProblemMemo:{self.problem.reference}-{self.user.username}'


class ProblemComment(TimeRemarkBase):
    problem = models.ForeignKey(
        Problem, on_delete=models.CASCADE, related_name='problem_comment_set')
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='official_problem_comment_set')
    title = models.TextField(max_length=100)
    comment = RichTextField(config_name='minimal')
    parent = models.ForeignKey(
        'self', on_delete=models.CASCADE, null=True, blank=True, related_name='reply_comments')
    hit = models.IntegerField(default=1, verbose_name='조회수')

    class Meta:
        verbose_name = verbose_name_plural = "기출문제 코멘트"
        unique_together = ['problem', 'user']
        db_table = 'a_official_problem_comment'

    def __str__(self):
        return f'[Official]ProblemComment:{self.problem.reference}-{self.user.username}'


class ProblemTag(TagBase):
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = verbose_name_plural = "기출문제 태그"
        db_table = 'a_official_problem_tag'

    def __str__(self):
        return f'[Official]ProblemTag:{self.name}'


class ProblemTaggedItem(TimeRemarkBase, TaggedItemBase):
    tag = models.ForeignKey(ProblemTag, on_delete=models.CASCADE, related_name='tagged_items')
    content_object = models.ForeignKey(
        Problem, on_delete=models.CASCADE, related_name='problem_tagged_items')
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='official_problem_tagged_items')
    is_tagged = models.BooleanField(default=True)

    class Meta:
        verbose_name = verbose_name_plural = "태그된 기출문제"
        unique_together = ('tag', 'content_object', 'user')
        db_table = 'a_official_problem_tagged_item'


class ProblemCollect(TimeRemarkBase):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='official_problem_collect_set')
    title = models.CharField(max_length=20)
    order = models.IntegerField()

    class Meta:
        verbose_name = verbose_name_plural = "기출문제 컬렉션"
        unique_together = ["user", "title"]
        db_table = 'a_official_problem_collect'

    def __str__(self):
        return (f'[Official]ProblemCollect:{self.title}-{self.user.username}'
                f'(id:{self.id},user_id:{self.user_id})')


class ProblemCollectedItem(TimeRemarkBase):
    collect = models.ForeignKey(
        ProblemCollect, on_delete=models.CASCADE, related_name='collected_items')
    problem = models.ForeignKey(
        Problem, on_delete=models.CASCADE, related_name='problem_collected_items')
    order = models.IntegerField()

    class Meta:
        verbose_name = verbose_name_plural = "컬렉션에 추가된 기출문제"
        unique_together = ['collect', 'problem']
        db_table = 'a_official_problem_collected_item'

    def __str__(self):
        return (f'[Official]ProblemCollectedItem:{self.problem.reference}'
                f'(collect:{self.collect.title},collect_id:{self.collect_id}')

    def set_active(self):
        self.is_active = True
        self.save()

    def set_inactive(self):
        self.is_active = False
        self.save()
