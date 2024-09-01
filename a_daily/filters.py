from a_common.prime_test import filters as prime_filters
from . import models


class AnonymousProblemFilter(prime_filters.AnonymousProblemFilter):
    class Meta:
        model = models.Problem
        fields = ['circle', 'subject', 'round']


class ProblemFilter(prime_filters.ProblemFilter):
    app_name = 'a_daily'

    class Meta:
        model = models.Problem
        fields = ['circle', 'subject', 'round', 'likes', 'rates', 'solves', 'memos', 'tags']


class ExamFilter(prime_filters.ExamFilter):
    class Meta:
        model = models.Exam
        fields = ['circle', 'subject', 'round']
