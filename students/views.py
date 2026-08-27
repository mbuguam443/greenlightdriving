import json

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.views import View
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.db import models as db_models
from django.utils import timezone
from datetime import timedelta
from .models import Student, StudentEnrollment
from .forms import StudentForm, StudentEnrollmentForm


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
        from accounts.models import User
        context['status_choices'] = Student.STATUS_CHOICES
        context['current_status'] = self.request.GET.get('status', '')
        context['search_query'] = self.request.GET.get('search', '')
        context['branches'] = __import__('core.models', fromlist=['Branch']).Branch.objects.filter(is_active=True)
        context['registered_students'] = User.objects.filter(
            role='STUDENT', student_profile__isnull=True
        ).order_by('-created_at')
        return context


class StudentDetailView(StaffTestMixin, DetailView):
    model = Student
    template_name = 'students/student_detail.html'
    context_object_name = 'student'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        student = self.object
        from payments.models import Payment
        from lessons.models import PracticalLesson, TheoryLesson
        context['payments'] = Payment.objects.filter(student=student)[:10]
        context['practical_lessons'] = PracticalLesson.objects.filter(student=student).select_related('lesson_item', 'instructor__user', 'vehicle').order_by('lesson_item__order')
        context['theory_lessons'] = TheoryLesson.objects.filter(student=student).select_related('instructor__user').order_by('date')
        context['practical_completed'] = PracticalLesson.objects.filter(student=student, status='COMPLETED').count()
        context['practical_total'] = PracticalLesson.objects.filter(student=student).count()
        context['practical_percentage'] = int((context['practical_completed'] / context['practical_total'] * 100) if context['practical_total'] else 0)
        context['theory_completed'] = TheoryLesson.objects.filter(student=student, status='COMPLETED').count()
        context['theory_total'] = TheoryLesson.objects.filter(student=student).count()
        context['theory_percentage'] = int((context['theory_completed'] / context['theory_total'] * 100) if context['theory_total'] else 0)
        context['enrollments'] = StudentEnrollment.objects.filter(student=student).select_related('course', 'branch')
        return context


