import pytest
from django.db.models import F
from django.test import Client

from a_common.models import User
from a_official import models
from a_official.tests import factories

pytest_plugins = [
    'a_official.tests.fixtures',
    'a_official.tests.predict.normal.fixtures',
    'a_official.tests.predict.staff.fixtures',
]


@pytest.fixture
def official_test_staff(db, official_test_staff_info):
    return factories.UserFactory(**official_test_staff_info)


@pytest.fixture
def logged_staff_client(official_test_staff) -> Client:
    client = Client()
    client.force_login(official_test_staff)
    return client


@pytest.fixture
def official_test_statistics(exam):
    return factories.PredictStatisticsFactory(exam=exam)


@pytest.fixture
def official_test_score(official_test_student):
    return factories.PredictScoreFactory(student=official_test_student)


@pytest.fixture
def official_test_rank(official_test_student):
    return factories.PredictRankFactory(student=official_test_student)


@pytest.fixture
def official_test_answer_set(
        official_test_student: models.PredictStudent,
        official_test_problems: list[models.Problem],
        official_test_subject: str,
):
    answer_set = []
    for problem in official_test_problems:
        if problem.subject == official_test_subject:
            answer_set.append(factories.PredictAnswerFactory(student=official_test_student, problem=problem))
    return answer_set


@pytest.fixture
def base_staff_fixture(
        official_time_schedule: dict,
        official_test_staff: User,
        official_test_exam: models.Exam,
        official_subject_vars: dict,
        official_test_subject_tuples: tuple,
        official_test_urls: dict,
        official_test_problems: list,
        official_test_answer_counts: dict[list],
        official_test_subject: str
) -> dict:
    return dict(
        time_schedule=official_time_schedule,
        staff=official_test_staff,
        exam=official_test_exam,
        subject=official_test_subject,
        subject_vars=official_subject_vars,
        subject_tuples=official_test_subject_tuples,
        urls=official_test_urls,
        problems=official_test_problems,
        answer_counts=official_test_answer_counts,
    )


@pytest.fixture
def predict_staff_fixture(
        base_staff_fixture: dict,
        official_test_predict_exam: models.PredictExam,
) -> dict:
    return dict(
        base_staff_fixture,
        predict_exam=official_test_predict_exam,
    )


@pytest.fixture
def student_fixture(
        predict_fixture: dict,
        official_test_student: models.PredictStudent,
        official_test_score: models.PredictScore,
        official_test_rank: models.PredictRank,
) -> dict:
    return dict(
        predict_fixture,
        student=official_test_student,
        score=official_test_score,
        rank_total=official_test_rank,
    )


@pytest.fixture
def student_answer_fixture(
        student_fixture: dict,
        official_test_subject: str,
        official_test_answer_counts: dict,
        official_test_answer_set: dict,
) -> dict:
    update_list = []
    for idx, tac in enumerate(official_test_answer_counts[official_test_subject]):
        ans_student = official_test_answer_set[idx].answer
        setattr(tac, f'count{ans_student}', F(f'count{ans_student}') + 1)
        update_list.append(tac)
    models.PredictAnswerCount.objects.bulk_update(update_list, ['count_1', 'count_2', 'count_3', 'count_4'])
    return dict(
        student_fixture,
        answer_set=official_test_answer_set,
    )
