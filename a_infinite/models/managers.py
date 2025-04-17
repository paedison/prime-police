from django.apps import apps
from django.db import models


class ExamManager(models.Manager):
    pass


class ProblemManager(models.Manager):
    pass


class StatisticsManager(models.Manager):
    pass


class StudentManager(models.Manager):
    def with_select_related(self):
        return self.select_related('exam', 'user', 'score', 'rank')

    @staticmethod
    def get_annotate_dict_for_score_and_rank():
        annotate_dict = {'rank_num': models.F(f'rank__participants')}
        field_dict = {
            0: 'subject_0', 1: 'subject_1', 2: 'subject_2', 3: 'subject_3', 4: 'subject_4', 'sum': 'sum'
        }
        for key, fld in field_dict.items():
            annotate_dict[f'score_{key}'] = models.F(f'score__{fld}')
            annotate_dict[f'rank_{key}'] = models.F(f'rank__{fld}')
        return annotate_dict

    def infinite_qs_student_list_by_exam(self, exam):
        annotate_dict = self.get_annotate_dict_for_score_and_rank()
        return (
            self.with_select_related().filter(exam=exam).order_by('exam__round')
            .annotate(
                name=models.F('user__name'),
                latest_answer_time=models.Max('answers__created_at'),
                answer_count=models.Count('answers'),
                **annotate_dict
            )
        )

    def infinite_qs_student_by_user_and_exam_with_answer_count(self, user, exam):
        annotate_dict = self.get_annotate_dict_for_score_and_rank()
        qs_student = (
            self.with_select_related().filter(user=user, exam=exam).prefetch_related('answers')
            .annotate(**annotate_dict).order_by('-id').last()
        )
        if qs_student:
            answer_count_model = apps.get_model('a_infinite', 'Answer')
            answer_count = answer_count_model.objects.filter(student=qs_student).aggregate(
                subject_0=models.Count('id', filter=models.Q(problem__subject='형사')),
                subject_1=models.Count('id', filter=models.Q(problem__subject='헌법')),
                subject_2=models.Count('id', filter=models.Q(problem__subject='경찰')),
                subject_3=models.Count('id', filter=models.Q(problem__subject='범죄')),
                subject_4=models.Count('id', filter=models.Q(problem__subject='민법')),
            )
            qs_student.answer_count = answer_count
        return qs_student


class AnswerManager(models.Manager):
    def infinite_qs_answer_by_student_with_predict_result(self, student):
        return self.filter(
            problem__exam=student.exam, student=student).annotate(
            subject=models.F('problem__subject'),
            real_result=models.Case(
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

    def infinite_qs_answer_by_student(self, student):
        qs_answer = (
            self.filter(problem__exam=student.exam).values('problem__subject')
            .annotate(participant_count=models.Count('student_id', distinct=True))
        )
        return qs_answer


class AnswerCountManager(models.Manager):
    def infinite_qs_answer_count_by_exam_and_subject(self, exam, subject=None):
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

    def infinite_qs_answer_count_by_exam(self, exam):
        return self.filter(problem__exam=exam).annotate(
            no=models.F('problem__number'), sub=models.F('problem__subject'), ans=models.F('answer_predict'),
            ans_official=models.F('problem__answer')).order_by('sub', 'no')


class ScoreManager(models.Manager):
    def infinite_qs_score_by_student(self, student):
        qs_score = self.filter(student__exam=student.exam)
        return qs_score.values()


class RankManager(models.Manager):
    pass