class StudentCreateView(StaffTestMixin, CreateView):
    model = Student
    form_class = StudentForm
    template_name = 'students/student_form.html'
    success_url = reverse_lazy('students:list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from website.models import Course, CourseCategory
        from core.models import Branch
        from instructors.models import Instructor
        context['courses'] = Course.objects.filter(is_active=True)
        context['categories'] = CourseCategory.objects.all()
        context['branches'] = Branch.objects.filter(is_active=True)
        context['instructors'] = Instructor.objects.select_related('user')
        return context

    def form_valid(self, form):
        from django.contrib.auth import get_user_model
        from django.utils.crypto import get_random_string
        UserModel = get_user_model()

        first_name = form.cleaned_data['first_name'].strip()
        last_name = form.cleaned_data['last_name'].strip()
        phone = (form.cleaned_data.get('phone') or '').strip()
        email = ((form.cleaned_data.get('email') or '').strip().lower() or None)

        user = UserModel(
            email=email or f"student-{get_random_string(8).lower()}@greenlight.local",
            username=f"STU-{get_random_string(10).upper()}",
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            role='STUDENT',
            is_active=True,
        )
        default_pass = get_random_string(10)
        user.set_password(default_pass)
        user.save()

        student = form.save(commit=False)
        student.user = user
        student.save()
        form.save_m2m()

        # Generate lessons for the student's package
        from lessons.models import LessonItem, PracticalLesson, TheoryLesson
        from datetime import date, timedelta
        package_lesson_map = {
            'TEST': LessonItem.objects.filter(is_active=True, lesson_type='THEORY'),
            'HALF': LessonItem.objects.filter(is_active=True).exclude(lesson_type='ASSESSMENT').exclude(order__gte=11),
            'FULL': LessonItem.objects.filter(is_active=True),
        }
        lesson_items = package_lesson_map.get(student.package_choice, LessonItem.objects.none())
        lesson_date = date.today() + timedelta(days=1)
        for item in lesson_items:
            if item.lesson_type == 'PRACTICAL':
                PracticalLesson.objects.create(
                    student=student, lesson_item=item,
                    instructor=student.instructor, vehicle=student.vehicle,
                    date=lesson_date, status='NOT_STARTED',
                )
                lesson_date += timedelta(days=2)
            elif item.lesson_type == 'THEORY':
                TheoryLesson.objects.create(
                    student=student, lesson_item=item, topic=item.name,
                    instructor=student.instructor, date=lesson_date,
                    time_start='08:00', time_end='09:00', status='NOT_STARTED',
                )
                lesson_date += timedelta(days=1)

        messages.success(self.request, f'Student {user.full_name} created. Login account created with temporary password: {default_pass}')
        return redirect('students:detail', pk=student.pk)


class StudentEnrollmentCreateView(StaffTestMixin, CreateView):
    model = StudentEnrollment
    form_class = StudentEnrollmentForm
    template_name = 'students/enrollment_form.html'

    def dispatch(self, request, *args, **kwargs):
        self.student = get_object_or_404(Student, pk=kwargs['student_pk'])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.student = self.student
        response = super().form_valid(form)
        self._create_lessons(form.instance)
        messages.success(self.request, f'{self.student.user.full_name} enrolled in {form.instance.course.name}.')
        return response

    def get_success_url(self):
        return reverse_lazy('students:detail', kwargs={'pk': self.student.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['student'] = self.student
        return context

    def _create_lessons(self, enrollment):
        from datetime import date, timedelta
        from lessons.models import LessonItem, PracticalLesson, TheoryLesson
        package_lesson_map = {
            'TEST': LessonItem.objects.filter(is_active=True, lesson_type='THEORY'),
            'HALF': LessonItem.objects.filter(is_active=True).exclude(lesson_type='ASSESSMENT').exclude(order__gte=11),
            'FULL': LessonItem.objects.filter(is_active=True),
        }
        lesson_items = package_lesson_map.get(enrollment.package_choice, LessonItem.objects.none())
        lesson_date = date.today() + timedelta(days=1)
        for item in lesson_items:
            if item.lesson_type == 'PRACTICAL':
                PracticalLesson.objects.create(
                    student=self.student, enrollment=enrollment, lesson_item=item,
                    instructor=enrollment.instructor, vehicle=enrollment.vehicle,
                    date=lesson_date, status='NOT_STARTED',
                )
                lesson_date += timedelta(days=2)
            elif item.lesson_type == 'THEORY':
                TheoryLesson.objects.create(
                    student=self.student, enrollment=enrollment, lesson_item=item,
                    topic=item.name, instructor=enrollment.instructor, date=lesson_date,
                    time_start='08:00', time_end='09:00', status='NOT_STARTED',
                )
                lesson_date += timedelta(days=1)


class StudentUpdateView(StaffTestMixin, UpdateView):
    model = Student
    form_class = StudentForm
    template_name = 'students/student_form.html'
    success_url = reverse_lazy('students:list')

    def get_initial(self):
        initial = super().get_initial()
        user = self.object.user
        initial['first_name'] = user.first_name
        initial['last_name'] = user.last_name
        initial['phone'] = user.phone
        initial['email'] = user.email
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from website.models import Course, CourseCategory
        from core.models import Branch
        from instructors.models import Instructor
        context['courses'] = Course.objects.filter(is_active=True)
        context['categories'] = CourseCategory.objects.all()
        context['branches'] = Branch.objects.filter(is_active=True)
        context['instructors'] = Instructor.objects.select_related('user')
        return context

    def form_valid(self, form):
        user = self.object.user
        user.first_name = form.cleaned_data['first_name'].strip()
        user.last_name = form.cleaned_data['last_name'].strip()
        user.phone = (form.cleaned_data.get('phone') or '').strip()
        email = ((form.cleaned_data.get('email') or '').strip().lower() or None)
        if email:
            user.email = email
        user.save()
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
        from lessons.models import PracticalLesson, TheoryLesson

        today = date.today()
        active_students = Student.objects.filter(status='ACTIVE')
        pending_balance_count = 0
        for s in active_students:
            if s.balance > 0:
                pending_balance_count += 1

        # Recent payments as activity
        recent_payments = Payment.objects.filter(status='COMPLETED').order_by('-created_at')[:5]
        recent_activities = []
        for p in recent_payments:
            recent_activities.append({
                'description': f"Payment of KES {p.amount:,.0f} received from {p.student.user.full_name} ({p.receipt_number})",
                'timestamp': p.created_at,
            })

        # Today's lessons
        today_lessons = list(PracticalLesson.objects.filter(date=today).select_related('student__user', 'instructor__user', 'vehicle')[:5])
        today_lessons += list(TheoryLesson.objects.filter(date=today).select_related('student__user', 'instructor__user')[:5])
        today_lessons.sort(key=lambda x: x.date if hasattr(x, 'date') else x.created_at, reverse=True)

        # Revenue last 7 days for chart
        from datetime import timedelta
        revenue_labels = []
        revenue_data = []
        for i in range(6, -1, -1):
            day = today - timedelta(days=i)
            day_total = Payment.objects.filter(created_at__date=day, status='COMPLETED').aggregate(total=Sum('amount'))['total'] or 0
            revenue_labels.append(day.strftime('%a'))
            revenue_data.append(float(day_total))

        # Course distribution for chart
        from website.models import Course
        course_labels = []
        course_data = []
        for course in Course.objects.all():
            count = Student.objects.filter(course=course, status='ACTIVE').count()
            if count > 0:
                course_labels.append(course.name[:15])
                course_data.append(count)

        context = {
            'total_students': active_students.count(),
            'today_admissions': Admission.objects.filter(created_at__date=today).count(),
            'today_revenue': Payment.objects.filter(created_at__date=today, status='COMPLETED').aggregate(total=Sum('amount'))['total'] or 0,
            'total_revenue': Payment.objects.filter(status='COMPLETED').aggregate(total=Sum('amount'))['total'] or 0,
            'total_vehicles': Vehicle.objects.filter(is_available=True).count(),
            'total_instructors': Instructor.objects.filter(is_active=True).count(),
            'pending_balances': pending_balance_count,
            'recent_activities': recent_activities,
            'today_lessons': today_lessons,
            'revenue_labels': revenue_labels,
            'revenue_data': revenue_data,
            'revenue_labels_json': json.dumps(revenue_labels),
            'revenue_data_json': json.dumps(revenue_data),
            'course_labels': course_labels,
            'course_data': course_data,
        }
        return render(request, 'students/dashboard.html', context)



class GenerateLessonsView(StaffTestMixin, View):

    def get(self, request, pk):
        from lessons.models import PracticalLesson, TheoryLesson, LessonItem
        student = get_object_or_404(Student, pk=pk)
        package_lesson_map = {
            'TEST': LessonItem.objects.filter(is_active=True, lesson_type='THEORY'),
            'HALF': LessonItem.objects.filter(is_active=True).exclude(
                lesson_type__in=['ASSESSMENT']).exclude(order__gte=11),
            'FULL': LessonItem.objects.filter(is_active=True),
        }
        lesson_items = package_lesson_map.get(student.package_choice, [])
        lesson_date = timezone.now().date() + timedelta(days=1)
        created = 0
        for item in lesson_items:
            if item.lesson_type == 'PRACTICAL':
                if not PracticalLesson.objects.filter(student=student, lesson_item=item).exists():
                    PracticalLesson.objects.create(
                        student=student, lesson_item=item,
                        instructor=student.instructor, vehicle=student.vehicle,
                        date=lesson_date, status='NOT_STARTED',
                    )
                    lesson_date += timedelta(days=2)
                    created += 1
            else:
                if not TheoryLesson.objects.filter(student=student, lesson_item=item).exists():
                    TheoryLesson.objects.create(
                        student=student, lesson_item=item, topic=item.name,
                        instructor=student.instructor, date=lesson_date,
                        time_start='08:00', time_end='09:00', status='NOT_STARTED',
                    )
                    lesson_date += timedelta(days=1)
                    created += 1

        messages.success(request, f'{created} lessons generated for {student.user.full_name}.')
        return redirect('students:detail', pk=student.pk)



class ToggleReminderView(StaffTestMixin, View):
    def get(self, request, pk):
        student = get_object_or_404(Student, pk=pk)
        student.payment_reminder = not student.payment_reminder
        student.save(update_fields=['payment_reminder'])
        status = 'ON' if student.payment_reminder else 'OFF'

        if student.payment_reminder and student.balance > 0:
            from student_portal.models import Notification
            from student_portal.push import send_push
            message = f'Your outstanding balance is KES {student.balance:,.0f}. Please clear it to proceed with lessons and exams.'
            Notification.objects.create(
                student=student,
                title='Payment Reminder',
                message=message,
                notification_type='payment',
            )
            send_push(student, 'Payment Reminder', message)

        messages.success(request, f'Payment reminder {status} for {student.user.full_name}.')
        return redirect('students:detail', pk=student.pk)


class RemindAllView(StaffTestMixin, View):
    def get(self, request):
        from student_portal.models import Notification
        ids = [s.id for s in Student.objects.all() if s.balance > 0]
        students = list(Student.objects.filter(id__in=ids))
        count = len(students)
        Student.objects.filter(id__in=ids).update(payment_reminder=True)

        existing = set(
            Notification.objects.filter(student_id__in=ids, title='Payment Reminder', is_read=False)
            .values_list('student_id', flat=True)
        )
        notifications = [
            Notification(
                student=s,
                title='Payment Reminder',
                message=f'Your outstanding balance is KES {s.balance:,.0f}. Please clear it to proceed with lessons and exams.',
                notification_type='payment',
            )
            for s in students if s.id not in existing
        ]
        if notifications:
            Notification.objects.bulk_create(notifications)
            from student_portal.push import send_push
            for n in notifications:
                send_push(n.student, n.title, n.message)

        messages.success(request, f'Payment reminder enabled for {count} student(s) with an outstanding balance.')
        return redirect('students:list')


class ClearAllRemindersView(StaffTestMixin, View):
    def get(self, request):
        Student.objects.update(payment_reminder=False)
        messages.success(request, 'Payment reminders cleared for all students.')
        return redirect('students:list')


class UpdateDiscountView(StaffTestMixin, View):
    def post(self, request, pk):
        student = get_object_or_404(Student, pk=pk)
        try:
            discount = float(request.POST.get('discount', 0) or 0)
        except (ValueError, TypeError):
            discount = 0
        student.discount = max(discount, 0)
        student.discount_reason = request.POST.get('discount_reason', '')
        student.discount_description = request.POST.get('discount_description', '')
        student.save(update_fields=['discount', 'discount_reason', 'discount_description'])
        if student.discount > 0:
            messages.success(request, f'Discount of KES {student.discount:,.0f} applied for {student.user.full_name}.')
        else:
            messages.success(request, f'Discount removed for {student.user.full_name}.')
        return redirect('students:detail', pk=student.pk)
