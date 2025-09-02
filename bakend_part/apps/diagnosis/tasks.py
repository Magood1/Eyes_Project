# apps/diagnosis/tasks.py
from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded
from django.db import transaction
from django.utils import timezone
from django.conf import settings
from redis import Redis
import logging

from .models import Diagnosis
from .services import DjangoDiagnosisOrchestrator, get_orchestrator
from .exceptions import DiagnosisError, ModelInferenceError, ModelLoadingError

logger = logging.getLogger(__name__)
# تهيئة عميل Redis من إعدادات Celery
redis_client = Redis.from_url(settings.CELERY_BROKER_URL)

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def process_diagnosis(self, diagnosis_id: str):
    """
    مهمة Celery محصّنة بالكامل لمعالجة التشخيص.
    - Idempotent: آمنة للتكرار بفضل القفل الموزع وآلة الحالة.
    - Atomic: تستخدم المعاملات لضمان سلامة البيانات.
    - Robust: تتعامل مع الأخطاء القابلة وغير القابلة لإعادة المحاولة.
    """
    lock_key = f"lock:diagnosis:{diagnosis_id}"
    # يجب أن يكون timeout أطول بقليل من task_time_limit
    lock = redis_client.lock(lock_key, timeout=660)

    if not lock.acquire(blocking=False):
        logger.warning(f"Skipping diagnosis_id={diagnosis_id}. Already locked by another worker.")
        return {"status": "SKIPPED", "reason": "Already locked"}

    try:
        with transaction.atomic():
            # 1. قفل الصف لمنع التحديثات المتزامنة وضمان قراءة أحدث حالة
            diagnosis = Diagnosis.objects.select_for_update().get(id=diagnosis_id)

            # 2. التحقق من Idempotency: هل تمت معالجة هذه المهمة بالفعل أو هي قيد التشغيل؟
            if diagnosis.status in [Diagnosis.Status.SUCCESS, Diagnosis.Status.FAILURE, Diagnosis.Status.RUNNING]:
                logger.info(f"Skipping diagnosis_id={diagnosis_id}. Current state is '{diagnosis.status}'.")
                return {"status": "SKIPPED", "reason": f"Final or running state: {diagnosis.status}"}

            # 3. تحديث الحالة إلى "قيد التشغيل" لتكون مرئية للأنظمة الأخرى
            diagnosis.status = Diagnosis.Status.RUNNING
            diagnosis.worker_id = self.request.id
            diagnosis.started_at = timezone.now()
            diagnosis.save()

        # 4. تنفيذ منطق العمل الرئيسي (خارج المعاملة الأولية)
        
        orchestrator = get_orchestrator() # <-- استخدم الدالة للحصول على نسخة Singleton
        result_data = orchestrator.run_diagnosis_from_django_model(diagnosis_id)
        #orchestrator = DjangoDiagnosisOrchestrator()
        #result_data = orchestrator.run_diagnosis_from_django_model(diagnosis_id)

        # 5. تحديث الحالة النهائية عند النجاح
        Diagnosis.objects.filter(id=diagnosis_id).update(
            status=Diagnosis.Status.SUCCESS,
            result=result_data,
            finished_at=timezone.now()
        )
        logger.info(f"Successfully processed diagnosis_id={diagnosis_id}.")
        return {"status": "SUCCESS", "diagnosis_id": diagnosis_id}

    except (ModelInferenceError, ModelLoadingError, DiagnosisError, ValueError) as e:
        # أخطاء معروفة وغير قابلة لإعادة المحاولة (مثل "Diagnosis not found")
        logger.error(f"NON-RETRIABLE error for diagnosis_id={diagnosis_id}: {e}", exc_info=True)
        Diagnosis.objects.filter(id=diagnosis_id).update(
            status=Diagnosis.Status.FAILURE,
            error_message=str(e),
            finished_at=timezone.now()
        )
        return {"status": "FAILURE", "error": str(e)}

    except SoftTimeLimitExceeded:
        logger.error(f"Soft time limit exceeded for diagnosis_id={diagnosis_id}.")
        Diagnosis.objects.filter(id=diagnosis_id).update(
            status=Diagnosis.Status.FAILURE,
            error_message="Processing time limit exceeded.",
            finished_at=timezone.now()
        )
        return {"status": "FAILURE", "error": "Time limit exceeded"}

    except Exception as e:
        # أخطاء غير متوقعة (مشاكل شبكة، DB) -> أعد المحاولة
        logger.exception(f"RETRIABLE error for diagnosis_id={diagnosis_id}. Retrying...")
        Diagnosis.objects.filter(id=diagnosis_id).update(status=Diagnosis.Status.RETRY)
        self.retry(exc=e)

    finally:
        # 6. تحرير القفل دائمًا لضمان عدم بقاء النظام محجوزًا
        lock.release()

        
# from celery import shared_task
# from .models import Diagnosis
# from .services import DjangoDiagnosisOrchestrator
# from .repositories import DiagnosisRepository
# from .exceptions import DiagnosisError




# @shared_task(bind=True, max_retries=3, default_retry_delay=60)
# def process_diagnosis(self, diagnosis_id: str):
    
#     #مهمة Celery الآن تستدعي المنسق المتكامل مع Django.
#     print(f"INFO: Celery task started for diagnosis ID: {diagnosis_id}")
#     try:
#         orchestrator = DjangoDiagnosisOrchestrator()
#         orchestrator.run_diagnosis_from_django_model(diagnosis_id)
#     except Exception as e:
#         # إذا فشل المنسق بشكل غير متوقع، أعد المحاولة
#         print(f"ERROR: Orchestrator failed for diagnosis {diagnosis_id}. Retrying... Error: {e}")
#         self.retry(exc=e)



"""

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def process_diagnosis(self, diagnosis_id: str):

    #مهمة Celery غير متزامنة لتشغيل خط أنابيب التشخيص.

    print(f"INFO: Celery task started for diagnosis ID: {diagnosis_id}")
    repo = DiagnosisRepository()
    try:
        diagnosis = Diagnosis.objects.get(id=diagnosis_id)
        # في نظام حقيقي، ستحصل على بيانات المريض الديموغرافية من هنا
        demographics = {"age": 45, "gender": "male"} # بيانات وهمية
        
        # يمكنك تمرير مسار الصورة، أو بيانات الصورة مباشرة إذا كانت صغيرة
        image_data = diagnosis.left_fundus_image.read() 
        
        service = DiagnosisOrchestrationService()
        result = service.run_full_diagnosis(image_data, demographics)

        repo.update_with_success(diagnosis_id, result)
        print(f"INFO: Successfully processed diagnosis ID: {diagnosis_id}")
    except Diagnosis.DoesNotExist:
        print(f"ERROR: Diagnosis ID {diagnosis_id} not found.")
    except DiagnosisError as e:
        print(f"ERROR: A non-retriable diagnosis error occurred: {e}")
        repo.update_with_failure(diagnosis_id, str(e))
    except Exception as e:
        # أخطاء غير متوقعة (مشاكل شبكة، إلخ.) -> أعد المحاولة
        print(f"ERROR: An unexpected error occurred. Retrying... Error: {e}")
        self.retry(exc=e)

"""
