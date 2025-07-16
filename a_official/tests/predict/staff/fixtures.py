__all__ = [
    'official_test_staff_info',
]


import pytest


@pytest.fixture
def official_test_staff_info():
    return dict(
        email='staff@test.com',
        name='스탭',
        password='staff123!',
        prime_id='test_staff_id',
        is_staff=True
    )
