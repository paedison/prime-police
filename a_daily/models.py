from datetime import datetime

import pytz
from ckeditor.fields import RichTextField
from ckeditor_uploader.fields import RichTextUploadingField
from django.db import models
from django.urls import reverse
from taggit.managers import TaggableManager
from taggit.models import TaggedItemBase, TagBase

from a_common.constants import icon_set
from a_common.models import User


def year_default():
    return 2026


def year_choice() -> list:
    choice = [(year, f'{year}년') for year in range(2026, datetime.now().year + 3)]
    choice.reverse()
    return choice


def circle_choice() -> list:
    return [(circle, f'{circle}순환') for circle in range(1, 4)]


def round_choice() -> list:
    return [(_round, f'{_round}회차') for _round in range(1, 30)]


def subject_choice() -> dict:
    return {
        '형법': '형법', '경찰': '경찰학', '헌법': '헌법', '범죄': '범죄학',
        '형소': '형사소송법', '민법': '민법총칙',
    }


def number_choice() -> list:
    return [(number, f'{number}번') for number in range(1, 41)]


def answer_choice() -> dict:
    return {1: '①', 2: '②', 3: '③', 4: '④'}


def rating_choice() -> dict:
    return {1: '⭐️', 2: '⭐️⭐️', 3: '⭐️⭐️⭐️', 4: '⭐️⭐️⭐️⭐️', 5: '⭐️⭐️⭐️⭐️⭐️'}


def subject_fields() -> dict:
    return {
        '형법': 'hyeongbeob', '경찰': 'gyeongchal', '헌법': 'heonbeob', '범죄': 'beomjoe',
        '형소': 'hyeongso', '민법': 'minbeob',
    }


def get_remarks(message_type: str, remarks: str | None) -> str:
    utc_now = datetime.now(pytz.UTC).strftime('%Y-%m-%d %H:%M')
    separator = '|' if remarks else ''
    if remarks:
        remarks += f"{separator}{message_type}_at:{utc_now}"
    else:
        remarks = f"{message_type}_at:{utc_now}"
    return remarks


class ProblemTag(TagBase):
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = verbose_name_plural = "데일리테스트 태그"
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
        verbose_name = verbose_name_plural = "데일리테스트 태그 문제"
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
    year = models.IntegerField(choices=year_choice, default=year_default(), verbose_name='연도')
    circle = models.IntegerField(choices=circle_choice, default=1, verbose_name='순환')
    round = models.IntegerField(choices=round_choice, default=1, verbose_name='회차')
    subject = models.CharField(max_length=2, choices=subject_choice, default='형사', verbose_name='과목')
    number = models.IntegerField(choices=number_choice, default=1, verbose_name='문제 번호')
    answer = models.IntegerField(choices=answer_choice, default=1, verbose_name='정답')
    question = models.TextField(verbose_name='발문')
    data = RichTextUploadingField(config_name='problem', verbose_name='문제 내용')

    tags = TaggableManager(through=ProblemTaggedItem, blank=True)

    open_users = models.ManyToManyField(User, related_name='daily_opened_problems', through='ProblemOpen')
    like_users = models.ManyToManyField(User, related_name='daily_liked_problems', through='ProblemLike')
    rate_users = models.ManyToManyField(User, related_name='daily_rated_problems', through='ProblemRate')
    solve_users = models.ManyToManyField(User, related_name='daily_solved_problems', through='ProblemSolve')
    memo_users = models.ManyToManyField(User, related_name='daily_memoed_problems', through='ProblemMemo')
    comment_users = models.ManyToManyField(User, related_name='daily_commented_problems', through='ProblemComment')
    collections = models.ManyToManyField(
        'ProblemCollection', related_name='collected_problems', through='ProblemCollectionItem')

    class Meta:
        verbose_name = verbose_name_plural = "데일리테스트"
        unique_together = ['year', 'circle', 'round', 'subject', 'number']
        ordering = ['-year', 'id']

    def __str__(self):
        return f'[Daily]Problem(#{self.id}):{self.reference}'

    @property
    def circle_round_sub(self):
        return f'{self.circle}-{self.round}-{self.subject}'

    @property
    def reference(self):
        return f'{self.circle}-{self.round}-{self.subject}{self.number:02}'

    @property
    def circle_round_subject(self):
        return ' '.join([
            self.get_circle_display(), self.get_round_display(), self.get_subject_display()
        ])

    @property
    def full_reference(self):
        return ' '.join([self.circle_round_subject, self.get_number_display()])

    @property
    def subject_field(self):
        return subject_fields()[self.subject]

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
        return reverse('daily:problem-detail', args=[self.id])

    def get_like_url(self):
        return reverse('daily:like-problem', args=[self.id])

    def get_rate_url(self):
        return reverse('daily:rate-problem', args=[self.id])

    def get_solve_url(self):
        return reverse('daily:solve-problem', args=[self.id])

    def get_tag_url(self):
        return reverse('daily:tag-problem', args=[self.id])

    def get_collect_url(self):
        return reverse('daily:collect-problem', args=[self.id])

    def get_comment_create_url(self):
        return reverse('daily:comment-problem-create', args=[self.id])


