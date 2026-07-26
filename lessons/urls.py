from django.urls import path
from . import views

app_name = 'lessons'

urlpatterns = [
    path('', views.LessonListView.as_view(), name='list'),
    path('theory/', views.TheoryLessonListView.as_view(), name='theory_list'),
    path('practical/create/', views.PracticalLessonCreateView.as_view(), name='practical_create'),
    path('theory/create/', views.TheoryLessonCreateView.as_view(), name='theory_create'),
]
