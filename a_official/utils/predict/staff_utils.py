__all__ = [
    'AdminListContext', 'AdminDetailProblemContext',
    'AdminDetailStatisticsContext', 'AdminDetailCatalogContext', 'AdminDetailAnswerContext',
    'AdminCreateContext',
    'AdminUpdateAnswerOfficialContext', 'AdminUpdateScoreContext',
    'AdminUpdateRankContext', 'AdminUpdateStatisticsContext', 'AdminUpdateAnswerCountContext',
    'AdminExportExcelContext',
]

from collections import defaultdict
from dataclasses import dataclass

import numpy as np
import pandas as pd
from django.db.models import Count, F, QuerySet
from django.shortcuts import redirect
from scipy.stats import rankdata

from a_common.utils import HtmxHttpRequest, get_paginator_context
from a_common.utils.export_excel_methods import *
from a_common.utils.modify_models_methods import *
from a_official import models, forms
from a_official.utils.common_utils import *

_model = ModelData()

UPDATE_MESSAGES = {
    'raw_score': get_update_messages('원점수'),
    'score': get_update_messages('점수'),
    'rank': get_update_messages('등수'),
    'statistics': get_update_messages('통계'),
    'answer_count': get_update_messages('문항분석표'),
}


@dataclass(kw_only=True)
class AdminListContext:
    _request: HtmxHttpRequest

    def __post_init__(self):
        request_context = RequestContext(_request=self._request)
        self.view_type = request_context.view_type
        self.page_number = request_context.page_number

    def get_predict_exam_context(self):
        predict_exam_list = models.PredictExam.objects.select_related('exam')
        return get_paginator_context(predict_exam_list, self.page_number)


@dataclass(kw_only=True)
class AdminDetailProblemContext:
    _request: HtmxHttpRequest
    _context: dict

    def get_problem_context(self):
        return get_paginator_context(self._context['qs_problem'], self._context['page_number'])

    def get_answer_predict_context(self):
        return self.get_answer_dict(self._context['qs_answer_count'])

    def get_answer_official_context(self):
        return self.get_answer_dict(self._context['qs_problem'])

    def get_answer_dict(self, queryset: QuerySet) -> dict:
        subject_vars = self._context['subject_vars_dict']['base']
        query_dict = defaultdict(list)
        for query in queryset.order_by('id'):
            query_dict[query.subject].append(query)
        return {
            sub: {'id': str(idx), 'title': sub, 'page_obj': query_dict[sub]}
            for sub, (_, _, idx, _, _) in subject_vars.items()
        }


@dataclass(kw_only=True)
class AdminDetailStatisticsContext:
    _context: dict

    def get_statistics_context(self) -> dict:
        exam = self._context['exam']
        subject_vars_sum_first = self._context['subject_vars_dict']['sum_first']
        qs_statistics = _model.statistics.objects.select_related('exam').filter(exam=exam).first()
        statistics_context = {}
        for sub, (subject, fld, field_idx, problem_count, _) in subject_vars_sum_first.items():
            statistics_context[sub] = getattr(qs_statistics, fld)
            statistics_context[sub]['sub'] = sub
            statistics_context[sub]['field'] = fld
            statistics_context[sub]['subject'] = subject

        return statistics_context


@dataclass(kw_only=True)
class AdminDetailCatalogContext:
    _context: dict

    def get_catalog_context(self, for_search=False) -> dict:
        exam = self._context['exam']
        page_number = self._context['page_number']
        student_name = self._context['student_name']

        qs_student = _model.student.objects.filtered_student_by_exam(exam)
        if for_search:
            qs_student = qs_student.filter(name=student_name)
        catalog_context = get_paginator_context(qs_student, page_number)

        if catalog_context['page_obj']:
            for obj in catalog_context['page_obj']:
                self.update_page_obj(obj)

        catalog_context.update({'id': '0', 'title': '전체', 'prefix': 'Catalog', 'header': 'catalog_list'})
        return catalog_context

    def update_page_obj(self, obj):
        rank_model = _model.rank
        subject_fields_sum_first = self._context['subject_vars_dict']['sum_first']

        def get_rank_info(target_student, field: str):
            rank_info = {}
            rank = ratio = None
            target_rank = getattr(target_student, 'rank', None)
            if target_rank:
                rank = getattr(target_rank, field)
                participants = getattr(target_rank, 'participants')
                if rank and participants:
                    ratio = round(rank * 100 / participants, 1)
            rank_info[rank_model] = {'integer': rank, 'ratio': ratio}
            return rank_info

        if hasattr(obj, 'rank'):
            obj.members = {'participants': obj.rank.sum}
        if hasattr(obj, 'score'):
            obj.stat_data = {
                fld: {
                    'score': getattr(obj.score, fld, ''),
                    'rank_info': get_rank_info(obj, fld),
                } for (_, fld, _, _, _) in subject_fields_sum_first.values()
            }


