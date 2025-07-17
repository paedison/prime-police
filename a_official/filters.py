import django_filters

from . import models

CHOICES_LIKE = (
    ('all', '즐겨찾기 지정'),
    ('true', '즐겨찾기 추가'),
    ('false', '즐겨찾기 제거'),
    ('none', '즐겨찾기 미지정'),
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


class OfficialExamFilter(django_filters.FilterSet):
    year = django_filters.ChoiceFilter(
        field_name='year',
        label='',
        empty_label='[전체 연도]',
        choices=models.choices.year_choice,
    )
    is_active = django_filters.ChoiceFilter(
        field_name='is_active',
        label='',
        empty_label='[활성 상태]',
        choices={'True': '활성', 'False': '비활성'},
    )

    class Meta:
        model = models.Exam
        fields = ['year']

    @property
    def qs(self):
        return super().qs.select_related('predict_exam').prefetch_related('problems').order_by('-id')


class AnonymousOfficialProblemFilter(django_filters.FilterSet):
    year = django_filters.ChoiceFilter(
        field_name='year',
        label='',
        empty_label='[전체 연도]',
        choices=models.choices.year_choice,
    )
    subject = django_filters.ChoiceFilter(
        field_name='subject',
        label='',
        empty_label='[전체 과목]',
        choices=models.choices.subject_choice,
    )

    class Meta:
        model = models.Problem
        fields = ['year', 'subject']

    @property
    def qs(self):
        keyword = self.request.GET.get('keyword', '') or self.request.POST.get('keyword', '')
        queryset = super().qs.select_related('exam').prefetch_related(
            'like_users', 'rate_users', 'solve_users', 'memo_users',
            'likes', 'rates', 'solves', 'memos', 'tagged_problems', 'collected_problems',
        ).filter(exam__is_active=True)
        if keyword:
            return queryset.filter(data__icontains=keyword)
        return queryset


class OfficialProblemFilter(AnonymousOfficialProblemFilter):
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

    class Meta:
        model = models.Problem
        fields = ['year', 'subject', 'likes', 'rates', 'solves', 'memos', 'tags']

    def filter_likes(self, queryset, _, value):
        filter_dict = {
            'all': queryset.filter(like_users=self.request.user),
            'true': queryset.filter(likes__is_liked=True, like_users=self.request.user),
            'false': queryset.filter(likes__is_liked=False, like_users=self.request.user),
            'none': queryset.exclude(like_users=self.request.user),
        }
        return filter_dict[value]

    def filter_rates(self, queryset, _, value):
        filter_dict = {
            'all': queryset.filter(rates__isnull=False, rate_users=self.request.user),
            '1': queryset.filter(rates__rating=1, rate_users=self.request.user),
            '2': queryset.filter(rates__rating=2, rate_users=self.request.user),
            '3': queryset.filter(rates__rating=3, rate_users=self.request.user),
            '4': queryset.filter(rates__rating=4, rate_users=self.request.user),
            '5': queryset.filter(rates__rating=5, rate_users=self.request.user),
            'none': queryset.exclude(rate_users=self.request.user),
        }
        return filter_dict[value]

    def filter_solves(self, queryset, _, value):
        filter_dict = {
            'all': queryset.filter(solves__isnull=False, solve_users=self.request.user),
            'true': queryset.filter(solves__is_correct=True, solve_users=self.request.user),
            'false': queryset.filter(solves__is_correct=False, solve_users=self.request.user),
            'none': queryset.exclude(solve_users=self.request.user),
        }
        return filter_dict[value]

    def filter_memos(self, queryset, _, value):
        filter_dict = {
            'true': queryset.filter(memo_users=self.request.user),
            'none': queryset.exclude(memo_users=self.request.user),
        }
        return filter_dict[value]

    def filter_tags(self, queryset, _, value):
        id_list = models.ProblemTaggedItem.objects.filter(
            user=self.request.user, active=True).values_list('content_object_id', flat=True)
        filter_dict = {
            'true': queryset.filter(id__in=id_list),
            'none': queryset.exclude(id__in=id_list),
        }
        return filter_dict[value]
