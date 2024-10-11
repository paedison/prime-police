import django_filters
from django.apps import apps
from django.utils import timezone

from a_common.prime_test.model_settings import *

CHOICES_LIKE = [
    ('all', '즐겨찾기 지정'), ('true', '즐겨찾기 추가'),
    ('false', '즐겨찾기 제거'), ('none', '즐겨찾기 미지정'),
]
CHOICES_RATE = [
    ('all', '난이도 지정'), ('5', '★★★★★'), ('4', '★★★★☆'), ('3', '★★★☆☆'),
    ('2', '★★☆☆☆'), ('1', '★☆☆☆☆'), ('none', '난이도 미지정'),
]
CHOICES_SOLVE = [
    ('all', '정답 확인'), ('true', '맞힌 문제'),
    ('false', '틀린 문제'), ('none', '정답 미확인'),
]
CHOICES_MEMO = [('true', '메모 작성'), ('none', '메모 미작성')]
CHOICES_TAG = [('true', '태그 작성'), ('none', '태그 미작성')]


class AnonymousProblemFilter(django_filters.FilterSet):
    circle = django_filters.ChoiceFilter(
        field_name='circle', label='', empty_label='[전체 순환]', choices=circle_choice)
    subject = django_filters.ChoiceFilter(
        field_name='subject', label='', empty_label='[전체 과목]', choices=subject_choice)
    round = django_filters.ChoiceFilter(
        field_name='round', label='', empty_label='[전체 회차]', choices=round_choice)

    class Meta:
        fields = ['circle', 'subject', 'round']

    @property
    def qs(self):
        keyword = self.request.GET.get('keyword', '') or self.request.POST.get('keyword', '')
        queryset = super().qs.filter(
            semester=semester_default(), opened_at__lte=timezone.now()
        ).prefetch_related(
            'like_users', 'rate_users', 'solve_users', 'memo_users',
            'likes', 'rates', 'solves', 'memos', 'tagged_problems', 'collected_problems')
        if keyword:
            return queryset.filter(data__icontains=keyword)
        return queryset


class ProblemFilter(AnonymousProblemFilter):
    app_name = ''

    likes = django_filters.ChoiceFilter(
        label='', empty_label='[즐겨찾기]', choices=CHOICES_LIKE, method='filter_likes')
    rates = django_filters.ChoiceFilter(
        label='', empty_label='[난이도]', choices=CHOICES_RATE, method='filter_rates')
    solves = django_filters.ChoiceFilter(
        label='', empty_label='[정답]',  choices=CHOICES_SOLVE, method='filter_solves')
    memos = django_filters.ChoiceFilter(
        label='', empty_label='[메모]', choices=CHOICES_MEMO, method='filter_memos')
    tags = django_filters.ChoiceFilter(
        label='', empty_label='[태그]', choices=CHOICES_TAG, method='filter_tags')

    class Meta:
        fields = ['circle', 'subject', 'round', 'likes', 'rates', 'solves', 'memos', 'tags']

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
        students = self.models['Student'].objects.filter(user=self.request.user)
        ids = []

        if students:
            for student in students:
                filtered_qs = self.models['Problem'].objects.filter(
                    semester=student.semester, circle=student.circle,
                    subject=student.subject, round=student.round)

                if student.answer_confirmed:
                    answer_student = student.answer_student
                    answer_official = filtered_qs.order_by('number').values_list('answer', flat=True)
                    result = [answer_student[i] == answer_official[i] for i in range(len(answer_student))]
                    true_nums = [no for no, res in enumerate(result, start=1) if res]
                    false_nums = [no for no, res in enumerate(result, start=1) if not res]

                    if value == 'all':
                        ids.extend(filtered_qs.values_list('id', flat=True))
                    elif value == 'true':
                        ids.extend(filtered_qs.filter(number__in=true_nums).values_list('id', flat=True))
                    elif value == 'false':
                        ids.extend(filtered_qs.filter(number__in=false_nums).values_list('id', flat=True))
                else:
                    if value == 'none':
                        ids.extend(filtered_qs.values_list('id', flat=True))
        else:
            if value == 'none':
                ids.extend(queryset.values_list('id', flat=True))

        return queryset.filter(id__in=ids)

    def filter_memos(self, queryset, _, value):
        filter_dict = {
            'true': queryset.filter(memo_users=self.request.user),
            'none': queryset.exclude(memo_users=self.request.user),
        }
        return filter_dict[value]

    def filter_tags(self, queryset, _, value):
        id_list = self.models['ProblemTaggedItem'].objects.filter(
            user=self.request.user, active=True).values_list('content_object_id', flat=True)
        filter_dict = {
            'true': queryset.filter(id__in=id_list),
            'none': queryset.exclude(id__in=id_list),
        }
        return filter_dict[value]

    @property
    def models(self):
        try:
            app_config = apps.get_app_config(self.app_name)
            models = app_config.get_models()
            return {model.__name__: model for model in models}
        except Exception as e:
            print(e)
            return None


class ExamFilter(django_filters.FilterSet):
    circle = django_filters.ChoiceFilter(
        field_name='circle', label='', empty_label='[전체 순환]', choices=circle_choice)
    subject = django_filters.ChoiceFilter(
        field_name='subject', label='', empty_label='[전체 과목]', choices=subject_choice)
    round = django_filters.ChoiceFilter(
        field_name='round', label='', empty_label='[전체 회차]', choices=round_choice)

    class Meta:
        fields = ['circle', 'subject', 'round']

    @property
    def qs(self):
        return super().qs.filter(
            semester=semester_default(), opened_at__lte=timezone.now()).order_by('-id')
