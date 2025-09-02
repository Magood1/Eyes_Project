# apps/diagnosis/forms.py
from django import forms
from .models import Diagnosis

class DiagnosisUploadForm(forms.ModelForm):
    class Meta:
        model = Diagnosis
        fields = ['patient', 'left_fundus_image', 'right_fundus_image']
        widgets = {
            'patient': forms.HiddenInput(), # سيتم ملء المريض تلقائيًا
        }
        