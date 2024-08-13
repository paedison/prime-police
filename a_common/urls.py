from django.urls import path, include

from . import views

profile_urlpatterns = [
    path('profile/', views.profile_view, name='profile'),
    path('profile/user/<username>/', views.profile_view, name='user-profile'),
    path('profile/edit/', views.profile_edit_view, name='profile-edit'),
    path('profile/delete/', views.profile_delete_view, name='profile-delete'),
    path('profile/onboarding/', views.profile_edit_view, name='profile-onboarding'),
]

account_urlpatterns = [
    path('login/modal/', views.login_modal, name='account_login_modal'),
    path('logout/modal/', views.logout_modal, name='account_logout_modal'),
]

urlpatterns = [
    path('404/', views.page_404, name='404'),
    path('privacy/', views.privacy, name='privacy_policy'),
    path('profile/', include(profile_urlpatterns)),
    path('accounts/', include(account_urlpatterns)),
]
