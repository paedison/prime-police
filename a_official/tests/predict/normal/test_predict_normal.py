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
def test_list_page_without_predict_exam(logged_client: Client, base_fixture: dict):
    exam = base_fixture['exam']
    _, decoded = assert_response_contains_not(
        logged_client,
        base_fixture['urls']['list'],
        exam.full_reference,
    )


def test_list_page_with_predict_exam(logged_client: Client, predict_fixture: dict):
    exam = predict_fixture['exam']
    _, decoded = assert_response_contains(
        logged_client,
        predict_fixture['urls']['list'],
        exam.full_reference,
    )


# Test Register Page
def test_register_page_error_without_predict_exam(logged_client: Client, base_fixture: dict):
    assert_response_contains(
        logged_client,
        base_fixture['urls']['register'],
        '합격 예측 대상 시험이 아닙니다.',
    )


def test_register_page_error_existing_student(logged_client: Client, student_fixture: dict):
    assert_response_contains(
        logged_client,
        student_fixture['urls']['register'],
        '등록된 수험정보가 존재합니다.',
    )


def test_register_page_error_in_form(logged_client: Client, predict_fixture: dict):
    url_register = predict_fixture['urls']['register']
    student_info = predict_fixture['student_info']

    def assert_not_proper_form(key: str, error_message: str):
        student_info_copy = student_info.copy()
        student_info_copy.pop(key)
        response = logged_client.post(url_register, student_info_copy)

        assert response.status_code == 200
        assert error_message in response.content.decode('utf-8')

    assert_not_proper_form('serial', '필수 항목입니다.')
    assert_not_proper_form('name', '필수 항목입니다.')
    assert_not_proper_form('password', '필수 항목입니다.')
    assert_not_proper_form('selection', '필수 항목입니다.')


def test_register_page_success(logged_client: Client, predict_fixture: dict):
    time_schedule = predict_fixture['time_schedule']
    student_info = predict_fixture['student_info']
    _, _, field_idx, _, _ = predict_fixture['subject_tuples']

    url_register = predict_fixture['urls']['register']
    url_detail = predict_fixture['urls']['detail']
    url_input_current = predict_fixture['urls'][f'answer_input_{field_idx}']

    response = logged_client.post(url_register, student_info)
    assert response.status_code == 302

    student = models.PredictStudent.objects.get(
        user=predict_fixture['user'],
        exam=predict_fixture['exam'],
    )
    assert student.serial == student_info['serial']
    assert student.name == student_info['name']
    assert student.password == student_info['password']
    assert student.selection == student_info['selection']

    with freeze_time(time_schedule['after_exam_1_end']):
        _, decoded = assert_response_contains_not(
            logged_client,
            url_detail,
            '등록된 수험정보가 없습니다.'
        )

        assert url_input_current in decoded


# Test Answer Input Page
def test_answer_input_page_error_without_predict_exam(logged_client: Client, base_fixture: dict):
    assert_response_contains(
        logged_client,
        base_fixture['urls']['detail'],
        '합격 예측 대상 시험이 아닙니다.',
    )


def test_answer_input_page_error_without_student(logged_client: Client, predict_fixture: dict):
    time_schedule = predict_fixture['time_schedule']
    _, _, field_idx, _, _ = predict_fixture['subject_tuples']

    with freeze_time(time_schedule[f'after_exam_1_end']):
        assert_response_contains(
            logged_client,
            predict_fixture['urls'][f'answer_input_{field_idx}'],
            '등록된 수험정보가 없습니다.',
        )


def test_answer_input_page_success(logged_client: Client, student_fixture: dict):
    time_schedule = student_fixture['time_schedule']
    _, subject_fld, field_idx, _, _ = student_fixture['subject_tuples']

    with freeze_time(time_schedule[f'after_exam_1_end']):
        number = 1
        answer = 4
        response = logged_client.post(
            student_fixture['urls'][f'answer_input_{field_idx}'],
            data={'number': number, 'answer': answer},
        )
        assert 'total_answer_set' in response.client.cookies

        total_answer_set = json.loads(response.client.cookies.get('total_answer_set').value)
        assert total_answer_set[subject_fld][number - 1] == answer


# Test Answer Confirm Page
def test_answer_confirm_page_error_without_predict_exam(logged_client: Client, base_fixture: dict):
    _, _, field_idx, _, _ = base_fixture['subject_tuples']

    assert_response_contains(
        logged_client,
        base_fixture['urls'][f'answer_confirm_{field_idx}'],
        '합격 예측 대상 시험이 아닙니다.'
    )


def test_answer_confirm_page_error_without_student(logged_client: Client, predict_fixture: dict):
    time_schedule = predict_fixture['time_schedule']
    _, _, field_idx, _, _ = predict_fixture['subject_tuples']

    with freeze_time(time_schedule[f'after_exam_1_end']):
        assert_response_contains(
            logged_client,
            predict_fixture['urls'][f'answer_confirm_{field_idx}'],
            '등록된 수험정보가 없습니다.'
        )


