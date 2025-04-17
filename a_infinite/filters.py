import django_filters
from django.utils import timezone

from a_common.prime_test import filters as prime_filters
from a_common.prime_test.model_settings import *
from . import models


class AnonymousProblemFilter(django_filters.FilterSet):
    round = django_filters.ChoiceFilter(
        field_name='round', label='', empty_label='[전체 회차]', choices=round_choice)
    subject = django_filters.ChoiceFilter(
        field_name='subject', label='', empty_label='[전체 과목]', choices=infinite_subject_choice)

    class Meta:
        model = models.Problem
        fields = ['round', 'subject']

    @property
    def qs(self):
        keyword = self.request.GET.get('keyword', '') or self.request.POST.get('keyword', '')
        queryset = super().qs.filter(
            semester=semester_default(), exam__opened_at__lte=timezone.now()
        ).prefetch_related(
            'like_users', 'rate_users', 'solve_users', 'memo_users',
            'likes', 'rates', 'solves', 'memos', 'tagged_problems', 'collected_problems')
        if keyword:
            return queryset.filter(data__icontains=keyword)
        return queryset


class ProblemFilter(prime_filters.ProblemFilter):
    app_name = 'a_infinite'
    circle = None
    round = None
    subject = django_filters.ChoiceFilter(
        field_name='subject', label='', empty_label='[전체 과목]', choices=infinite_subject_choice)

    class Meta:
        model = models.Problem
        fields = ['exam', 'subject', 'likes', 'rates', 'solves', 'memos', 'tags']

    @property
    def qs(self):
        keyword = self.request.GET.get('keyword', '') or self.request.POST.get('keyword', '')
        queryset = self.queryset.filter(
            exam__semester=semester_default(), exam__exam_finished_at__lte=timezone.now()
        ).prefetch_related(
            'like_users', 'rate_users', 'solve_users', 'memo_users',
            'likes', 'rates', 'solves', 'memos', 'tagged_problems', 'collected_problems')
        if keyword:
            return queryset.filter(data__icontains=keyword)
        return queryset


class ExamFilter(prime_filters.ExamFilter):
    class Meta:
        model = models.Exam
        fields = ['round']
