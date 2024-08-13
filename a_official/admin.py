from django.contrib import admin
from unfold.admin import ModelAdmin

from . import models


class LikeChoiceInline(admin.TabularInline):
    model = models.ProblemLike
    extra = 3


# @admin.register(models.Unit)
# class UnitAdmin(ModelAdmin):
#     list_display = list_display_links = ['id', 'exam', 'name', 'order']
#     fieldsets = [(None, {'fields': ['exam', 'name', 'order', 'remarks']})]
#
#
# @admin.register(models.Department)
# class DepartmentAdmin(ModelAdmin):
#     list_display = list_display_links = ['id', 'exam', 'unit', 'name', 'order']
#     fieldsets = [(None, {'fields': ['exam', 'unit', 'name', 'order', 'remarks']})]
#
#
# @admin.register(models.Exam)
# class ExamAdmin(ModelAdmin):
#     list_display = list_display_links = ['id', 'year', 'exam', 'round']
#     fieldsets = [
#         (
#             None,
#             {
#                 'fields': [
#                     'year', 'exam', 'round', 'answer_official',
#                     'page_opened_at', 'exam_started_at', 'exam_finished_at',
#                     'answer_predict_opened_at', 'answer_official_opened_at',
#                     'remarks',
#                 ]
#             }
#         )
#     ]


@admin.register(models.Problem)
class ProblemAdmin(ModelAdmin):
    list_display = list_display_links = ['id', 'year', 'subject', 'number', 'answer', 'question']
    list_filter = ['year', 'subject']
    show_facets = admin.ShowFacets.ALWAYS
    save_on_top = True
    search_fields = ['question', 'data']
    show_full_result_count = True
    fieldsets = [
        (
            None,
            {
                'fields': ['year', 'subject', 'number', 'answer', 'question', 'data'],
            }
        )
    ]

    class Media:
        css = {'all': ['css/admin_custom.css']}


@admin.register(models.ProblemOpen)
class ProblemOpenAdmin(ModelAdmin):
    list_display = list_display_links = ['id', 'created_at', 'user', 'reference', 'ip_address']
    fieldsets = [(None, {'fields': ['user', 'reference', 'ip_address', 'remarks']})]


@admin.register(models.ProblemLike)
class ProblemLikeAdmin(ModelAdmin):
    list_display = list_display_links = ['id', 'created_at', 'user', 'reference', 'is_liked']
    fieldsets = [(None, {'fields': ['user', 'problem', 'is_liked', 'remarks']})]


@admin.register(models.ProblemRate)
class ProblemRateAdmin(ModelAdmin):
    list_display = list_display_links = ['id', 'created_at', 'user', 'reference', 'rating']
    fieldsets = [(None, {'fields': ['user', 'problem', 'rating', 'remarks']})]


@admin.register(models.ProblemSolve)
class ProblemSolveAdmin(ModelAdmin):
    list_display = list_display_links = ['id', 'created_at', 'user', 'reference', 'answer', 'is_correct']
    fieldsets = [(None, {'fields': ['user', 'problem', 'answer', 'is_correct', 'remarks']})]


@admin.register(models.ProblemMemo)
class ProblemMemoAdmin(ModelAdmin):
    list_display = list_display_links = ['id', 'created_at', 'user', 'reference', 'content']
    fieldsets = [(None, {'fields': ['user', 'problem', 'content', 'remarks']})]


@admin.register(models.ProblemComment)
class ProblemCommentAdmin(ModelAdmin):
    list_display = list_display_links = ['id', 'created_at', 'user', 'reference', 'title']
    fieldsets = [(None, {'fields': ['user', 'problem', 'title', 'content', 'parent', 'hit']})]


@admin.register(models.ProblemTag)
class ProblemTagAdmin(ModelAdmin):
    list_display = list_display_links = ['id', 'created_at', 'name', 'slug']
    fieldsets = [(None, {'fields': ['tag', 'slug']})]


@admin.register(models.ProblemTaggedItem)
class ProblemTaggedItemAdmin(ModelAdmin):
    list_display = list_display_links = ['id', 'created_at', 'user', 'reference', 'tag_name']
    fieldsets = [(None, {'fields': ['user', 'content_object', 'tag', 'active', 'remarks']})]


@admin.register(models.ProblemCollection)
class ProblemCollectAdmin(ModelAdmin):
    list_display = list_display_links = ['id', 'created_at', 'user', 'title', 'order']
    fieldsets = [(None, {'fields': ['user', 'title', 'order']})]


@admin.register(models.ProblemCollectionItem)
class ProblemCollectedItemAdmin(ModelAdmin):
    list_display = list_display_links = ['id', 'created_at', 'reference', 'collect_title', 'order']
    fieldsets = [(None, {'fields': ['collect', 'problem', 'order', 'remarks']})]
