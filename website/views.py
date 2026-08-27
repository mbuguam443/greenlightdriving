from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, FormView, TemplateView, CreateView, UpdateView, DeleteView
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy, reverse
from django.db.models import Q
from django.http import HttpResponse
from .models import (
    CourseCategory, Course, Testimonial, FAQ, BlogPost,
    GalleryImage, ContactMessage, SiteContent
)
from core.models import Branch, SiteSettings


class SitemapView(TemplateView):
    template_name = 'website/sitemap.xml'
    content_type = 'application/xml'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['courses'] = Course.objects.filter(is_active=True)
        context['posts'] = BlogPost.objects.filter(is_published=True)
        context['branches'] = Branch.objects.filter(is_active=True)
        context['scheme'] = self.request.scheme
        context['domain'] = self.request.get_host()
        return context


class RobotsTxtView(TemplateView):
    template_name = 'website/robots.txt'
    content_type = 'text/plain'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['scheme'] = self.request.scheme
        context['domain'] = self.request.get_host()
        return context


class StaffMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)
        if request.user.role not in ('SUPER_ADMIN', 'MANAGER', 'RECEPTIONIST', 'READ_ONLY_ADMIN'):
            from django.contrib.auth.views import redirect_to_login
            return redirect_to_login(request.get_full_path())
        return super().dispatch(request, *args, **kwargs)


# ==================== PUBLIC VIEWS ====================

class HomeView(TemplateView):
    template_name = 'website/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['featured_courses'] = Course.objects.filter(is_active=True)[:6]
        context['testimonials'] = Testimonial.objects.filter(is_active=True)[:5]
        context['branches'] = Branch.objects.filter(is_active=True)
        context['latest_posts'] = BlogPost.objects.filter(is_published=True)[:3]
        context['stats'] = {
            'students_trained': 5000,
            'vehicles': 25,
            'years_experience': 15,
            'pass_rate': 98,
        }
        return context


class AboutView(TemplateView):
    template_name = 'website/about.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            context['content'] = SiteContent.objects.get(key='about')
        except SiteContent.DoesNotExist:
            context['content'] = None
        return context


class CourseListView(ListView):
    model = Course
    template_name = 'website/courses.html'
    context_object_name = 'courses'
    paginate_by = 12

    def get_queryset(self):
        queryset = Course.objects.filter(is_active=True)
        category = self.request.GET.get('category')
        if category:
            queryset = queryset.filter(category__slug=category)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = CourseCategory.objects.all()
        context['current_category'] = self.request.GET.get('category', '')
        return context


class CourseDetailView(DetailView):
    model = Course
    template_name = 'website/course_detail.html'
    context_object_name = 'course'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['related_courses'] = Course.objects.filter(
            category=self.object.category, is_active=True
        ).exclude(pk=self.object.pk)[:3]
        return context


class PricingView(ListView):
    model = CourseCategory
    template_name = 'website/pricing.html'
    context_object_name = 'categories'

    def get_queryset(self):
        return CourseCategory.objects.prefetch_related('courses').all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['courses'] = Course.objects.filter(is_active=True).select_related('category')
        return context


class BranchListView(ListView):
    model = Branch
    template_name = 'website/branches.html'
    context_object_name = 'branches'

    def get_queryset(self):
        return Branch.objects.filter(is_active=True)


class BranchDetailView(DetailView):
    model = Branch
    template_name = 'website/branch_detail.html'
    context_object_name = 'branch'
    slug_url_kwarg = 'slug'


class GalleryView(ListView):
    model = GalleryImage
    template_name = 'website/gallery.html'
    context_object_name = 'images'
    paginate_by = 18

    def get_queryset(self):
        queryset = GalleryImage.objects.filter(is_active=True)
        category = self.request.GET.get('category')
        if category:
            queryset = queryset.filter(category=category)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['gallery_categories'] = GalleryImage.objects.filter(
            is_active=True
        ).values_list('category', flat=True).distinct()
        context['current_category'] = self.request.GET.get('category', '')
        return context


class TestimonialListView(ListView):
    model = Testimonial
    template_name = 'website/testimonials.html'
    context_object_name = 'testimonials'
    paginate_by = 12

    def get_queryset(self):
        return Testimonial.objects.filter(is_active=True)


class FAQListView(ListView):
    model = FAQ
    template_name = 'website/faq.html'
    context_object_name = 'faqs'

    def get_queryset(self):
        queryset = FAQ.objects.filter(is_active=True)
        category = self.request.GET.get('category')
        if category:
            queryset = queryset.filter(category=category)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['faq_categories'] = FAQ.CATEGORY_CHOICES
        context['current_category'] = self.request.GET.get('category', '')
        return context


