from django.db import models
from django.db.models.functions import Greatest

from . import choices


def get_default_statistics():
    return {"participants": 0, "max": 0, "t10": 0, "t25": 0, "t50": 0, "avg": 0}


def get_subject_tuple() -> tuple:
    return '형사', '헌법', '경찰', '범죄', '민법', '행법', '행학'


class Statistics(models.Model):
    subject_0 = models.JSONField(default=get_default_statistics, verbose_name='형사법')
    subject_1 = models.JSONField(default=get_default_statistics, verbose_name='헌법')
    subject_2 = models.JSONField(default=get_default_statistics, verbose_name='경찰학')
    subject_3 = models.JSONField(default=get_default_statistics, verbose_name='범죄학')
    subject_4 = models.JSONField(default=get_default_statistics, verbose_name='민법총칙')
    subject_5 = models.JSONField(default=get_default_statistics, verbose_name='행정법')
    subject_6 = models.JSONField(default=get_default_statistics, verbose_name='행정학')
    sum = models.JSONField(default=get_default_statistics, verbose_name='총점')

    class Meta:
        abstract = True


class Student(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성 일시')
    serial = models.CharField(max_length=10, verbose_name='수험번호')
    name = models.CharField(max_length=20, verbose_name='이름')
    password = models.CharField(max_length=10, verbose_name='비밀번호')
    selection = models.CharField(max_length=2, choices=choices.selection_choice, verbose_name='선택과목')

    class Meta:
        abstract = True


class Answer(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='작성 일시')
    answer = models.IntegerField(choices=choices.answer_choice, default=1, verbose_name='답안')

    class Meta:
        abstract = True


def get_case_for_answer(answer: int):
    return models.When(
        models.Q(**{f'count_{answer}': Greatest('count_1', 'count_2', 'count_3', 'count_4')}),
        then=models.Value(answer),
    )


class AnswerCount(models.Model):
    problem = None
    count_1 = models.IntegerField(default=0, verbose_name='①')
    count_2 = models.IntegerField(default=0, verbose_name='②')
    count_3 = models.IntegerField(default=0, verbose_name='③')
    count_4 = models.IntegerField(default=0, verbose_name='④')
    count_0 = models.IntegerField(default=0, verbose_name='미표기')
    count_multiple = models.IntegerField(default=0, verbose_name='중복표기')
    count_sum = models.IntegerField(default=0, verbose_name='총계')
    answer_predict = models.GeneratedField(
        expression=models.Case(
            get_case_for_answer(1), get_case_for_answer(2),
            get_case_for_answer(3), get_case_for_answer(4), default=None,
        ),
        output_field=models.IntegerField(),
        db_persist=True,
    )

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

    def get_answer_predict_rate(self):
        if self.count_sum:
            return getattr(self, f'count_{self.answer_predict}') * 100 / self.count_sum


class Score(models.Model):
    subject_0 = models.FloatField(null=True, blank=True, verbose_name='형사법')
    subject_1 = models.FloatField(null=True, blank=True, verbose_name='한법')
    subject_2 = models.FloatField(null=True, blank=True, verbose_name='경찰학')
    subject_3 = models.FloatField(null=True, blank=True, verbose_name='범죄학')
    subject_4 = models.FloatField(null=True, blank=True, verbose_name='민법총칙')
    subject_5 = models.FloatField(null=True, blank=True, verbose_name='행정법')
    subject_6 = models.FloatField(null=True, blank=True, verbose_name='행정학')
    sum = models.FloatField(null=True, blank=True, verbose_name='총점 표준점수')

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self.sum = self.calculate_sum()
        super().save(*args, **kwargs)

    def calculate_sum(self):
        return sum(score for i in range(7) if (score := getattr(self, f'subject_{i}')) is not None)


class Rank(models.Model):
    subject_0 = models.IntegerField(null=True, blank=True, verbose_name='형사법')
    subject_1 = models.IntegerField(null=True, blank=True, verbose_name='헌법')
    subject_2 = models.IntegerField(null=True, blank=True, verbose_name='경찰학')
    subject_3 = models.IntegerField(null=True, blank=True, verbose_name='범죄학')
    subject_4 = models.IntegerField(null=True, blank=True, verbose_name='민법총칙')
    subject_5 = models.IntegerField(null=True, blank=True, verbose_name='행정법')
    subject_6 = models.IntegerField(null=True, blank=True, verbose_name='행정학')
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
