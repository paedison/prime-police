from django.db import models
from django.urls import reverse_lazy

from a_common.models import User
from a_mock.models import queryset, abstract_models, Exam, Problem

verbose_name_prefix = '[모의고사] '


class Statistics(abstract_models.Statistics):
    objects = queryset.StatisticsQuerySet().as_manager()
    exam = models.OneToOneField(Exam, on_delete=models.CASCADE, related_name='statistics', verbose_name='시험')

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}00_시험통계'
        constraints = [models.UniqueConstraint(fields=['exam'], name='unique_mock_statistics')]

    def __str__(self):
        return f'{self.exam.reference} 통계'


class Student(abstract_models.Student):
    objects = queryset.StudentQuerySet().as_manager()
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='students', verbose_name='시험')
    answer_count = {'subject_0': 0, 'subject_1': 0, 'subject_2': 0, 'subject_3': 0, 'subject_4': 0}

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}01_수험정보'
        constraints = [models.UniqueConstraint(fields=['exam', 'serial'], name='unique_mock_student')]

    def __str__(self):
        return f'{self.exam.reference}-{self.serial}({self.name})'

    def get_staff_detail_student_url(self):
        return reverse_lazy('mock:staff-detail-student', args=[self.id])

    def get_staff_detail_student_print_url(self):
        return reverse_lazy('mock:staff-detail-student-print', args=[self.id])


class Answer(abstract_models.Answer):
    objects = queryset.AnswerQuerySet().as_manager()
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='answers', verbose_name='학생')
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE, related_name='answers', verbose_name='문제')

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}03_답안'
        constraints = [models.UniqueConstraint(fields=['student', 'problem'], name='unique_mock_answer')]

    def __str__(self):
        return f'{self.student.student_info}-{self.problem.reference}'


class AnswerCount(abstract_models.AnswerCount):
    objects = queryset.AnswerCountQuerySet().as_manager()
    problem = models.OneToOneField(Problem, on_delete=models.CASCADE, related_name='answer_count', verbose_name='문제')

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}04_답안 개수'
        db_table = 'a_mock_answer_count'

    def __str__(self):
        return self.problem.reference


class Score(abstract_models.Score):
    objects = queryset.ScoreQuerySet().as_manager()
    student = models.OneToOneField(Student, on_delete=models.CASCADE, related_name='score', verbose_name='학생')

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}05_점수'

    def __str__(self):
        return f'{self.student.exam.reference}-{self.student.name}'


class Rank(abstract_models.Rank):
    objects = queryset.RankQuerySet().as_manager()
    student = models.OneToOneField(Student, on_delete=models.CASCADE, related_name='rank', verbose_name='학생')

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}06_등수'

    def __str__(self):
        return f'{self.student.exam.reference}-{self.student.name}'


class AnswerCountTopRank(abstract_models.AnswerCount):
    problem = models.OneToOneField(Problem, on_delete=models.CASCADE, related_name='answer_count_top_rank')

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}07_답안 개수(상위권)'
        db_table = 'a_mock_answer_count_top_rank'


class AnswerCountMidRank(abstract_models.AnswerCount):
    problem = models.OneToOneField(Problem, on_delete=models.CASCADE, related_name='answer_count_mid_rank')

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}08_답안 개수(중위권)'
        db_table = 'a_mock_answer_count_mid_rank'


class AnswerCountLowRank(abstract_models.AnswerCount):
    problem = models.OneToOneField(Problem, on_delete=models.CASCADE, related_name='answer_count_low_rank')

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}09_답안 개수(하위권)'
        db_table = 'a_mock_answer_count_low_rank'
