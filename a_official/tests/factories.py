import factory
import random
from faker import Faker
from a_official import models

fake = Faker("ko_KR")


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.User

    email = factory.LazyAttribute(lambda _: fake.unique.email())
    name = factory.LazyAttribute(lambda _: fake.user_name())
    password = factory.PostGenerationMethodCall('set_password', 'password123!')


class ExamFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Exam


class ProblemFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Problem

    exam = factory.SubFactory(ExamFactory)
    subject = factory.Iterator(['언어', '추리'])
    number = factory.Sequence(lambda n: n + 1)


class PredictExamFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.PredictExam

    exam = factory.SubFactory(ExamFactory)
    is_active = True


class PredictStatisticsFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.PredictStatistics

    exam = factory.SubFactory(ExamFactory)


class PredictStudentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.PredictStudent

    user = factory.SubFactory(UserFactory)
    exam = factory.SubFactory(ExamFactory)
    serial = factory.LazyAttribute(lambda _: fake.unique.random_number(digits=4))
    name = factory.LazyAttribute(lambda _: fake.name())
    password = factory.LazyAttribute(lambda _: fake.password())


class PredictAnswerFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.PredictAnswer

    student = factory.SubFactory(PredictStudentFactory)
    problem = factory.SubFactory(ProblemFactory)
    answer = factory.LazyAttribute(lambda _: random.randint(1, 4))


class PredictAnswerCountFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.PredictAnswerCount

    problem = factory.SubFactory(ProblemFactory)


class PredictScoreFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.PredictScore

    student = factory.SubFactory(PredictStudentFactory)


class PredictRankFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.PredictRank

    student = factory.SubFactory(PredictStudentFactory)


class PredictAnswerCountTopRankFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.PredictAnswerCountTopRank

    problem = factory.SubFactory(ProblemFactory)


class PredictAnswerCountMidRankFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.PredictAnswerCountMidRank

    problem = factory.SubFactory(ProblemFactory)


class PredictAnswerCountLowRankFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.PredictAnswerCountLowRank

    problem = factory.SubFactory(ProblemFactory)
