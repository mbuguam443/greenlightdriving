from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.ReportIndexView.as_view(), name='index'),
    path('revenue/', views.RevenueReportView.as_view(), name='revenue'),
    path('admissions/', views.AdmissionReportView.as_view(), name='admissions'),
    path('outstanding/', views.OutstandingBalanceView.as_view(), name='outstanding'),
    path('instructors/', views.InstructorPerformanceView.as_view(), name='instructor_performance'),
    path('vehicles/', views.VehicleUtilizationView.as_view(), name='vehicle_utilization'),
    path('branches/', views.BranchPerformanceView.as_view(), name='branch_performance'),
    path('students/', views.StudentProgressReportView.as_view(), name='student_progress'),
]
