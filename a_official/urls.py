from django.urls import path, include

from a_official.views import normal_views, staff_views

app_name = 'official'

staff_problem_patterns = [
    path('list/', staff_views.problem_list_view, name='staff-official-list'),
    path('detail/<int:pk>/', staff_views.problem_detail_view, name='staff-official-detail'),

    path('create/', staff_views.official_exam_create_view, name='staff-official-exam-create'),
    path('active/<int:pk>/', staff_views.official_exam_active_view, name='staff-official-exam-active'),
    path('update/', staff_views.official_update_view, name='staff-official-update'),
]

staff_predict_patterns = [
    path('list/', staff_views.predict_list_view, name='staff-predict-list'),
    path('detail/<int:pk>/', staff_views.predict_detail_view, name='staff-predict-detail'),

    path('create/', staff_views.predict_create_view, name='staff-predict-create'),
    path('update/<int:pk>/', staff_views.predict_update_view, name='staff-predict-update'),
    path('student/<int:pk>/', staff_views.predict_student_detail_view, name='staff-predict-student-detail'),

    path('print/statistics/<int:pk>/', staff_views.predict_statistics_print, name='staff-predict-statistics-print'),
    path('print/catalog/<int:pk>/', staff_views.predict_catalog_print, name='staff-predict-catalog-print'),
    path('print/answer/<int:pk>/', staff_views.predict_answer_print, name='staff-predict-answer-print'),

    path('excel/statistics/<int:pk>/', staff_views.predict_statistics_excel, name='staff-predict-statistics-excel'),
    path('excel/prime_id/<int:pk>/', staff_views.predict_prime_id_excel, name='staff-predict-prime_id-excel'),
    path('excel/catalog/<int:pk>/', staff_views.predict_catalog_excel, name='staff-predict-catalog-excel'),
    path('excel/answer/<int:pk>/', staff_views.predict_answer_excel, name='staff-predict-answer-excel'),
]

collection_patterns = [
    path('', normal_views.collection_list_view, name='collection-list'),
    path('create/', normal_views.collection_create, name='collection-create'),
    path('<int:pk>/', normal_views.collection_detail_view, name='collection-detail'),
]

problem_patterns = [
    path('', normal_views.problem_list_view, name='base'),
    path('<int:pk>/', normal_views.problem_detail_view, name='problem-detail'),

    path('like/<int:pk>/', normal_views.like_problem, name='like-problem'),
    path('rate/<int:pk>/', normal_views.rate_problem, name='rate-problem'),
    path('solve/<int:pk>/', normal_views.solve_problem, name='solve-problem'),
    path('memo/<int:pk>/', normal_views.memo_problem, name='memo-problem'),
    path('tag/<int:pk>/', normal_views.tag_problem, name='tag-problem'),
    path('collect/<int:pk>/', normal_views.collect_problem, name='collect-problem'),

    path('collection/', include(collection_patterns)),
]

predict_patterns = [
    path('list/', normal_views.predict_list_view, name='predict-list'),
    path('detail/<int:pk>/', normal_views.predict_detail_view, name='predict-detail'),
    path('register/', normal_views.predict_register_view, name='predict-register'),

    path('answer/input/<int:pk>/<str:subject_field>/',
         normal_views.predict_answer_input_view, name='predict-answer-input'),
    path('answer/confirm/<int:pk>/<str:subject_field>/',
         normal_views.predict_answer_confirm_view, name='predict-answer-confirm'),
]

urlpatterns = [
    path('staff/problem/', include(staff_problem_patterns)),
    path('staff/predict/', include(staff_predict_patterns)),
    path('problem/', include(problem_patterns)),
    path('predict/', include(predict_patterns)),
]
