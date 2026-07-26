from django.urls import path
from . import views

app_name = 'ntsa'

urlpatterns = [
    path('', views.NTSAListView.as_view(), name='list'),
    path('<int:pk>/', views.NTSADetailView.as_view(), name='detail'),
    path('create/', views.NTSARecordCreateView.as_view(), name='create'),
    path('<int:pk>/update/', views.NTSARecordUpdateView.as_view(), name='update'),
    path('<int:pk>/delete/', views.NTSARecordDeleteView.as_view(), name='delete'),
]
