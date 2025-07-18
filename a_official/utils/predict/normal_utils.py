__all__ = [
    'TemporaryAnswerContext',
    'NormalListContext', 'NormalDetailAnswerContext', 'NormalDetailStatisticsContext',
    'NormalRegisterContext', 'NormalAnswerInputContext', 'NormalAnswerConfirmContext', 'ChartContext',
]

import json
from collections import defaultdict
from dataclasses import dataclass

import numpy as np
import pandas as pd
from django.db.models import Count, F
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django_htmx.http import reswap

from a_common.utils import HtmxHttpRequest, update_context_data
from a_common.utils.export_excel_methods import *
from a_common.utils.modify_models_methods import *
from a_official.utils.common_utils import *

_model = ModelData()

UPDATE_MESSAGES = {
    'raw_score': get_update_messages('원점수'),
    'score': get_update_messages('표준점수'),
    'rank': get_update_messages('등수'),
    'statistics': get_update_messages('통계'),
    'answer_count': get_update_messages('문항분석표'),
}


@dataclass(kw_only=True)
class TemporaryAnswerContext:
    _request: HtmxHttpRequest
    _context: dict

    def __post_init__(self):
        self._exam = self._context['exam']
        self._subject_field = self._context.get('subject_field', '')
        self._student = self._context['student']

    def get_total_answer_set(self) -> dict:
        subject_vars = self._context['subject_vars']
        empty_answer_set = {fld: [0 for _ in range(cnt)] for _, (_, fld, _, cnt, _) in subject_vars.items()}
        total_answer_set_cookie = self._request.COOKIES.get('total_answer_set', '{}')
        total_answer_set = json.loads(total_answer_set_cookie) or empty_answer_set
        return total_answer_set

    def get_answer_student_list_for_subject(self):
        total_answer_set = self.get_total_answer_set()
        answer_data = total_answer_set.get(self._subject_field, [])
        return [{'no': no, 'ans': ans} for no, ans in enumerate(answer_data, start=1)]

    def get_answer_student_for_subject(self):
        total_answer_set = self.get_total_answer_set()
        return total_answer_set.get(self._subject_field, [])


