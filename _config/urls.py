from django.contrib import admin
from django.urls import path, include

from a_common.views import index_view

urlpatterns = [
    path("__debug__/", include("debug_toolbar.urls")),
    path('', index_view, name='index'),
    path('', include('a_common.urls')),

    path('admin/', include('admin_honeypot.urls', namespace='admin_honeypot')),
    path('check_in_as_admin/', admin.site.urls),
    path('account/', include('allauth.urls')),
    path('ckeditor/', include('ckeditor_uploader.urls')),  # CKEditor URLs

    path('official/', include('a_official.urls')),
    path('daily/', include('a_daily.urls')),
    path('notice/', include('a_notice.urls')),
]
