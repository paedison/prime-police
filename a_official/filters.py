from datetime import datetime

import django_filters

from .models import (
    year_choices, subject_choices,
    Problem,
)

current_year = datetime.now().year

CHOICES_LIKE = (
    ('true', '즐겨찾기 추가'),
    ('none', '즐겨찾기 미추가'),
)
CHOICES_RATE = (
    ('all', '난이도 지정'),
    ('5', '★★★★★'),
    ('4', '★★★★☆'),
    ('3', '★★★☆☆'),
    ('2', '★★☆☆☆'),
    ('1', '★☆☆☆☆'),
    ('none', '난이도 미지정'),
)
CHOICES_SOLVE = (
    ('all', '정답 확인'),
    ('true', '맞힌 문제'),
    ('false', '틀린 문제'),
    ('none', '정답 미확인'),
)
CHOICES_MEMO = (
    ('true', '메모 작성'),
    ('none', '메모 미작성'),
)
CHOICES_TAG = (
    ('true', '태그 작성'),
    ('none', '태그 미작성'),
)
CHOICES_COMMENT = (
    ('true', '코멘트 작성'),
    ('none', '코멘트 미작성'),
)


class AnonymousOfficialListFilter(django_filters.FilterSet):
    year = django_filters.ChoiceFilter(
        field_name='year',
        label='',
        empty_label='[전체 연도]',
        choices=year_choices,
    )
    subject = django_filters.ChoiceFilter(
        field_name='subject',
        label='',
        empty_label='[전체 과목]',
        choices=subject_choices,
    )

    class Meta:
        model = Problem
        fields = ['year', 'subject']

    @property
    def qs(self):
        keyword = self.request.GET.get('keyword', '') or self.request.POST.get('keyword', '')
        queryset = super().qs.prefetch_related(
            'like_users', 'rate_users', 'solve_users', 'memo_users', 'comment_users',
            'problem_like_set', 'problem_rate_set', 'problem_solve_set',
            'problem_memo_set', 'problem_comment_set',
            'problem_tagged_items', 'problem_collected_items',
        )
        if keyword:
            return queryset.filter(data__icontains=keyword)
        return queryset


class OfficialListFilter(AnonymousOfficialListFilter):
    likes = django_filters.ChoiceFilter(
        label='',
        empty_label='[즐겨찾기]',
        choices=CHOICES_LIKE,
        method='filter_likes',
    )
    rates = django_filters.ChoiceFilter(
        label='',
        empty_label='[난이도]',
        choices=CHOICES_RATE,
        method='filter_rates',
    )
    solves = django_filters.ChoiceFilter(
        label='',
        empty_label='[정답]',
        choices=CHOICES_SOLVE,
        method='filter_solves',
    )
    memos = django_filters.ChoiceFilter(
        label='',
        empty_label='[메모]',
        choices=CHOICES_MEMO,
        method='filter_memos',
    )
    tags = django_filters.ChoiceFilter(
        label='',
        empty_label='[태그]',
        choices=CHOICES_TAG,
        method='filter_tags',
    )
    comments = django_filters.ChoiceFilter(
        label='',
        empty_label='[코멘트]',
        choices=CHOICES_COMMENT,
        method='filter_comments',
    )

    class Meta:
        model = Problem
        fields = ['year', 'subject', 'likes', 'rates', 'solves', 'memos', 'comments', 'tags']

    def filter_likes(self, queryset, name, value):
        filter_dict = {
            'true': queryset.filter(like_users=self.request.user),
            'none': queryset.exclude(like_users=self.request.user),
        }
        return filter_dict[value]

    def filter_rates(self, queryset, name, value):
        filter_dict = {
            'all': queryset.filter(problemrate__isnull=False, rate_users=self.request.user),
            '1': queryset.filter(problemrate__rating=1, rate_users=self.request.user),
            '2': queryset.filter(problemrate__rating=2, rate_users=self.request.user),
            '3': queryset.filter(problemrate__rating=3, rate_users=self.request.user),
            '4': queryset.filter(problemrate__rating=4, rate_users=self.request.user),
            '5': queryset.filter(problemrate__rating=5, rate_users=self.request.user),
            'none': queryset.exclude(rate_users=self.request.user),
        }
        return filter_dict[value]

    def filter_solves(self, queryset, name, value):
        filter_dict = {
            'all': queryset.filter(problemsolve__isnull=False, solve_users=self.request.user),
            'true': queryset.filter(problemsolve__is_correct=True, solve_users=self.request.user),
            'false': queryset.filter(problemsolve__is_correct=False, solve_users=self.request.user),
            'none': queryset.exclude(solve_users=self.request.user),
        }
        return filter_dict[value]

    def filter_memos(self, queryset, name, value):
        filter_dict = {
            'true': queryset.filter(memo_users=self.request.user),
            'none': queryset.exclude(memo_users=self.request.user),
        }
        return filter_dict[value]

    def filter_tags(self, queryset, name, value):
        filter_dict = {
            'true': queryset.filter(tag_users=self.request.user),
            'none': queryset.exclude(tag_users=self.request.user),
        }
        return filter_dict[value]

    def filter_comments(self, queryset, name, value):
        filter_dict = {
            'true': queryset.filter(comment_users__isnull=False),
            'none': queryset.exclude(comment_users__isnull=True),
        }
        return filter_dict[value]


class AnonymousOfficialDetailFilter(django_filters.FilterSet):
    problem = django_filters.ChoiceFilter(
        field_name='problem',
        label='',
        choices=year_choices,
    )

    class Meta:
        model = Problem
        fields = ['problem']

    @property
    def qs(self):
        year = self.request.GET.get('year', '')
        sub = self.request.GET.get('sub', '')
        queryset = super().qs.filter(year=year, subject=sub)
        return queryset
