from django.urls import path, include

from . import views

account_urlpatterns = [
    path('signup/', views.SignupView.as_view(), name='account_signup'),
    path('login/', views.LoginView.as_view(), name='account_login'),
    path("inactive/", views.AccountInactiveView.as_view(), name="account_inactive"),
    path('login/modal/', views.login_modal_view, name='account_login_modal'),
    path('logout/modal/', views.logout_modal_view, name='account_logout_modal'),
    path('password/change/', views.PasswordChangeView.as_view(), name='account_change_password'),
    path('password/changed/', views.changed_password_view, name='changed_password'),
]

urlpatterns = [
    path('404/', views.page_404, name='404'),
    path('privacy/', views.privacy, name='privacy_policy'),
    path('search/', views.search_view, name='search'),
    path('account/', include(account_urlpatterns)),
]
