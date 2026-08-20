from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from . import views

urlpatterns = [
    # Auth
    path('auth/register/', views.RegisterView.as_view(), name='register'),
    path('auth/login/', views.LoginView.as_view(), name='login'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Public
    path('site-info/', views.SiteInfoView.as_view(), name='site_info'),
    path('courses/', views.CourseListView.as_view(), name='courses'),
    path('course-categories/', views.CourseCategoryListView.as_view(), name='course_categories'),
    path('branches/', views.BranchListView.as_view(), name='branches'),
    path('testimonials/', views.TestimonialListView.as_view(), name='testimonials'),
    path('faqs/', views.FAQListView.as_view(), name='faqs'),
    path('blog/', views.BlogPostListView.as_view(), name='blog'),
    path('gallery/', views.GalleryListView.as_view(), name='gallery'),
    path('events/', views.PublicEventListView.as_view(), name='events'),
    path('contact/', views.ContactView.as_view(), name='contact'),

    # Student
    path('student/dashboard/', views.StudentDashboardView.as_view(), name='student_dashboard'),
    path('student/lessons/', views.StudentLessonsView.as_view(), name='student_lessons'),
    path('student/lessons/<int:pk>/attendance/', views.StudentAttendanceView.as_view(), name='student_attendance'),
    path('student/payments/', views.StudentPaymentsView.as_view(), name='student_payments'),
    path('student/mpesa/initiate/', views.StudentMpesaInitiateView.as_view(), name='student_mpesa'),
    path('student/notifications/', views.StudentNotificationsView.as_view(), name='student_notifications'),
    path('student/notifications/<int:pk>/', views.StudentNotificationsView.as_view(), name='student_notification_action'),
    path('student/events/', views.StudentEventsView.as_view(), name='student_events'),
    path('student/documents/', views.StudentDocumentsView.as_view(), name='student_documents'),
    path('student/ntsa/', views.StudentNTSAView.as_view(), name='student_ntsa'),
    path('student/push-token/', views.StudentPushTokenView.as_view(), name='student_push_token'),
    path('student/chat/', views.StudentChatView.as_view(), name='student_chat'),
    path('student/profile/', views.StudentProfileView.as_view(), name='student_profile'),

    # Admin
    path('admin/dashboard/', views.AdminDashboardView.as_view(), name='admin_dashboard'),
    path('admin/students/', views.AdminStudentsView.as_view(), name='admin_students'),
    path('admin/students/<int:pk>/', views.AdminStudentDetailView.as_view(), name='admin_student_detail'),
    path('admin/payments/', views.AdminPaymentsView.as_view(), name='admin_payments'),
    path('admin/notifications/', views.AdminNotificationsView.as_view(), name='admin_notifications'),
    path('admin/notifications/<int:pk>/reply-read/', views.AdminMarkReplyReadView.as_view(), name='admin_mark_reply_read'),
    path('admin/chat/', views.AdminChatView.as_view(), name='admin_chat'),
    path('admin/lessons/<int:pk>/approve/', views.AdminLessonApproveView.as_view(), name='admin_lesson_approve'),
    path('admin/admissions/', views.AdminAdmissionsView.as_view(), name='admin_admissions'),
    path('admin/admissions/<int:pk>/action/', views.AdminAdmissionsView.as_view(), name='admin_admission_action'),
    path('admin/profile/', views.AdminProfileView.as_view(), name='admin_profile'),
]
