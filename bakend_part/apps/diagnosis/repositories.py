# apps/diagnosis/repositories.py
# apps/diagnosis/repositories.py
from typing import Optional
from .models import Diagnosis

class DiagnosisRepository:
    """
    طبقة لعزل منطق استعلامات قاعدة البيانات المتعلقة بالتشخيص.
    توفر واجهة نظيفة للوصول إلى البيانات دون كشف تفاصيل ORM.
    """
    
    def get_by_id(self, diagnosis_id: str) -> Optional[Diagnosis]:
        """
        يجلب سجل تشخيص واحد باستخدام معرفه الأساسي (ID).
        يستخدم select_related لتحسين الأداء عن طريق جلب بيانات المريض المرتبطة في استعلام واحد.
        """
        try:
            return Diagnosis.objects.select_related("patient").get(id=diagnosis_id)
        except Diagnosis.DoesNotExist:
            return None

    # ملاحظة: تم نقل منطق update_with_success و update_with_failure
    # إلى مهمة Celery مباشرة للتحكم الدقيق في المعاملات وآلة الحالة (FSM).
    
# from .models import Diagnosis

# class DiagnosisRepository:
    
#     def get_by_id(self, diagnosis_id: str):
#         return Diagnosis.objects.select_related("patient").filter(id=diagnosis_id).first()

#     """يعزل منطق استعلام قاعدة البيانات للتشخيص."""
#     def update_with_success(self, diagnosis_id, result_data):
#         Diagnosis.objects.filter(id=diagnosis_id).update(
#             status=Diagnosis.Status.SUCCESS,
#             result=result_data
#         )

#     def update_with_failure(self, diagnosis_id, error_message):
#         Diagnosis.objects.filter(id=diagnosis_id).update(
#             status=Diagnosis.Status.FAILURE,
#             error_message=error_message
#         )