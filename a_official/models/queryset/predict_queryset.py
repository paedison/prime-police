from django.db import models


class PredictStatisticsQuerySet(models.QuerySet):
    def filtered_statistics_by_exam(self, exam):
        return self.select_related('exam').filter(exam=exam).order_by('id')


class PredictStudentQuerySet(models.QuerySet):
    def annotated_student_for_normal_view(self, user, exam):
        annotate_dict = {'rank_num': models.F(f'rank__participants')}
        field_dict = {'0': 'subject_0', '1': 'subject_1', '2': 'subject_2', '3': 'subject_3', 'sum': 'sum'}
        for key, fld in field_dict.items():
            annotate_dict[f'score_{key}'] = models.F(f'score__{fld}')
            annotate_dict[f'rank_{key}'] = models.F(f'rank__{fld}')

        qs_student = (
            self.select_related('exam', 'score', 'rank', 'user')
            .annotate(**annotate_dict).prefetch_related('answers')
            .filter(user=user, exam=exam).order_by('id').last()
        )
        if qs_student:
            qs_student_answers = qs_student.answers.values(
                subject=models.F('problem__subject')).annotate(answer_count=models.Count('id'))
            answer_count_sum = 0
            for qs_sa in qs_student_answers:
                qs_student.answer_count[qs_sa['subject']] = qs_sa['answer_count']
                answer_count_sum += qs_sa['answer_count']
            qs_student.answer_count['총점'] = answer_count_sum

        return qs_student

    def annotate_score_and_rank(self):
        annotate_dict = {
            'participants': models.F(f'rank__participants'),
        }
        field_dict = {
            '0': 'subject_0', '1': 'subject_1', '2': 'subject_2', '3': 'subject_3',
            '4': 'subject_4', '5': 'subject_5', '6': 'subject_6', 'sum': 'sum'
        }
        for key, fld in field_dict.items():
            annotate_dict[f'score_{key}'] = models.F(f'score__{fld}')
            annotate_dict[f'rank_{key}'] = models.F(f'rank__{fld}')
        return self.annotate(**annotate_dict)

    @staticmethod
    def get_annotate_dict_for_score_and_rank():
        annotate_dict = {'rank_num': models.F(f'rank__participants')}
        field_dict = {
            '0': 'subject_0', '1': 'subject_1', '2': 'subject_2', '3': 'subject_3',
            '4': 'subject_0', '5': 'subject_5', '6': 'subject_6', 'sum': 'sum'
        }
        for key, fld in field_dict.items():
            annotate_dict[f'score_{key}'] = models.F(f'score__{fld}')
            annotate_dict[f'rank_{key}'] = models.F(f'rank__{fld}')
        return annotate_dict

    def average_scores_over(self, exam, score: int):
        return self.filter(exam=exam, score__sum__gte=score).values_list('score__sum', flat=True)

    def registered_exam_student(self, request, exam_list):
        if request.user.is_authenticated:
            return (
                self.select_related('exam', 'score', 'rank')
                .filter(user=request.user, exam__in=exam_list).order_by('id')
            )

    def filtered_student_by_exam(self, exam):
        return (
            self.annotate_score_and_rank()
            .select_related('exam', 'score', 'rank').filter(exam=exam)
            .annotate(
                has_rank_sum=models.Case(
                    models.When(rank__sum__isnull=False, then=models.Value(0)),
                    default=models.Value(1),
                    output_field=models.IntegerField(),
                ),
                latest_answer_time=models.Max('answers__created_at'),
                answer_count=models.Count('answers'),
            ).order_by('has_rank_sum', 'rank__sum')
        )

    def exam_student_with_answer_count(self, user, exam):
        annotate_dict = self.get_annotate_dict_for_score_and_rank()
        qs_student = (
            self.select_related('exam', 'score', 'rank', 'user')
            .filter(user=user, exam=exam).prefetch_related('answers')
            .annotate(**annotate_dict).order_by('id').last()
        )
        if qs_student:
            qs_student_answers = qs_student.answers.values(
                subject=models.F('problem__subject')).annotate(answer_count=models.Count('id'))
            answer_count_sum = 0
            for qs_sa in qs_student_answers:
                qs_student.answer_count[qs_sa['subject']] = qs_sa['answer_count']
                answer_count_sum += qs_sa['answer_count']
            qs_student.answer_count['총점'] = answer_count_sum
        return qs_student


