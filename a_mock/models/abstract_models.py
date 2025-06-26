from datetime import datetime

from django.db import models


def year_choice() -> list:
    years = [(year, f'{year}년') for year in range(2023, datetime.now().year + 2)]
    years.reverse()
    return years


def get_next_year() -> int:
    return datetime.now().year + 1


def subject_choice() -> dict:
    return {'형사': '형사법', '헌법': '헌법', '경찰': '경찰학', '범죄': '범죄학', '민법': '민법총칙'}


def get_subject_tuple() -> tuple:
    return '형사', '헌법', '경찰', '범죄', '민법'

def number_choice() -> list:
    return [(number, f'{number}번') for number in range(1, 41)]


def answer_choice() -> dict:
    return {
        1: '①', 2: '②', 3: '③', 4: '④',
        12: '①②', 13: '①③', 14: '①④', 23: '②③', 24: '②④', 34: '③④',
        123: '①②③', 124: '①②④', 134: '①③④', 234: '②③④',
        1234: '①②③④',
    }


def get_default_statistics():
    return {'subject': '', 'participants': 0, 'max': 0, 't10': 0, 't25': 0, 't50': 0, 'avg': 0}


class Statistics(models.Model):
    subject_0 = models.JSONField(default=get_default_statistics, verbose_name='형사법')
    subject_1 = models.JSONField(default=get_default_statistics, verbose_name='헌법')
    subject_2 = models.JSONField(default=get_default_statistics, verbose_name='경찰학')
    subject_3 = models.JSONField(default=get_default_statistics, verbose_name='범죄학')
    subject_4 = models.JSONField(default=get_default_statistics, verbose_name='민법총칙')
    sum = models.JSONField(default=get_default_statistics, verbose_name='총점')

    class Meta:
        abstract = True


class Student(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성 일시')
    name = models.CharField(max_length=20, verbose_name='이름')
    serial = models.CharField(max_length=10, verbose_name='수험번호')
    password = models.CharField(max_length=10, null=True, blank=True, verbose_name='비밀번호')

    class Meta:
        abstract = True

    @property
    def student_info(self):
        return f'{self.serial}-{self.name}'


class Answer(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성 일시')
    answer = models.IntegerField(choices=answer_choice, default=1, verbose_name='답안')

    class Meta:
        abstract = True


class AnswerCount(models.Model):
    problem = None
    count_1 = models.IntegerField(default=0, verbose_name='①')
    count_2 = models.IntegerField(default=0, verbose_name='②')
    count_3 = models.IntegerField(default=0, verbose_name='③')
    count_4 = models.IntegerField(default=0, verbose_name='④')
    count_0 = models.IntegerField(default=0, verbose_name='미표기')
    count_multiple = models.IntegerField(default=0, verbose_name='중복표기')
    count_sum = models.IntegerField(default=0, verbose_name='총계')
    answer_predict = models.IntegerField(default=1, verbose_name='예상정답')

    class Meta:
        abstract = True

    def get_answer_rate(self, ans: int):
        if self.count_sum:
            if 1 <= self.problem.answer <= 4:
                count_target = getattr(self, f'count_{ans}')
            else:
                answer_official_list = [int(digit) for digit in str(self.problem.answer)]
                count_target = sum(
                    getattr(self, f'count_{ans_official}') for ans_official in answer_official_list
                )
            return count_target * 100 / self.count_sum


class Score(models.Model):
    subject_0 = models.FloatField(null=True, blank=True, verbose_name='형사법')
    subject_1 = models.FloatField(null=True, blank=True, verbose_name='한법')
    subject_2 = models.FloatField(null=True, blank=True, verbose_name='경찰학')
    subject_3 = models.FloatField(null=True, blank=True, verbose_name='범죄학')
    subject_4 = models.FloatField(null=True, blank=True, verbose_name='민법총칙')
    sum = models.FloatField(null=True, blank=True, verbose_name='총점')

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self.sum = self.calculate_sum()
        super().save(*args, **kwargs)

    def calculate_sum(self):
        return sum(score for i in range(5) if (score := getattr(self, f'subject_{i}')) is not None)


class Rank(models.Model):
    subject_0 = models.IntegerField(null=True, blank=True, verbose_name='형사법')
    subject_1 = models.IntegerField(null=True, blank=True, verbose_name='헌법')
    subject_2 = models.IntegerField(null=True, blank=True, verbose_name='경찰학')
    subject_3 = models.IntegerField(null=True, blank=True, verbose_name='범죄학')
    subject_4 = models.IntegerField(null=True, blank=True, verbose_name='민법총칙')
    sum = models.IntegerField(null=True, blank=True, verbose_name='총점')
    participants = models.IntegerField(null=True, blank=True, verbose_name='총 인원')

    class Meta:
        abstract = True

    def get_rank_raio(self, rank_code: str):
        _rank = getattr(self, rank_code)
        if self.participants:
            return _rank / self.participants

    def get_rank_raio_by_sub(self, sub: str):
        subject_tuple = get_subject_tuple()
        if sub in subject_tuple and self.participants:
            return getattr(self, f'subject_{subject_tuple.index(sub)}') / self.participants
