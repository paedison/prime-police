from debug_toolbar.toolbar import debug_toolbar_urls
from django.contrib import admin
from django.urls import path, include

import a_common.views as common_views

urlpatterns = [
    path('', common_views.index_view, name='index'),
    path('', include('a_common.urls')),
    path('robots.txt', common_views.robots_txt, name='robots_txt'),

    path('admin/', include('admin_honeypot.urls', namespace='admin_honeypot')),
    path('check_in_as_admin/', admin.site.urls),
    path('account/', include('allauth.urls')),
    path('ckeditor/', include('ckeditor_uploader.urls')),  # CKEditor URLs

    path('official/', include('a_official.urls')),
    path('daily/', include('a_daily.urls')),
    path('board/', include('a_board.urls')),
    path('weekly/', include('a_weekly.urls')),
    path('infinite/', include('a_infinite.urls')),
] + debug_toolbar_urls()
