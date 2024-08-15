from django.core.paginator import Paginator

from a_common.models import User
from . import models


def get_page_obj_and_range(page_number, page_data, per_page=10):
    paginator = Paginator(page_data, per_page)
    page_obj = paginator.page(page_number)
    page_range = paginator.get_elided_page_range(number=page_number, on_each_side=3, on_ends=1)
    return page_obj, page_range


def get_sub_title(exam_circle, exam_round, exam_subject, end_string='데일리테스트') -> str:
    title_parts = []
    if exam_circle:
        title_parts.append(f'{exam_circle}순환')

    if exam_round:
        title_parts.append(f'{exam_round}회차')

    if exam_subject:
        title_parts.append(models.subject_choice()[exam_subject])

    if not exam_circle and not exam_round and not exam_subject:
        title_parts.append('전체')
    sub_title = f'{" ".join(title_parts)} {end_string}'
    return sub_title


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


def get_list_data(custom_data) -> list:
    organized_dict = {}
    organized_list = []
    for prob in custom_data:
        key = f'{prob.year}{prob.subject}'
        if key not in organized_dict:
            organized_dict[key] = []
        organized_dict[key].append(prob)

    for key, items in organized_dict.items():
        num_empty_instances = 5 - (len(items) % 5)
        if num_empty_instances < 5:
            items.extend([None] * num_empty_instances)
        for i in range(0, len(items), 5):
            row = items[i:i+5]
            organized_list.extend(row)
    return organized_list


def get_custom_data(user: User) -> dict:
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


def get_all_comments(queryset, problem_id=None):
    if problem_id:
        queryset = queryset.filter(problem_id=problem_id)
    parent_comments = queryset.filter(parent__isnull=True).order_by('-created_at')
    child_comments = queryset.exclude(parent__isnull=True).order_by('parent_id', '-created_at')
    all_comments = []
    for comment in parent_comments:
        all_comments.append(comment)
        all_comments.extend(child_comments.filter(parent=comment))
    return all_comments
