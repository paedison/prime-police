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


@admin.register(models.ProblemOpen)
class ProblemOpenAdmin(ModelAdmin):
    list_display = list_display_links = ['id', 'created_at', 'user', 'reference', 'ip_address']
    fields = ['user', 'reference', 'ip_address', 'remarks']


@admin.register(models.ProblemLike)
class ProblemLikeAdmin(ModelAdmin):
    list_display = list_display_links = ['id', 'created_at', 'user', 'reference', 'is_liked']
    fields = ['user', 'problem', 'is_liked', 'remarks']


@admin.register(models.ProblemRate)
class ProblemRateAdmin(ModelAdmin):
    list_display = list_display_links = ['id', 'created_at', 'user', 'reference', 'rating']
    fields = ['user', 'problem', 'rating', 'remarks']


@admin.register(models.ProblemSolve)
class ProblemSolveAdmin(ModelAdmin):
    list_display = list_display_links = ['id', 'created_at', 'user', 'reference', 'answer', 'is_correct']
    fields = ['user', 'problem', 'answer', 'is_correct', 'remarks']


@admin.register(models.ProblemMemo)
class ProblemMemoAdmin(ModelAdmin):
    list_display = list_display_links = ['id', 'created_at', 'user', 'reference', 'content']
    fields = ['user', 'problem', 'content', 'remarks']


@admin.register(models.ProblemTag)
class ProblemTagAdmin(ModelAdmin):
    list_display = list_display_links = ['id', 'created_at', 'name', 'slug']
    fields = ['tag', 'slug']


@admin.register(models.ProblemTaggedItem)
class ProblemTaggedItemAdmin(ModelAdmin):
    list_display = list_display_links = ['id', 'created_at', 'user', 'reference', 'tag_name']
    fields = ['user', 'content_object', 'tag', 'active', 'remarks']


@admin.register(models.ProblemCollection)
class ProblemCollectAdmin(ModelAdmin):
    list_display = list_display_links = ['id', 'created_at', 'user', 'title', 'order']
    fields = ['user', 'title', 'order']


@admin.register(models.ProblemCollectionItem)
class ProblemCollectedItemAdmin(ModelAdmin):
    list_display = list_display_links = ['id', 'created_at', 'reference', 'collect_title', 'order']
    fields = ['collect', 'problem', 'order', 'remarks']


@admin.register(models.Exam)
class ExamAdmin(ModelAdmin):
    readonly_fields = ['id', 'participants', 'statistics']
    common_fields = ['semester', 'circle', 'subject', 'round', 'open_datetime']
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
