from django.contrib import admin
from .models import LessonItem, PracticalLesson, TheoryLesson


@admin.register(LessonItem)
class LessonItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'order', 'is_active')
    list_editable = ('order', 'is_active')


@admin.register(PracticalLesson)
class PracticalLessonAdmin(admin.ModelAdmin):
    list_display = ('student', 'lesson_item', 'instructor', 'date', 'status')
    list_filter = ('status', 'date')
    list_editable = ('status',)


@admin.register(TheoryLesson)
class TheoryLessonAdmin(admin.ModelAdmin):
    list_display = ('student', 'topic', 'instructor', 'date', 'time_start', 'status')
    list_filter = ('status', 'date')