@dataclass(kw_only=True)
class AdminDetailAnswerContext:
    _context: dict

    def get_answer_context(self, for_pagination=False, per_page=10) -> dict:
        subject_vars = self._context['subject_vars_dict']['base']
        sub_list = [sub for sub in subject_vars]
        qs_answer_count_group = {sub: [] for sub in subject_vars}
        answer_context = {}

        subject = self._context['exam_subject'] if for_pagination else None
        qs_answer_count = _model.ac_all.objects.filtered_by_exam_and_subject(self._context['exam'], subject)
        for qs_ac in qs_answer_count:
            sub = qs_ac.subject
            if sub not in qs_answer_count_group:
                qs_answer_count_group[sub] = []
            qs_answer_count_group[sub].append(qs_ac)

        for sub, qs_answer_count in qs_answer_count_group.items():
            if qs_answer_count:
                data_answers = self.get_answer_data(qs_answer_count)
                context = get_paginator_context(data_answers, self._context['page_number'], per_page)
                context.update({
                    'id': str(sub_list.index(sub)),
                    'title': sub,
                    'prefix': 'Answer',
                    'header': 'answer_list',
                    'answer_count': 4,
                })
                answer_context[sub] = context

        return answer_context

    def get_answer_data(self, qs_answer_count: QuerySet) -> QuerySet:
        subject_vars = self._context['subject_vars_dict']['base']
        for qs_ac in qs_answer_count:
            sub = qs_ac.subject
            field = subject_vars[sub][1]
            ans_official = qs_ac.ans_official

            answer_official_list = []
            if ans_official > 5:
                answer_official_list = [int(digit) for digit in str(ans_official)]

            qs_ac.no = qs_ac.number
            qs_ac.ans_official = ans_official
            qs_ac.ans_official_circle = qs_ac.problem.get_answer_display()
            qs_ac.ans_predict_circle = models.choices.answer_choice()[qs_ac.ans_predict] if qs_ac.ans_predict else None
            qs_ac.ans_list = answer_official_list
            qs_ac.field = field

            qs_ac.rate_correct = qs_ac.get_answer_rate(ans_official)
            qs_ac.rate_correct_top = qs_ac.problem.predict_answer_count_top_rank.get_answer_rate(ans_official)
            qs_ac.rate_correct_mid = qs_ac.problem.predict_answer_count_mid_rank.get_answer_rate(ans_official)
            qs_ac.rate_correct_low = qs_ac.problem.predict_answer_count_low_rank.get_answer_rate(ans_official)
            try:
                qs_ac.rate_gap = qs_ac.rate_correct_top - qs_ac.rate_correct_low
            except TypeError:
                qs_ac.rate_gap = None

        return qs_answer_count


@dataclass(kw_only=True)
class AdminCreateContext:
    _context: dict

    def __post_init__(self):
        self._form = self._context['form']
        self._exam = _model.exam.objects.get(year=self._form.cleaned_data['year'])

    def process_post_request(self):
        self.create_predict_exam_model_instance()
        _model.statistics.objects.get_or_create(exam=self._exam)
        self.create_answer_count_model_instances()
        return redirect(self._context['config'].url_list)

    def create_predict_exam_model_instance(self):
        predict_exam, _ = _model.predict_exam.objects.get_or_create(exam=self._exam)
        predict_exam.is_active = True
        predict_exam.page_opened_at = self._form.cleaned_data['page_opened_at']
        predict_exam.exam_started_at = self._form.cleaned_data['exam_started_at']
        predict_exam.exam_finished_at = self._form.cleaned_data['exam_finished_at']
        predict_exam.answer_predict_opened_at = self._form.cleaned_data['answer_predict_opened_at']
        predict_exam.answer_official_opened_at = self._form.cleaned_data['answer_official_opened_at']
        predict_exam.predict_closed_at = self._form.cleaned_data['predict_closed_at']
        predict_exam.save()

    def create_answer_count_model_instances(self) -> None:
        problems = _model.problem.objects.filter(exam=self._exam).order_by('id')
        for model in _model.ac_model_set.values():
            list_create = []
            for problem in problems:
                append_list_create(model, list_create, problem=problem)
            bulk_create_or_update(model, list_create, [], [])


