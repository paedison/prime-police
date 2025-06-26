from collections import defaultdict
from dataclasses import dataclass

from a_common.utils import HtmxHttpRequest
from a_mock import models
from a_mock.utils.common_utils import *


@dataclass(kw_only=True)
class StudentAnswerData:
    request: HtmxHttpRequest
    student: models.Student

    def __post_init__(self):
        self.exam_data = ExamData(exam=self.student.exam)
        self.model = ModelData()

        self._subject_vars_sum = self.exam_data.subject_vars_sum
        self.qs_student_answer = self.model.answer.objects.mock_qs_answer_by_student_with_result(self.student)

    def get_stat_data(self):
        stat_data = self.get_empty_dict_stat_data()
        participants_dict = self.get_participants_dict()
        qs_score = self.model.score.objects.mock_qs_score_by_student(self.student)

        scores = {sub: [] for sub in self._subject_vars_sum}
        for sub, stat in stat_data.items():
            fld = stat['field']
            participants = participants_dict.get(sub, 0)
            stat['participants'] = participants
            for qs_s in qs_score:
                fld_score = qs_s[fld]
                if fld_score is not None:
                    scores[sub].append(fld_score)

            student_score = getattr(self.student.score, fld)
            if scores[sub] and student_score:
                sorted_scores = sorted(scores[sub], reverse=True)

                def get_top_score(_sorted_scores, percentage):
                    if _sorted_scores:
                        threshold = max(1, int(participants * percentage))
                        return _sorted_scores[threshold - 1]

                stat.update({
                    'score': student_score,
                    'rank': sorted_scores.index(student_score) + 1,
                    'max_score': sorted_scores[0],
                    'top_score_10': get_top_score(sorted_scores, 0.10),
                    'top_score_25': get_top_score(sorted_scores, 0.25),
                    'top_score_50': get_top_score(sorted_scores, 0.50),
                    'avg_score': round(sum(sorted_scores) / participants, 1),
                })

        return stat_data

    def get_empty_dict_stat_data(self):
        total_answer_count = 0
        stat_data = {}
        for sub, (subject, fld, fld_idx, problem_count) in self._subject_vars_sum.items():
            saved_answers = []
            answer_count = max(self.student.answer_count.get(fld, 0), len(saved_answers))
            total_answer_count += answer_count
            stat_data[sub] = {
                'field': fld, 'sub': sub, 'subject': subject,
                'participants': 0, 'problem_count': problem_count,
                'rank': 0, 'score': 0, 'max_score': 0,
                'top_score_10': 0, 'top_score_25': 0, 'top_score_50': 0, 'avg_score': 0,
            }
        return stat_data

    def get_participants_dict(self):
        qs_answer = self.model.answer.objects.mock_qs_answer_by_student(self.student)
        participants_dict = {qs_a['problem__subject']: qs_a['participant_count'] for qs_a in qs_answer}
        participants_dict['총점'] = participants_dict[min(participants_dict)] if participants_dict else 0
        return participants_dict


