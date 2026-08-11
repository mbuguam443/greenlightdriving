from django.shortcuts import render, redirect
from django.db import models
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.views import View
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy, reverse
from django.http import HttpResponseRedirect
from django.utils import timezone
from .models import User
from .forms import LoginForm, UserProfileForm, UserAdminForm, StudentRegistrationForm


class LoginView(View):
    def _get_redirect_url(self, user):
        if user.role == 'STUDENT':
            return reverse('student_portal:dashboard')
        return reverse('dashboard')

    def get(self, request):
        if request.user.is_authenticated:
            return HttpResponseRedirect(self._get_redirect_url(request.user))
        form = LoginForm()
        response = render(request, 'accounts/login.html', {'form': form})
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response['Pragma'] = 'no-cache'
        return response

    def post(self, request):
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            user = authenticate(request, username=email, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {user.first_name}!')
                # Send login notification
                from django.core.mail import send_mail
                try:
                    send_mail(
                        'Green Light - Login Alert',
                        f'Hi {user.full_name},\n\nYour account was logged into.\nTime: {timezone.now().strftime("%d %b %Y %H:%M")}\nIP: {self._get_ip(request)}\n\nIf this wasn\'t you, contact us.',
                        None, [user.email], fail_silently=True,
                    )
                except Exception:
                    pass
                next_url = request.GET.get('next')
                if not next_url:
                    next_url = self._get_redirect_url(user)
                response = HttpResponseRedirect(next_url)
                response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
                response['Pragma'] = 'no-cache'
        return response

    def _get_ip(self, request):
        xff = request.META.get('HTTP_X_FORWARDED_FOR')
        return xff.split(',')[0] if xff else request.META.get('REMOTE_ADDR', '')


class LogoutView(View):
    def get(self, request):
        logout(request)
        messages.info(request, 'You have been logged out.')
        return redirect('website:home')

    def post(self, request):
        logout(request)
        messages.info(request, 'You have been logged out.')
        return redirect('website:home')


class RegisterView(View):
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('website:home')
        form = StudentRegistrationForm()
        return render(request, 'accounts/register.html', {'form': form})

    def post(self, request):
        form = StudentRegistrationForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            user = User(
                username=data['email'], email=data['email'],
                first_name=data['first_name'], last_name=data['last_name'],
                phone=data.get('phone', ''), role='STUDENT', is_active=False,
            )
            user.set_password(data['password'])
            user.save()
            user.generate_otp()
            from django.core.mail import send_mail
            try:
                send_mail(
                    'Green Light - Verify Your Account',
                    f'Your verification code is: {user.otp}',
                    None, [user.email], fail_silently=True,
                )
            except Exception:
                pass
            request.session['verify_email'] = user.email
            messages.success(request, 'Account created! Check your email for the verification code.')
            return redirect('accounts:verify_otp')
        return render(request, 'accounts/register.html', {'form': form})


class VerifyOTPView(View):
    def get(self, request):
        email = request.session.get('verify_email')
        if not email:
            return redirect('accounts:register')
        return render(request, 'accounts/verify_otp.html', {'email': email})

    def post(self, request):
        email = request.session.get('verify_email')
        if not email:
            return redirect('accounts:register')
        otp = request.POST.get('otp', '').strip()
        from .models import User
        user = User.objects.filter(email=email, otp=otp).first()
        if user:
            user.is_active = True
            user.is_verified = True
            user.otp = ''
            user.save()
            del request.session['verify_email']
            login(request, user)
            from django.core.mail import send_mail
            try:
                send_mail(
                    'Green Light - Login Alert',
                    f'Hi {user.full_name},\n\nYour account was just logged into.\nTime: {timezone.now().strftime("%d %b %Y %H:%M")}\n\nIf this wasn\'t you, contact us immediately.',
                    None, [user.email], fail_silently=True,
                )
            except Exception:
                pass
            messages.success(request, 'Verified! Welcome to Green Light.')
            return redirect('student_portal:dashboard' if user.role == 'STUDENT' else 'dashboard')
        messages.error(request, 'Invalid code. Try again.')
        return render(request, 'accounts/verify_otp.html', {'email': email})


class ProfileView(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, 'accounts/profile.html', {'user': request.user})


class ProfileUpdateView(LoginRequiredMixin, View):
    def get(self, request):
        form = UserProfileForm(instance=request.user)
        return render(request, 'accounts/profile_edit.html', {'form': form})

    def post(self, request):
        form = UserProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('accounts:profile')
        return render(request, 'accounts/profile_edit.html', {'form': form})


class StaffRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.role in ('SUPER_ADMIN', 'MANAGER', 'RECEPTIONIST')


class UserListView(StaffRequiredMixin, ListView):
    model = User
    template_name = 'accounts/user_list.html'
    context_object_name = 'users'
    paginate_by = 20

    def get_queryset(self):
        queryset = User.objects.all()
        role = self.request.GET.get('role')
        search = self.request.GET.get('search')
        if role:
            queryset = queryset.filter(role=role)
        if search:
            queryset = queryset.filter(
                models.Q(email__icontains=search) |
                models.Q(first_name__icontains=search) |
                models.Q(last_name__icontains=search)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['roles'] = User.ROLE_CHOICES
        context['current_role'] = self.request.GET.get('role', '')
        context['search_query'] = self.request.GET.get('search', '')
        return context


class UserCreateView(StaffRequiredMixin, CreateView):
    model = User
    form_class = UserAdminForm
    template_name = 'accounts/user_form.html'
    success_url = reverse_lazy('accounts:user_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from core.models import Branch
        context['branches'] = Branch.objects.filter(is_active=True)
        return context

    def form_valid(self, form):
        user = form.save(commit=False)
        user.set_password(form.cleaned_data.get('password', 'temp1234'))
        user.save()
        messages.success(self.request, 'User created successfully.')
        return super().form_valid(form)


class UserUpdateView(StaffRequiredMixin, UpdateView):
    model = User
    form_class = UserAdminForm
    template_name = 'accounts/user_form.html'
    success_url = reverse_lazy('accounts:user_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from core.models import Branch
        context['branches'] = Branch.objects.filter(is_active=True)
        return context

    def form_valid(self, form):
        messages.success(self.request, 'User updated successfully.')
        return super().form_valid(form)


class UserDeleteView(StaffRequiredMixin, DeleteView):
    model = User
    template_name = 'accounts/user_confirm_delete.html'
    success_url = reverse_lazy('accounts:user_list')

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'User deleted successfully.')
        return super().delete(request, *args, **kwargs)
