from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views import View
from django.views.generic import ListView, DetailView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.db import models
from django.conf import settings
import time
from .models import Admission
from .forms import OnlineAdmissionForm, AdmissionUpdateForm, InternalAdmissionForm
from website.models import Course, CourseCategory
from core.models import Branch


class OnlineAdmissionView(View):
    FORM_LOAD_TIME = '_form_load_time'

    def get(self, request):
        form = OnlineAdmissionForm()
        # Store timestamp when form was loaded
        request.session[self.FORM_LOAD_TIME] = time.time()
        import random
        a = random.randint(1, 20)
        b = random.randint(1, 20)
        op = random.choice(['+', '-', '×'])
        if op == '+':
            answer = a + b
        elif op == '-':
            a, b = max(a, b), min(a, b)
            answer = a - b
        else:
            answer = a * b
        import hashlib
        captcha_hash = hashlib.sha256(f"{answer}{settings.SECRET_KEY}".encode()).hexdigest()[:16]
        return render(request, 'admissions/online_admission.html', {
            'form': form,
            'captcha_question': f'What is {a} {op} {b}?',
            'captcha_hash': captcha_hash,
            'captcha_answer': answer,
        })

    def post(self, request):
        form = OnlineAdmissionForm(request.POST, request.FILES)

        # Timestamp check — reject if submitted too fast (under 3 seconds)
        load_time = request.session.get(self.FORM_LOAD_TIME)
        if load_time:
            elapsed = time.time() - load_time
            if elapsed < 3:
                messages.error(request, 'Form submitted too quickly. Please take your time filling it out.')
                return render(request, 'admissions/online_admission.html', {'form': form})

        if form.is_valid():
            admission = form.save()
            del request.session[self.FORM_LOAD_TIME]
            messages.success(request, f'Application submitted successfully! Your admission number is {admission.admission_number}.')
            return redirect('admissions:confirmation', pk=admission.pk)
        messages.error(request, 'Please correct the errors below.')
        return render(request, 'admissions/online_admission.html', {'form': form})


class AdmissionConfirmationView(View):
    def get(self, request, pk):
        admission = get_object_or_404(Admission, pk=pk)
        return render(request, 'admissions/confirmation.html', {'admission': admission})


class LoadCoursesView(View):
    def get(self, request):
        category_id = request.GET.get('category_id')
        courses = list(Course.objects.filter(category_id=category_id, is_active=True).values('id', 'name'))
        return JsonResponse(courses, safe=False)


class AdmissionListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Admission
    template_name = 'admissions/admission_list.html'
    context_object_name = 'admissions'
    paginate_by = 20

    def test_func(self):
        return self.request.user.role in ('SUPER_ADMIN', 'MANAGER', 'RECEPTIONIST')

    def get_queryset(self):
        queryset = Admission.objects.all()
        status = self.request.GET.get('status')
        search = self.request.GET.get('search')
        if status:
            queryset = queryset.filter(status=status)
        if search:
            queryset = queryset.filter(
                models.Q(admission_number__icontains=search) |
                models.Q(first_name__icontains=search) |
                models.Q(last_name__icontains=search) |
                models.Q(email__icontains=search)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = Admission.STATUS_CHOICES
        context['current_status'] = self.request.GET.get('status', '')
        context['search_query'] = self.request.GET.get('search', '')
        context['branches'] = Branch.objects.all()
        context['courses'] = Course.objects.filter(is_active=True)
        context['status_filter'] = self.request.GET.get('status', '')
        context['branch_filter'] = self.request.GET.get('branch', '')
        context['course_filter'] = self.request.GET.get('course', '')
        return context


class AdmissionDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Admission
    template_name = 'admissions/admission_detail.html'
    context_object_name = 'admission'

    def test_func(self):
        return self.request.user.role in ('SUPER_ADMIN', 'MANAGER', 'RECEPTIONIST')


class AdmissionUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Admission
    form_class = AdmissionUpdateForm
    template_name = 'admissions/admission_update.html'
    success_url = reverse_lazy('admissions:list')

    def test_func(self):
        return self.request.user.role in ('SUPER_ADMIN', 'MANAGER', 'RECEPTIONIST')

    def form_valid(self, form):
        messages.success(self.request, 'Admission updated successfully.')
        return super().form_valid(form)


class InternalAdmissionCreateView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Staff-only internal admission form — no captcha, no spam protection."""

    def test_func(self):
        return self.request.user.role in ('SUPER_ADMIN', 'MANAGER', 'RECEPTIONIST')

    def get(self, request):
        form = InternalAdmissionForm()
        return render(request, 'admissions/internal_admission_form.html', {'form': form})

    def post(self, request):
        form = InternalAdmissionForm(request.POST, request.FILES)
        if form.is_valid():
            admission = form.save()
            messages.success(request, f'Admission {admission.admission_number} created successfully.')
            return redirect('admissions:detail', pk=admission.pk)
        messages.error(request, 'Please correct the errors below.')
        return render(request, 'admissions/internal_admission_form.html', {'form': form})
