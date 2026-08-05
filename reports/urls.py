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
    path('activity/', views.ActivityReportView.as_view(), name='activity'),
    path('backup/', views.BackupView.as_view(), name='backup'),
    path('pdf/payments/', views.PaymentReportPDFView.as_view(), name='pdf_payments'),
    path('pdf/enquiries/', views.EnquiryReportPDFView.as_view(), name='pdf_enquiries'),
    path('pdf/students/', views.StudentReportPDFView.as_view(), name='pdf_students'),
    path('pdf/lessons/', views.LessonReportPDFView.as_view(), name='pdf_lessons'),
    path('pdf/vehicles/', views.VehicleReportPDFView.as_view(), name='pdf_vehicles'),
    path('pdf/instructors/', views.InstructorReportPDFView.as_view(), name='pdf_instructors'),
    path('pdf/admissions/', views.AdmissionReportPDFView.as_view(), name='pdf_admissions'),
    path('pdf/attendance/', views.AttendanceReportPDFView.as_view(), name='pdf_attendance'),
]
