from django.contrib import admin
from unfold.admin import ModelAdmin


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


class ProblemOpenAdmin(ModelAdmin):
    list_display = list_display_links = ['id', 'created_at', 'user', 'reference', 'ip_address']
    fields = ['user', 'reference', 'ip_address', 'remarks']


class ProblemLikeAdmin(ModelAdmin):
    list_display = list_display_links = ['id', 'created_at', 'user', 'reference', 'is_liked']
    fields = ['user', 'problem', 'is_liked', 'remarks']


class ProblemRateAdmin(ModelAdmin):
    list_display = list_display_links = ['id', 'created_at', 'user', 'reference', 'rating']
    fields = ['user', 'problem', 'rating', 'remarks']


class ProblemSolveAdmin(ModelAdmin):
    list_display = list_display_links = ['id', 'created_at', 'user', 'reference', 'answer', 'is_correct']
    fields = ['user', 'problem', 'answer', 'is_correct', 'remarks']


class ProblemMemoAdmin(ModelAdmin):
    list_display = list_display_links = ['id', 'created_at', 'user', 'reference', 'content']
    fields = ['user', 'problem', 'content', 'remarks']


class ProblemTagAdmin(ModelAdmin):
    list_display = list_display_links = ['id', 'created_at', 'name', 'slug']
    fields = ['tag', 'slug']


class ProblemTaggedItemAdmin(ModelAdmin):
    list_display = list_display_links = ['id', 'created_at', 'user', 'reference', 'tag_name']
    fields = ['user', 'content_object', 'tag', 'active', 'remarks']


class ProblemCollectionAdmin(ModelAdmin):
    list_display = list_display_links = ['id', 'created_at', 'user', 'title', 'order']
    fields = ['user', 'title', 'order']


class ProblemCollectionItemAdmin(ModelAdmin):
    list_display = list_display_links = ['id', 'created_at', 'reference', 'collect_title', 'order']
    fields = ['collect', 'problem', 'order', 'remarks']


class ExamAdmin(ModelAdmin):
    readonly_fields = ['id', 'participants', 'statistics']
    common_fields = ['semester', 'circle', 'subject', 'round']
    list_display = list_display_links = ['id'] + common_fields + ['open_datetime', 'participants']
    fields = readonly_fields + common_fields + ['opened_at']
    list_filter = ['semester', 'circle', 'subject', 'round']
    show_facets = admin.ShowFacets.ALWAYS
    save_on_top = True
    show_full_result_count = True

    def open_datetime(self, obj):
        if obj.opened_at:
            return obj.opened_at.strftime('%Y/%m/%d %H:%I')
        return '-'

    open_datetime.short_description = '공개일시'


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


class AnswerCountAdmin(ModelAdmin):
    list_display = list_display_links = [
        'id', 'semester', 'circle', 'subject', 'round', 'number',
        'count_1', 'count_2', 'count_3', 'count_4', 'count_0', 'count_multiple', 'count_total',
    ]
    readonly_fields = [
        'id', 'semester', 'circle', 'subject', 'round', 'number',
        'count_1', 'count_2', 'count_3', 'count_4', 'count_0', 'count_multiple', 'count_total', 'data',
    ]
    fields = None
    fieldsets = [
        (
            None, {
                'fields': (
                    ('semester', 'circle', 'subject', 'round', 'number'),
                    ('count_1', 'count_2', 'count_3', 'count_4', 'count_total'),
                )
            }
        ),
    ]
