from django.db import models

from a_common.models import User
from .base_settings import (
    get_current_year, year_choices, exam_choices, subject_choices, number_choices,
    TimeRecordField, TimeRemarkChoiceBase, TimeChoiceBase, unit_choices, department_choices,
)


class Student(TimeRemarkChoiceBase):
    year = models.IntegerField(choices=year_choices, default=get_current_year())
    exam = models.CharField(max_length=10, choices=exam_choices, default='프모')
    round = models.IntegerField(default=1)

    name = models.CharField(max_length=20)
    serial = models.CharField(max_length=10)
    unit = models.CharField(max_length=10, choices=unit_choices, default='경위')
    department = models.CharField(max_length=10, choices=department_choices, default='일반')

    password = models.CharField(max_length=10, null=True, blank=True)
    prime_id = models.CharField(max_length=15, null=True, blank=True)

    answer = models.JSONField(default=dict)
    answer_count = models.JSONField(default=dict)
    answer_confirmed = models.JSONField(default=dict)
    answer_all_confirmed_at = models.DateTimeField(null=True, blank=True)

    score = models.JSONField(default=dict)
    rank_total = models.JSONField(default=dict)
    rank_department = models.JSONField(default=dict)
    participants_total = models.JSONField(default=dict)
    participants_department = models.JSONField(default=dict)

    class Meta:
        verbose_name = "프라임모의고사 수험정보"
        verbose_name_plural = "프라임모의고사 수험정보"
        unique_together = ['year', 'exam', 'round', 'serial']

    def __str__(self):
        return f'[Police]PrimeStudent:{self.reference}({self.student_info})'

    @property
    def reference(self):
        return f'{self.year}{self.exam}{self.round}'

    @property
    def student_info(self):
        return f'{self.serial}-{self.name}'


class RegisteredStudent(TimeRecordField):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='prime_registered_students')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='registered_students')

    class Meta:
        verbose_name = "프라임모의고사 수험정보 연결"
        verbose_name_plural = "프라임모의고사 수험정보 연결"
        unique_together = ['user', 'student']
        db_table = 'a_prime_registered_student'

    def __str__(self):
        return f'[Police]PrimeRegisteredStudent:{self.student.reference}({self.student.student_info})'


class AnswerRecord(TimeRemarkChoiceBase):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='answer_records')
    subject = models.CharField(max_length=2, choices=subject_choices)
    number = models.IntegerField(choices=number_choices, default=1)
    answer = models.IntegerField(default=0)

    class Meta:
        verbose_name = "프라임모의고사 답안 제출"
        verbose_name_plural = "프라임모의고사 답안 제출"
        unique_together = ['student', 'subject', 'number']
        db_table = 'a_prime_answer_record'

    def __str__(self):
        return (f'[Police]PrimeAnswerRecord:{self.student.reference}-{self.subject}{self.number}'
                f'({self.student.student_info})')


class AnswerCount(TimeChoiceBase):
    year = models.IntegerField(choices=year_choices, default=get_current_year())
    exam = models.CharField(max_length=2, choices=exam_choices, default='경위')
    round = models.IntegerField(default=0)

    subject = models.CharField(max_length=2, choices=subject_choices)
    number = models.IntegerField()
    answer = models.IntegerField(null=True, blank=True)

    count_1 = models.IntegerField(default=0)
    count_2 = models.IntegerField(default=0)
    count_3 = models.IntegerField(default=0)
    count_4 = models.IntegerField(default=0)
    count_5 = models.IntegerField(default=0)
    count_0 = models.IntegerField(default=0)
    count_None = models.IntegerField(default=0)
    count_multiple = models.IntegerField(default=0)
    count_total = models.IntegerField(default=0)

    class Meta:
        verbose_name = "프라임모의고사 답안 개수"
        verbose_name_plural = "프라임모의고사 답안 개수"
        unique_together = ['year', 'exam', 'round', 'subject', 'number']
        db_table = 'a_prime_answer_count'

    def __str__(self):
        return f'[Police]PrimeAnswerCount:{self.reference}-{self.subject}{self.number}'

    @property
    def reference(self):
        return f'{self.year}{self.exam}{self.round}'

    # @property
    # def count_total(self):
    #     counts = [
    #         self.count_1, self.count_2, self.count_3, self.count_4, self.count_5,
    #         self.count_0, self.count_None,
    #     ]
    #     return sum(filter(None, counts))

    def get_rate(self, answer: int | None):
        if self.count_total != 0:
            return getattr(self, f'count_{answer}') / self.count_total * 100

    @property
    def rate_0(self): return self.get_rate(0)

    @property
    def rate_1(self): return self.get_rate(1)

    @property
    def rate_2(self): return self.get_rate(2)

    @property
    def rate_3(self): return self.get_rate(3)

    @property
    def rate_4(self): return self.get_rate(4)

    @property
    def rate_5(self): return self.get_rate(5)
