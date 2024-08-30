from django.core.paginator import Paginator

from . import models


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
        title_parts.append(models.subject_choice()[exam_subject])
    if exam_round:
        title_parts.append(f'{exam_round}회차')
    if not exam_circle and not exam_round and not exam_subject:
        title_parts.append('전체')
    sub_title = f'{" ".join(title_parts)} {end_string}'
    return sub_title
