from django.core.paginator import Paginator
from django.http import HttpRequest
from django_htmx.middleware import HtmxDetails

from .constants import icon_set
from .prime_test.model_settings import subject_choice, semester_default


class HtmxHttpRequest(HttpRequest):
    htmx: HtmxDetails


def update_context_data(context: dict = None, **kwargs):
    if context:
        context.update(kwargs)
        return context
    return kwargs


def detect_encoding(file_path):
    with open(file_path, 'rb') as f:
        first_bytes = f.read(3)
    return 'utf-8-sig' if first_bytes == b'\xef\xbb\xbf' else 'utf-8'


def get_page_obj_and_range(page_number, page_data, per_page=10):
    paginator = Paginator(page_data, per_page)
    page_obj = paginator.page(page_number)
    page_range = paginator.get_elided_page_range(number=page_number, on_each_side=3, on_ends=1)
    return page_obj, page_range


def get_sub_title(exam_circle, exam_round, exam_subject, end_string='문제') -> str:
    title_parts = []
    if exam_circle:
        title_parts.append(f'{exam_circle}순환')
    if exam_subject:
        title_parts.append(subject_choice()[exam_subject])
    if exam_round:
        title_parts.append(f'{exam_round}회차')
    if not exam_circle and not exam_round and not exam_subject:
        title_parts.append('전체')
    return f'{" ".join(title_parts)} {end_string}'


def get_prev_next_prob(pk, custom_data) -> tuple:
    custom_list = list(custom_data.values_list('id', flat=True))
    prev_prob = next_prob = None
    if custom_list:
        last_id = len(custom_list) - 1
        q = custom_list.index(pk)
        if q != 0:
            prev_prob = custom_data[q - 1]
        if q != last_id:
            next_prob = custom_data[q + 1]
    return prev_prob, next_prob


def get_list_data(queryset, student) -> list:
    list_data = []
    for data in queryset:
        if student and student.answer_student:
            data.is_correct = data.answer == student.answer_student[data.number - 1]
        list_data.append(data)
    return list_data


def get_custom_data(user, models) -> dict:
    if user.is_authenticated:
        return {
            'like': models.ProblemLike.objects.filter(user=user).select_related('user', 'problem'),
            'rate': models.ProblemRate.objects.filter(user=user).select_related('user', 'problem'),
            'solve': models.ProblemSolve.objects.filter(user=user).select_related('user', 'problem'),
            'memo': models.ProblemMemo.objects.filter(user=user).select_related('user', 'problem'),
            'tag': models.ProblemTaggedItem.objects.filter(
                user=user, active=True).select_related('user', 'content_object'),
            'collection': models.ProblemCollectionItem.objects.filter(
                collection__user=user).select_related('collection__user', 'problem'),
        }
    return {'like': [], 'rate': [], 'solve': [], 'memo': [], 'tag': [], 'collection': []}


def get_custom_icons(user, models, problem, custom_data: dict):
    def get_status(status_type, field=None, default: bool | int | None = False):
        for dt in custom_data[status_type]:
            problem_id = getattr(dt, 'problem_id', getattr(dt, 'content_object_id', ''))
            if problem_id == problem.id:
                default = getattr(dt, field) if field else True
        return default

    is_liked = get_status(status_type='like', field='is_liked')
    rating = get_status(status_type='rate', field='rating', default=0)
    is_memoed = get_status('memo')
    is_tagged = get_status('tag')
    is_collected = get_status('collection')

    is_correct = None
    student: models.Student | None = models.Student.objects.filter(
        user=user, semester=problem.semester, circle=problem.circle,
        subject=problem.subject, round=problem.round).first()
    if student and student.answer_confirmed:
        is_correct = problem.answer == student.answer_student[problem.number - 1]

    problem.icon_like=icon_set.ICON_LIKE[f'{is_liked}']
    problem.icon_rate=icon_set.ICON_RATE[f'star{rating}']
    problem.icon_solve=icon_set.ICON_SOLVE[f'{is_correct}']
    problem.icon_memo=icon_set.ICON_MEMO[f'{is_memoed}']
    problem.icon_tag=icon_set.ICON_TAG[f'{is_tagged}']
    problem.icon_collection=icon_set.ICON_COLLECTION[f'{is_collected}']


def get_exam_info(instance):
    return {
        'semester': semester_default(), 'circle': instance.circle,
        'subject': instance.subject, 'round': instance.round
    }


def get_student(request: HtmxHttpRequest, models, exam_info: dict):
    return models.Student.objects.filter(user=request.user, **exam_info).first()


def get_statistics(score_list: list, score: float) -> dict:
    participants = len(score_list)
    sorted_scores = sorted(score_list, reverse=True)
    try:
        rank = sorted_scores.index(score) + 1
        max_score = round(sorted_scores[0], 1)
        top_10_threshold = max(1, int(participants * 0.1))
        top_20_threshold = max(1, int(participants * 0.2))
        top_score_10 = round(sorted_scores[top_10_threshold - 1], 1)
        top_score_20 = round(sorted_scores[top_20_threshold - 1], 1)
        avg_score = round(sum(score_list) / participants if participants else 0, 1)
    except ValueError:
        rank = max_score = top_score_10 = top_score_20 = avg_score = None
    return {
        'participants': participants, 'rank': rank,
        'max': max_score, 't10': top_score_10, 't20': top_score_20, 'avg': avg_score,
    }