class PredictAnswerQuerySet(models.QuerySet):
    def filtered_by_exam_student(self, student):
        fields = [
            'problem',
            'problem__predict_answer_count',
            'problem__predict_answer_count_top_rank',
            'problem__predict_answer_count_mid_rank',
            'problem__predict_answer_count_low_rank'
        ]
        is_result_correct = models.Case(
            models.When(answer=models.F('problem__answer'), then=models.Value(True)),
            default=models.Value(False),
            output_field=models.BooleanField()
        )
        is_predict_correct = models.Case(
            models.When(
                answer=models.F('problem__predict_answer_count__answer_predict'), then=models.Value(True)),
            default=models.Value(False),
            output_field=models.BooleanField()
        )
        return (
            self.select_related(*fields).filter(student=student)
            .annotate(
                subject=models.F('problem__subject'),
                is_result_correct=is_result_correct,
                is_predict_correct=is_predict_correct,
            )
        )

    def filtered_by_exam_student_and_stat_type(
            self, student, stat_type='all', is_filtered=False):
        qs = self.filter(problem__exam=student.exam).values('problem__subject').annotate(
            participant_count=models.Count('student_id', distinct=True))
        if stat_type != 'all':
            qs = qs.filter(**{f'student__{stat_type}': getattr(student, stat_type)})
        if is_filtered:
            qs = qs.filter(student__is_filtered=True)
        return qs

    def filtered_by_exam_student_and_sub(self, student, sub: str):
        return self.filter(student=student, problem__subject=sub).annotate(
            answer_official=models.F('problem__answer'), answer_student=models.F('answer'))


class PredictAnswerCountQuerySet(models.QuerySet):
    def filtered_by_exam_and_subject(self, exam, subject=None):
        annotate_dict = {
            'subject': models.F('problem__subject'),
            'number': models.F('problem__number'),
            'ans_predict': models.F(f'problem__predict_answer_count__answer_predict'),
            'ans_official': models.F('problem__answer'),
        }

        for rank in ['all', 'top', 'mid', 'low']:
            for fld in ['count_1', 'count_2', 'count_3', 'count_4', 'count_sum']:
                if rank == 'all':
                    f_expr = fld
                else:
                    f_expr = f'problem__predict_answer_count_{rank}_rank__{fld}'
                annotate_dict[f'{fld}_{rank}'] = models.F(f_expr)

        annotate_dict['subject_code'] = models.Case(
                models.When(subject='형사', then=0),
                models.When(subject='헌법', then=1),
                models.When(subject='경찰', then=2),
                models.When(subject='범죄', then=3),
                models.When(subject='민법', then=4),
                models.When(subject='행법', then=5),
                models.When(subject='행학', then=6),
                default=7,
                output_field=models.IntegerField(),
            )

        qs_answer_count = (
            self.filter(problem__exam=exam)
            .annotate(**annotate_dict).order_by('subject_code', 'problem__number')
            .select_related(
                f'problem',
                f'problem__predict_answer_count_top_rank',
                f'problem__predict_answer_count_mid_rank',
                f'problem__predict_answer_count_low_rank',
            )
        )
        if subject:
            qs_answer_count = qs_answer_count.filter(subject=subject)
        return qs_answer_count

    def predict_filtered_by_exam(self, exam):
        return self.filter(problem__exam=exam).annotate(
            no=models.F('problem__number'),
            number=models.F('problem__number'),
            sub=models.F('problem__subject'),
            subject=models.F('problem__subject'),
            ans=models.F('answer_predict'),
            ans_official=models.F('problem__answer')).order_by('sub', 'no')


class PredictScoreQuerySet(models.QuerySet):
    def predict_filtered_scores_of_student(
            self, student, stat_type='all', is_filtered=False):
        qs = self.filter(student__exam=student.exam)
        if stat_type != 'all':
            qs = qs.filter(**{f'student__{stat_type}': getattr(student, stat_type)})
        if is_filtered:
            qs = qs.filter(student__is_filtered=is_filtered)
        return qs.values()
