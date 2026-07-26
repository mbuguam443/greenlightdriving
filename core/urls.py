from django.urls import path
from django.views.generic import ListView
from core.models import Branch

app_name = 'core'

urlpatterns = [
    path('branches/', ListView.as_view(model=Branch, template_name='core/branch_list.html', context_object_name='branches', paginate_by=12), name='branch_list'),
]
