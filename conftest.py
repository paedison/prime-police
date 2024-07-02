import pytest

from pytest_factoryboy import register
from a_official.factories import UserFactory, OfficialProblemFactory

register(UserFactory)
register(OfficialProblemFactory)
