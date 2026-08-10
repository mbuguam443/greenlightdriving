from django import forms
from .models import Student
from website.models import CourseCategory, Course
from core.models import Branch
from instructors.models import Instructor
from vehicles.models import Vehicle


class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ['user', 'admission', 'category', 'course', 'package_choice', 'branch', 'instructor',
                  'vehicle', 'status', 'expected_graduation', 'notes']
        widgets = {
            'user': forms.Select(attrs={'class': 'form-select'}),
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
