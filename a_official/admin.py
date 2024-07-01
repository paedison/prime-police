from django.contrib import admin
from unfold.admin import ModelAdmin

from . import models


class LikeChoiceInline(admin.TabularInline):
    model = models.ProblemLike
    extra = 3


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
                'classes': ['extrapretty']
            }
        )
    ]

    class Media:
        css = {'all': ['css/admin_custom.css']}


admin.site.register(models.ProblemOpen)
admin.site.register(models.ProblemLike)
admin.site.register(models.ProblemRate)
admin.site.register(models.ProblemSolve)
admin.site.register(models.ProblemMemo)
admin.site.register(models.ProblemComment)
admin.site.register(models.ProblemTag)
admin.site.register(models.ProblemTaggedItem)
admin.site.register(models.ProblemCollect)
admin.site.register(models.ProblemCollectedItem)
