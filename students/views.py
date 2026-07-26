from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.views import View
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.db import models as db_models
from .models import Student
from .forms import StudentForm


class StaffTestMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role in ('SUPER_ADMIN', 'MANAGER', 'RECEPTIONIST')


class StudentListView(StaffTestMixin, ListView):
    model = Student
    template_name = 'students/student_list.html'
    context_object_name = 'students'
    paginate_by = 20

    def get_queryset(self):
        queryset = Student.objects.select_related('user', 'course', 'branch', 'instructor')
        status = self.request.GET.get('status')
        search = self.request.GET.get('search')
        branch = self.request.GET.get('branch')
        if status:
            queryset = queryset.filter(status=status)
        if branch:
            queryset = queryset.filter(branch_id=branch)
        if search:
            queryset = queryset.filter(
                db_models.Q(student_number__icontains=search) |
                db_models.Q(user__first_name__icontains=search) |
                db_models.Q(user__last_name__icontains=search) |
                db_models.Q(user__email__icontains=search)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = Student.STATUS_CHOICES
        context['current_status'] = self.request.GET.get('status', '')
        context['search_query'] = self.request.GET.get('search', '')
        context['branches'] = __import__('core.models', fromlist=['Branch']).Branch.objects.filter(is_active=True)
        return context


class StudentDetailView(StaffTestMixin, DetailView):
    model = Student
    template_name = 'students/student_detail.html'
    context_object_name = 'student'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        student = self.object
        from payments.models import Payment
        from lessons.models import PracticalLesson
        context['payments'] = Payment.objects.filter(student=student)[:10]
        context['lessons'] = PracticalLesson.objects.filter(student=student).order_by('-date')[:10]
        return context


class StudentCreateView(StaffTestMixin, CreateView):
    model = Student
    form_class = StudentForm
    template_name = 'students/student_form.html'
    success_url = reverse_lazy('students:list')

    def form_valid(self, form):
        messages.success(self.request, 'Student created successfully.')
        return super().form_valid(form)


class StudentUpdateView(StaffTestMixin, UpdateView):
    model = Student
    form_class = StudentForm
    template_name = 'students/student_form.html'
    success_url = reverse_lazy('students:list')

    def form_valid(self, form):
        messages.success(self.request, 'Student updated successfully.')
        return super().form_valid(form)


class StudentDeleteView(StaffTestMixin, DeleteView):
    model = Student
    template_name = 'students/student_confirm_delete.html'
    success_url = reverse_lazy('students:list')

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Student deleted successfully.')
        return super().delete(request, *args, **kwargs)


class IndexView(LoginRequiredMixin, View):
    def get(self, request):
        if request.user.role == 'STUDENT':
            return redirect('student_portal:dashboard')
        from django.db.models import Sum, Count
        from datetime import date
        from payments.models import Payment
        from admissions.models import Admission
        from vehicles.models import Vehicle
        from instructors.models import Instructor

        today = date.today()
        active_students = Student.objects.filter(status='ACTIVE')
        pending_balance_count = 0
        for s in active_students:
            if s.balance > 0:
                pending_balance_count += 1
        context = {
            'total_students': active_students.count(),
            'today_admissions': Admission.objects.filter(created_at__date=today).count(),
            'today_revenue': Payment.objects.filter(created_at__date=today, status='COMPLETED').aggregate(total=Sum('amount'))['total'] or 0,
            'total_vehicles': Vehicle.objects.filter(is_available=True).count(),
            'total_instructors': Instructor.objects.count(),
            'pending_balances': pending_balance_count,
        }
        return render(request, 'students/dashboard.html', context)
