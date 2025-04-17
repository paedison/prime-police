from django.db import models

from a_common.prime_test.model_settings import *


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

    class Meta:
        abstract = True


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

    def save(self, *args, **kwargs):
        self.answer_predict = self.calculate_answer_predict()
        super().save(*args, **kwargs)

    def calculate_answer_predict(self):
        source = [self.count_1, self.count_2, self.count_3, self.count_4]
        return source.index(max(source)) + 1

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


class ExtendedAnswerCount(AnswerCount):
    filtered_count_1 = models.IntegerField(default=0, verbose_name='[필터링]①')
    filtered_count_2 = models.IntegerField(default=0, verbose_name='[필터링]②')
    filtered_count_3 = models.IntegerField(default=0, verbose_name='[필터링]③')
    filtered_count_4 = models.IntegerField(default=0, verbose_name='[필터링]④')
    filtered_count_0 = models.IntegerField(default=0, verbose_name='[필터링]미표기')
    filtered_count_multiple = models.IntegerField(default=0, verbose_name='[필터링]중복표기')
    filtered_count_sum = models.IntegerField(default=0, verbose_name='[필터링]총계')

    class Meta:
        abstract = True


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
        subject_tuple = infinite_subject_tuple()
        if sub in subject_tuple and self.participants:
            return getattr(self, f'subject_{subject_tuple.index(sub)}') / self.participants


class ExtendedRank(Rank):
    filtered_subject_0 = models.IntegerField(null=True, blank=True, verbose_name='[필터링]형사법')
    filtered_subject_1 = models.IntegerField(null=True, blank=True, verbose_name='[필터링]헌법')
    filtered_subject_2 = models.IntegerField(null=True, blank=True, verbose_name='[필터링]경찰학')
    filtered_subject_3 = models.IntegerField(null=True, blank=True, verbose_name='[필터링]범죄학')
    filtered_subject_4 = models.IntegerField(null=True, blank=True, verbose_name='[필터링]민법총칙')
    filtered_sum = models.IntegerField(null=True, blank=True, verbose_name='[필터링]총점')
    filtered_participants = models.IntegerField(null=True, blank=True, verbose_name='[필터링]총 인원')

    class Meta:
        abstract = True
