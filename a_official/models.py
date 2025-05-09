from datetime import datetime

from ckeditor.fields import RichTextField
from ckeditor_uploader.fields import RichTextUploadingField
from django.db import models
from django.urls import reverse_lazy
from taggit.managers import TaggableManager
from taggit.models import TaggedItemBase, TagBase

from a_common.constants import icon_set
from a_common.models import User
from a_common.prime_test.model_settings import number_choice, answer_choice, rating_choice, get_remarks


def default_year():
    return datetime.now().year + 1


def year_choice() -> list:
    choice = [(year, f'{year}년') for year in range(2023, datetime.now().year + 2)]
    choice.reverse()
    return choice


def exam_choice() -> dict:
    return {'경위': '경위공채'}


def subject_choice() -> dict:
    return {
        '형사': '형사법', '헌법': '헌법', '경찰': '경찰학', '범죄': '범죄학',
        '민법': '민법총칙', '행법': '행정법', '행학': '행정학',
    }


def subject_fields() -> dict:
    return {
        '형사': 'hyeongsa', '헌법': 'heonbeob', '경찰': 'gyeongchal', '범죄': 'beomjoe',
        '민법': 'minbeob', '행법': 'haengbeob', '행학': 'haenghag',
    }


class ProblemTag(TagBase):
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = verbose_name_plural = "07_태그"
        db_table = 'a_official_problem_tag'

    def __str__(self):
        return f'[Official]ProblemTag(#{self.id}):{self.name}'


class ProblemTaggedItem(TaggedItemBase):
    tag = models.ForeignKey(ProblemTag, on_delete=models.CASCADE, related_name="tagged_items")
    content_object = models.ForeignKey('Problem', on_delete=models.CASCADE, related_name='tagged_problems')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='official_tagged_items')
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    remarks = models.TextField(null=True, blank=True)

    class Meta:
        verbose_name = verbose_name_plural = "08_태그 문제"
        unique_together = ['tag', 'content_object', 'user']
        db_table = 'a_official_problem_tagged_item'

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
    year = models.IntegerField(choices=year_choice, default=default_year, verbose_name='연도')
    exam = models.CharField(max_length=2, choices=exam_choice, default='경위', verbose_name='시험')
    subject = models.CharField(max_length=2, choices=subject_choice, default='형사', verbose_name='과목')
    number = models.IntegerField(choices=number_choice, default=1, verbose_name='문제 번호')
    answer = models.IntegerField(choices=answer_choice, default=1, verbose_name='정답')
    question = models.TextField(verbose_name='발문')
    data = RichTextUploadingField(config_name='problem', verbose_name='문제 내용')

    tags = TaggableManager(through=ProblemTaggedItem, blank=True)

    open_users = models.ManyToManyField(User, related_name='official_opened_problems', through='ProblemOpen')
    like_users = models.ManyToManyField(User, related_name='official_liked_problems', through='ProblemLike')
    rate_users = models.ManyToManyField(User, related_name='official_rated_problems', through='ProblemRate')
    solve_users = models.ManyToManyField(User, related_name='official_solved_problems', through='ProblemSolve')
    memo_users = models.ManyToManyField(User, related_name='official_memoed_problems', through='ProblemMemo')
    collections = models.ManyToManyField(
        'ProblemCollection', related_name='collected_problems', through='ProblemCollectionItem')

    class Meta:
        verbose_name = verbose_name_plural = "01_문제"
        unique_together = ['year', 'exam', 'subject', 'number']
        ordering = ['-year', 'id']

    def __str__(self):
        return f'[Official]Problem(#{self.id}):{self.reference}'

    @property
    def exam_code(self):
        return f'{self.year}{self.subject}'

    @property
    def exam_name(self):
        return f'{self.get_year_display()} {self.get_subject_display()}'

    @property
    def reference(self):
        return f'{self.year}{self.subject}{self.number:02}'

    @property
    def year_subject(self):
        return ' '.join([self.get_year_display(), self.get_subject_display()])

    @property
    def full_reference(self):
        return ' '.join([self.year_subject, self.get_number_display()])

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

    @staticmethod
    def get_list_url():
        return reverse_lazy('official:base')

    def get_absolute_url(self):
        return reverse_lazy('official:problem-detail', args=[self.id])

    def get_like_url(self):
        return reverse_lazy('official:like-problem', args=[self.id])

    def get_rate_url(self):
        return reverse_lazy('official:rate-problem', args=[self.id])

    def get_solve_url(self):
        return reverse_lazy('official:solve-problem', args=[self.id])

    def get_memo_url(self):
        return reverse_lazy('official:memo-problem', args=[self.id])

    def get_tag_url(self):
        return reverse_lazy('official:tag-problem', args=[self.id])

    def get_collect_url(self):
        return reverse_lazy('official:collect-problem', args=[self.id])