def test_answer_confirm_page_after_exam_1_end(logged_client: Client, student_fixture):
    subject = student_fixture['subject']
    subject_vars = student_fixture['subject_vars']
    _, subject_fld, field_idx, problem_count, _ = student_fixture['subject_tuples']

    time_schedule = student_fixture['time_schedule']
    exam = student_fixture['exam']
    student = student_fixture['student']

    with freeze_time(time_schedule[f'after_exam_1_end']):
        total_answer_set = {subject_fld: [random.randint(1, 4) for _ in range(problem_count)]}
        logged_client.cookies['total_answer_set'] = json.dumps(total_answer_set)

        response = logged_client.post(student_fixture['urls'][f'answer_confirm_{field_idx}'])
        assert response.status_code == 200
        if field_idx != len(subject_vars) - 1:
            assert student_fixture['urls'][f'answer_input_{field_idx + 1}'] in response.content.decode()
        else:
            assert student_fixture['urls']['detail'] in response.content.decode()

        qs_student_answer = models.PredictAnswer.objects.filter(student=student, problem__subject=subject)
        student_answer_dict = {qs_sa.problem: qs_sa for qs_sa in qs_student_answer}
        assert qs_student_answer.count() == problem_count

        qs_answer_count = models.PredictAnswerCount.objects.filter(problem__exam=exam, problem__subject=subject)
        for qs_ac in qs_answer_count:
            ans = student_answer_dict[qs_ac.problem].answer
            assert getattr(qs_ac, f'count_{ans}') == 1


# Test Detail Page
def test_detail_page_error_without_predict_exam(logged_client: Client, base_fixture: dict):
    assert_response_contains(
        logged_client,
        base_fixture['urls']['detail'],
        '합격 예측 대상 시험이 아닙니다.',
    )


def test_detail_page_error_without_student(logged_client: Client, predict_fixture: dict):
    assert_response_contains(
        logged_client,
        predict_fixture['urls']['detail'],
        '등록된 수험정보가 없습니다.',
    )


def test_detail_page_with_student(logged_client: Client, student_fixture: dict):
    time_schedule = student_fixture['time_schedule']

    with freeze_time(time_schedule['before_exam']):
        assert_response_contains(
            logged_client,
            student_fixture['urls']['detail'],
            '시험 시작 전입니다.',
        )

    assert_response_contains(
        logged_client,
        student_fixture['urls']['detail'],
        '시험 진행 중입니다.',
    )

    with freeze_time(time_schedule['after_exam_1_end']):
        assert_response_contains(
            logged_client,
            student_fixture['urls']['detail'],
            '시험 진행 중입니다.',
            '답안을 제출해주세요.',
            student_fixture['urls']['answer_input_1'],
        )


def test_detail_page_gathering_answers_before_answer_predict_opened(
        logged_client: Client, student_answer_fixture: dict):
    time_schedule = student_answer_fixture['time_schedule']

    with freeze_time(time_schedule['before_answer_predict_opened']):
        assert_response_contains(
            logged_client,
            student_answer_fixture['urls']['detail'],
            '답안 수집중입니다.',
        )


def test_detail_page_score_predict_before_answer_official_opened(
        logged_client: Client, student_answer_fixture: dict):
    time_schedule = student_answer_fixture['time_schedule']
    subject = student_answer_fixture['subject']
    answer_set = student_answer_fixture['answer_set']
    _, _, _, _, score_per_problem = student_answer_fixture['subject_tuples']

    correct_count = 0
    for answer in answer_set:
        if answer.answer == answer.problem.predict_answer_count.answer_predict:
            correct_count += 1
    score_predict = correct_count * score_per_problem

    with freeze_time(time_schedule['before_answer_official_opened']):
        response = logged_client.get(student_answer_fixture['urls']['detail'])
        context = response.context[0]
        assert 'stat_data' in context
        assert 'score_predict' in context['stat_data'][subject]
        assert score_predict == context['stat_data'][subject]['score_predict']


def test_detail_page_score_after_answer_official_opened(
        logged_client: Client, student_answer_fixture: dict):
    time_schedule = student_answer_fixture['time_schedule']
    subject = student_answer_fixture['subject']
    answer_set = student_answer_fixture['answer_set']

    correct_count = 0
    for answer in answer_set:
        if answer.answer == answer.problem.answer:
            correct_count += 1

    subject_vars = student_answer_fixture['subject_vars']
    score_per_problem = subject_vars[subject][-1]
    score = correct_count * score_per_problem

    student = student_answer_fixture['student']
    setattr(student.score, subject, score)

    with freeze_time(time_schedule['after_answer_official_opened']):
        response = logged_client.get(student_answer_fixture['urls']['detail'])
        context = response.context[0]
        assert 'stat_data' in context
        assert 'score_result' in context['stat_data'][subject]
        assert score == context['stat_data'][subject]['score_result']