@dataclass(kw_only=True)
class AdminUpdateAnswerOfficialContext:
    _request: HtmxHttpRequest
    _context: dict

    def update_problem_model_for_answer_official(self) -> tuple[bool | None, str]:
        problem_model = _model.problem
        exam = self._context['exam']
        message_dict = {
            None: '에러가 발생했습니다.',
            True: '정답을 업데이트했습니다.',
            False: '기존 정답과 일치합니다.',
        }
        list_create, list_update = [], []

        form = forms.UploadFileForm(self._request.POST, self._request.FILES)
        file = self._request.FILES.get('file')

        if form.is_valid():
            df = pd.read_excel(file, header=0, index_col=0)
            df = df.infer_objects(copy=False)
            df.fillna(value=0, inplace=True)

            for subject, rows in df.items():
                for number, answer in rows.items():
                    if answer:
                        try:
                            problem = problem_model.objects.get(exam=exam, subject=subject[0:2], number=number)
                            if problem.answer != answer:
                                problem.answer = answer
                                list_update.append(problem)
                        except problem_model.DoesNotExist:
                            problem = problem_model(exam=exam, subject=subject, number=number, answer=answer)
                            list_create.append(problem)
                        except ValueError as error:
                            print(error)
            update_fields = ['answer']
            is_updated = bulk_create_or_update(problem_model, list_create, list_update, update_fields)
        else:
            is_updated = None
            print(form)
        return is_updated, message_dict[is_updated]


@dataclass(kw_only=True)
class AdminUpdateScoreContext:
    _context: dict

    @with_update_message(UPDATE_MESSAGES['score'])
    def update_scores(self):
        return [self.update_score_model()]

    @with_bulk_create_or_update()
    def update_score_model(self):
        exam = self._context['exam']
        subject_vars = self._context['subject_vars_dict']['base']
        subject_fields_sum = self._context['subject_fields_dict']['sum_first']

        score_model = _model.score
        answer_model = _model.answer

        list_create, list_update = [], []
        qs_student = _model.student.objects.filter(exam=exam).order_by('id')
        for qs_s in qs_student:
            original_score_instance, _ = score_model.objects.get_or_create(student=qs_s)

            score_dict = {}
            fields_not_match = []
            for sub, (_, fld, field_idx, _, score_per_problem) in subject_vars.items():
                qs_answer = (
                    answer_model.objects.filter(student=qs_s, problem__subject=sub)
                    .annotate(answer_correct=F('problem__answer'), answer_student=F('answer'))
                )
                if qs_answer:
                    correct_count = 0
                    for entry in qs_answer:
                        answer_correct_list = [int(digit) for digit in str(entry.answer_correct)]
                        correct_count += 1 if entry.answer_student in answer_correct_list else 0
                    sco = correct_count * score_per_problem
                    score_dict[fld] = sco
                    fields_not_match.append(getattr(original_score_instance, fld) != sco)

            score_sum = sum([sco for sco in score_dict.values() if sco is not None])
            fields_not_match.append(original_score_instance.sum != score_sum)

            if any(fields_not_match):
                for fld, score in score_dict.items():
                    setattr(original_score_instance, fld, score)
                original_score_instance.sum = score_sum
                list_update.append(original_score_instance)

        return score_model, list_create, list_update, subject_fields_sum