@dataclass(kw_only=True)
class ChartData:
    stat_data_total: dict
    student: models.Student | None

    def __post_init__(self):
        exam_data = ExamData(exam=self.student.exam)

        self._subject_vars_sum = exam_data.subject_vars_sum
        self._subject_vars = exam_data.subject_vars
        self._student_score_list = self.get_student_score_list()

    def get_student_score_list(self):
        if self.student:
            return [getattr(self.student.score, fld) for (_, fld, _, _) in self._subject_vars_sum.values()]

    def get_dict_stat_chart(self) -> dict:
        chart_score = {
            'avg': [], 'top_50': [], 'top_25': [], 'top_10': [], 'max': [],
        }
        if self.student:
            chart_score['my_score'] = self._student_score_list

        for stat in self.stat_data_total.values():
            chart_score['avg'].append(stat['avg_score'])
            chart_score['top_10'].append(stat['top_score_10'])
            chart_score['top_25'].append(stat['top_score_25'])
            chart_score['top_50'].append(stat['top_score_50'])
            chart_score['max'].append(stat['max_score'])

        score_list = [score for score in self._student_score_list if score is not None]
        chart_score['min_score'] = (min(score_list) // 5) * 5 if score_list else 0
        return chart_score

    def get_dict_stat_frequency(self) -> dict:
        score_frequency_list = models.Student.objects.values_list('score__sum', flat=True)
        scores = [round(score, 1) for score in score_frequency_list]
        sorted_freq, target_bin = self.frequency_table_by_bin(scores)

        score_label, score_data, score_color = [], [], []
        for key, val in sorted_freq.items():
            score_label.append(key)
            score_data.append(val)
            color = 'rgba(255, 99, 132, 0.5)' if key == target_bin else 'rgba(54, 162, 235, 0.5)'
            score_color.append(color)

        return {'score_data': score_data, 'score_label': score_label, 'score_color': score_color}

    def frequency_table_by_bin(self, scores: list, bin_size: int = 10) -> tuple[dict, str | None]:
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
        if self.student and self.student.score.sum:  # noqa
            bin_start = int((self.student.score.sum // bin_size) * bin_size)  # noqa
            bin_end = bin_start + bin_size
            target_bin = f'{bin_start}~{bin_end}'

        return sorted_freq, target_bin


@dataclass(kw_only=True)
class ResultDetailData:
    request: HtmxHttpRequest
    student: models.Student

    def __post_init__(self):
        request_data = RequestData(request=self.request)
        exam_data = ExamData(exam=self.student.exam)

        self._subject_vars = exam_data.subject_vars
        self._answer_data = StudentAnswerData(request=self.request, student=self.student)
        self._qs_student_answer = self._answer_data.qs_student_answer

        self.view_type = request_data.view_type
        self.stat_data = self._answer_data.get_stat_data()
        self.chart_data = ChartData(stat_data_total=self.stat_data, student=self.student)

    def get_stat_data_context(self) -> dict:
        return {'stat_data': self.stat_data}

    def get_answer_context(self) -> dict:
        subject_vars = self._subject_vars
        answer_context = {
            sub: {
                'id': str(idx), 'title': sub, 'subject': subject, 'field': fld,
                'loop_list': self.get_loop_list(problem_count),
                'page_obj': [],
            }
            for sub, (subject, fld, idx, problem_count) in subject_vars.items()
        }

        for line in self._qs_student_answer:
            sub = line.problem.subject
            ans_official = line.problem.answer
            ans_student = line.answer

            line.no = line.problem.number
            line.ans_official = ans_official
            line.ans_official_circle = line.problem.get_answer_display()

            line.ans_student = ans_student
            line.ans_student_circle = line.get_answer_display()
            line.field = subject_vars[sub][1]

            line.rate_correct = line.problem.answer_count.get_answer_rate(ans_official)
            line.rate_correct_top = line.problem.answer_count_top_rank.get_answer_rate(ans_official)
            line.rate_correct_mid = line.problem.answer_count_mid_rank.get_answer_rate(ans_official)
            line.rate_correct_low = line.problem.answer_count_low_rank.get_answer_rate(ans_official)
            if line.rate_correct_top is not None and line.rate_correct_low is not None:
                line.rate_gap = line.rate_correct_top - line.rate_correct_low
            else:
                line.rate_gap = 0

            line.rate_selection = line.problem.answer_count.get_answer_rate(ans_student)
            line.rate_selection_top = line.problem.answer_count_top_rank.get_answer_rate(ans_student)
            line.rate_selection_mid = line.problem.answer_count_mid_rank.get_answer_rate(ans_student)
            line.rate_selection_low = line.problem.answer_count_low_rank.get_answer_rate(ans_student)

            answer_context[sub]['page_obj'].append(line)
        return {'answer_context': answer_context}

    @staticmethod
    def get_loop_list(problem_count):
        loop_list = []
        quotient = problem_count // 10
        counter = [10] * quotient
        remainder = problem_count % 10
        if remainder:
            counter.append(remainder)
        loop_min = 0
        for loop_idx in range(quotient):
            loop_list.append({'counter': counter[loop_idx], 'min': loop_min})
            loop_min += 10
        return loop_list
