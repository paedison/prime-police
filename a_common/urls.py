from django.urls import path, include

from . import views

account_urlpatterns = [
    path('login/modal/', views.login_modal_view, name='account_login_modal'),
    path('logout/modal/', views.logout_modal_view, name='account_logout_modal'),
    path('password/changed/', views.changed_password_view, name='changed_password'),
    path("password/reset/done/", views.password_reset_done, name="account_reset_password_done"),
]

urlpatterns = [
    path('404/', views.page_404, name='404'),
    path('privacy/', views.privacy, name='privacy_policy'),
    path('search/', views.search_view, name='search'),
    path('account/', include(account_urlpatterns)),
]