@dataclass(kw_only=True)
class AdminUpdateRankContext:
    _context: dict

    @with_update_message(UPDATE_MESSAGES['rank'])
    def update_ranks(self):
        return [self.update_rank_model()]

    @with_bulk_create_or_update()
    def update_rank_model(self):
        exam = self._context['exam']
        subject_fields_sum = self._context['subject_fields_dict']['sum_first']

        rank_model = _model.rank
        qs_rank = rank_model.objects.filter(student__exam=exam)
        qs_rank_dict = {qs_r.student: qs_r for qs_r in qs_rank}

        list_create, list_update = [], []

        qs_student = _model.student.objects.filtered_student_by_exam(exam)
        score_np_data_dict = self.get_score_np_data_dict_for_rank(qs_student)
        for qs_s in qs_student:
            rank_obj_exists = True
            rank_obj = qs_rank_dict.get(qs_s)
            if rank_obj is None:
                rank_obj_exists = False
                rank_obj = rank_model(student=qs_s)

            def set_rank_obj_field(target_list):
                ranks = {
                    fld: rankdata(-score_np_data_dict[fld], method='min') for fld in subject_fields_sum
                }  # 높은 점수가 1등
                participants = len(score_np_data_dict['sum'])

                need_to_append = False
                for fld in subject_fields_sum:
                    score = getattr(qs_s.score, fld)
                    if hasattr(rank_obj, fld) and np.size(score_np_data_dict[fld]) and score:
                        idx = np.where(score_np_data_dict[fld] == score)[0][0]
                        new_rank = int(ranks[fld][idx])
                        if getattr(rank_obj, fld) != new_rank or getattr(rank_obj, 'participants') != participants:
                            need_to_append = True
                            setattr(rank_obj, fld, new_rank)
                            setattr(rank_obj, 'participants', participants)
                if need_to_append:
                    target_list.append(rank_obj)

            def set_rank_obj_field_to_null(target_list):
                need_to_append = False
                for fld in subject_fields_sum:
                    if hasattr(rank_obj, fld):
                        if getattr(rank_obj, fld) is not None or rank_obj.participants is not None:
                            need_to_append = True
                            setattr(rank_obj, fld, None)
                            rank_obj.participants = None
                if need_to_append:
                    target_list.append(rank_obj)

            if rank_obj_exists:
                if score_np_data_dict:
                    set_rank_obj_field(list_update)
                else:
                    set_rank_obj_field_to_null(list_update)
            else:
                if score_np_data_dict:
                    set_rank_obj_field(list_create)
                else:
                    set_rank_obj_field_to_null(list_create)

        update_fields = subject_fields_sum + ['participants']
        return rank_model, list_create, list_update, update_fields

    def get_score_np_data_dict_for_rank(self, qs_student) -> dict[str: np.array]:
        subject_fields_sum = self._context['subject_fields_dict']['sum_first']

        score_dict = {fld: [] for fld in subject_fields_sum}
        for field in subject_fields_sum:
            for qs_s in qs_student:
                score = getattr(qs_s.score, field)
                if score is not None:
                    score_dict[field].append(score)

        score_np_data_dict = {}
        for fld, score_list in score_dict.items():
            score_np_data_dict[fld] = np.array(score_list)

        return score_np_data_dict


@dataclass(kw_only=True)
class AdminUpdateStatisticsContext:
    _context: dict

    def __post_init__(self):
        self._exam = self._context['exam']
        self._subject_fields_sum = self._context['subject_fields_dict']['sum_first']

    @with_update_message(UPDATE_MESSAGES['statistics'])
    def update_statistics(self):
        return [self.update_statistics_model()]

    @with_bulk_create_or_update()
    def update_statistics_model(self):
        statistics_model = _model.statistics
        list_update = []
        list_create = []

        data_statistics = self.get_data_statistics()
        try:
            new_query = statistics_model.objects.get(exam=self._exam)
            fields_not_match = any(getattr(new_query, fld) != val for fld, val in data_statistics.items())
            if fields_not_match:
                for fld, val in data_statistics.items():
                    setattr(new_query, fld, val)
                list_update.append(new_query)
        except statistics_model.DoesNotExist:
            list_create.append(statistics_model(psat=self._exam, **data_statistics))
        return statistics_model, list_create, list_update, self._subject_fields_sum

    def get_data_statistics(self) -> dict:
        subject_vars_sum = self._context['subject_vars_dict']['sum_first']
        qs_score = (
            _model.score.objects.filter(student__exam=self._exam).order_by('student')
            .values(*self._subject_fields_sum)
        )

        df = pd.DataFrame(qs_score)
        df_dict = {fld: df[df[fld] != 0][[fld]].dropna() for fld in self._subject_fields_sum}

        participants_sum = min(
            participants for fld_idx in range(7)
            if (participants := df_dict[f'subject_{fld_idx}'].shape[0])
        )

        data_statistics = {}
        for sub, (subject, fld, _, problem_count, _) in subject_vars_sum.items():
            df_fld = df_dict[fld]
            participants = participants_sum if fld == 'sum' else df_fld.shape[0]

            scores_stat = dict(max=0, t10=0, t25=0, t50=0, avg=0)
            if participants:
                score_np = df_fld.to_numpy()
                if score_np.size > 0:
                    scores_stat = get_stat_from_scores(score_np)
            data_statistics[fld] = dict(sub=sub, subject=subject, participants=participants, **scores_stat)

        return data_statistics


