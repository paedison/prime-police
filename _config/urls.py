from django.contrib import admin
from django.urls import path, include

from a_official.views import problem_list_view

urlpatterns = [
    path("__debug__/", include("debug_toolbar.urls")),
    path('', problem_list_view, name='index'),
    path('', include('a_common.urls')),

    path('admin/', include('admin_honeypot.urls', namespace='admin_honeypot')),
    path('check_in_as_admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path('ckeditor/', include('ckeditor_uploader.urls')),  # CKEditor URLs

    path('official/', include('a_official.urls')),
    path('prime/', include('a_prime.urls')),
    path('notice/', include('a_notice.urls')),
]
