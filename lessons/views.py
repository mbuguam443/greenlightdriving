from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views import View
from django.views.generic import ListView, CreateView
from django.urls import reverse_lazy
from django.db import models
from .models import PracticalLesson, TheoryLesson, LessonItem
from .forms import PracticalLessonForm, TheoryLessonForm


class StaffTestMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role in ('SUPER_ADMIN', 'MANAGER', 'INSTRUCTOR', 'RECEPTIONIST')


class LessonListView(StaffTestMixin, ListView):
    model = PracticalLesson
    template_name = 'lessons/lesson_list.html'
    context_object_name = 'lessons'
    paginate_by = 20

    def get_queryset(self):
        return PracticalLesson.objects.select_related('student', 'student__user', 'lesson_item', 'instructor').all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['lesson_items'] = LessonItem.objects.filter(is_active=True)
        context['active_tab'] = 'practical'
        return context


class TheoryLessonListView(StaffTestMixin, ListView):
    model = TheoryLesson
    template_name = 'lessons/theory_list.html'
    context_object_name = 'lessons'
    paginate_by = 20

    def get_queryset(self):
        return TheoryLesson.objects.select_related('student', 'student__user', 'instructor').all()


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

    def form_valid(self, form):
        from django.contrib import messages
        messages.success(self.request, 'Lesson scheduled successfully.')
        return super().form_valid(form)


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
