from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Q
from .models import NTSARecord
from .forms import NTSARecordForm


class StaffTestMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role in ('SUPER_ADMIN', 'MANAGER', 'RECEPTIONIST')


class NTSAListView(StaffTestMixin, ListView):
    model = NTSARecord
    template_name = 'ntsa/ntsa_list.html'
    context_object_name = 'ntsa_records'
    paginate_by = 20

    def get_queryset(self):
        queryset = NTSARecord.objects.select_related('student', 'student__user').all()

        q = self.request.GET.get('q', '').strip()
        pdl_status = self.request.GET.get('pdl_status', '')
        licence = self.request.GET.get('licence', '')

        if q:
            queryset = queryset.filter(
                Q(student__user__first_name__icontains=q) |
                Q(student__user__last_name__icontains=q) |
                Q(student__admission_number__icontains=q)
            )
        if pdl_status:
            if pdl_status == 'not_started':
                queryset = queryset.filter(pdl_status='not_started')
            else:
                queryset = queryset.filter(pdl_status=pdl_status)
        if licence == 'issued':
            queryset = queryset.filter(licence_issued=True)
        elif licence == 'not_issued':
            queryset = queryset.filter(licence_issued=False)

        return queryset


class NTSADetailView(StaffTestMixin, DetailView):
    model = NTSARecord
    template_name = 'ntsa/ntsa_detail.html'
    context_object_name = 'record'


class NTSARecordCreateView(StaffTestMixin, CreateView):
    model = NTSARecord
    form_class = NTSARecordForm
    template_name = 'ntsa/ntsa_form.html'
    success_url = reverse_lazy('ntsa:list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from students.models import Student
        context['students'] = Student.objects.filter(status='ACTIVE').select_related('user')
        return context

    def form_valid(self, form):
        messages.success(self.request, 'NTSA record created successfully.')
        return super().form_valid(form)


class NTSARecordUpdateView(StaffTestMixin, UpdateView):
    model = NTSARecord
    form_class = NTSARecordForm
    template_name = 'ntsa/ntsa_form.html'
    success_url = reverse_lazy('ntsa:list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from students.models import Student
        context['students'] = Student.objects.filter(status='ACTIVE').select_related('user')
        return context

    def form_valid(self, form):
        messages.success(self.request, 'NTSA record updated successfully.')
        return super().form_valid(form)


class NTSARecordDeleteView(StaffTestMixin, DeleteView):
    model = NTSARecord
    template_name = 'ntsa/ntsa_confirm_delete.html'
    success_url = reverse_lazy('ntsa:list')

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'NTSA record deleted successfully.')
        return super().delete(request, *args, **kwargs)