class ProblemOpen(models.Model):
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE, related_name='opens')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='daily_opens')
    ip_address = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = verbose_name_plural = "데일리테스트 확인 기록"
        db_table = 'a_daily_problem_open'

    def __str__(self):
        return f'[Daily]ProblemOpen(#{self.id}):{self.problem.reference}-{self.user.username}'

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
        verbose_name = verbose_name_plural = "데일리테스트 즐겨찾기"
        unique_together = ['user', 'problem']
        ordering = ['-id']
        db_table = 'a_daily_problem_like'

    def __str__(self):
        status = 'Liked' if self.is_liked else 'Unliked'
        return f'[Daily]ProblemLike(#{self.id}):{self.problem.reference}({status})-{self.user.username}'

    @property
    def reference(self):
        return self.problem.reference

    @property
    def year_subject(self):
        return self.problem.circle_round_subject

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
        verbose_name = verbose_name_plural = "데일리테스트 난이도"
        unique_together = ['user', 'problem']
        ordering = ['-id']
        db_table = 'a_daily_problem_rate'

    def __str__(self):
        return f'[Daily]ProblemRate(#{self.id}):{self.problem.reference}({self.rating})-{self.user.username}'

    @property
    def reference(self):
        return self.problem.reference

    @property
    def year_subject(self):
        return self.problem.circle_round_subject

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
        verbose_name = verbose_name_plural = "데일리테스트 정답확인"
        unique_together = ['user', 'problem']
        ordering = ['-id']
        db_table = 'a_daily_problem_solve'

    def __str__(self):
        status = 'Correct' if self.is_correct else 'Wrong'
        return f'[Daily]ProblemSolve(#{self.id}):{self.problem.reference}({status})-{self.user.username}'

    @property
    def reference(self):
        return self.problem.reference

    @property
    def year_subject(self):
        return self.problem.circle_round_subject

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
        verbose_name = verbose_name_plural = "데일리테스트 메모"
        unique_together = ['user', 'problem']
        ordering = ['-id']
        db_table = 'a_daily_problem_memo'

    def __str__(self):
        return f'[Daily]ProblemMemo(#{self.id}):{self.problem.reference}-{self.user.username}'

    @property
    def reference(self):
        return self.problem.reference

    @property
    def year_subject(self):
        return self.problem.circle_round_subject


class ProblemComment(models.Model):
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='daily_comments')
    title = models.TextField(max_length=100, default='')
    content = RichTextField(config_name='minimal', default='')
    like_users = models.ManyToManyField(
        User, related_name='daily_liked_comments', through='ProblemCommentLike')
    parent = models.ForeignKey(
        'self', on_delete=models.CASCADE, null=True, blank=True, related_name='reply_comments')
    hit = models.IntegerField(default=1, verbose_name='조회수')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = verbose_name_plural = "데일리테스트 코멘트"
        ordering = ['-id']
        db_table = 'a_daily_problem_comment'

    def __str__(self):
        prefix = '↪ ' if self.parent else ''
        return f'{prefix}[Daily]ProblemComment(#{self.id}):{self.problem.reference}-{self.user.username}'

    @property
    def reference(self):
        return self.problem.reference

    @property
    def year_subject(self):
        return self.problem.circle_round_subject


class ProblemCommentLike(models.Model):
    comment = models.ForeignKey(ProblemComment, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='daily_problem_comment_likes')
    is_liked = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    remarks = models.TextField(null=True, blank=True)

    def __str__(self):
        return f'[Daily]ProblemCommentLike(#{self.id}):{self.comment.problem.reference}-{self.user.username}'

    class Meta:
        db_table = 'a_daily_problem_comment_like'

    @property
    def reference(self):
        return self.comment.problem.reference

    @property
    def year_subject(self):
        return self.comment.problem.circle_round_subject

    def save(self, *args, **kwargs):
        message_type = kwargs.pop('message_type', 'liked')
        self.remarks = get_remarks(message_type, self.remarks)
        super().save(*args, **kwargs)


class ProblemCollection(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='daily_collections')
    title = models.CharField(max_length=20)
    order = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = verbose_name_plural = "데일리테스트 컬렉션"
        unique_together = ['user', 'title']
        ordering = ['user', 'order']
        db_table = 'a_daily_problem_collection'

    def __str__(self):
        return f'[Daily]ProblemCollection(#{self.id}):{self.title}-{self.user.username}'


class ProblemCollectionItem(models.Model):
    collection = models.ForeignKey(ProblemCollection, on_delete=models.CASCADE, related_name='collected_items')
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE, related_name='collected_problems')
    order = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = verbose_name_plural = "데일리테스트 컬렉션 문제"
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
    def year_subject(self):
        return self.problem.circle_round_subject
