from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.views import View
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.db import models
from django.utils import timezone
from datetime import timedelta
from .models import PracticalLesson, TheoryLesson, LessonItem
from .forms import PracticalLessonForm, TheoryLessonForm


class StaffTestMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role in ('SUPER_ADMIN', 'MANAGER', 'INSTRUCTOR', 'RECEPTIONIST')


class LessonListView(StaffTestMixin, ListView):
    model = PracticalLesson
    template_name = 'lessons/lesson_list.html'
    context_object_name = 'lessons'
    paginate_by = 50

    def get_queryset(self):
        qs = PracticalLesson.objects.select_related(
            'student', 'student__user', 'lesson_item',
            'instructor', 'instructor__user', 'vehicle',
        ).all()
        status = self.request.GET.get('status')
        search = self.request.GET.get('search')
        date_f = self.request.GET.get('date')
        instructor_f = self.request.GET.get('instructor')
        if status:
            qs = qs.filter(status=status)
        if search:
            qs = qs.filter(
                models.Q(student__user__first_name__icontains=search) |
                models.Q(student__user__last_name__icontains=search) |
                models.Q(student__student_number__icontains=search)
            )
        if date_f:
            qs = qs.filter(date=date_f)
        if instructor_f:
            qs = qs.filter(instructor_id=instructor_f)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from instructors.models import Instructor
        context['instructors'] = Instructor.objects.select_related('user').all()
        context['status_filter'] = self.request.GET.get('status', '')
        context['search_query'] = self.request.GET.get('search', '')
        context['date_filter'] = self.request.GET.get('date', '')
        context['instructor_filter'] = self.request.GET.get('instructor', '')
        context['active_tab'] = 'practical'

        lessons = context['lessons']
        grouped = {}
        for lesson in lessons:
            sid = lesson.student_id
            if sid not in grouped:
                grouped[sid] = {'student': lesson.student, 'lessons': [], 'completed': 0}
            grouped[sid]['lessons'].append(lesson)
            if lesson.status == 'COMPLETED':
                grouped[sid]['completed'] += 1
        context['grouped_lessons'] = list(grouped.values())
        return context


class TheoryLessonListView(StaffTestMixin, ListView):
    model = TheoryLesson
    template_name = 'lessons/theory_list.html'
    context_object_name = 'lessons'
    paginate_by = 20

    def get_queryset(self):
        return TheoryLesson.objects.select_related(
            'student', 'student__user', 'instructor', 'instructor__user'
        ).all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from instructors.models import Instructor
        context['instructors'] = Instructor.objects.select_related('user').all()
        context['active_tab'] = 'theory'
        return context


