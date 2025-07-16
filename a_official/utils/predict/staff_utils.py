__all__ = [
    'AdminListContext', 'AdminDetailContext',
    'AdminDetailStatisticsContext', 'AdminDetailCatalogContext', 'AdminDetailAnswerContext',
    'AdminCreateData',
    'AdminUpdateAnswerOfficialContext', 'AdminUpdateScoreContext',
    'AdminUpdateRankContext', 'AdminUpdateStatisticsContext', 'AdminUpdateAnswerCountContext',
    'AdminExportExcelData',
]

from collections import defaultdict
from dataclasses import dataclass

import numpy as np
import pandas as pd
from django.db.models import Count, F, QuerySet
from scipy.stats import rankdata

from a_common.utils import HtmxHttpRequest, get_paginator_context
from a_common.utils.export_excel_methods import *
from a_common.utils.modify_models_methods import *
from a_official import models, forms
from a_official.utils.common_utils import RequestData, ModelData, ExamData, get_stat_from_scores

_model = ModelData()

UPDATE_MESSAGES = {
    'raw_score': get_update_messages('원점수'),
    'score': get_update_messages('표준점수'),
    'rank': get_update_messages('등수'),
    'statistics': get_update_messages('통계'),
    'answer_count': get_update_messages('문항분석표'),
}


@dataclass(kw_only=True)
class AdminListContext:
    _request: HtmxHttpRequest

    def __post_init__(self):
        request_data = RequestData(_request=self._request)
        self.view_type = request_data.view_type
        self.page_number = request_data.page_number

    def get_predict_exam_context(self):
        predict_exam_list = models.PredictExam.objects.select_related('exam')
        return get_paginator_context(predict_exam_list, self.page_number)


@dataclass(kw_only=True)
class AdminDetailContext:
    _request: HtmxHttpRequest
    _context: dict

    def __post_init__(self):
        self._exam = self._context['exam']
        self._subject_vars_dict = self._context['subject_vars_dict']
        self._qs_problem = _model.problem.objects.filtered_problem_by_exam(self._exam)

        self.answer = AdminDetailAnswerContext(_context=self._context)

    def get_problem_context(self):
        page_number = self._context['page_number']
        return {'problem_context': get_paginator_context(self._qs_problem, page_number)}

    def get_answer_predict_context(self):
        qs_answer_count = _model.ac_all.objects.filtered_by_exam_and_subject(self._exam)
        return {'answer_predict_context': self.get_answer_dict(qs_answer_count)}

    def get_answer_official_context(self):
        return {'answer_official_context': self.get_answer_dict(self._qs_problem)}

    def get_answer_dict(self, queryset: QuerySet) -> dict:
        subject_vars = self._subject_vars_dict['base']
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

    def get_admin_statistics_context(self) -> dict:
        exam = self._context['exam']
        subject_vars_sum_first = self._context['subject_vars_dict']['sum_first']
        qs_statistics = _model.statistics.objects.select_related('exam').filter(exam=exam).first()
        statistics_context = {}
        for sub, (subject, fld, field_idx, problem_count, _) in subject_vars_sum_first.items():
            statistics_context[sub] = getattr(qs_statistics, fld)
            statistics_context[sub]['sub'] = sub
            statistics_context[sub]['field'] = fld
            statistics_context[sub]['subject'] = subject

        return {'statistics_context': statistics_context}


@dataclass(kw_only=True)
class AdminDetailCatalogContext:
    _context: dict

    def get_admin_catalog_context(self, for_search=False) -> dict:
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
        return {'catalog_context': catalog_context}

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

    def get_admin_answer_context(self, for_pagination=False, per_page=10) -> dict:
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

        return {'answer_context': answer_context}

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
class AdminCreateData:
    _form: forms.PredictExamForm

    def __post_init__(self):
        year = self._form.cleaned_data['year']
        self._exam = _model.exam.objects.get(year=year)

    def process_post_request(self):
        self.create_predict_exam_model_instance()
        _model.statistics.objects.get_or_create(exam=self._exam)
        self.create_answer_count_model_instances()

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
    _exam: models.Exam

    def update_problem_model_for_answer_official(self) -> tuple[bool | None, str]:
        problem_model = _model.problem
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
                            problem = problem_model.objects.get(exam=self._exam, subject=subject[0:2], number=number)
                            if problem.answer != answer:
                                problem.answer = answer
                                list_update.append(problem)
                        except problem_model.DoesNotExist:
                            problem = problem_model(exam=self._exam, subject=subject, number=number, answer=answer)
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
        subject_vars = self._context['subject_vars_dict']['base']
        qs_student = _model.student.objects.filter(exam=self._context['exam']).order_by('id')
        score_model = _model.score
        answer_model = _model.answer
        list_create, list_update = [], []

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

        update_fields = [
            'subject_0', 'subject_1', 'subject_2', 'subject_3', 'subject_4', 'subject_5', 'subject_6', 'sum']
        return score_model, list_create, list_update, update_fields


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
        qs_student = _model.student.objects.filtered_student_by_exam(exam)

        list_create, list_update = [], []
        subject_fields_sum = [f'{fld}' for fld in subject_fields_sum]

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
                    if np.size(score_np_data_dict[fld]):
                        idx = np.where(score_np_data_dict[fld] == score)[0][0]
                        new_rank = int(ranks[fld][idx])
                        if hasattr(rank_obj, fld):
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

        score_dict = {}
        for field in subject_fields_sum:
            if field not in score_dict:
                score_dict[field] = []
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
        self._subject_vars_sum = self._context['subject_vars_dict']['sum_first']
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
        qs_score = (
            _model.score.objects.filter(student__exam=self._exam).order_by('student')
            .values(*self._subject_fields_sum)
        )
        score_df = pd.DataFrame(qs_score)
        participants_sum = min([score_df[score_df[f'subject_{fld_idx}'] >= 0].shape[0] for fld_idx in range(4)])

        data_statistics = {}
        for sub, (subject, fld, _, problem_count, _) in self._subject_vars_sum.items():
            participants = participants_sum if fld == 'sum' else score_df[score_df[fld] >= 0].shape[0]

            if participants:
                score_np = score_df[[fld]].to_numpy()
                if score_np.size > 0:
                    scores_stat = get_stat_from_scores(score_np)
                    data_statistics[fld] = dict(sub=sub, subject=subject, participants=participants, **scores_stat)
            else:
                data_statistics[fld] = dict(sub=sub, subject=subject, participants=0, max=0, t10=0,t25=0, t50=0, avg=0)

        return data_statistics


