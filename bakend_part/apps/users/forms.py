# apps/users/forms.py
from django import forms
from .models import Patient

class PatientForm(forms.ModelForm):
    class Meta:
        model = Patient
        fields = ['full_name', 'date_of_birth', 'gender', 'clinic']
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
        }