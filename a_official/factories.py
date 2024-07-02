import random

import factory
from faker import Faker

from a_common.models import User
from a_official.models import Problem, ProblemLike

fake = Faker()


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User
        django_get_or_create = ('username',)

    email = fake.email()
    username = email.split('@')[0]


def get_random_subject():
    subject_dict = Problem.get_subject_choices()
    subject_list = []
    for subjects in subject_dict.values():
        for subject in subjects.keys():
            subject_list.append(subject)
    subject_key = random.randint(0, len(subject_list))
    return subject_list[subject_key]


class OfficialProblemFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Problem

    year = random.randint(2023, 2024)
    subject = factory.Iterator(['형사', '헌법', '경찰', '범죄', '민법'])
    number = random.randint(1, 40)
    answer = random.randint(1, 4)
    question = fake.sentence()
    data = fake.sentence()


class OfficialProblemLikeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ProblemLike

    problem = factory.SubFactory(OfficialProblemFactory)
    user = factory.SubFactory(UserFactory)