class BlogListView(ListView):
    model = BlogPost
    template_name = 'website/blog.html'
    context_object_name = 'posts'
    paginate_by = 9

    def get_queryset(self):
        return BlogPost.objects.filter(is_published=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['recent_posts'] = BlogPost.objects.filter(is_published=True)[:5]
        return context


class BlogDetailView(DetailView):
    model = BlogPost
    template_name = 'website/blog_detail.html'
    context_object_name = 'post'

    def get_queryset(self):
        return BlogPost.objects.filter(is_published=True)

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        obj.views_count += 1
        obj.save(update_fields=['views_count'])
        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['recent_posts'] = BlogPost.objects.filter(
            is_published=True
        ).exclude(pk=self.object.pk)[:3]
        return context


class ContactView(FormView):
    template_name = 'website/contact.html'
    success_url = reverse_lazy('website:contact')

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, {
            'branches': Branch.objects.filter(is_active=True)
        })

    def post(self, request, *args, **kwargs):
        name = request.POST.get('name', '')
        email = request.POST.get('email', '')
        phone = request.POST.get('phone', '')
        subject = request.POST.get('subject', '')
        message_text = request.POST.get('message', '')

        if name and email and subject and message_text:
            ContactMessage.objects.create(
                name=name, email=email, phone=phone,
                subject=subject, message=message_text
            )
            messages.success(request, 'Your message has been sent. We will get back to you shortly!')
        else:
            messages.error(request, 'Please fill in all required fields.')
        
        return render(request, self.template_name, {
            'branches': Branch.objects.filter(is_active=True),
            'form_data': request.POST
        })


# ==================== MANAGEMENT VIEWS ====================

class WebIndexView(StaffMixin, TemplateView):
    template_name = 'website/manage/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_courses'] = Course.objects.count()
        context['active_courses'] = Course.objects.filter(is_active=True).count()
        context['total_posts'] = BlogPost.objects.count()
        context['published_posts'] = BlogPost.objects.filter(is_published=True).count()
        context['total_testimonials'] = Testimonial.objects.count()
        context['total_faqs'] = FAQ.objects.count()
        context['total_gallery'] = GalleryImage.objects.count()
        context['unread_messages'] = ContactMessage.objects.filter(is_read=False).count()
        context['recent_messages'] = ContactMessage.objects.all()[:5]
        return context


# CourseCategory
class CategoryListView(StaffMixin, ListView):
    model = CourseCategory
    template_name = 'website/manage/category_list.html'
    context_object_name = 'categories'


class CategoryCreateView(StaffMixin, CreateView):
    model = CourseCategory
    template_name = 'website/manage/category_form.html'
    fields = ['name', 'slug', 'description', 'order']
    success_url = reverse_lazy('website:manage_categories')


class CategoryUpdateView(StaffMixin, UpdateView):
    model = CourseCategory
    template_name = 'website/manage/category_form.html'
    fields = ['name', 'slug', 'description', 'order']
    success_url = reverse_lazy('website:manage_categories')


class CategoryDeleteView(StaffMixin, DeleteView):
    model = CourseCategory
    template_name = 'website/manage/confirm_delete.html'
    success_url = reverse_lazy('website:manage_categories')


# Course
class CourseListView2(StaffMixin, ListView):
    model = Course
    template_name = 'website/manage/course_list.html'
    context_object_name = 'courses'
    paginate_by = 20

    def get_queryset(self):
        queryset = Course.objects.select_related('category').all()
        q = self.request.GET.get('q')
        if q:
            queryset = queryset.filter(Q(name__icontains=q) | Q(category__name__icontains=q))
        return queryset


class CourseCreateView(StaffMixin, CreateView):
    model = Course
    template_name = 'website/manage/course_form.html'
    fields = ['category', 'name', 'slug', 'description', 'short_description', 'duration', 'full_course_price', 'half_course_price', 'test_only_price', 'features', 'image', 'is_active']
    success_url = reverse_lazy('website:manage_courses')

    def form_valid(self, form):
        response = super().form_valid(form)
        from django.contrib import messages
        messages.success(self.request, f'Course "{self.object.name}" created successfully!')
        return response


class CourseUpdateView(StaffMixin, UpdateView):
    model = Course
    template_name = 'website/manage/course_form.html'
    fields = ['category', 'name', 'slug', 'description', 'short_description', 'duration', 'full_course_price', 'half_course_price', 'test_only_price', 'features', 'image', 'is_active']
    success_url = reverse_lazy('website:manage_courses')

    def form_valid(self, form):
        response = super().form_valid(form)
        from django.contrib import messages
        messages.success(self.request, f'Course "{self.object.name}" updated successfully!')
        return response


class CourseDeleteView(StaffMixin, DeleteView):
    model = Course
    template_name = 'website/manage/confirm_delete.html'
    success_url = reverse_lazy('website:manage_courses')

    def form_valid(self, form):
        from django.contrib import messages
        messages.success(self.request, 'Course deleted successfully!')
        return super().form_valid(form)


