from django.contrib.auth.models import User
from django import template

from a_common.utils import update_context_data
from a_common.constants import icon_set
from .. import models

register = template.Library()


@register.inclusion_tag('a_daily/templatetags/icons.html')
def custom_icons(user: User, problem: models.Problem, custom_data: dict):
    def get_status(status_type, field=None, default: bool | int | None = False):
        for dt in custom_data[status_type]:
            problem_id = getattr(dt, 'problem_id', getattr(dt, 'content_object_id', ''))
            if problem_id == problem.id:
                default = getattr(dt, field) if field else True
        return default

    is_liked = get_status(status_type='like', field='is_liked')
    rating = get_status(status_type='rate', field='rating', default=0)
    is_correct = get_status(status_type='solve', field='is_correct', default=None)
    is_memoed = get_status('memo')
    is_tagged = get_status('tag')
    is_collected = get_status('collection')

    return update_context_data(
        user=user, problem=problem,
        icon_like=icon_set.ICON_LIKE[f'{is_liked}'],
        icon_rate=icon_set.ICON_RATE[f'star{rating}'],
        icon_solve=icon_set.ICON_SOLVE[f'{is_correct}'],
        icon_memo=icon_set.ICON_MEMO[f'{is_memoed}'],
        icon_tag=icon_set.ICON_TAG[f'{is_tagged}'],
        icon_collection=icon_set.ICON_COLLECTION[f'{is_collected}'],
    )


@register.inclusion_tag('a_daily/templatetags/tags.html')
def tag(user: User, problem: models.Problem, custom_data: dict):
    tags = []
    for dt in custom_data['tag']:
        if dt.content_object_id == problem.id:
            tags.append(dt.tag.name)
    return update_context_data(user=user, problem=problem, tags=tags)
