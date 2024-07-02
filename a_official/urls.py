from django.urls import path, include

from .views.problem_views import (
    problem_list_view, problem_list_filter, problem_detail_view,
    like_problem, rate_problem, solve_problem,
    tag_problem_create, tag_problem_remove,
    comment_problem_create, comment_problem_update, comment_problem_delete,
)

app_name = 'official'

problem_patterns = [
    path('', problem_detail_view, name='problem-detail-base'),
    path('<int:pk>/', problem_detail_view, name='problem-detail'),
    path('like/<int:pk>/', like_problem, name='like-problem'),
    path('rate/<int:pk>/', rate_problem, name='rate-problem'),
    path('solve/<int:pk>/', solve_problem, name='solve-problem'),
    path('tag/add/<int:pk>/', tag_problem_create, name='tag-problem-create'),
    path('tag/remove/<int:pk>/', tag_problem_remove, name='tag-problem-remove'),
    path('comment/create/<int:pk>/', comment_problem_create, name='comment-problem-create'),
    path('comment/update/<int:pk>/', comment_problem_update, name='comment-problem-update'),
    path('comment/delete/<int:pk>/', comment_problem_delete, name='comment-problem-delete'),
]

urlpatterns = [
    path('', problem_list_view, name='problem-list'),
    path('filter/list/', problem_list_filter, name='problem-list-filter'),
    path('category/<tag>/', problem_list_view, name='category'),

    path('problem/', include(problem_patterns)),
]