@dataclass(kw_only=True)
class AdminUpdateAnswerCountContext:
    _context: dict

    @with_update_message(UPDATE_MESSAGES['answer_count'])
    def update_answer_counts(self):
        return [
            self.update_answer_count_model(_model.ac_all),
            self.update_answer_count_model(_model.ac_top),
            self.update_answer_count_model(_model.ac_mid),
            self.update_answer_count_model(_model.ac_low),
        ]

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
            answers = {f'count_multiple': 0}
            for ans, cnt in answer_distribution.items():
                if ans <= 4:
                    answers[f'count_{ans}'] = cnt
                else:
                    answers[f'count_multiple'] = cnt
            answers[f'count_sum'] = sum(answers[fld] for fld in count_fields)

            try:
                instance = ac_model.objects.get(problem_id=problem_id)
                fields_not_match = any(getattr(instance, fld) != val for fld, val in answers.items())
                if fields_not_match:
                    for fld, val in answers.items():
                        setattr(instance, fld, val)
                    list_update.append(instance)
            except ac_model.DoesNotExist:
                list_create.append(ac_model(problem_id=problem_id, **answers))
        update_fields = [
            'problem_id', f'count_0', 'count_1', 'count_2', 'count_3', 'count_4',
            'count_multiple', 'count_sum',
        ]
        return ac_model, list_create, list_update, update_fields


