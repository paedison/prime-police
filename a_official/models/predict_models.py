from django.db import models
from django.urls import reverse_lazy
from django.utils import timezone

from a_official.models import abstract_models, Exam, Problem
from a_official.models.queryset import predict_queryset as queryset
from a_common.models import User

verbose_name_prefix = '[합격예측] '


class PredictExam(models.Model):
    exam = models.OneToOneField(Exam, on_delete=models.CASCADE, related_name='predict_exam')
    is_active = models.BooleanField(default=False, verbose_name='활성')
    page_opened_at = models.DateTimeField(default=timezone.now, verbose_name='페이지 오픈 일시')
    exam_started_at = models.DateTimeField(default=timezone.now, verbose_name='시험 시작 일시')
    exam_finished_at = models.DateTimeField(default=timezone.now, verbose_name='시험 종료 일시')
    answer_predict_opened_at = models.DateTimeField(default=timezone.now, verbose_name='예상 정답 공개 일시')
    answer_official_opened_at = models.DateTimeField(default=timezone.now, verbose_name='공식 정답 공개 일시')
    predict_closed_at = models.DateTimeField(default=timezone.now, verbose_name='합격 에측 종료 일시')

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}00_LEET'
        db_table = 'a_official_predict_exam'
        ordering = ['-id']

    def __str__(self):
        return self.reference

    @property
    def year(self):
        return self.exam.year

    @property
    def reference(self):
        return f'{self.exam.year}{self.exam.exam}'

    def is_not_page_opened(self):
        return timezone.now() <= self.page_opened_at

    def is_not_started(self):
        return self.page_opened_at < timezone.now() <= self.exam_started_at

    def is_started(self):
        return self.exam_started_at < timezone.now()

    def is_going_on(self):
        return self.exam_started_at < timezone.now() <= self.exam_finished_at

    def is_not_finished(self):
        return timezone.now() <= self.exam_finished_at

    def is_collecting_answer(self):
        return self.exam_finished_at < timezone.now() <= self.answer_predict_opened_at

    def is_answer_predict_opened(self):
        return self.answer_predict_opened_at < timezone.now() <= self.answer_official_opened_at

    def is_answer_official_opened(self):
        return self.answer_official_opened_at <= timezone.now()

    def is_predict_closed(self):
        return self.predict_closed_at <= timezone.now()


class PredictStatistics(abstract_models.Statistics):
    objects = queryset.PredictStatisticsQuerySet.as_manager()
    exam = models.OneToOneField(Exam, on_delete=models.CASCADE, related_name='predict_statistics', verbose_name='시험')

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}01_시험통계'
        db_table = 'a_official_predict_statistics'

    def __str__(self):
        return f'{self.exam.reference} 통계'


class PredictStudent(abstract_models.Student):
    objects = queryset.PredictStudentQuerySet.as_manager()
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='predict_students', verbose_name='시험')
    user = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='official_predict_students'
    )
    answer_count = {'형사': 0, '헌법': 0, '경찰': 0, '범죄': 0, '민법': 0, '행법': 0, '행학': 0}

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}02_수험정보'
        db_table = 'a_official_predict_student'
        constraints = [models.UniqueConstraint(fields=['exam', 'serial'], name='unique_official_predict_student')]

    def __str__(self):
        return self.student_info

    @property
    def student_info(self):
        return f'{self.exam.reference}-{self.serial}-{self.name}'

    def get_admin_detail_student_url(self):
        return reverse_lazy('official:admin-detail-student', args=['predict', self.id])


class PredictAnswer(abstract_models.Answer):
    objects = queryset.PredictAnswerQuerySet.as_manager()
    student = models.ForeignKey(PredictStudent, on_delete=models.CASCADE, related_name='answers')
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE, related_name='predict_answers')

    answer_student = answer_correct = None

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}03_답안'
        db_table = 'a_official_predict_answer'
        constraints = [
            models.UniqueConstraint(fields=['student', 'problem'], name='unique_official_predict_answer')
        ]

    def __str__(self):
        return f'{self.student.student_info}-{self.problem.reference}'


class PredictAnswerCount(abstract_models.AnswerCount):
    objects = queryset.PredictAnswerCountQuerySet.as_manager()
    problem = models.OneToOneField(Problem, on_delete=models.CASCADE, related_name='predict_answer_count')

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}04_답안 개수'
        db_table = 'a_official_predict_answer_count'

    def __str__(self):
        return self.problem.reference


class PredictScore(abstract_models.Score):
    objects = queryset.PredictScoreQuerySet.as_manager()
    student = models.OneToOneField(PredictStudent, on_delete=models.CASCADE, related_name='score')

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}05_점수'
        db_table = 'a_official_predict_score'

    def __str__(self):
        return self.student.student_info


class PredictRank(abstract_models.Rank):
    student = models.OneToOneField(PredictStudent, on_delete=models.CASCADE, related_name='rank')

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}06_등수(전체)'
        db_table = 'a_official_predict_rank'

    def __str__(self):
        return self.student.student_info


class PredictAnswerCountTopRank(abstract_models.AnswerCount):
    problem = models.OneToOneField(Problem, on_delete=models.CASCADE, related_name='predict_answer_count_top_rank')

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}09_답안 개수(상위권)'
        db_table = 'a_official_predict_answer_count_top_rank'

    def __str__(self):
        return self.problem.reference


class PredictAnswerCountMidRank(abstract_models.AnswerCount):
    problem = models.OneToOneField(Problem, on_delete=models.CASCADE, related_name='predict_answer_count_mid_rank')

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}10_답안 개수(중위권)'
        db_table = 'a_official_predict_answer_count_mid_rank'

    def __str__(self):
        return self.problem.reference


class PredictAnswerCountLowRank(abstract_models.AnswerCount):
    problem = models.OneToOneField(Problem, on_delete=models.CASCADE, related_name='predict_answer_count_low_rank')

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}11_답안 개수(하위권)'
        db_table = 'a_official_predict_answer_count_low_rank'

    def __str__(self):
        return self.problem.reference
