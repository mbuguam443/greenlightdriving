from django.urls import path
from . import views

app_name = 'lessons'

urlpatterns = [
    path('', views.LessonListView.as_view(), name='list'),
    path('theory/', views.TheoryLessonListView.as_view(), name='theory_list'),
    path('practical/create/', views.PracticalLessonCreateView.as_view(), name='practical_create'),
    path('practical/<int:pk>/update/', views.PracticalLessonUpdateView.as_view(), name='practical_update'),
    path('practical/<int:pk>/quick-status/', views.PracticalLessonQuickStatusView.as_view(), name='practical_quick_status'),
    path('practical/<int:pk>/delete/', views.PracticalLessonDeleteView.as_view(), name='practical_delete'),
    path('practical/<int:pk>/attendance/', views.PracticalLessonAttendanceView.as_view(), name='practical_attendance'),
    path('theory/create/', views.TheoryLessonCreateView.as_view(), name='theory_create'),
    path('theory/<int:pk>/update/', views.TheoryLessonUpdateView.as_view(), name='theory_update'),
    path('theory/<int:pk>/delete/', views.TheoryLessonDeleteView.as_view(), name='theory_delete'),
    path('theory/<int:pk>/attendance/', views.TheoryLessonAttendanceView.as_view(), name='theory_attendance'),
    path('theory/<int:pk>/quick-status/', views.TheoryLessonQuickStatusView.as_view(), name='theory_quick_status'),
]
