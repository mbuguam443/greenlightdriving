from django.urls import path
from . import views

app_name = 'instructors'

urlpatterns = [
    path('', views.InstructorListView.as_view(), name='list'),
    path('create/', views.InstructorCreateView.as_view(), name='create'),
    path('<int:pk>/', views.InstructorDetailView.as_view(), name='detail'),
    path('<int:pk>/update/', views.InstructorUpdateView.as_view(), name='update'),
    path('<int:pk>/delete/', views.InstructorDeleteView.as_view(), name='delete'),
]
