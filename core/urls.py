from django.urls import path
from django.views.generic import ListView
from core.models import Branch
from . import views

app_name = 'core'

urlpatterns = [
    path('branches/', ListView.as_view(model=Branch, template_name='core/branch_list.html', context_object_name='branches', paginate_by=12), name='branch_list'),
    path('daily-log/', views.DailyLogListView.as_view(), name='daily_log'),
    path('daily-log/create/', views.DailyLogCreateView.as_view(), name='daily_log_create'),
    path('daily-log/<int:pk>/update/', views.DailyLogUpdateView.as_view(), name='daily_log_update'),
    path('daily-log/<int:pk>/delete/', views.DailyLogDeleteView.as_view(), name='daily_log_delete'),
    path('daily-log/pdf/', views.DailyLogPDFView.as_view(), name='daily_log_pdf'),
]
