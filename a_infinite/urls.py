from django.urls import path, include

from .views import problem_views, answer_views, staff_views

app_name = 'infinite'

problem_patterns = [
    path('', problem_views.problem_list_view, name='problem-list'),
    path('<int:pk>/', problem_views.problem_detail_view, name='problem-detail'),

    path('like/<int:pk>/', problem_views.like_problem, name='like-problem'),
    path('rate/<int:pk>/', problem_views.rate_problem, name='rate-problem'),
    path('memo/<int:pk>/', problem_views.memo_problem, name='memo-problem'),
    path('tag/<int:pk>/', problem_views.tag_problem, name='tag-problem'),
    path('collect/<int:pk>/', problem_views.collect_problem, name='collect-problem'),

    path('collection/', problem_views.collection_list_view, name='collection-list'),
    path('collection/create/', problem_views.collection_create, name='collection-create'),
    path('collection/<int:pk>/', problem_views.collection_detail_view, name='collection-detail'),
]

answer_patterns = [
    path('', answer_views.list_view, name='answer-list'),
    path('<int:pk>/', answer_views.detail_view, name='answer-detail'),
    path('input/<int:pk>/<str:subject_field>/', answer_views.answer_input_view, name='answer-input'),
    path('confirm/<int:pk>/<str:subject_field>/', answer_views.answer_confirm_view, name='answer-confirm'),
]

staff_patterns = [
    path('', staff_views.menu_list_view, name='staff-menu'),
    path('create/exam/', staff_views.exam_create_view, name='staff-exam-create'),

    path('detail/<int:pk>/', staff_views.detail_view, name='staff-detail'),
    path('detail/student/<int:pk>/', staff_views.detail_student_view, name='staff-detail-student'),
    path('detail/student/print/<int:pk>/', staff_views.detail_student_print_view, name='staff-detail-student-print'),
    path('update/<int:pk>/', staff_views.update_view, name='staff-update'),

    path('print/statistics/<int:pk>/', staff_views.statistics_print_view, name='staff-statistics-print'),
    path('print/catalog/<int:pk>/', staff_views.catalog_print_view, name='staff-catalog-print'),
    path('print/answers/<int:pk>/', staff_views.answers_print_view, name='staff-answers-print'),

    path('export/statistics/excel/<int:pk>/',
         staff_views.export_statistics_excel_view, name='staff-export-statistics-excel'),
    path('export/catalog/excel/<int:pk>/',
         staff_views.export_catalog_excel_view, name='staff-export-catalog-excel'),
    path('export/answers/excel/<int:pk>/', staff_views.export_answers_excel_view, name='staff-export-answers-excel'),
]

urlpatterns = [
    path('problem/', include(problem_patterns)),
    path('answer/', include(answer_patterns)),
    path('staff/', include(staff_patterns)),
    # path('rank/<int:pk>/', answer_views.rank_verify, name='rank-verify'),
]
