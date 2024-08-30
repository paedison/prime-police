from django.urls import path

from . import views

app_name = 'weekly'

urlpatterns = [
    path('', views.answer_list_view, name='answer-list'),
    path('<int:pk>/', views.answer_detail_view, name='answer-detail'),
    path('input/<int:pk>/', views.answer_input_view, name='answer-input'),
    path('confirm/<int:pk>/', views.answer_confirm_view, name='answer-confirm'),
    path('rank/<int:pk>/', views.rank_verify, name='rank-verify'),
]
