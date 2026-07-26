from django import forms
from .models import Instructor


class InstructorForm(forms.ModelForm):
    class Meta:
        model = Instructor
        fields = ['user', 'license_number', 'experience_years', 'specialization', 'bio', 'is_available']
        widgets = {
            'user': forms.Select(attrs={'class': 'form-select'}),
            'license_number': forms.TextInput(attrs={'class': 'form-control'}),
            'experience_years': forms.NumberInput(attrs={'class': 'form-control'}),
            'specialization': forms.TextInput(attrs={'class': 'form-control'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_available': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
