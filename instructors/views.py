from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Q
from .models import Instructor
from .forms import InstructorForm


class StaffTestMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role in ('SUPER_ADMIN', 'MANAGER', 'RECEPTIONIST', 'READ_ONLY_ADMIN')


class InstructorListView(StaffTestMixin, ListView):
    model = Instructor
    template_name = 'instructors/instructor_list.html'
    context_object_name = 'instructors'
    paginate_by = 20

    def get_queryset(self):
        queryset = Instructor.objects.select_related('user').all()

        q = self.request.GET.get('q', '').strip()
        status = self.request.GET.get('status', '')
        experience = self.request.GET.get('experience', '')

        if q:
            queryset = queryset.filter(
                Q(user__first_name__icontains=q) |
                Q(user__last_name__icontains=q) |
                Q(license_number__icontains=q) |
                Q(phone__icontains=q)
            )
        if status == 'active':
            queryset = queryset.filter(is_active=True)
        elif status == 'inactive':
            queryset = queryset.filter(is_active=False)
        if experience == 'junior':
            queryset = queryset.filter(experience_years__lte=2)
        elif experience == 'mid':
            queryset = queryset.filter(experience_years__gte=3, experience_years__lte=5)
        elif experience == 'senior':
            queryset = queryset.filter(experience_years__gte=6)

        return queryset


class InstructorDetailView(StaffTestMixin, DetailView):
    model = Instructor
    template_name = 'instructors/instructor_detail.html'
    context_object_name = 'instructor'


class InstructorCreateView(StaffTestMixin, CreateView):
    model = Instructor
    form_class = InstructorForm
    template_name = 'instructors/instructor_form.html'
    success_url = reverse_lazy('instructors:list')

    def form_valid(self, form):
        messages.success(self.request, 'Instructor added successfully.')
        return super().form_valid(form)


class InstructorUpdateView(StaffTestMixin, UpdateView):
    model = Instructor
    form_class = InstructorForm
    template_name = 'instructors/instructor_form.html'
    success_url = reverse_lazy('instructors:list')

    def form_valid(self, form):
        messages.success(self.request, 'Instructor updated successfully.')
        return super().form_valid(form)


class InstructorDeleteView(StaffTestMixin, DeleteView):
    model = Instructor
    template_name = 'instructors/instructor_confirm_delete.html'
    success_url = reverse_lazy('instructors:list')

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Instructor deleted successfully.')
        return super().delete(request, *args, **kwargs)
