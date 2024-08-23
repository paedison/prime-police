from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import Post


@admin.register(Post)
class PostAdmin(ModelAdmin):
    list_display = list_display_links = [
        'id', 'user', 'title', 'created_at', 'modified_at', 'top_fixed', 'is_hidden']
    list_filter = ['top_fixed', 'is_hidden']
    save_on_top = True
    search_fields = ['title', 'content']
    show_full_result_count = True
    fields = ['user', 'title', 'content', 'top_fixed', 'is_hidden']
