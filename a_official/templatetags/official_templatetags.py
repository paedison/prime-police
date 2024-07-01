from django.contrib.auth.models import User
from django.template import Library

from a_common import utils as common_utils
from a_common.constants import icon_set
from a_official.models import (
    Problem, ProblemLike, ProblemTag, ProblemTaggedItem,
)

register = Library()


@register.inclusion_tag('a_official/templatetags/icons.html')
def icons(user: User, problem: Problem):
    problem_likes = ProblemLike.objects.filter(
        problem=problem, is_liked=True
    )
    like_exists = False
    if user.is_authenticated:
        like_exists = problem_likes.filter(user=user).exists()
    icon_like = icon_set.ICON_LIKE[f'{like_exists}']
    like_counts = problem_likes.count()

    rating = 0
    if user in problem.rate_users.all():
        rating = problem.problem_rate_set.filter(user=user).first().rating
    icon_rate = icon_set.ICON_RATE[f'star{rating}']

    is_correct = None
    if user in problem.solve_users.all():
        is_correct = problem.problem_solve_set.filter(user=user).first().is_correct
    icon_solve = icon_set.ICON_SOLVE[f'{is_correct}']

    is_memoed = False
    if user in problem.memo_users.all():
        is_memoed = problem.problem_memo_set.filter(user=user).first().is_correct
    icon_memo = icon_set.ICON_MEMO[f'{is_memoed}']

    context = common_utils.update_context_data(
        user=user,
        problem=problem,
        icon_like=icon_like,
        like_counts=like_counts,
        icon_rate=icon_rate,
        icon_solve=icon_solve,
        icon_memo=icon_memo,
    )
    return context


@register.inclusion_tag('a_official/templatetags/tags.html')
def tag(user: User, problem: Problem):
    tags = ProblemTaggedItem.objects.filter(
        user=user, content_object=problem, is_tagged=True).values_list('tag__name', flat=True)
    return {
        'user': user,
        'problem': problem,
        'tags': tags,
    }


@register.filter
def subtract(value, arg) -> int:  # Subtract arg from value
    return arg - int(value)
