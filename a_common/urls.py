from django.urls import path, include

from . import views

profile_urlpatterns = [
    path('', views.profile_view, name='profile'),
    path('user/<username>/', views.profile_view, name='user-profile'),
    path('edit/', views.profile_edit_view, name='profile-edit'),
    path('delete/', views.profile_delete_view, name='profile-delete'),
    path('onboarding/', views.profile_edit_view, name='profile-onboarding'),
]

account_urlpatterns = [
    path('login/', views.LoginView.as_view(), name='account_login'),
    path('login/modal/', views.login_modal, name='account_login_modal'),
    path('logout/modal/', views.logout_modal, name='account_logout_modal'),
]

urlpatterns = [
    path('404/', views.page_404, name='404'),
    path('privacy/', views.privacy, name='privacy_policy'),
    path('profile/', include(profile_urlpatterns)),
    path('account/', include(account_urlpatterns)),
]
