from django import forms
from .models import Instructor
from vehicles.models import Vehicle


class InstructorForm(forms.ModelForm):
    assigned_vehicle = forms.ModelChoiceField(
        queryset=Vehicle.objects.filter(is_available=True),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )

    class Meta:
        model = Instructor
        fields = ['user', 'phone', 'license_number', 'license_class', 'license_expiry',
                  'experience_years', 'branch', 'photo', 'bio', 'is_active']
        widgets = {
            'user': forms.Select(attrs={'class': 'form-select'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'license_number': forms.TextInput(attrs={'class': 'form-control'}),
            'license_class': forms.Select(attrs={'class': 'form-select'}),
            'license_expiry': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'experience_years': forms.NumberInput(attrs={'class': 'form-control'}),
            'branch': forms.Select(attrs={'class': 'form-select'}),
            'photo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk and self.instance.assigned_vehicle:
            self.fields['assigned_vehicle'].initial = self.instance.assigned_vehicle

    def save(self, commit=True):
        instructor = super().save(commit=False)
        if commit:
            instructor.save()
        vehicle = self.cleaned_data.get('assigned_vehicle')
        if vehicle:
            Vehicle.objects.filter(assigned_instructor=instructor).update(assigned_instructor=None)
            vehicle.assigned_instructor = instructor
            vehicle.save(update_fields=['assigned_instructor'])
        elif self.instance.pk:
            Vehicle.objects.filter(assigned_instructor=instructor).update(assigned_instructor=None)
        return instructor
