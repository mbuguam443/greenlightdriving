from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views import View
from django.views.generic import ListView, DetailView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.db import models
from .models import Admission
from .forms import OnlineAdmissionForm, AdmissionUpdateForm, InternalAdmissionForm
from website.models import Course, CourseCategory
from core.models import Branch


class OnlineAdmissionView(LoginRequiredMixin, View):

    def get(self, request):
        initial = {
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
            'email': request.user.email,
        }
        if hasattr(request.user, 'phone') and request.user.phone:
            initial['phone'] = request.user.phone
        form = OnlineAdmissionForm(initial=initial)
        return render(request, 'admissions/online_admission.html', {
            'form': form,
            'course_categories': CourseCategory.objects.all(),
            'branches': Branch.objects.filter(is_active=True),
        })

    def post(self, request):
        form = OnlineAdmissionForm(request.POST, request.FILES)

        if form.is_valid():
            admission = form.save()
            messages.success(request, f'Application submitted successfully! Your admission number is {admission.admission_number}.')
            return redirect('admissions:confirmation', pk=admission.pk)
        messages.error(request, 'Please correct the errors below.')
        return render(request, 'admissions/online_admission.html', {
            'form': form,
            'course_categories': CourseCategory.objects.all(),
            'branches': Branch.objects.filter(is_active=True),
        })


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
        old_status = self.get_object().status
        new_status = form.cleaned_data.get('status')
        response = super().form_valid(form)

        if new_status == 'APPROVED' and old_status != 'APPROVED':
            self._create_student_profile(self.object)

        if new_status:
            messages.success(self.request, f'Admission updated to {new_status}.')
        return response

    def _create_student_profile(self, admission):
        from students.models import Student
        from django.utils import timezone
        from datetime import timedelta, date
        from lessons.models import PracticalLesson, TheoryLesson, LessonItem
        from instructors.models import Instructor
        from vehicles.models import Vehicle

        from accounts.models import User
        user = User.objects.filter(email=admission.email).first()

        if not user:
            user = User(
                username=admission.email,
                email=admission.email,
                first_name=admission.first_name,
                last_name=admission.last_name,
                phone=admission.phone,
                role='STUDENT',
            )
            user.set_password('student1234')
            user.save()
            messages.success(self.request, f'New student account created: {admission.email} / student1234')

        if Student.objects.filter(user=user).exists():
            messages.warning(self.request, f'Student profile already exists for {user.email}.')
            return

        # Assign first available instructor and vehicle
        instructor = Instructor.objects.filter(is_active=True).first()
        vehicle = Vehicle.objects.filter(is_available=True).first()

        student = Student(
            user=user,
            admission=admission,
            category=admission.category,
            course=admission.course,
            package_choice=admission.package_choice,
            branch=admission.branch,
            instructor=instructor,
            vehicle=vehicle,
            status='ACTIVE',
            expected_graduation=timezone.now().date() + timedelta(days=90),
        )
        student.save()
        messages.success(self.request, f'Student profile created: {student.student_number}')

        # Auto-create lesson records based on package choice
        package_lesson_map = {
            'TEST': LessonItem.objects.filter(is_active=True, lesson_type='THEORY'),
            'HALF': LessonItem.objects.filter(is_active=True).exclude(
                lesson_type__in=['ASSESSMENT']).exclude(order__gte=11),
            'FULL': LessonItem.objects.filter(is_active=True),
        }
        lesson_items = package_lesson_map.get(admission.package_choice, [])
        lesson_date = date.today() + timedelta(days=1)
        created_count = 0
        for item in lesson_items:
            if item.lesson_type == 'PRACTICAL':
                if not PracticalLesson.objects.filter(student=student, lesson_item=item).exists():
                    PracticalLesson.objects.create(
                        student=student, lesson_item=item, instructor=instructor,
                        vehicle=vehicle, date=lesson_date, status='NOT_STARTED',
                    )
                    lesson_date += timedelta(days=2)
                    created_count += 1
            elif item.lesson_type == 'THEORY':
                if not TheoryLesson.objects.filter(student=student, lesson_item=item).exists():
                    TheoryLesson.objects.create(
                        student=student, lesson_item=item, topic=item.name,
                        instructor=instructor, date=lesson_date,
                        time_start='08:00', time_end='09:00', status='NOT_STARTED',
                    )
                    lesson_date += timedelta(days=1)
                    created_count += 1
        if created_count:
            messages.success(self.request, f'{created_count} lessons auto-created with instructor & vehicle.')


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
