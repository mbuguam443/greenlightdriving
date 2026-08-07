from django.urls import path
from . import views

app_name = 'student_portal'

urlpatterns = [
    path('', views.PortalDashboardView.as_view(), name='dashboard'),
    path('schedule/', views.PortalScheduleView.as_view(), name='schedule'),
    path('lessons/', views.PortalLessonsView.as_view(), name='lessons'),
    path('payments/', views.PortalPaymentsView.as_view(), name='payments'),
    path('progress/', views.PortalProgressView.as_view(), name='progress'),
    path('certificates/', views.PortalCertificatesView.as_view(), name='certificates'),
    path('documents/', views.PortalDocumentsView.as_view(), name='documents'),
    path('events/', views.PortalEventsView.as_view(), name='events'),
    path('reports/progress/', views.PortalProgressReportPDFView.as_view(), name='report_progress'),
    path('reports/payment/', views.PortalPaymentReportPDFView.as_view(), name='report_payment'),
    path('reports/enrollment/', views.PortalEnrollmentReportPDFView.as_view(), name='report_enrollment'),
    path('reports/attendance/', views.PortalAttendanceReportPDFView.as_view(), name='report_attendance'),
    path('notifications/', views.PortalNotificationsView.as_view(), name='notifications'),
    path('notifications/<int:pk>/read/', views.ReadNotificationView.as_view(), name='read_notification'),
    path('profile/', views.PortalProfileView.as_view(), name='profile'),
    path('manage/documents/', views.DocListView.as_view(), name='manage_documents'),
    path('manage/documents/add/', views.DocCreateView.as_view(), name='manage_document_add'),
    path('manage/documents/<int:pk>/edit/', views.DocUpdateView.as_view(), name='manage_document_edit'),
    path('manage/documents/<int:pk>/delete/', views.DocDeleteView.as_view(), name='manage_document_delete'),
    path('manage/events/', views.EventListView.as_view(), name='manage_events'),
    path('manage/events/add/', views.EventCreateView.as_view(), name='manage_event_add'),
    path('manage/events/<int:pk>/edit/', views.EventUpdateView.as_view(), name='manage_event_edit'),
    path('manage/events/<int:pk>/delete/', views.EventDeleteView.as_view(), name='manage_event_delete'),
    path('manage/notification/', views.NotificationCreateView.as_view(), name='manage_notification'),
    path('manage/notification/history/', views.NotificationHistoryView.as_view(), name='manage_notification_history'),
]