@dataclass(kw_only=True)
class AdminExportExcelData:
    _exam: models.Exam

    def __post_init__(self):
        exam_data = ExamData(_exam=self._exam)

        self._subject_vars = exam_data.subject_vars
        self._subject_vars_avg = exam_data.subject_vars_sum
        self._sub_list = [sub for sub in self._subject_vars]

    def get_statistics_response(self) -> HttpResponse:
        qs_statistics = models.PredictStatistics.objects.filter(exam=self._exam).order_by('id')
        df = pd.DataFrame.from_records(qs_statistics.values())

        filename = f'{self._exam.full_reference}_성적통계.xlsx'
        drop_columns = ['id', 'exam_id']
        column_label = [('직렬', '')]

        subject_vars = self._subject_vars_avg
        subject_vars_total = subject_vars.copy()
        for sub, (subject, fld, idx, problem_count) in subject_vars.items():
            subject_vars_total[f'[필터링]{sub}'] = (f'[필터링]{subject}', f'filtered_{fld}', idx, problem_count)

        for (subject, fld, _, _) in subject_vars_total.values():
            drop_columns.append(fld)
            column_label.extend([
                (subject, '총 인원'), (subject, '최고'), (subject, '상위10%'), (subject, '상위20%'), (subject, '평균'),
            ])
            df_subject = pd.json_normalize(df[fld])
            df = pd.concat([df, df_subject], axis=1)

        df.drop(columns=drop_columns, inplace=True)
        df.columns = pd.MultiIndex.from_tuples(column_label)

        return get_response_for_excel_file(df, filename)

    def get_prime_id_response(self) -> HttpResponse:
        qs_student = models.PredictStudent.objects.filter(exam=self._exam).values(
            'id', 'created_at', 'name', 'prime_id').order_by('id')
        df = pd.DataFrame.from_records(qs_student)
        df['created_at'] = df['created_at'].dt.tz_convert('Asia/Seoul').dt.tz_localize(None)

        filename = f'{self._exam.full_reference}_참여자명단.xlsx'
        column_label = [('ID', ''), ('등록일시', ''), ('이름', ''), ('프라임법학원 ID', '')]
        df.columns = pd.MultiIndex.from_tuples(column_label)
        return get_response_for_excel_file(df, filename)

    def get_catalog_response(self) -> HttpResponse:
        total_student_list = models.PredictStudent.objects.filtered_student_by_exam(self._exam)
        filtered_student_list = total_student_list.filter(is_filtered=True)
        filename = f'{self._exam.full_reference}_성적일람표.xlsx'

        df1 = self.get_catalog_df_for_excel(total_student_list)
        df2 = self.get_catalog_df_for_excel(filtered_student_list, True)

        excel_data = io.BytesIO()
        with pd.ExcelWriter(excel_data, engine='openpyxl') as writer:
            df1.to_excel(writer, sheet_name='전체')
            df2.to_excel(writer, sheet_name='필터링')

        return get_response_for_excel_file(df1, filename, excel_data)

    def get_catalog_df_for_excel(self, student_list: QuerySet, is_filtered=False) -> pd.DataFrame:
        column_list = [
            'id', 'exam_id', 'category_id', 'user_id',
            'name', 'serial', 'password', 'is_filtered', 'prime_id', 'unit', 'department',
            'created_at', 'latest_answer_time', 'answer_count',
            'score_sum', 'rank_tot_num', 'rank_dep_num', 'filtered_rank_tot_num', 'filtered_rank_dep_num',
        ]
        for sub_type in ['0', '1', '2', '3', 'avg']:
            column_list.append(f'score_{sub_type}')
            for stat_type in ['rank', 'filtered_rank']:
                for dep_type in ['tot', 'dep']:
                    column_list.append(f'{stat_type}_{dep_type}_{sub_type}')
        df = pd.DataFrame.from_records(student_list.values(*column_list))
        df['created_at'] = df['created_at'].dt.tz_convert('Asia/Seoul').dt.tz_localize(None)
        df['latest_answer_time'] = df['latest_answer_time'].dt.tz_convert('Asia/Seoul').dt.tz_localize(None)

        field_list = ['num', '0', '1', '2', '3', 'avg']
        if is_filtered:
            for key in field_list:
                df[f'rank_tot_{key}'] = df[f'filtered_rank_tot_{key}']
                df[f'rank_dep_{key}'] = df[f'filtered_rank_dep_{key}']

        drop_columns = []
        for key in field_list:
            drop_columns.extend([f'filtered_rank_tot_{key}', f'filtered_rank_dep_{key}'])

        column_label = [
            ('DB정보', 'ID'), ('DB정보', 'PSAT ID'), ('DB정보', '카테고리 ID'), ('DB정보', '사용자 ID'),
            ('수험정보', '이름'), ('수험정보', '수험번호'), ('수험정보', '비밀번호'),
            ('수험정보', '필터링 여부'), ('수험정보', '프라임 ID'), ('수험정보', '모집단위'), ('수험정보', '직렬'),
            ('답안정보', '등록일시'), ('답안정보', '최종답안 등록일시'), ('답안정보', '제출 답안수'),
            ('성적정보', 'PSAT 총점'), ('성적정보', '전체 총 인원'), ('성적정보', '직렬 총 인원'),
        ]
        for sub in self._subject_vars_avg:
            column_label.extend([(sub, '점수'), (sub, '전체 등수'), (sub, '직렬 등수')])

        df.drop(columns=drop_columns, inplace=True)
        df.columns = pd.MultiIndex.from_tuples(column_label)

        return df

    def get_answer_response(self) -> HttpResponse:
        qs_answer_count = models.PredictAnswerCount.objects.filtered_by_exam_and_subject(self._exam)
        filename = f'{self._exam.full_reference}_문항분석표.xlsx'

        df1 = self.get_answer_df_for_excel(qs_answer_count)
        df2 = self.get_answer_df_for_excel(qs_answer_count, True)

        excel_data = io.BytesIO()
        with pd.ExcelWriter(excel_data, engine='openpyxl') as writer:
            df1.to_excel(writer, sheet_name='전체')
            df2.to_excel(writer, sheet_name='필터링')

        return get_response_for_excel_file(df1, filename, excel_data)

    @staticmethod
    def get_answer_df_for_excel(
            qs_answer_count: QuerySet[models.PredictAnswerCount], is_filtered=False) -> pd.DataFrame:
        prefix = 'filtered_' if is_filtered else ''
        column_list = ['id', 'problem_id', 'subject', 'number', 'ans_official', 'ans_predict']
        for rank_type in ['all', 'top', 'mid', 'low']:
            for num in ['1', '2', '3', '4', '5', 'sum']:
                column_list.append(f'{prefix}count_{num}_{rank_type}')

        column_label = [
            ('DB정보', 'ID'), ('DB정보', '문제 ID'),
            ('문제정보', '과목'), ('문제정보', '번호'), ('문제정보', '정답'), ('문제정보', '예상 정답'),
        ]
        for rank_type in ['전체', '상위권', '중위권', '하위권']:
            column_label.extend([
                (rank_type, '①'), (rank_type, '②'), (rank_type, '③'),
                (rank_type, '④'), (rank_type, '⑤'), (rank_type, '합계'),
            ])

        df = pd.DataFrame.from_records(qs_answer_count.values(*column_list))
        df.columns = pd.MultiIndex.from_tuples(column_label)
        return df
