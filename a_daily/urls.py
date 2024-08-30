from django.urls import path, include

from .views import problem_views, answer_views

app_name = 'daily'

problem_patterns = [
    path('', problem_views.problem_list_view, name='problem-list'),
    path('<int:pk>/', problem_views.problem_detail_view, name='problem-detail'),

    path('like/<int:pk>/', problem_views.like_problem, name='like-problem'),
    path('rate/<int:pk>/', problem_views.rate_problem, name='rate-problem'),
    # path('solve/<int:pk>/', problem_views.solve_problem, name='solve-problem'),
    path('memo/<int:pk>/', problem_views.memo_problem, name='memo-problem'),
    path('tag/<int:pk>/', problem_views.tag_problem, name='tag-problem'),
    path('collect/<int:pk>/', problem_views.collect_problem, name='collect-problem'),

    path('collection/', problem_views.collection_list_view, name='collection-list'),
    path('collection/create/', problem_views.collection_create, name='collection-create'),
    path('collection/<int:pk>/', problem_views.collection_detail_view, name='collection-detail'),
]

answer_patterns = [
    path('', answer_views.answer_list_view, name='answer-list'),
    path('<int:pk>/', answer_views.answer_detail_view, name='answer-detail'),
    path('input/<int:pk>/', answer_views.answer_input_view, name='answer-input'),
    path('confirm/<int:pk>/', answer_views.answer_confirm_view, name='answer-confirm'),
]

urlpatterns = [
    path('problem/', include(problem_patterns)),
    path('answer/', include(answer_patterns)),
    path('rank/<int:pk>/', answer_views.rank_verify, name='rank-verify'),
]