@dataclass(kw_only=True)
class ChartContext:
    _stat_data: dict
    _student: _model.student | None

    def __post_init__(self):
        selection = self._student.selection if self._student else '민법'
        self._subject_variants = SubjectVariants(_selection=selection)

        self._subject_vars = self._subject_variants.subject_vars
        self._subject_fields_sum = self._subject_variants.subject_fields_sum
        self._student_score_list = self.get_student_score_list()

    def get_student_score_list(self):
        if self._student:
            return [getattr(self._student.score, fld) or 0 for fld in self._subject_fields_sum]

    def get_dict_stat_chart(self) -> dict:
        chart_score = {
            'avg': [], 't50': [], 't25': [], 't10': [], 'max': [],
        }
        if self._student:
            chart_score['my_score'] = self._student_score_list

        for stat in self._stat_data.values():
            chart_score['avg'].append(stat['avg'])
            chart_score['t50'].append(stat['t50'])
            chart_score['t25'].append(stat['t25'])
            chart_score['t10'].append(stat['t10'])
            chart_score['max'].append(stat['max'])

        score_list = [score for score in self._student_score_list if score is not None]
        chart_score['min_score'] = (min(score_list) // 5) * 5 if score_list else 0
        return chart_score

    def get_dict_stat_frequency(self) -> dict:
        score_frequency_list = _model.student.objects.average_scores_over(self._student.exam, 50)
        scores = [round(score, 1) for score in score_frequency_list]
        sorted_freq, target_bin = self.frequency_table_by_bin(scores)

        score_label, score_data, score_color = [], [], []
        for key, val in sorted_freq.items():
            score_label.append(key)
            score_data.append(val)
            color = 'rgba(255, 99, 132, 0.5)' if key == target_bin else 'rgba(54, 162, 235, 0.5)'
            score_color.append(color)

        return {'score_data': score_data, 'score_label': score_label, 'score_color': score_color}

    def frequency_table_by_bin(self, scores: list, bin_size: int = 5) -> tuple[dict, str | None]:
        freq = defaultdict(int)
        for score in scores:
            bin_start = int((score // bin_size) * bin_size)
            bin_end = bin_start + bin_size
            bin_label = f'{bin_start}~{bin_end}'
            freq[bin_label] += 1

        # bin_start 기준으로 정렬
        sorted_freq = dict(sorted(freq.items(), key=lambda x: int(x[0].split('~')[0])))

        # 특정 점수의 구간 구하기
        target_bin = None
        if self._student and self._student.score.sum:  # noqa
            bin_start = int((self._student.score.sum // bin_size) * bin_size)  # noqa
            bin_end = bin_start + bin_size
            target_bin = f'{bin_start}~{bin_end}'

        return sorted_freq, target_bin


@dataclass(kw_only=True)
class NormalListContext:
    _request: HtmxHttpRequest

    def get_qs_exams(self):
        qs_exam = _model.exam.objects.predict_exam_active()
        qs_student = _model.student.objects.registered_exam_student(self._request, qs_exam)
        if qs_student:
            student_dict = {qs_s.exam: qs_s for qs_s in qs_student}
            for qs_e in qs_exam:
                qs_e.student = student_dict.get(qs_e)
        return qs_exam

    def get_login_url(self):
        return reverse_lazy('account_login') + '?next=' + self._request.get_full_path()


@dataclass(kw_only=True)
class NormalDetailAnswerContext:
    _request: HtmxHttpRequest
    _context: dict

    def __post_init__(self):
        self._student = self._context['student']
        self._subject_vars_dict = self._context['subject_vars_dict']
        self._subject_vars = self._subject_vars_dict['base']
        self.update_student()
        self.is_confirmed_data = self.get_is_confirmed_data()

    def get_is_confirmed_data(self) -> dict[str, bool]:
        is_confirmed_data = {sub: False for sub in self._subject_vars}
        confirmed_sub_list = self._context['qs_student_answer'].values_list('subject', flat=True).distinct()
        for sub in confirmed_sub_list:
            is_confirmed_data[sub] = True
        is_confirmed_data['총점'] = all(is_confirmed_data.values())  # Add is_confirmed_data for '총점'
        return is_confirmed_data

    def update_student(self):
        if self._student:
            selection_field = self._subject_vars[self._student.selection][1]
            self._student.score_selection = getattr(self._student.score, selection_field)
            self._student.rank_selection = getattr(self._student.rank, selection_field)

    def is_analyzing(self):
        return self._student and hasattr(self._student, 'score') and self._student.score.sum is None

    @staticmethod
    def get_loop_list(problem_count: int):
        loop_list = []
        quotient = problem_count // 10
        counter_list = [10] * quotient
        remainder = problem_count % 10
        if remainder:
            counter_list.append(remainder)
        loop_min = 0
        for idx, counter in enumerate(counter_list):
            loop_list.append({'counter': counter, 'min': loop_min})
            loop_min += 10
        return loop_list

    def get_normal_answer_context(self) -> dict:
        subject_vars = self._subject_vars
        context = {
            sub: {
                'id': str(idx), 'title': subject, 'subject': subject, 'field': fld,
                'url_answer_input': self._student.exam.get_predict_answer_input_url(fld),
                'is_confirmed': self.is_confirmed_data[sub],
                'loop_list': self.get_loop_list(problem_count),
                'page_obj': [],
            }
            for sub, (subject, fld, idx, problem_count, _) in subject_vars.items()
        }
        qs_student_answer = self._context['qs_student_answer']

        for qs_sa in qs_student_answer:
            sub = qs_sa.problem.subject
            ans_official = qs_sa.problem.answer
            ans_student = qs_sa.answer
            ans_predict = qs_sa.problem.predict_answer_count.answer_predict

            qs_sa.no = qs_sa.problem.number
            qs_sa.ans_official = ans_official
            qs_sa.ans_official_circle = qs_sa.problem.get_answer_display

            qs_sa.ans_student = ans_student
            qs_sa.field = subject_vars[sub][1]

            qs_sa.ans_predict = ans_predict
            qs_sa.rate_accuracy = qs_sa.problem.predict_answer_count.get_answer_predict_rate()

            qs_sa.rate_correct = qs_sa.problem.predict_answer_count.get_answer_rate(ans_official)
            qs_sa.rate_correct_top = qs_sa.problem.predict_answer_count_top_rank.get_answer_rate(ans_official)
            qs_sa.rate_correct_mid = qs_sa.problem.predict_answer_count_mid_rank.get_answer_rate(ans_official)
            qs_sa.rate_correct_low = qs_sa.problem.predict_answer_count_low_rank.get_answer_rate(ans_official)
            if qs_sa.rate_correct_top is not None and qs_sa.rate_correct_low is not None:
                qs_sa.rate_gap = qs_sa.rate_correct_top - qs_sa.rate_correct_low
            else:
                qs_sa.rate_gap = 0

            qs_sa.rate_selection = qs_sa.problem.predict_answer_count.get_answer_rate(ans_student)
            qs_sa.rate_selection_top = qs_sa.problem.predict_answer_count_top_rank.get_answer_rate(ans_student)
            qs_sa.rate_selection_mid = qs_sa.problem.predict_answer_count_mid_rank.get_answer_rate(ans_student)
            qs_sa.rate_selection_low = qs_sa.problem.predict_answer_count_low_rank.get_answer_rate(ans_student)

            context[sub]['page_obj'].append(qs_sa)
        return context


@dataclass(kw_only=True)
class NormalDetailStatisticsContext:
    _request: HtmxHttpRequest
    _context: dict

    def __post_init__(self):
        self._student = self._context['student']
        self._subject_vars_dict = self._context['subject_vars_dict']
        self.qs_student_answer = _model.answer.objects.filtered_by_exam_student(self._student)

    def get_is_confirmed_data(self) -> dict[str, bool]:
        subject_vars = self._subject_vars_dict['base']
        is_confirmed_data = {sub: False for sub in subject_vars}
        confirmed_sub_list = self.qs_student_answer.values_list('subject', flat=True).distinct()
        for sub in confirmed_sub_list:
            is_confirmed_data[sub] = True
        is_confirmed_data['총점'] = all(is_confirmed_data.values())  # Add is_confirmed_data for '총점'
        return is_confirmed_data

    def get_stat_data(self) -> dict:
        answer_count_dict = self.get_answer_count_dict()
        subject_vars_sum = self._subject_vars_dict['sum_last']
        time_schedule = self._context['time_schedule']
        is_confirmed_data = self.get_is_confirmed_data()

        stat_data = {}
        for sub, (subject, fld, _, problem_count, _) in subject_vars_sum.items():
            url_answer_input = ''
            if self._student:
                url_answer_input = self._student.exam.get_predict_answer_input_url(fld) if sub != '총점' else ''
            answer_count = answer_count_dict[sub] if sub != '총점' else sum(answer_count_dict.values())

            stat_data[sub] = {
                'field': fld, 'sub': sub, 'subject': subject,
                'start_time': time_schedule[sub][0],
                'end_time': time_schedule[sub][1],

                'is_confirmed': is_confirmed_data[sub],
                'url_answer_input': url_answer_input,

                'problem_count': problem_count,
                'answer_count': answer_count,

                'participants': 0,
                'score_predict': 0, 'score_result': 0,
                'rank': 0, 'max': 0, 't10': 0, 't25': 0, 't50': 0, 'avg': 0,
            }

        predict_exam = self._student.exam.predict_exam
        if predict_exam.is_answer_predict_opened():
            self.update_score(stat_data, 'predict')
        if predict_exam.is_answer_official_opened():
            self.update_score(stat_data, 'result')

        for sub, (subject, fld, _, problem_count, _) in subject_vars_sum.items():
            participants = self.get_participants(sub)
            if participants:
                score_np = self.get_score_np(fld)
                if predict_exam.is_answer_official_opened:
                    score = getattr(self._student.score, fld)
                    if score_np.size > 0 and score in score_np:
                        scores_stat = get_stat_from_scores(score_np)
                        sorted_scores = np.sort(score_np)[::-1]
                        flat_scores = sorted_scores.flatten()
                        rank = int(np.where(flat_scores == score)[0][0] + 1)
                        stat_data[sub].update(scores_stat | {'participants': participants, 'rank': rank})
        return stat_data

    def get_answer_count_dict(self) -> dict[str, int]:
        total_answer_set = self._context['total_answer_set']
        subject_vars = self._subject_vars_dict['base']

        answer_count_dict = {}
        for sub, (_, fld, _, _, _) in subject_vars.items():
            answer_list = total_answer_set.get(fld)
            saved_answers = []
            if answer_list:
                saved_answers = [ans for ans in answer_list if ans]
            answer_count_dict[sub] = len(saved_answers)
            if hasattr(self._student, 'answer_count'):
                answer_count_dict[sub] = self._student.answer_count.get(sub, 0)

        return answer_count_dict

    def get_participants(self, sub: str):
        subject_vars = self._subject_vars_dict['base']
        qs_answer = (
            _model.answer.objects.filter(problem__exam=self._student.exam)
            .order_by('student').values(sub=F('problem__subject')).distinct()
        )
        df = pd.DataFrame(qs_answer)
        if not df.empty:
            if sub == '총점':
                return min([df[df['sub'] == _sub].shape[0] for _sub in subject_vars])
            return df[df['sub'] == sub].shape[0]

    def get_score_np(self, fld: str):
        qs_score = (
            _model.score.objects.filter(student__exam=self._student.exam).order_by('student')
            .values('subject_0', 'subject_1', 'subject_2', 'subject_3', 'subject_4', 'subject_5', 'subject_6', 'sum')
        )
        df = pd.DataFrame(qs_score)
        if fld in df.columns:
            return df[df[fld] != 0][[fld]].dropna().to_numpy()
        return np.array([])

    def update_score(self, stat_data: dict, score_type: str):
        subject_vars = self._subject_vars_dict['base']
        correct_count_list = (
            self.qs_student_answer.filter(**{f'is_{score_type}_correct': True})
            .values('subject').annotate(correct_counts=Count(f'is_{score_type}_correct'))
        )
        exam_sum = 0
        for entry in correct_count_list:
            sub = entry['subject']
            if sub in subject_vars:
                correct_counts = entry['correct_counts']
                per_problem = subject_vars[sub][-1]
                score = correct_counts * per_problem
                exam_sum += score
                stat_data[sub][f'score_{score_type}'] = score
        stat_data['총점'][f'score_{score_type}'] = exam_sum


@dataclass(kw_only=True)
class NormalRegisterContext:
    _request: HtmxHttpRequest
    _context: dict

    def process_register(self):
        form = self._context['form']
        exam = self._context['exam']
        student_model = _model.student

        serial = form.cleaned_data['serial']
        if student_model.objects.filter(exam=exam, serial=serial).exists():
            form.add_error('serial', '이미 등록된 수험번호입니다.')
            form.add_error('serial', '만약 수험번호를 등록하신 적이 없다면 관리자에게 문의해주세요.')

        if form.errors:
            context = update_context_data(self._context, form=form)
            return render(self._request, 'a_official/predict_register.html', context)

        student, is_created = student_model.objects.get_or_create(
            exam=exam, user=self._request.user, serial=serial,
            name=form.cleaned_data['name'],
            password=form.cleaned_data['password'],
            selection=form.cleaned_data['selection'],
            phone_number=form.cleaned_data['phone_number']
        )

        if is_created:
            _model.score.objects.create(student=student)
            _model.rank.objects.create(student=student)
        return redirect(exam.get_predict_detail_url())


@dataclass(kw_only=True)
class NormalAnswerInputContext:
    _request: HtmxHttpRequest
    _context: dict

    def already_submitted(self):
        student = self._context['student']
        sub = self._context['sub']
        cnt = self._context['problem_count']
        return _model.answer.objects.filter(student=student, problem__subject=sub).count() == cnt

    def process_post_request_to_answer_input(self):
        problem_count = self._context['problem_count']
        subject_field = self._context['subject_field']
        total_answer_set = self._context['total_answer_set']

        try:
            no = int(self._request.POST.get('number'))
            ans = int(self._request.POST.get('answer'))
        except Exception as e:
            print(e)
            return reswap(HttpResponse(''), 'none')

        answer_temporary = {'no': no, 'ans': ans}
        context = update_context_data(self._context, answer=answer_temporary)
        response = render(self._request, 'a_official/snippets/predict_answer_button.html', context)

        if 1 <= no <= problem_count and 1 <= ans <= 5:
            total_answer_set[subject_field][no - 1] = ans
            response.set_cookie('total_answer_set', json.dumps(total_answer_set), max_age=3600)
            return response
        else:
            print('Answer is not appropriate.')
            return reswap(HttpResponse(''), 'none')


@dataclass(kw_only=True)
class NormalAnswerConfirmContext:
    _request: HtmxHttpRequest
    _context: dict

    def __post_init__(self):
        self._student = self._context['student']
        self._exam = self._context['exam']
        self._subject_vars = self._context['subject_vars']
        self._sub = self._context['sub']

    def get_answer_all_confirmed(self) -> bool:
        answer_student_counts = _model.answer.objects.filter(student=self._student).count()
        problem_count_sum = sum([value[3] for value in self._subject_vars.values()])
        return answer_student_counts == problem_count_sum

    def get_header(self):
        subject = self._context['subject']
        return f'{subject} 답안 제출'

    def process_post_request_to_answer_confirm(self):
        answer_student = self._context['answer_student']
        is_confirmed = all(answer_student)
        if is_confirmed:
            self.create_confirmed_answers(answer_student)
            self.update_answer_counts_after_confirm(answer_student)
            self.update_participants_of_statistics()

        next_url = self.get_next_url_for_answer_input()
        context = update_context_data(
            self._context, header=self.get_header(), is_confirmed=is_confirmed, next_url=next_url)
        return render(self._request, 'a_official/snippets/modal_answer_confirmed.html', context)

    @with_bulk_create_or_update()
    def create_confirmed_answers(self, answer_student):
        list_create = []
        for number, answer in enumerate(answer_student, start=1):
            problem = _model.problem.objects.get(exam=self._exam, subject=self._sub, number=number)
            list_create.append(_model.answer(student=self._student, problem=problem, answer=answer))
        return _model.answer, list_create, [], []

    def update_answer_counts_after_confirm(self, answer_student) -> None:
        qs_answer_count = _model.ac_all.objects.predict_filtered_by_exam(self._exam).filter(sub=self._sub)

        count_all = 0
        for qs_ac in qs_answer_count:
            ans_student = answer_student[qs_ac.number - 1]
            setattr(qs_ac, f'count_{ans_student}', F(f'count_{ans_student}') + 1)
            setattr(qs_ac, f'count_sum', F(f'count_sum') + 1)
            count_all += 1
            qs_ac.save()

        if count_all:
            print(f'{count_all} {_model.ac_all} instances saved.')

    def update_participants_of_statistics(self) -> None:
        target, _ = _model.statistics.objects.get_or_create(exam=self._exam)
        getattr(target, self._context['subject_field'])['participants'] += 1
        answer_all_confirmed = self.get_answer_all_confirmed()
        if answer_all_confirmed:
            target.sum['participants'] += 1
        target.save()

    def get_next_url_for_answer_input(self) -> str:
        qs_answer = (
            _model.answer.objects.filter(student=self._student)
            .values(subject=F('problem__subject'))
            .annotate(answer_count=Count('id'))
            .order_by('subject')
        )
        answer_count_dict = {entry['subject']: entry['answer_count'] for entry in qs_answer}

        for sub, (_, fld, _, _, _) in self._subject_vars.items():
            if not answer_count_dict.get(sub):
                return self._exam.get_predict_answer_input_url(fld)
        return self._exam.get_predict_detail_url()