class PracticalLessonCreateView(StaffTestMixin, CreateView):
    model = PracticalLesson
    form_class = PracticalLessonForm
    template_name = 'lessons/lesson_form.html'
    success_url = reverse_lazy('lessons:list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from students.models import Student
        from instructors.models import Instructor
        from vehicles.models import Vehicle
        context['students'] = Student.objects.filter(status='ACTIVE').select_related('user')
        context['instructors'] = Instructor.objects.select_related('user')
        context['vehicles'] = Vehicle.objects.filter(is_available=True)
        context['lesson_items'] = LessonItem.objects.filter(is_active=True)
        return context

    def get_initial(self):
        initial = super().get_initial()
        from students.models import Student
        student_id = self.request.GET.get('student')
        if student_id:
            student = Student.objects.filter(pk=student_id).first()
            if student:
                initial['student'] = student.pk
                initial['instructor'] = student.instructor_id
                initial['vehicle'] = student.vehicle_id
                initial['date'] = timezone.now().date() + timedelta(days=1)
        return initial

    def form_valid(self, form):
        from django.contrib import messages
        from django.db import IntegrityError

        if self.request.POST.get('bulk'):
            student_ids = self.request.POST.getlist('students')
            if not student_ids:
                messages.error(self.request, 'Select at least one student.')
                return self.form_invalid(form)
            created = 0
            skipped = 0
            for sid in student_ids:
                try:
                    lesson = form.save(commit=False)
                    lesson.pk = None
                    lesson.student_id = int(sid)
                    lesson.save()
                    created += 1
                except IntegrityError:
                    skipped += 1
            messages.success(self.request, f'{created} lessons created. {skipped} skipped (already existed).')
            return redirect(self.success_url)

        try:
            response = super().form_valid(form)
            self._notify(form.instance, 'created')
            messages.success(self.request, 'Lesson saved successfully.')
            return response
        except IntegrityError:
            messages.error(self.request, 'This lesson already exists for this student.')
            return self.form_invalid(form)

    def _notify(self, lesson, action):
        from student_portal.models import Notification
        Notification.objects.create(
            student=lesson.student,
            title=f'New Lesson: {lesson.lesson_item.name}',
            message=f'A new practical lesson "{lesson.lesson_item.name}" has been added for {lesson.date.strftime("%d %b %Y")}.',
            notification_type='lesson',
        )


class TheoryLessonCreateView(StaffTestMixin, CreateView):
    model = TheoryLesson
    form_class = TheoryLessonForm
    template_name = 'lessons/theory_form.html'
    success_url = reverse_lazy('lessons:theory_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from students.models import Student
        from instructors.models import Instructor
        context['students'] = Student.objects.filter(status='ACTIVE').select_related('user')
        context['instructors'] = Instructor.objects.select_related('user')
        return context

    def get_initial(self):
        initial = super().get_initial()
        from students.models import Student
        student_id = self.request.GET.get('student')
        if student_id:
            student = Student.objects.filter(pk=student_id).first()
            if student:
                initial['student'] = student.pk
                initial['instructor'] = student.instructor_id
                initial['date'] = timezone.now().date() + timedelta(days=1)
        return initial

    def form_valid(self, form):
        from django.contrib import messages
        response = super().form_valid(form)
        messages.success(self.request, 'Theory lesson saved successfully.')
        return response



class PracticalLessonUpdateView(StaffTestMixin, UpdateView):
    model = PracticalLesson
    form_class = PracticalLessonForm
    template_name = 'lessons/lesson_update.html'
    success_url = reverse_lazy('lessons:list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from students.models import Student
        from instructors.models import Instructor
        from vehicles.models import Vehicle
        context['students'] = Student.objects.filter(status='ACTIVE').select_related('user')
        context['instructors'] = Instructor.objects.select_related('user')
        context['vehicles'] = Vehicle.objects.filter(is_available=True)

        lesson_items = LessonItem.objects.filter(is_active=True)
        student_id = self.request.GET.get('student') or (self.request.POST.get('student') if self.request.method == 'POST' else None)
        if student_id:
            existing = PracticalLesson.objects.filter(student_id=student_id).values_list('lesson_item_id', flat=True)
            lesson_items = lesson_items.exclude(id__in=existing)
        context['lesson_items'] = lesson_items
        return context

    def form_valid(self, form):
        messages.success(self.request, 'Lesson updated successfully.')
        return super().form_valid(form)


class PracticalLessonQuickStatusView(StaffTestMixin, View):
    def post(self, request, pk):
        lesson = get_object_or_404(PracticalLesson, pk=pk)
        new_status = request.POST.get('status', '')
        if new_status in dict(PracticalLesson.STATUS_CHOICES):
            lesson.status = new_status
            if new_status == 'COMPLETED':
                from django.utils import timezone
                lesson.completed_at = timezone.now()
            lesson.save()
            messages.success(request, f'{lesson.lesson_item.name} → {lesson.get_status_display()}')
        return redirect('lessons:list')


class TheoryLessonUpdateView(StaffTestMixin, UpdateView):
    model = TheoryLesson
    form_class = TheoryLessonForm
    template_name = 'lessons/theory_update.html'
    success_url = reverse_lazy('lessons:theory_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from students.models import Student
        from instructors.models import Instructor
        context['students'] = Student.objects.filter(status='ACTIVE').select_related('user')
        context['instructors'] = Instructor.objects.select_related('user')
        return context

    def form_valid(self, form):
        from django.contrib import messages
        messages.success(self.request, 'Theory lesson updated successfully.')
        return super().form_valid(form)



class PracticalLessonDeleteView(StaffTestMixin, DeleteView):
    model = PracticalLesson

    def get(self, request, *args, **kwargs):
        return self.delete(request, *args, **kwargs)

    def get_success_url(self):
        if self.object and self.object.student:
            return reverse_lazy('students:detail', kwargs={'pk': self.object.student.pk})
        return reverse_lazy('lessons:list')

    def form_valid(self, form):
        messages.success(self.request, 'Lesson deleted.')
        return super().form_valid(form)


class TheoryLessonDeleteView(StaffTestMixin, DeleteView):
    model = TheoryLesson

    def get(self, request, *args, **kwargs):
        return self.delete(request, *args, **kwargs)

    def get_success_url(self):
        if self.object and self.object.student:
            return reverse_lazy('students:detail', kwargs={'pk': self.object.student.pk})
        return reverse_lazy('lessons:theory_list')

    def form_valid(self, form):
        messages.success(self.request, 'Theory lesson deleted.')
        return super().form_valid(form)



class PracticalLessonAttendanceView(StaffTestMixin, View):
    def get(self, request, pk):
        lesson = get_object_or_404(PracticalLesson, pk=pk)
        lesson.attended = not lesson.attended
        if lesson.attended:
            from django.utils import timezone
            lesson.completed_at = timezone.now()
        else:
            lesson.completed_at = None
        lesson.save(update_fields=['attended', 'completed_at'])
        messages.success(request, f'{lesson.lesson_item.name} attendance: {"Present" if lesson.attended else "Absent"}')
        return redirect('lessons:list')



class TheoryLessonAttendanceView(StaffTestMixin, View):
    def get(self, request, pk):
        lesson = get_object_or_404(TheoryLesson, pk=pk)
        lesson.attended = not lesson.attended
        lesson.save(update_fields=['attended'])
        messages.success(request, f'Theory attendance: {"Present" if lesson.attended else "Absent"}')
        return redirect('lessons:theory_list')