@dataclass(kw_only=True)
class AdminUpdateAnswerCountContext:
    _context: dict

    @with_update_message(UPDATE_MESSAGES['answer_count'])
    def update_answer_counts(self):
        return [self.update_answer_count_model(model) for model in _model.ac_model_set.values()]

    @with_bulk_create_or_update()
    def update_answer_count_model(self, ac_model):
        list_update = []
        list_create = []

        lookup_field = 'student__rank__sum'
        top_rank_threshold = 0.27
        mid_rank_threshold = 0.73
        participants_function = F(f'student__rank__participants')

        lookup_exp = {}
        if ac_model == _model.ac_top:
            lookup_exp[f'{lookup_field}__lte'] = participants_function * top_rank_threshold
        elif ac_model == _model.ac_mid:
            lookup_exp[f'{lookup_field}__gt'] = participants_function * top_rank_threshold
            lookup_exp[f'{lookup_field}__lte'] = participants_function * mid_rank_threshold
        elif ac_model == _model.ac_low:
            lookup_exp[f'{lookup_field}__gt'] = participants_function * mid_rank_threshold

        qs_answer = (
            _model.answer.objects.filter(problem__exam=self._context['exam'], **lookup_exp)
            .select_related('student', 'student__rank')
            .values('problem_id', 'answer')
            .annotate(count=Count('id')).order_by('problem_id', 'answer')
        )
        answer_distribution_dict = defaultdict(lambda: {i: 0 for i in range(5)})
        for qs_a in qs_answer:
            problem_id = qs_a['problem_id']
            answer = qs_a['answer']
            count = qs_a['count']
            answer_distribution_dict[problem_id][answer] = count

        count_fields = ['count_0', 'count_1', 'count_2', 'count_3', 'count_4', 'count_multiple']
        for problem_id, answer_distribution in answer_distribution_dict.items():
            answers = {'count_multiple': 0}
            for ans, cnt in answer_distribution.items():
                if ans <= 4:
                    answers[f'count_{ans}'] = cnt
                else:
                    answers['count_multiple'] = cnt
            answers['count_sum'] = sum(answers[fld] for fld in count_fields)

            try:
                instance = ac_model.objects.get(problem_id=problem_id)
                fields_not_match = any(getattr(instance, fld) != val for fld, val in answers.items())
                if fields_not_match:
                    for fld, val in answers.items():
                        setattr(instance, fld, val)
                    list_update.append(instance)
            except ac_model.DoesNotExist:
                list_create.append(ac_model(problem_id=problem_id, **answers))

        update_fields = count_fields + ['count_sum']
        return ac_model, list_create, list_update, update_fields


