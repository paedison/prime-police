from django.urls import path, include

from .views import result_views, staff_views

app_name = 'mock'

result_patterns = [
    path('', result_views.index_view, name='index'),
]

staff_patterns = [
    path('', staff_views.list_view, name='staff-list'),
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
    path('staff/', include(staff_patterns)),
    path('result/', include(result_patterns)),
]
