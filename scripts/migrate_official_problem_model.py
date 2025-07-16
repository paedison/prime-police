from a_common.utils import bulk_create_or_update
from a_official import models


def run():
    list_update = []
    qs_exam = models.Exam.objects.all()
    exam_dict = {qs_e.year: qs_e for qs_e in qs_exam}
    qs_problem = models.Problem.objects.all()
    for qs_p in qs_problem:
        exam = exam_dict.get(qs_p.year)
        if exam and qs_p.exam_id != exam.id:
            qs_p.exam_id = exam.id
            list_update.append(qs_p)
    bulk_create_or_update(models.Problem, [], list_update, ['exam_id'])
