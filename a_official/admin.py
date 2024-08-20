from django.contrib import admin
from unfold.admin import ModelAdmin

from . import models


@admin.register(models.Problem)
class ProblemAdmin(ModelAdmin):
    list_display = list_display_links = ['id', 'year', 'subject', 'number', 'answer', 'question']
    list_filter = ['year', 'subject']
    show_facets = admin.ShowFacets.ALWAYS
    save_on_top = True
    search_fields = ['question', 'data']
    show_full_result_count = True
    fields = ['year', 'subject', 'number', 'answer', 'question', 'data']

    class Media:
        css = {'all': ['css/admin_custom.css']}


@admin.register(models.ProblemOpen)
class ProblemOpenAdmin(ModelAdmin):
    list_display = list_display_links = ['id', 'created_at', 'user', 'reference', 'ip_address']
    fields = ['user', 'reference', 'ip_address', 'remarks']

    class Media:
        css = {'all': ['css/admin_custom.css']}


@admin.register(models.ProblemLike)
class ProblemLikeAdmin(ModelAdmin):
    list_display = list_display_links = ['id', 'created_at', 'user', 'reference', 'is_liked']
    fields = ['user', 'problem', 'is_liked', 'remarks']

    class Media:
        css = {'all': ['css/admin_custom.css']}


@admin.register(models.ProblemRate)
class ProblemRateAdmin(ModelAdmin):
    list_display = list_display_links = ['id', 'created_at', 'user', 'reference', 'rating']
    fields = ['user', 'problem', 'rating', 'remarks']

    class Media:
        css = {'all': ['css/admin_custom.css']}


@admin.register(models.ProblemSolve)
class ProblemSolveAdmin(ModelAdmin):
    list_display = list_display_links = ['id', 'created_at', 'user', 'reference', 'answer', 'is_correct']
    fields = ['user', 'problem', 'answer', 'is_correct', 'remarks']

    class Media:
        css = {'all': ['css/admin_custom.css']}


@admin.register(models.ProblemMemo)
class ProblemMemoAdmin(ModelAdmin):
    list_display = list_display_links = ['id', 'created_at', 'user', 'reference', 'content']
    fields = ['user', 'problem', 'content', 'remarks']

    class Media:
        css = {'all': ['css/admin_custom.css']}


@admin.register(models.ProblemTag)
class ProblemTagAdmin(ModelAdmin):
    list_display = list_display_links = ['id', 'created_at', 'name', 'slug']
    fields = ['tag', 'slug']

    class Media:
        css = {'all': ['css/admin_custom.css']}


@admin.register(models.ProblemTaggedItem)
class ProblemTaggedItemAdmin(ModelAdmin):
    list_display = list_display_links = ['id', 'created_at', 'user', 'reference', 'tag_name']
    fields = ['user', 'content_object', 'tag', 'active', 'remarks']

    class Media:
        css = {'all': ['css/admin_custom.css']}


@admin.register(models.ProblemCollection)
class ProblemCollectAdmin(ModelAdmin):
    list_display = list_display_links = ['id', 'created_at', 'user', 'title', 'order']
    fields = ['user', 'title', 'order']

    class Media:
        css = {'all': ['css/admin_custom.css']}


@admin.register(models.ProblemCollectionItem)
class ProblemCollectedItemAdmin(ModelAdmin):
    list_display = list_display_links = ['id', 'created_at', 'reference', 'collect_title', 'order']
    fields = ['collect', 'problem', 'order', 'remarks']

    class Media:
        css = {'all': ['css/admin_custom.css']}
