from django.urls import path, include

from . import views

app_name = 'official'

problem_patterns = [
    path('', views.problem_detail_view, name='problem-detail-base'),
    path('<int:pk>/', views.problem_detail_view, name='problem-detail'),
    path('like/<int:pk>/', views.like_problem, name='like-problem'),
    path('rate/<int:pk>/', views.rate_problem, name='rate-problem'),
    path('solve/<int:pk>/', views.solve_problem, name='solve-problem'),
    path('tag/<int:pk>/', views.tag_problem, name='tag-problem'),

    path('comment/create/<int:pk>/', views.comment_problem_create, name='comment-problem-create'),
    path('comment/update/<int:pk>/', views.comment_problem_update, name='comment-problem-update'),
    path('comment/delete/<int:pk>/', views.comment_problem_delete, name='comment-problem-delete'),
]

urlpatterns = [
    path('', views.problem_list_view, name='problem-list'),
    path('category/<tag>/', views.problem_list_view, name='category'),

    path('problem/', include(problem_patterns)),
]
