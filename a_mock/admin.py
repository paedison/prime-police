from django.contrib import admin
from unfold.admin import ModelAdmin

from . import models


@admin.register(models.Exam)
class ExamAdmin(ModelAdmin):
    readonly_fields = ['id']
    common_fields = ['year', 'page_opened_at', 'exam_started_at', 'exam_finished_at']
    list_display = list_display_links = ['id'] + common_fields
    fields = readonly_fields + common_fields
    list_filter = ['year']
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
