import json
import random

from django.test import Client
from freezegun import freeze_time

from a_official import models


def assert_response_contains(client: Client, url, *expected_message: str):
    response = client.get(url)
    decoded = response.content.decode('utf-8')
    for message in expected_message:
        assert message in decoded
    return response, decoded


def assert_response_contains_not(client: Client, url: str, *not_expected_message: str):
    response = client.get(url)
    decoded = response.content.decode('utf-8')
    for message in not_expected_message:
        assert message not in decoded
    return response, decoded


# Test List Page
def test_list_page_without_predict_exam(logged_staff_client: Client, base_staff_fixture: dict):
    exam = base_staff_fixture['exam']
    _, decoded = assert_response_contains_not(
        logged_staff_client,
        base_staff_fixture['urls']['staff_list'],
        exam.get_year_display(),
    )


def test_list_page_with_predict_exam(logged_staff_client: Client, predict_staff_fixture: dict):
    exam = predict_staff_fixture['exam']
    _, decoded = assert_response_contains(
        logged_staff_client,
        predict_staff_fixture['urls']['staff_list'],
        exam.get_year_display(),
    )


# Test Detail Page
def test_detail_page_error_without_predict_exam(logged_staff_client: Client, base_staff_fixture: dict):
    assert_response_contains(
        logged_staff_client,
        base_staff_fixture['urls']['detail'],
        '합격 예측 대상 시험이 아닙니다.'
    )


# def test_detail_page_error_without_student(logged_staff_client: Client, predict_fixture: dict):
#     assert_response_contains(
#         logged_staff_client,
#         predict_fixture['urls']['detail'],
#         '등록된 수험정보가 없습니다.'
#     )
#
#
# def test_detail_page_with_student(logged_staff_client: Client, student_fixture: dict):
#     time_schedule = student_fixture['time_schedule']
#
#     with freeze_time(time_schedule['before_exam']):
#         assert_response_contains(
#             logged_staff_client,
#             student_fixture['urls']['detail'],
#             '시험 시작 전입니다.'
#         )
#
#     assert_response_contains(
#         logged_staff_client,
#         student_fixture['urls']['detail'],
#         '시험 진행 중입니다.'
#     )
#
#     with freeze_time(time_schedule['after_exam_1_end']):
#         assert_response_contains(
#             logged_staff_client,
#             student_fixture['urls']['detail'],
#             '시험 진행 중입니다.',
#             '답안을 제출해주세요.',
#             student_fixture['urls']['answer_input_1'],
#         )
#
#
# def test_detail_page_gathering_answers_before_answer_predict_opened(
#         logged_staff_client: Client, student_answer_fixture: dict):
#     time_schedule = student_answer_fixture['time_schedule']
#
#     with freeze_time(time_schedule['before_answer_predict_opened']):
#         assert_response_contains(
#             logged_staff_client,
#             student_answer_fixture['urls']['detail'],
#             '답안 수집중입니다.',
#         )
#
#
# def test_detail_page_score_predict_before_answer_official_opened(
#         logged_staff_client: Client, student_answer_fixture: dict):
#     time_schedule = student_answer_fixture['time_schedule']
#     subject = student_answer_fixture['subject']
#     answer_set = student_answer_fixture['answer_set']
#     _, _, _, _, score_per_problem = student_answer_fixture['subject_tuples']
#
#     correct_count = 0
#     for answer in answer_set:
#         if answer.answer == answer.problem.predict_answer_count.answer_predict:
#             correct_count += 1
#     score_predict = correct_count * score_per_problem
#
#     with freeze_time(time_schedule['before_answer_official_opened']):
#         response = logged_staff_client.get(student_answer_fixture['urls']['detail'])
#         context = response.context[0]
#         assert 'stat_data' in context
#         assert 'score_predict' in context['stat_data'][subject]
#         assert score_predict == context['stat_data'][subject]['score_predict']
#
#
# def test_detail_page_score_after_answer_official_opened(
#         logged_staff_client: Client, student_answer_fixture: dict):
#     time_schedule = student_answer_fixture['time_schedule']
#     subject = student_answer_fixture['subject']
#     answer_set = student_answer_fixture['answer_set']
#
#     correct_count = 0
#     for answer in answer_set:
#         if answer.answer == answer.problem.answer:
#             correct_count += 1
#
#     subject_vars = student_answer_fixture['subject_vars']
#     score_per_problem = subject_vars[subject][-1]
#     score = correct_count * score_per_problem
#
#     student = student_answer_fixture['student']
#     setattr(student.score, subject, score)
#
#     with freeze_time(time_schedule['after_answer_official_opened']):
#         response = logged_staff_client.get(student_answer_fixture['urls']['detail'])
#         context = response.context[0]
#         assert 'stat_data' in context
#         assert 'score' in context['stat_data'][subject]
#         assert score == context['stat_data'][subject]['score']
