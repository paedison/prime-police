from django.db import models

from . import managers
from a_common.models import User
from a_infinite.models import abstract_models, Exam, Problem

verbose_name_prefix = '[성적결과] '


class Statistics(abstract_models.Statistics):
    objects = managers.StudentManager()
    exam = models.OneToOneField(Exam, on_delete=models.CASCADE, related_name='statistics', verbose_name='시험')

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}00_시험통계'

    def __str__(self):
        return f'{self.exam.reference} 통계'


class Student(abstract_models.Student):
    objects = managers.StudentManager()
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='students', verbose_name='시험')
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='infinite_students', verbose_name='사용자')
    answer_count = {'subject_0': 0, 'subject_1': 0, 'subject_2': 0, 'subject_3': 0, 'subject_4': 0}

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}01_수험정보'
        constraints = [models.UniqueConstraint(fields=['exam', 'user'], name='unique_infinite_student')]

    def __str__(self):
        return f'{self.exam.reference}-{self.user.name}'


class Answer(abstract_models.Answer):
    objects = managers.AnswerManager()
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='answers', verbose_name='학생')
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE, related_name='answers', verbose_name='문제')

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}02_답안'
        constraints = [models.UniqueConstraint(fields=['student', 'problem'], name='unique_infinite_answer')]

    def __str__(self):
        return f'{self.student}-{self.problem.reference}'


class AnswerCount(abstract_models.AnswerCount):
    objects = managers.AnswerCountManager()
    problem = models.OneToOneField(
        Problem, on_delete=models.CASCADE, related_name='answer_count', verbose_name='문제')

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}03_답안 개수'
        db_table = 'a_infinite_answer_count'

    def __str__(self):
        return self.problem.reference


class Score(abstract_models.Score):
    objects = managers.ScoreManager()
    student = models.OneToOneField(Student, on_delete=models.CASCADE, related_name='score', verbose_name='학생')

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}04_점수'

    def __str__(self):
        return self.student


class Rank(abstract_models.Rank):
    objects = managers.RankManager()
    student = models.OneToOneField(Student, on_delete=models.CASCADE, related_name='rank', verbose_name='학생')

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}05_등수'

    def __str__(self):
        return self.student


class AnswerCountTopRank(abstract_models.AnswerCount):
    problem = models.OneToOneField(Problem, on_delete=models.CASCADE, related_name='answer_count_top_rank')

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}06_답안 개수(상위권)'
        db_table = 'a_infinite_answer_count_top_rank'


class AnswerCountMidRank(abstract_models.AnswerCount):
    problem = models.OneToOneField(Problem, on_delete=models.CASCADE, related_name='answer_count_mid_rank')

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}07_답안 개수(중위권)'
        db_table = 'a_infinite_answer_count_mid_rank'


class AnswerCountLowRank(abstract_models.AnswerCount):
    problem = models.OneToOneField(Problem, on_delete=models.CASCADE, related_name='answer_count_low_rank')

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}08_답안 개수(하위권)'
        db_table = 'a_infinite_answer_count_low_rank'
