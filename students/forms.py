from django import forms
from django.contrib.auth import get_user_model
from .models import Student, StudentEnrollment
from website.models import CourseCategory, Course
from core.models import Branch
from instructors.models import Instructor
from vehicles.models import Vehicle

User = get_user_model()


class StudentForm(forms.ModelForm):
    first_name = forms.CharField(label='First Name', max_length=150,
                                 widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Student first name'}))
    last_name = forms.CharField(label='Last Name', max_length=150,
                                widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Student last name'}))
    phone = forms.CharField(label='Phone', required=False, max_length=20,
                            widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 07XXXXXXXX'}))
    email = forms.EmailField(label='Email', required=False,
                             widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'student@example.com'}))

    class Meta:
        model = Student
        fields = ['first_name', 'last_name', 'phone', 'email', 'admission', 'category', 'course',
                  'package_choice', 'branch', 'instructor', 'vehicle', 'status',
                  'expected_graduation', 'notes']
        widgets = {
            'admission': forms.Select(attrs={'class': 'form-select'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'course': forms.Select(attrs={'class': 'form-select'}),
            'package_choice': forms.Select(attrs={'class': 'form-select'}),
            'branch': forms.Select(attrs={'class': 'form-select'}),
            'instructor': forms.Select(attrs={'class': 'form-select'}),
            'vehicle': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'expected_graduation': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['admission'].required = False
        self.fields['instructor'].required = False
        self.fields['vehicle'].required = False
        self.fields['instructor'].queryset = Instructor.objects.filter(is_active=True).select_related('user')
        self.fields['vehicle'].queryset = Vehicle.objects.filter(is_available=True)

    def clean(self):
        cleaned = super().clean()
        email = (cleaned.get('email') or '').strip().lower()
        if email:
            existing = User.objects.filter(email=email)
            if self.instance and self.instance.pk and self.instance.user_id:
                existing = existing.exclude(pk=self.instance.user_id)
            if existing.exists():
                raise forms.ValidationError({'email': 'A user with this email already exists.'})
        return cleaned


class StudentEnrollmentForm(forms.ModelForm):
    class Meta:
        model = StudentEnrollment
        fields = ['course', 'package_choice', 'branch', 'instructor', 'vehicle', 'expected_graduation', 'notes']
        widgets = {
            'course': forms.Select(attrs={'class': 'form-select'}),
            'package_choice': forms.Select(attrs={'class': 'form-select'}),
            'branch': forms.Select(attrs={'class': 'form-select'}),
            'instructor': forms.Select(attrs={'class': 'form-select'}),
            'vehicle': forms.Select(attrs={'class': 'form-select'}),
            'expected_graduation': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['course'].queryset = Course.objects.filter(is_active=True)
        self.fields['branch'].queryset = Branch.objects.filter(is_active=True)
        self.fields['instructor'].queryset = Instructor.objects.filter(is_active=True).select_related('user')
        self.fields['vehicle'].queryset = Vehicle.objects.filter(is_available=True)
        self.fields['instructor'].required = False
        self.fields['vehicle'].required = False
