from django import forms
from .models import NTSARecord


class NTSARecordForm(forms.ModelForm):
    class Meta:
        model = NTSARecord
        fields = ['student', 'pdl_status', 'pdl_date', 'pdl_number',
                  'theory_exam_status', 'theory_exam_date', 'theory_exam_score',
                  'practical_exam_status', 'practical_exam_date',
                  'driving_test_status', 'driving_test_date',
                  'licence_issued', 'licence_number', 'licence_issue_date', 'licence_expiry_date',
                  'notes']
        widgets = {
            'student': forms.Select(attrs={'class': 'form-select'}),
            'pdl_status': forms.Select(attrs={'class': 'form-select'}),
            'pdl_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'pdl_number': forms.TextInput(attrs={'class': 'form-control'}),
            'theory_exam_status': forms.Select(attrs={'class': 'form-select'}),
            'theory_exam_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'theory_exam_score': forms.NumberInput(attrs={'class': 'form-control'}),
            'practical_exam_status': forms.Select(attrs={'class': 'form-select'}),
            'practical_exam_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'driving_test_status': forms.Select(attrs={'class': 'form-select'}),
            'driving_test_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'licence_issued': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'licence_number': forms.TextInput(attrs={'class': 'form-control'}),
            'licence_issue_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'licence_expiry_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