class ProblemOpen(models.Model):
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE, related_name='opens')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='official_opens')
    ip_address = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = verbose_name_plural = "02_확인기록"
        db_table = 'a_official_problem_open'

    def __str__(self):
        return f'[Official]ProblemOpen(#{self.id}):{self.problem.reference}-{self.user}'

    @property
    def reference(self):
        return self.problem.reference


class ProblemLike(models.Model):
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='official_likes')
    is_liked = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    remarks = models.TextField(null=True, blank=True)

    class Meta:
        verbose_name = verbose_name_plural = "03_즐겨찾기"
        unique_together = ['user', 'problem']
        ordering = ['-id']
        db_table = 'a_official_problem_like'

    def __str__(self):
        status = 'Liked' if self.is_liked else 'Unliked'
        return f'[Official]ProblemLike(#{self.id}):{self.problem.reference}({status})-{self.user}'

    @property
    def reference(self):
        return self.problem.reference

    @property
    def year_subject(self):
        return self.problem.year_subject

    def save(self, *args, **kwargs):
        message_type = kwargs.pop('message_type', 'liked')
        self.remarks = get_remarks(message_type, self.remarks)
        super().save(*args, **kwargs)


class ProblemRate(models.Model):
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE, related_name='rates')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='official_rates')
    rating = models.IntegerField(choices=rating_choice, default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    remarks = models.TextField(null=True, blank=True)

    class Meta:
        verbose_name = verbose_name_plural = "04_난이도"
        unique_together = ['user', 'problem']
        ordering = ['-id']
        db_table = 'a_official_problem_rate'

    def __str__(self):
        return f'[Official]ProblemRate(#{self.id}):{self.problem.reference}({self.rating})-{self.user}'

    @property
    def reference(self):
        return self.problem.reference

    @property
    def year_subject(self):
        return self.problem.year_subject

    def save(self, *args, **kwargs):
        message_type = f'rated({self.rating})'
        self.remarks = get_remarks(message_type, self.remarks)
        super().save(*args, **kwargs)


class ProblemSolve(models.Model):
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE, related_name='solves')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='official_solves')
    answer = models.IntegerField(choices=answer_choice, default=1)
    is_correct = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    remarks = models.TextField(null=True, blank=True)

    class Meta:
        verbose_name = verbose_name_plural = "05_정답확인"
        unique_together = ['user', 'problem']
        ordering = ['-id']
        db_table = 'a_official_problem_solve'

    def __str__(self):
        status = 'Correct' if self.is_correct else 'Wrong'
        return f'[Official]ProblemSolve(#{self.id}):{self.problem.reference}({status})-{self.user}'

    @property
    def reference(self):
        return self.problem.reference

    @property
    def year_subject(self):
        return self.problem.year_subject

    def save(self, *args, **kwargs):
        message_type = 'correct' if self.is_correct else 'wrong'
        message_type = f'{message_type}({self.answer})'
        self.remarks = get_remarks(message_type, self.remarks)
        super().save(*args, **kwargs)


class ProblemMemo(models.Model):
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE, related_name='memos')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='official_memos')
    content = RichTextField(config_name='minimal', default='')
    created_at = models.DateTimeField(auto_now_add=True)
    remarks = models.TextField(null=True, blank=True)

    class Meta:
        verbose_name = verbose_name_plural = "06_메모"
        unique_together = ['user', 'problem']
        ordering = ['-id']
        db_table = 'a_official_problem_memo'

    def __str__(self):
        return f'[Official]ProblemMemo(#{self.id}):{self.problem.reference}-{self.user}'

    @property
    def reference(self):
        return self.problem.reference

    @property
    def year_subject(self):
        return self.problem.year_subject


class ProblemCollection(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='official_collections')
    title = models.CharField(max_length=20)
    order = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = verbose_name_plural = "09_컬렉션"
        unique_together = ['user', 'title']
        ordering = ['user', 'order']
        db_table = 'a_official_problem_collection'

    def __str__(self):
        return f'[Official]ProblemCollection(#{self.id}):{self.title}-{self.user}'

    def get_detail_url(self):
        return reverse_lazy('official:collection-detail', args=[self.id])


class ProblemCollectionItem(models.Model):
    collection = models.ForeignKey(ProblemCollection, on_delete=models.CASCADE, related_name='collected_items')
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE, related_name='collected_problems')
    order = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = verbose_name_plural = "10_컬렉션 문제"
        unique_together = ['collection', 'problem']
        ordering = ['collection__user', 'collection', 'order']
        db_table = 'a_official_problem_collection_item'

    def __str__(self):
        return f'[Official]ProblemCollectionItem(#{self.id}):{self.collection.title}-{self.problem.reference}'

    @property
    def collect_title(self):
        return self.collection.title

    @property
    def reference(self):
        return self.problem.reference

    @property
    def year_subject(self):
        return self.problem.year_subject
