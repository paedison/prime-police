from a_common.utils import bulk_create_or_update
from a_official import models


def run():
    list_update = []
    qs_problem = models.Problem.objects.all()
    for qs_p in qs_problem:
        exam = models.Exam.objects.filter(year=qs_p.year).first()
        if exam and qs_p.exam_id != exam.id:
            qs_p.exam_id = exam.id
            list_update.append(qs_p)
    bulk_create_or_update(models.Problem, [], list_update, ['exam_id'])
