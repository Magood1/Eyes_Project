# apps/diagnosis/serializers.py
from rest_framework import serializers
from .models import Diagnosis

class DiagnosisCreateSerializer(serializers.ModelSerializer):
    """Serializer لإنشاء طلب تشخيص جديد، الآن يتطلب patient_id."""
    patient_id = serializers.UUIDField(write_only=True)
    
    class Meta:
        model = Diagnosis
        fields = ('id', 'patient_id', 'left_fundus_image', 'right_fundus_image')
        read_only_fields = ('id',)

class DiagnosisDetailSerializer(serializers.ModelSerializer):
    """Serializer لعرض التفاصيل الكاملة لسجل التشخيص."""
    class Meta:
        model = Diagnosis
        fields = '__all__'



