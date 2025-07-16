__all__ = [
    'official_test_exam', 'official_test_urls', 'official_test_predict_exam',
    'official_test_problems', 'official_test_answer_counts',
]


from collections import defaultdict

import pytest
from django.urls import reverse

from a_official.tests import factories
from .common import official_test_exam_info, official_time_schedule, official_subject_vars


@pytest.fixture
def official_test_exam(official_test_exam_info):
    return factories.ExamFactory(**official_test_exam_info)


@pytest.fixture
def official_test_urls(official_test_exam, official_subject_vars):
    official_urls = {
        'list': reverse('official:predict-list'),
        'detail': reverse('official:predict-detail', args=[official_test_exam.id]),
        'register': reverse('official:predict-register'),

        'staff_list': reverse('official:staff-predict-list'),
        'staff_detail': reverse('official:staff-predict-detail', args=[official_test_exam.id]),
        'staff_create': reverse('official:staff-predict-create'),
        'staff_update': reverse('official:staff-predict-update', args=[official_test_exam.id]),

        'staff_print_statistics': reverse('official:staff-predict-statistics-print', args=[official_test_exam.id]),
        'staff_print_catalog': reverse('official:staff-predict-catalog-print', args=[official_test_exam.id]),
        'staff_print_answer': reverse('official:staff-predict-answer-print', args=[official_test_exam.id]),

        'staff_excel_statistics': reverse('official:staff-predict-statistics-excel', args=[official_test_exam.id]),
        'staff_excel_catalog': reverse('official:staff-predict-catalog-excel', args=[official_test_exam.id]),
        'staff_excel_answer': reverse('official:staff-predict-answer-excel', args=[official_test_exam.id]),
    }
    for (_, subject_fld, field_idx, _, _) in official_subject_vars.values():
        official_urls[f'answer_input_{field_idx}'] = reverse(
            'official:predict-answer-input', args=[official_test_exam.id, subject_fld])
        official_urls[f'answer_confirm_{field_idx}'] = reverse(
            'official:predict-answer-confirm', args=[official_test_exam.id, subject_fld])
    return official_urls


@pytest.fixture
def official_test_predict_exam(official_test_exam, official_time_schedule):
    def get_time(key):
        return {key: official_time_schedule[key]}

    return factories.PredictExamFactory(
        exam=official_test_exam,
        is_active=True,
        **get_time('exam_started_at'),
        **get_time('exam_finished_at'),
        **get_time('answer_predict_opened_at'),
        **get_time('answer_official_opened_at'),
        **get_time('predict_closed_at'),
    )


@pytest.fixture
def official_test_problems(official_test_exam, official_subject_vars):
    created = []
    for sub, (_, _, _, count, _) in official_subject_vars.items():
        for number in range(1, count + 1):
            created.append(factories.ProblemFactory(exam=official_test_exam, subject=sub, number=number))
    return created


@pytest.fixture
def official_test_answer_counts(official_test_problems):
    created = defaultdict(list)
    factories_dict = {
        'all': factories.PredictAnswerCountFactory,
        'top': factories.PredictAnswerCountTopRankFactory,
        'mid': factories.PredictAnswerCountMidRankFactory,
        'low': factories.PredictAnswerCountLowRankFactory,
    }
    for problem in official_test_problems:
        for key, factory in factories_dict.items():
            created[key].append(factory(problem=problem))
    return created

