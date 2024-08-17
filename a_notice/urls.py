from django.urls import path, include

from . import views

app_name = 'notice'

comment_urlpatterns = [
    path('', views.comment_list_view, name='comment_list'),
    path('create/', views.comment_create_view, name='comment_create'),
    path('update/<int:pk>/', views.comment_update_view, name='comment_update'),
    path('delete/<int:pk>/', views.comment_delete_view, name='comment_delete'),
]

urlpatterns = [
    path('', views.list_view, name='base'),
    path('<int:pk>/', views.detail_view, name='detail'),
    path('create/', views.create_view, name='create'),
    path('update/<int:pk>/', views.update_view, name='update'),
    path('delete/<int:pk>/', views.delete_view, name='delete'),

    path('comment/', include(comment_urlpatterns)),
]
