__all__ = [
    'fixed_now', 'official_test_exam_info', 'official_time_schedule',
    'official_subject_vars', 'official_subject_selection',
]


import datetime

import pytest
from django.utils import timezone


@pytest.fixture(scope='session')
def fixed_now():
    return timezone.now()


@pytest.fixture(scope='session')
def official_test_exam_info():
    return dict(year=2026, is_active=True)


@pytest.fixture
def official_time_schedule(fixed_now):
    finish_time = fixed_now + datetime.timedelta(minutes=230)
    return dict(
        now=fixed_now,

        exam_started_at=fixed_now,
        exam_finished_at=finish_time,
        answer_predict_opened_at=fixed_now + datetime.timedelta(minutes=350),
        answer_official_opened_at=fixed_now + datetime.timedelta(minutes=400),
        predict_closed_at=fixed_now + datetime.timedelta(minutes=450),

        exam_1_end_time=fixed_now + datetime.timedelta(minutes=80),
        exam_2_start_time=fixed_now + datetime.timedelta(minutes=110),
        exam_2_end_time=finish_time,

        before_exam=fixed_now - datetime.timedelta(minutes=10),
        after_exam_1_end=fixed_now + datetime.timedelta(minutes=90),
        after_exam_2_end=fixed_now + datetime.timedelta(minutes=250),
        before_answer_predict_opened=fixed_now + datetime.timedelta(minutes=325),
        before_answer_official_opened=fixed_now + datetime.timedelta(minutes=375),
        after_answer_official_opened=fixed_now + datetime.timedelta(minutes=425)
    )


@pytest.fixture
def official_subject_vars():
    return dict(
        형사=('형사법', 'subject_0', 0, 40, 3),
        헌법=('헌법', 'subject_1', 1, 40, 1.5),
        경찰=('경찰학', 'subject_2', 2, 40, 3),
        범죄=('범죄학', 'subject_3', 3, 40, 1.5),
        민법=('민법총칙', 'subject_4', 4, 40, 1),
        행법=('행정법', 'subject_5', 5, 40, 1),
        행학=('행정학', 'subject_6', 6, 40, 1)
    )


@pytest.fixture
def official_subject_selection():
    return ['민법', '행법', '행학']
