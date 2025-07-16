__all__ = [
    'official_test_user_info', 'official_test_student_info',
    'official_test_subject', 'official_test_subject_tuples',
]


import pytest


@pytest.fixture
def official_test_user_info():
    return dict(
        email='normal@test.com',
        name='일반',
        password='normal123!',
        prime_id='test_normal_id',
    )


@pytest.fixture
def official_test_student_info():
    return dict(
        serial='9999',
        name='일반',
        password='1234',
        selection='민법',
    )


@pytest.fixture
def official_test_subject():
    return '형사'


@pytest.fixture
def official_test_subject_tuples(official_subject_vars, official_test_subject):
    return official_subject_vars[official_test_subject]
