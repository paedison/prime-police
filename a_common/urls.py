from django.urls import path

from .views import *

urlpatterns = [
    # profile
    path('profile/', profile_view, name='profile'),
    path('profile/user/<username>/', profile_view, name='user-profile'),
    path('profile/edit/', profile_edit_view, name='profile-edit'),
    path('profile/delete/', profile_delete_view, name='profile-delete'),
    path('profile/onboarding/', profile_edit_view, name='profile-onboarding'),

    # account
    path('login/modal/', login_modal, name='account_login_modal'),
    path('logout/modal/', logout_modal, name='account_logout_modal'),

]
