from django.contrib import admin
from .models import (
    CourseCategory, Course, Testimonial, FAQ, BlogPost,
    GalleryImage, ContactMessage, SiteContent
)


@admin.register(CourseCategory)
class CourseCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'order')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('order',)


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'duration', 'full_course_price', 'is_active', 'created_at')
    list_filter = ('category', 'is_active')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ('full_course_price', 'is_active')


@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ('name', 'course', 'rating', 'is_active', 'created_at')
    list_filter = ('rating', 'is_active')
    list_editable = ('is_active',)


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ('question', 'category', 'order', 'is_active')
    list_filter = ('category', 'is_active')
    list_editable = ('order', 'is_active')
    ordering = ('order',)


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'is_published', 'views_count', 'created_at')
    list_filter = ('is_published', 'created_at')
    search_fields = ('title', 'content')
    prepopulated_fields = {'slug': ('title',)}
    list_editable = ('is_published',)
    readonly_fields = ('views_count',)


@admin.register(GalleryImage)
class GalleryImageAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'order', 'is_active')
    list_filter = ('category', 'is_active')
    list_editable = ('order', 'is_active')


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'subject', 'is_read', 'created_at')
    list_filter = ('is_read',)
    list_editable = ('is_read',)
    readonly_fields = ('name', 'email', 'phone', 'subject', 'message', 'created_at')


@admin.register(SiteContent)
class SiteContentAdmin(admin.ModelAdmin):
    list_display = ('key', 'title', 'updated_at')
    search_fields = ('key', 'title')
