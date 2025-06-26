from django.apps import apps
from django.db import models


class ExamQuerySet(models.QuerySet):
    def mock_qs_exam_list(self):
        return self.select_related('statistics').order_by('-year')


class ProblemQuerySet(models.QuerySet):
    def get_qs_problem(self, **kwargs):
        return self.filter(**kwargs).order_by('subject', 'number')


class StatisticsQuerySet(models.QuerySet):
    pass


class StudentQuerySet(models.QuerySet):
    def with_select_related(self):
        return self.select_related('exam', 'score', 'rank')

    @staticmethod
    def get_annotate_dict_for_score_and_rank():
        annotate_dict = {'rank_num': models.F(f'rank__participants')}
        field_dict = {0: 'subject_0', 1: 'subject_1', 2: 'subject_2', 3: 'subject_3', 4: 'subject_4', 'sum': 'sum'}
        for key, fld in field_dict.items():
            annotate_dict[f'score_{key}'] = models.F(f'score__{fld}')
            annotate_dict[f'rank_{key}'] = models.F(f'rank__{fld}')
        return annotate_dict

    @staticmethod
    def get_answer_count(student):
        answer_count_model = apps.get_model('a_mock', 'Answer')
        return answer_count_model.objects.filter(student=student).aggregate(
            subject_0=models.Count('id', filter=models.Q(problem__subject='형사')),
            subject_1=models.Count('id', filter=models.Q(problem__subject='헌법')),
            subject_2=models.Count('id', filter=models.Q(problem__subject='경찰')),
            subject_3=models.Count('id', filter=models.Q(problem__subject='범죄')),
            subject_4=models.Count('id', filter=models.Q(problem__subject='민법')),
        )

    def mock_qs_student_list(self, **kwargs):
        annotate_dict = self.get_annotate_dict_for_score_and_rank()
        return (
            self.with_select_related().filter(**kwargs).order_by('-id')
            .annotate(answer_count=models.Count('answers'), **annotate_dict)
        )

    def mock_qs_student_list_by_exam(self, exam):
        annotate_dict = self.get_annotate_dict_for_score_and_rank()
        return (
            self.with_select_related().filter(exam=exam)
            .annotate(**annotate_dict).order_by('rank_sum')
        )

    def mock_student_with_answer_count(self, **kwargs):
        annotate_dict = self.get_annotate_dict_for_score_and_rank()
        student = (
            self.with_select_related().filter(**kwargs).prefetch_related('answers')
            .annotate(**annotate_dict).first()
        )
        if student:
            student.answer_count = self.get_answer_count(student)
        return student


class AnswerQuerySet(models.QuerySet):
    def mock_qs_answer_by_student_with_result(self, student):
        return self.filter(student=student).annotate(
            subject=models.F('problem__subject'),
            result=models.Case(
                models.When(answer=models.F('problem__answer'), then=models.Value(True)),
                default=models.Value(False),
                output_field=models.BooleanField(),
            ),
        ).select_related(
            'problem',
            'problem__answer_count',
            'problem__answer_count_top_rank',
            'problem__answer_count_mid_rank',
            'problem__answer_count_low_rank',
        )

    def mock_qs_answer_by_student(self, student):
        qs_answer = (
            self.filter(problem__exam=student.exam).values('problem__subject')
            .annotate(participant_count=models.Count('student_id', distinct=True))
        )
        return qs_answer

    def mock_qs_answer_with_sub_number(self, student):
        return (
            self.filter(student=student)
            .annotate(sub=models.F('problem__subject'), number=models.F('problem__number'))
            .order_by('sub', 'number')
        )

    def filtered_by_psat_student(self, student):
        fields = [
            'problem',
            'problem__predict_answer_count',
            'problem__predict_answer_count_top_rank',
            'problem__predict_answer_count_mid_rank',
            'problem__predict_answer_count_low_rank'
        ]
        result = models.Case(
            models.When(answer=models.F('problem__answer'), then=models.Value(True)),
            default=models.Value(False),
            output_field=models.BooleanField()
        )
        predict_result = models.Case(
            models.When(
                answer=models.F('problem__predict_answer_count__answer_predict'), then=models.Value(True)),
            default=models.Value(False),
            output_field=models.BooleanField()
        )
        return (
            self.select_related(*fields).filter(student=student)
            .annotate(subject=models.F('problem__subject'), result=result, predict_result=predict_result)
        )


class AnswerCountQuerySet(models.QuerySet):
    def mock_qs_answer_count_by_exam_and_subject(self, exam, subject=None):
        annotate_dict = {
            'subject': models.F('problem__subject'),
            'number': models.F('problem__number'),
            'ans_predict': models.F(f'problem__answer_count__answer_predict'),
            'ans_official': models.F('problem__answer'),
        }
        for rank in ['all', 'top', 'mid', 'low']:
            for fld in ['count_1', 'count_2', 'count_3', 'count_4', 'count_sum']:
                if rank == 'all':
                    f_expr = f'{fld}'
                else:
                    f_expr = f'problem__answer_count_{rank}_rank__{fld}'
                annotate_dict[f'{fld}_{rank}'] = models.F(f_expr)
        qs_answer_count = (
            self.filter(problem__exam=exam)
            .order_by('problem__subject', 'problem__number').annotate(**annotate_dict)
            .select_related(
                f'problem',
                f'problem__answer_count_top_rank',
                f'problem__answer_count_mid_rank',
                f'problem__answer_count_low_rank',
            )
        )
        if subject:
            qs_answer_count = qs_answer_count.filter(subject=subject)
        return qs_answer_count

    def mock_qs_answer_count_by_exam(self, exam):
        return self.filter(problem__exam=exam).annotate(
            no=models.F('problem__number'), sub=models.F('problem__subject'), ans=models.F('answer_predict'),
            ans_official=models.F('problem__answer')).order_by('sub', 'no')


class ScoreQuerySet(models.QuerySet):
    def mock_qs_score_by_student(self, student):
        qs_score = self.filter(student__exam=student.exam)
        return qs_score.values()


class RankQuerySet(models.QuerySet):
    pass
