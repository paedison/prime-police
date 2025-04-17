from django.contrib import admin
from unfold.admin import ModelAdmin

from a_common.prime_test import admin as prime_admin
from . import models


@admin.register(models.Exam)
class ExamAdmin(ModelAdmin):
    readonly_fields = ['id']
    common_fields = ['semester', 'round', 'page_opened_at', 'exam_started_at', 'exam_finished_at']
    list_display = list_display_links = ['id'] + common_fields
    fields = readonly_fields + common_fields
    list_filter = ['semester', 'round']
    show_facets = admin.ShowFacets.ALWAYS
    save_on_top = True
    show_full_result_count = True


@admin.register(models.Problem)
class ProblemAdmin(ModelAdmin):
    readonly_fields = ['id']
    common_fields = ['exam', 'subject', 'number', 'answer', 'question']
    list_display = list_display_links = readonly_fields + common_fields
    fields = readonly_fields + common_fields + ['data']
    list_filter = ['exam', 'subject']
    show_facets = admin.ShowFacets.ALWAYS
    save_on_top = True
    search_fields = ['question', 'data']
    show_full_result_count = True


admin.site.register(models.ProblemOpen, prime_admin.ProblemOpenAdmin)
admin.site.register(models.ProblemLike, prime_admin.ProblemLikeAdmin)
admin.site.register(models.ProblemRate, prime_admin.ProblemRateAdmin)
admin.site.register(models.ProblemSolve, prime_admin.ProblemSolveAdmin)
admin.site.register(models.ProblemMemo, prime_admin.ProblemMemoAdmin)
admin.site.register(models.ProblemTag, prime_admin.ProblemTagAdmin)
admin.site.register(models.ProblemTaggedItem, prime_admin.ProblemTaggedItemAdmin)
admin.site.register(models.ProblemCollection, prime_admin.ProblemCollectionAdmin)
admin.site.register(models.ProblemCollectionItem, prime_admin.ProblemCollectionItemAdmin)


@admin.register(models.Statistics)
class StatisticsAdmin(ModelAdmin):
    readonly_fields = list_display = list_display_links = [
        'id', 'exam', 'subject_0', 'subject_1', 'subject_2', 'subject_3', 'subject_4', 'sum',
    ]


@admin.register(models.Student)
class StudentAdmin(ModelAdmin):
    readonly_fields = ['id', 'create_datetime', 'name']
    common_fields = ['exam']
    list_display = list_display_links = readonly_fields + common_fields
    fields = readonly_fields + common_fields
    list_filter = ['exam']
    show_facets = admin.ShowFacets.ALWAYS
    save_on_top = True
    show_full_result_count = True

    def create_datetime(self, obj):
        if obj.created_at:
            return obj.created_at.strftime('%Y/%m/%d %H:%I')
        return '-'

    def name(self, obj):
        return obj.user.name

    create_datetime.short_description = '생성일시'
    name.short_description = '이름'


@admin.register(models.Answer)
class AnswerAdmin(ModelAdmin):
    readonly_fields = list_display = list_display_links = [
        'id', 'created_at', 'student', 'problem', 'answer',
    ]


@admin.register(models.AnswerCount)
class AnswerCountAdmin(ModelAdmin):
    list_display = list_display_links = [
        'id', 'problem',
        'count_1', 'count_2', 'count_3', 'count_4', 'count_0', 'count_multiple', 'count_sum',
    ]
    readonly_fields = [
        'id', 'problem',
        'count_1', 'count_2', 'count_3', 'count_4', 'count_0', 'count_multiple', 'count_sum', 'answer_predict',
    ]
    fields = None
    fieldsets = [
        (
            None, {
                'fields': (
                    'problem',
                    ('count_1', 'count_2', 'count_3', 'count_4', 'count_total'),
                )
            }
        ),
    ]
