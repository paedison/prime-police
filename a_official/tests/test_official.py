import random

import pytest
from django.urls import reverse
from pytest_django.asserts import assertTemplateUsed

from a_common.constants import icon_set
from a_official.models import ProblemLike, ProblemRate, ProblemSolve, ProblemTag, ProblemTaggedItem

pytestmark = pytest.mark.django_db


@pytest.fixture
def sample_user(user_factory): return user_factory()


@pytest.fixture
def sample_problem(official_problem_factory): return official_problem_factory()


def parse_remarks_text_to_dict(remarks_text) -> list:
    items = remarks_text.split('|')
    result_list = []
    for item in items:
        key, value = item.split(':', 1)  # Split only on the first occurrence of ':'
        result_list.append({key: value})
    return result_list


def get_remarks_key_list(remarks) -> list:
    items = remarks.split('|')
    remarks_key_list = []
    for item in items:
        key, value = item.split(':', 1)  # Split only on the first occurrence of ':'
        remarks_key_list.append(key)
    return remarks_key_list


def test_like_and_unlike_problem(client, sample_user, sample_problem):
    client.force_login(sample_user)
    url = reverse('official:like-problem', kwargs={'pk': sample_problem.pk})

    problem_count = ProblemLike.objects.filter(problem=sample_problem, is_liked=True).count()
    assert problem_count == 0

    # Like problem
    response = client.post(url)
    assert response.status_code == 200

    problem_count = ProblemLike.objects.filter(problem=sample_problem, is_liked=True).count()
    assert problem_count == 1

    problem_like = ProblemLike.objects.get(problem=sample_problem, user=sample_user)
    assert problem_like.is_liked is True

    remarks_key = get_remarks_key_list(problem_like.remarks)[0]
    assert remarks_key == 'liked_at'

    icon_like = icon_set.ICON_LIKE[f'{problem_like.is_liked}']
    response_html = f'{icon_like} {problem_count}'
    assert response.content.decode('utf-8') == response_html

    # Unlike problem
    response = client.post(url)
    assert response.status_code == 200

    problem_count = ProblemLike.objects.filter(problem=sample_problem, is_liked=True).count()
    assert problem_count == 0

    problem_like.refresh_from_db()
    assert problem_like.is_liked is False

    icon_like = icon_set.ICON_LIKE[f'{problem_like.is_liked}']
    response_html = f'{icon_like} {problem_count}'
    assert response.content.decode('utf-8') == response_html

    remarks_key = get_remarks_key_list(problem_like.remarks)[1]
    assert remarks_key == 'unliked_at'


def test_rate_problem(client, sample_user, sample_problem):
    client.force_login(sample_user)
    url = reverse('official:rate-problem', kwargs={'pk': sample_problem.pk})
    rating = random.randint(1, 5)
    post_data = {'rating': f'{rating}'}

    # Load rate modal
    response = client.get(url)
    assert response.context['problem'] == sample_problem
    assertTemplateUsed(response, 'a_official/snippets/rate_modal.html')

    # First rate
    response = client.post(url, data=post_data)
    assert response.status_code == 200

    problem_rate = ProblemRate.objects.get(problem=sample_problem, user=sample_user)
    assert problem_rate.rating == rating

    remarks_key = get_remarks_key_list(problem_rate.remarks)[0]
    assert remarks_key == 'rated_at'

    icon_rate = icon_set.ICON_RATE[f'star{rating}']
    assert response.content.decode('utf-8') == icon_rate

    # Second rate
    response = client.post(url, data=post_data)
    assert response.status_code == 200

    problem_rate.refresh_from_db()
    assert problem_rate.rating == rating

    icon_rate = icon_set.ICON_RATE[f'star{rating}']
    assert response.content.decode('utf-8') == icon_rate

    remarks_key = get_remarks_key_list(problem_rate.remarks)[1]
    assert remarks_key == 'rated_at'


def test_solve_problem(client, sample_user, official_problem_factory):
    answer_correct = 1
    sample_problem = official_problem_factory(answer=answer_correct)
    client.force_login(sample_user)
    url = reverse('official:solve-problem', kwargs={'pk': sample_problem.pk})

    # Load solve modal
    response = client.get(url)
    assert response.context['problem'] == sample_problem
    assertTemplateUsed(response, 'a_official/snippets/solve_modal.html')

    # First solve
    answer = 1
    post_data = {'answer': f'{answer}'}
    response = client.post(url, data=post_data)
    assert response.status_code == 200

    problem_solve = ProblemSolve.objects.get(problem=sample_problem, user=sample_user)
    assert problem_solve.answer == answer
    assert problem_solve.is_correct is True

    icon_solve = icon_set.ICON_SOLVE[f'{problem_solve.is_correct}']
    assert response.context['icon_solve'] == icon_solve
    assertTemplateUsed(response, 'a_official/snippets/solve_result.html')

    remarks_key = get_remarks_key_list(problem_solve.remarks)[0]
    assert remarks_key == 'correct_at'

    # Second solve
    answer = 2
    post_data = {'answer': f'{answer}'}
    response = client.post(url, data=post_data)
    assert response.status_code == 200

    problem_solve.refresh_from_db()
    assert problem_solve.answer == answer
    assert problem_solve.is_correct is False

    icon_solve = icon_set.ICON_SOLVE[f'{problem_solve.is_correct}']
    assert response.context['icon_solve'] == icon_solve
    assertTemplateUsed(response, 'a_official/snippets/solve_result.html')

    remarks_key = get_remarks_key_list(problem_solve.remarks)[1]
    assert remarks_key == 'wrong_at'


def test_tag_problem_create_and_remove(client, sample_user, sample_problem):
    client.force_login(sample_user)
    url = reverse('official:tag-problem-create', kwargs={'pk': sample_problem.pk})

    # Tag create
    tag_name = 'test_tag'
    post_data = {'tag': f'{tag_name}'}
    response = client.post(url, data=post_data)
    assert response.status_code == 200

    tag = ProblemTag.objects.get(name=tag_name)
    tagged_item = ProblemTaggedItem.objects.get(
        tag=tag, content_object=sample_problem, user=sample_user)
    assert tag.name == tag_name
    assert tagged_item.is_tagged is True

    remarks_key = get_remarks_key_list(tagged_item.remarks)[0]
    assert remarks_key == 'tagged_at'

    # Tag remove
    url = reverse('official:tag-problem-remove', kwargs={'pk': sample_problem.pk})
    response = client.post(url, data=post_data)
    assert response.status_code == 200

    tag.refresh_from_db()
    tagged_item.refresh_from_db()
    assert tagged_item.is_tagged is False

    remarks_key = get_remarks_key_list(tagged_item.remarks)[1]
    assert remarks_key == 'untagged_at'
