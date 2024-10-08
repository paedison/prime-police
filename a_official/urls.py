from django.urls import path, include

from . import views

app_name = 'official'

collection_patterns = [
    path('', views.collection_list_view, name='collection-list'),
    path('create/', views.collection_create, name='collection-create'),
    path('<int:pk>/', views.collection_detail_view, name='collection-detail'),
]

urlpatterns = [
    path('', views.problem_list_view, name='base'),
    path('<int:pk>/', views.problem_detail_view, name='problem-detail'),

    path('like/<int:pk>/', views.like_problem, name='like-problem'),
    path('rate/<int:pk>/', views.rate_problem, name='rate-problem'),
    path('solve/<int:pk>/', views.solve_problem, name='solve-problem'),
    path('memo/<int:pk>/', views.memo_problem, name='memo-problem'),
    path('tag/<int:pk>/', views.tag_problem, name='tag-problem'),
    path('collect/<int:pk>/', views.collect_problem, name='collect-problem'),

    path('collection/', include(collection_patterns)),
]