# BlogPost
class BlogListView2(StaffMixin, ListView):
    model = BlogPost
    template_name = 'website/manage/blog_list.html'
    context_object_name = 'posts'
    paginate_by = 20

    def get_queryset(self):
        queryset = BlogPost.objects.select_related('author').all()
        q = self.request.GET.get('q')
        if q:
            queryset = queryset.filter(Q(title__icontains=q))
        return queryset


class BlogCreateView(StaffMixin, CreateView):
    model = BlogPost
    template_name = 'website/manage/blog_form.html'
    fields = ['title', 'slug', 'excerpt', 'content', 'featured_image', 'author', 'meta_title', 'meta_description', 'is_published']
    success_url = reverse_lazy('website:manage_blog')

    def form_valid(self, form):
        if not form.instance.author:
            form.instance.author = self.request.user
        return super().form_valid(form)


class BlogUpdateView(StaffMixin, UpdateView):
    model = BlogPost
    template_name = 'website/manage/blog_form.html'
    fields = ['title', 'slug', 'excerpt', 'content', 'featured_image', 'author', 'meta_title', 'meta_description', 'is_published']
    success_url = reverse_lazy('website:manage_blog')


class BlogDeleteView(StaffMixin, DeleteView):
    model = BlogPost
    template_name = 'website/manage/confirm_delete.html'
    success_url = reverse_lazy('website:manage_blog')


# Testimonial
class TestimonialListView2(StaffMixin, ListView):
    model = Testimonial
    template_name = 'website/manage/testimonial_list.html'
    context_object_name = 'testimonials'


class TestimonialCreateView(StaffMixin, CreateView):
    model = Testimonial
    template_name = 'website/manage/testimonial_form.html'
    fields = ['name', 'course', 'rating', 'comment', 'photo', 'is_active']
    success_url = reverse_lazy('website:manage_testimonials')


class TestimonialUpdateView(StaffMixin, UpdateView):
    model = Testimonial
    template_name = 'website/manage/testimonial_form.html'
    fields = ['name', 'course', 'rating', 'comment', 'photo', 'is_active']
    success_url = reverse_lazy('website:manage_testimonials')


class TestimonialDeleteView(StaffMixin, DeleteView):
    model = Testimonial
    template_name = 'website/manage/confirm_delete.html'
    success_url = reverse_lazy('website:manage_testimonials')


# FAQ
class FAQListView2(StaffMixin, ListView):
    model = FAQ
    template_name = 'website/manage/faq_list.html'
    context_object_name = 'faqs'


class FAQCreateView(StaffMixin, CreateView):
    model = FAQ
    template_name = 'website/manage/faq_form.html'
    fields = ['question', 'answer', 'category', 'order', 'is_active']
    success_url = reverse_lazy('website:manage_faqs')


class FAQUpdateView(StaffMixin, UpdateView):
    model = FAQ
    template_name = 'website/manage/faq_form.html'
    fields = ['question', 'answer', 'category', 'order', 'is_active']
    success_url = reverse_lazy('website:manage_faqs')


class FAQDeleteView(StaffMixin, DeleteView):
    model = FAQ
    template_name = 'website/manage/confirm_delete.html'
    success_url = reverse_lazy('website:manage_faqs')


# Gallery
class GalleryListView2(StaffMixin, ListView):
    model = GalleryImage
    template_name = 'website/manage/gallery_list.html'
    context_object_name = 'images'


class GalleryCreateView(StaffMixin, CreateView):
    model = GalleryImage
    template_name = 'website/manage/gallery_form.html'
    fields = ['title', 'image', 'category', 'description', 'order', 'is_active']
    success_url = reverse_lazy('website:manage_gallery')


class GalleryUpdateView(StaffMixin, UpdateView):
    model = GalleryImage
    template_name = 'website/manage/gallery_form.html'
    fields = ['title', 'image', 'category', 'description', 'order', 'is_active']
    success_url = reverse_lazy('website:manage_gallery')


class GalleryDeleteView(StaffMixin, DeleteView):
    model = GalleryImage
    template_name = 'website/manage/confirm_delete.html'
    success_url = reverse_lazy('website:manage_gallery')


# Contact Messages
class MessageListView(StaffMixin, ListView):
    model = ContactMessage
    template_name = 'website/manage/message_list.html'
    context_object_name = 'messages_list'
    paginate_by = 20


class MessageDetailView(StaffMixin, DetailView):
    model = ContactMessage
    template_name = 'website/manage/message_detail.html'
    context_object_name = 'msg'

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        obj.is_read = True
        obj.save(update_fields=['is_read'])
        return obj


class MessageDeleteView(StaffMixin, DeleteView):
    model = ContactMessage
    template_name = 'website/manage/confirm_delete.html'
    success_url = reverse_lazy('website:manage_messages')
