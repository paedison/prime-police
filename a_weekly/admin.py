from django.contrib import admin
from unfold.admin import ModelAdmin

from . import models


@admin.register(models.Problem)
class ProblemAdmin(ModelAdmin):
    readonly_fields = ['id']
    common_fields = ['semester', 'circle', 'subject', 'round', 'number', 'answer', 'question']
    list_display = list_display_links = readonly_fields + common_fields
    fields = readonly_fields + common_fields + ['data']
    list_filter = ['semester', 'circle', 'subject', 'round']
    show_facets = admin.ShowFacets.ALWAYS
    save_on_top = True
    search_fields = ['question', 'data']
    show_full_result_count = True


@admin.register(models.Exam)
class ExamAdmin(ModelAdmin):
    readonly_fields = ['id', 'participants', 'statistics', 'open_datetime']
    common_fields = ['semester', 'circle', 'subject', 'round']
    list_display = list_display_links = ['id'] + common_fields
    fields = readonly_fields + common_fields
    list_filter = ['semester', 'circle', 'subject', 'round']
    show_facets = admin.ShowFacets.ALWAYS
    save_on_top = True
    show_full_result_count = True

    def open_datetime(self, obj):
        if obj.opened_at:
            return obj.opened_at.strftime('%Y/%m/%d %H:%I')
        return '-'

    open_datetime.short_description = '공개일시'


@admin.register(models.Student)
class StudentAdmin(ModelAdmin):
    readonly_fields = ['id', 'create_datetime', 'name', 'answer_confirmed', 'score', 'rank']
    common_fields = ['semester', 'circle', 'subject', 'round']
    list_display = list_display_links = readonly_fields + common_fields
    fields = readonly_fields + common_fields + ['answer_student']
    list_filter = ['semester', 'circle', 'subject', 'round']
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
