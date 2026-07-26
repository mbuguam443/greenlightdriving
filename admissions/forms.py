import time
import hashlib
from django import forms
from django.conf import settings
from .models import Admission
from website.models import CourseCategory, Course


class OnlineAdmissionForm(forms.ModelForm):
    # Honeypot — bots fill this, humans don't see it
    website = forms.CharField(required=False, widget=forms.HiddenInput(attrs={'tabindex': '-1', 'autocomplete': 'off'}))

    # Math captcha
    captcha_question = forms.CharField(
        label='Security Check',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Answer the math question',
            'autocomplete': 'off',
        }),
        help_text='',
    )

    class Meta:
        model = Admission
        fields = ['first_name', 'last_name', 'email', 'phone', 'date_of_birth', 'gender',
                  'national_id', 'address', 'passport_photo', 'national_id_image',
                  'category', 'course', 'branch', 'preferred_schedule']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'national_id': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'passport_photo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'national_id_image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-select', 'id': 'category-select'}),
            'course': forms.Select(attrs={'class': 'form-select', 'id': 'course-select'}),
            'branch': forms.Select(attrs={'class': 'form-select'}),
            'preferred_schedule': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        self.captcha_answer = None
        self.captcha_expected = None
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = CourseCategory.objects.all()
        self.fields['course'].queryset = Course.objects.none()

        if 'category' in self.data:
            try:
                category_id = int(self.data.get('category'))
                self.fields['course'].queryset = Course.objects.filter(category_id=category_id, is_active=True)
            except (ValueError, TypeError):
                pass
        elif self.instance.pk:
            self.fields['course'].queryset = Course.objects.filter(
                category=self.instance.category, is_active=True
            )

        # Generate captcha
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

        self.captcha_expected = str(answer)
        self.fields['captcha_question'].label = f'What is {a} {op} {b}?'

        # Store captcha hash in initial data
        captcha_hash = hashlib.sha256(f"{answer}{settings.SECRET_KEY}".encode()).hexdigest()[:16]
        self.fields['captcha_question'].widget.attrs['data-hash'] = captcha_hash

    def clean_website(self):
        value = self.cleaned_data.get('website')
        if value:
            raise forms.ValidationError('Spam detected.')
        return value

    def clean_captcha_question(self):
        answer = self.cleaned_data.get('captcha_question', '').strip()
        if not answer:
            raise forms.ValidationError('Please answer the security question.')
        try:
            user_answer = int(answer)
        except ValueError:
            raise forms.ValidationError('Please enter a valid number.')
        if str(user_answer) != self.captcha_expected:
            raise forms.ValidationError('Incorrect answer. Please try again.')
        return answer

    def clean_first_name(self):
        name = self.cleaned_data.get('first_name', '').strip()
        if len(name) < 2:
            raise forms.ValidationError('Name is too short.')
        if name.isdigit():
            raise forms.ValidationError('Name cannot be only numbers.')
        return name

    def clean_last_name(self):
        name = self.cleaned_data.get('last_name', '').strip()
        if len(name) < 2:
            raise forms.ValidationError('Name is too short.')
        if name.isdigit():
            raise forms.ValidationError('Name cannot be only numbers.')
        return name

    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '').strip()
        phone = phone.replace(' ', '').replace('-', '').replace('+', '')
        if not phone.isdigit() or len(phone) < 9:
            raise forms.ValidationError('Please enter a valid phone number.')
        return phone

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        spam_domains = ['tempmail.com', 'throwaway.com', 'guerrillamail.com',
                        'mailinator.com', 'yopmail.com', 'trashmail.com']
        domain = email.split('@')[-1] if '@' in email else ''
        if domain in spam_domains:
            raise forms.ValidationError('Please use your real email address.')
        return email


class AdmissionUpdateForm(forms.ModelForm):
    class Meta:
        model = Admission
        fields = ['status', 'notes']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class InternalAdmissionForm(forms.ModelForm):
    """Internal form for staff — no spam protection, no captcha."""

    class Meta:
        model = Admission
        fields = ['first_name', 'last_name', 'email', 'phone', 'date_of_birth', 'gender',
                  'national_id', 'address', 'passport_photo', 'national_id_image',
                  'category', 'course', 'branch', 'preferred_schedule']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'national_id': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'passport_photo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'national_id_image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-select', 'id': 'category-select'}),
            'course': forms.Select(attrs={'class': 'form-select', 'id': 'course-select'}),
            'branch': forms.Select(attrs={'class': 'form-select'}),
            'preferred_schedule': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = CourseCategory.objects.all()
        self.fields['course'].queryset = Course.objects.none()

        if 'category' in self.data:
            try:
                category_id = int(self.data.get('category'))
                self.fields['course'].queryset = Course.objects.filter(category_id=category_id, is_active=True)
            except (ValueError, TypeError):
                pass
        elif self.instance.pk:
            self.fields['course'].queryset = Course.objects.filter(
                category=self.instance.category, is_active=True
            )