@dataclass(kw_only=True)
class AdminExportExcelContext:
    _exam: models.Exam

    def __post_init__(self):
        self._subject_variants = SubjectVariants(_selection='')
        self._subject_vars_sum = self._subject_variants.subject_vars_sum
        self._subject_vars_sum_first = self._subject_variants.subject_vars_sum_first

    def get_admin_statistics_context(self) -> dict:
        exam = self._exam
        qs_statistics = _model.statistics.objects.select_related('exam').filter(exam=exam).first()
        statistics_context = {}
        for sub, (subject, fld, field_idx, problem_count, _) in self._subject_vars_sum_first.items():
            statistics_context[sub] = getattr(qs_statistics, fld)
            statistics_context[sub]['sub'] = sub
            statistics_context[sub]['field'] = fld
            statistics_context[sub]['subject'] = subject

        return statistics_context

    def get_statistics_response(self) -> HttpResponse:
        statistics_context = self.get_admin_statistics_context()
        df = pd.DataFrame(statistics_context)
        df = df.T

        df.drop(columns=['sub', 'field'], inplace=True)
        df.columns = ['과목', '총 인원', '최고', '상위10%', '상위25%', '상위50%', '평균']
        df = df.reset_index(drop=True)
        df = df.set_index('과목')

        filename = f'{self._exam.full_reference}_성적통계.xlsx'
        return get_response_for_excel_file(df, filename)

    def get_catalog_response(self) -> HttpResponse:
        student_list = models.PredictStudent.objects.filtered_student_by_exam(self._exam)
        filename = f'{self._exam.full_reference}_성적일람표.xlsx'
        df = self.get_catalog_df_for_excel(student_list)
        return get_response_for_excel_file(df, filename)

    def get_catalog_df_for_excel(self, student_list: QuerySet) -> pd.DataFrame:
        column_list = [
            'id', 'exam_id', 'user_id',
            'name', 'serial', 'password',
            'created_at', 'latest_answer_time', 'answer_count', 'participants',
        ]
        for sub_type in ['sum', '0', '1', '2', '3', '4', '5', '6']:
            column_list.append(f'score_{sub_type}')
            column_list.append(f'rank_{sub_type}')
        df = pd.DataFrame.from_records(student_list.values(*column_list))
        df['created_at'] = df['created_at'].dt.tz_convert('Asia/Seoul').dt.tz_localize(None)
        df['latest_answer_time'] = df['latest_answer_time'].dt.tz_convert('Asia/Seoul').dt.tz_localize(None)

        drop_columns = []
        column_label = [
            ('DB정보', 'ID'), ('DB정보', '시험ID'), ('DB정보', '사용자 ID'),
            ('수험정보', '이름'), ('수험정보', '수험번호'), ('수험정보', '비밀번호'),
            ('답안정보', '등록일시'), ('답안정보', '최종답안 등록일시'), ('답안정보', '제출 답안수'), ('답안정보', '총 인원'),
        ]
        for (subject, _, _, _, _) in self._subject_vars_sum_first.values():
            column_label.extend([(subject, '점수')])
            column_label.extend([(subject, '등수')])

        df.drop(columns=drop_columns, inplace=True)
        df.columns = pd.MultiIndex.from_tuples(column_label)

        return df

    def get_answer_response(self) -> HttpResponse:
        qs_answer_count = models.PredictAnswerCount.objects.filtered_by_exam_and_subject(self._exam)
        filename = f'{self._exam.full_reference}_문항분석표.xlsx'
        df = self.get_answer_df_for_excel(qs_answer_count)
        return get_response_for_excel_file(df, filename)

    @staticmethod
    def get_answer_df_for_excel(
            qs_answer_count: QuerySet[models.PredictAnswerCount]) -> pd.DataFrame:
        column_list = ['id', 'problem_id', 'subject', 'number', 'ans_official', 'ans_predict']
        for rank_type in ['all', 'top', 'mid', 'low']:
            for num in ['1', '2', '3', '4', 'sum']:
                column_list.append(f'count_{num}_{rank_type}')

        column_label = [
            ('DB정보', 'ID'), ('DB정보', '문제 ID'),
            ('문제정보', '과목'), ('문제정보', '번호'), ('문제정보', '정답'), ('문제정보', '예상 정답'),
        ]
        for rank_type in ['전체', '상위권', '중위권', '하위권']:
            column_label.extend([
                (rank_type, '①'), (rank_type, '②'), (rank_type, '③'), (rank_type, '④'), (rank_type, '합계'),
            ])
        df = pd.DataFrame.from_records(qs_answer_count.values(*column_list))
        df.columns = pd.MultiIndex.from_tuples(column_label)
        return df
