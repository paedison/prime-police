from django.contrib import admin

from a_common.prime_test import admin as prime_admin
from . import models

admin.site.register(models.Problem, prime_admin.ProblemAdmin)
admin.site.register(models.ProblemOpen, prime_admin.ProblemOpenAdmin)
admin.site.register(models.ProblemLike, prime_admin.ProblemLikeAdmin)
admin.site.register(models.ProblemRate, prime_admin.ProblemRateAdmin)
admin.site.register(models.ProblemSolve, prime_admin.ProblemSolveAdmin)
admin.site.register(models.ProblemMemo, prime_admin.ProblemMemoAdmin)
admin.site.register(models.ProblemTag, prime_admin.ProblemTagAdmin)
admin.site.register(models.ProblemTaggedItem, prime_admin.ProblemTaggedItemAdmin)
admin.site.register(models.ProblemCollection, prime_admin.ProblemCollectionAdmin)
admin.site.register(models.ProblemCollectionItem, prime_admin.ProblemCollectionItemAdmin)
admin.site.register(models.Exam, prime_admin.ExamAdmin)
admin.site.register(models.Student, prime_admin.StudentAdmin)
admin.site.register(models.AnswerCount, prime_admin.AnswerCountAdmin)
