from django.urls import path
from . import views

app_name = 'students'

urlpatterns = [
    path('list/', views.StudentListView.as_view(), name='list'),
    path('create/', views.StudentCreateView.as_view(), name='create'),
    path('<int:pk>/', views.StudentDetailView.as_view(), name='detail'),
    path('<int:pk>/update/', views.StudentUpdateView.as_view(), name='update'),
    path('<int:pk>/delete/', views.StudentDeleteView.as_view(), name='delete'),
    path('<int:pk>/generate-lessons/', views.GenerateLessonsView.as_view(), name='generate_lessons'),
    path('<int:pk>/toggle-reminder/', views.ToggleReminderView.as_view(), name='toggle_reminder'),
]
