from django.urls import path
from . import views

app_name = 'admissions'

urlpatterns = [
    path('apply/', views.OnlineAdmissionView.as_view(), name='online_admission'),
    path('confirmation/<int:pk>/', views.AdmissionConfirmationView.as_view(), name='confirmation'),
    path('api/courses/', views.LoadCoursesView.as_view(), name='load_courses'),
    path('new/', views.InternalAdmissionCreateView.as_view(), name='internal_create'),
    path('', views.AdmissionListView.as_view(), name='list'),
    path('<int:pk>/', views.AdmissionDetailView.as_view(), name='detail'),
    path('<int:pk>/update/', views.AdmissionUpdateView.as_view(), name='update'),
    path('inquiries/', views.InquiryListView.as_view(), name='inquiry_list'),
    path('inquiries/create/', views.InquiryCreateView.as_view(), name='inquiry_create'),
    path('inquiries/<int:pk>/toggle/', views.InquiryToggleView.as_view(), name='inquiry_toggle'),
    path('inquiries/<int:pk>/convert/', views.InquiryConvertView.as_view(), name='inquiry_convert'),
]
