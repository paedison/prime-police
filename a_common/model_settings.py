__all__ = [
    'semester_default', 'answer_default', 'statistics_default',
    'semester_choice', 'circle_choice', 'round_choice',
    'subject_choice', 'number_choice', 'answer_choice',
    'rating_choice', 'get_remarks',
    'BaseProblem', 'BaseProblemOpen', 'BaseProblemLike', 'BaseProblemRate',
    'BaseProblemSolve', 'BaseProblemMemo', 'BaseProblemTag', 'BaseProblemTaggedItem',
    'BaseProblemCollection', 'BaseProblemCollectionItem',
    'BaseExam', 'BaseStudent', 'BaseAnswerCount',
]

from datetime import datetime

import pytz
from ckeditor.fields import RichTextField
from ckeditor_uploader.fields import RichTextUploadingField
from django.db import models
from django.utils import timezone
from taggit.managers import TaggableManager
from taggit.models import TaggedItemBase, TagBase

from a_common.constants import icon_set
from a_common.models import User


def semester_default():
    return 75


def answer_default():
    return [0 for _ in range(10)]


def statistics_default():
    return {"max": 0, "t10": 0, "t20": 0, "avg": 0}


def semester_choice() -> list:
    choice = [(semester, f'{semester}기') for semester in range(75, semester_default() + 1)]
    choice.reverse()
    return choice


def circle_choice() -> list:
    return [(circle, f'{circle}순환') for circle in range(1, 4)]


def round_choice() -> list:
    return [(_round, f'제{_round}회') for _round in range(1, 31)]


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


def get_remarks(message_type: str, remarks: str | None) -> str:
    utc_now = datetime.now(pytz.UTC).strftime('%Y-%m-%d %H:%M')
    separator = '|' if remarks else ''
    if remarks:
        remarks += f"{separator}{message_type}_at:{utc_now}"
    else:
        remarks = f"{message_type}_at:{utc_now}"
    return remarks


class BaseProblemTag(TagBase):
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = verbose_name_plural = "07_태그"
        abstract = True


class BaseProblemTaggedItem(TaggedItemBase):
    tag = models.ForeignKey(BaseProblemTag, on_delete=models.CASCADE)
    content_object = models.ForeignKey('BaseProblem', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    remarks = models.TextField(null=True, blank=True)

    class Meta:
        verbose_name = verbose_name_plural = "08_태그 문제"
        unique_together = ['tag', 'content_object', 'user']
        abstract = True

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


class BaseProblem(models.Model):
    semester = models.IntegerField(choices=semester_choice, default=semester_default(), verbose_name='기수')
    circle = models.IntegerField(choices=circle_choice, default=1, verbose_name='순환')
    subject = models.CharField(max_length=2, choices=subject_choice, default='형사', verbose_name='과목')
    round = models.IntegerField(choices=round_choice, default=1, verbose_name='회차')
    number = models.IntegerField(choices=number_choice, default=1, verbose_name='문제 번호')
    answer = models.IntegerField(choices=answer_choice, default=1, verbose_name='정답')
    question = models.TextField(default='', verbose_name='발문')
    data = RichTextUploadingField(config_name='problem', default='', verbose_name='문제 내용')
    opened_at = models.DateField(default=timezone.now, verbose_name='공개일')

    tags = TaggableManager()

    open_users = models.ManyToManyField(User)
    like_users = models.ManyToManyField(User)
    rate_users = models.ManyToManyField(User)
    solve_users = models.ManyToManyField(User)
    memo_users = models.ManyToManyField(User)
    collections = models.ManyToManyField('BaseProblemCollection')

    class Meta:
        verbose_name = verbose_name_plural = "01_문제"
        unique_together = ['semester', 'circle', 'round', 'subject', 'number']
        ordering = ['-semester', 'id']
        abstract = True

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


class BaseProblemOpen(models.Model):
    problem = models.ForeignKey(BaseProblem, on_delete=models.CASCADE, related_name='opens')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    ip_address = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = verbose_name_plural = "02_확인기록"
        # ordering = ['-id']
        abstract = True

    @property
    def reference(self):
        return self.problem.reference


class BaseProblemLike(models.Model):
    problem = models.ForeignKey(BaseProblem, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    is_liked = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    remarks = models.TextField(null=True, blank=True)

    class Meta:
        verbose_name = verbose_name_plural = "03_즐겨찾기"
        unique_together = ['user', 'problem']
        ordering = ['-id']
        abstract = True

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


class BaseProblemRate(models.Model):
    problem = models.ForeignKey(BaseProblem, on_delete=models.CASCADE, related_name='rates')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField(choices=rating_choice, default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    remarks = models.TextField(null=True, blank=True)

    class Meta:
        verbose_name = verbose_name_plural = "04_난이도"
        unique_together = ['user', 'problem']
        ordering = ['-id']
        abstract = True

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


class BaseProblemSolve(models.Model):
    problem = models.ForeignKey(BaseProblem, on_delete=models.CASCADE, related_name='solves')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    answer = models.IntegerField(choices=answer_choice, default=1)
    is_correct = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    remarks = models.TextField(null=True, blank=True)

    class Meta:
        verbose_name = verbose_name_plural = "05_정답확인"
        unique_together = ['user', 'problem']
        ordering = ['-id']
        abstract = True

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


class BaseProblemMemo(models.Model):
    problem = models.ForeignKey(BaseProblem, on_delete=models.CASCADE, related_name='memos')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = RichTextField(config_name='minimal', default='')
    created_at = models.DateTimeField(auto_now_add=True)
    remarks = models.TextField(null=True, blank=True)

    class Meta:
        verbose_name = verbose_name_plural = "06_메모"
        unique_together = ['user', 'problem']
        ordering = ['-id']
        abstract = True

    @property
    def reference(self):
        return self.problem.reference

    @property
    def semester_circle_round_subject(self):
        return self.problem.semester_circle_subject_round


class BaseProblemCollection(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=20)
    order = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = verbose_name_plural = "09_컬렉션"
        unique_together = ['user', 'title']
        ordering = ['user', 'order']
        abstract = True


class BaseProblemCollectionItem(models.Model):
    collection = models.ForeignKey(BaseProblemCollection, on_delete=models.CASCADE, related_name='collected_items')
    problem = models.ForeignKey(BaseProblem, on_delete=models.CASCADE, related_name='collected_problems')
    order = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = verbose_name_plural = "10_컬렉션 문제"
        unique_together = ['collection', 'problem']
        ordering = ['collection__user', 'collection', 'order']
        abstract = True

    @property
    def collect_title(self):
        return self.collection.title

    @property
    def reference(self):
        return self.problem.reference

    @property
    def semester_circle_round_subject(self):
        return self.problem.semester_circle_subject_round


class BaseExam(models.Model):
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
        abstract = True

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


class BaseStudent(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성일시')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
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
        abstract = True

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

    def get_rank_ratio(self, participants: int):
        if participants:
            return round(self.rank * 100 / participants, 1)


class BaseAnswerCount(models.Model):
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
        ordering = ['-semester', '-circle', 'subject', 'round', 'number']
        abstract = True

    @property
    def full_reference(self):
        return ' '.join([
            self.get_semester_display(),
            self.get_circle_display(),
            self.get_subject_display(),
            self.get_round_display(),
            f'{self.number}번',
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
