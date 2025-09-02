# eye2_project/celery.py
import os
from celery import Celery
from celery.signals import task_prerun, task_postrun
from django.db import connection, connections
import logging

logger = logging.getLogger(__name__)

# قم بتعيين متغير البيئة الافتراضي لإعدادات Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eye2_project.settings.development')

app = Celery('eye2_project')

# استخدم 'CELERY' كبادئة لجميع إعدادات Celery في settings.py
app.config_from_object('django.conf:settings', namespace='CELERY')

# اكتشاف المهام تلقائيًا من جميع تطبيقات Django المسجلة
app.autodiscover_tasks()

# --- إدارة اتصالات قاعدة البيانات (أفضل ممارسة) ---
@task_prerun.connect
def on_task_prerun(*args, **kwargs):
    """قبل بدء كل مهمة، تأكد من إغلاق أي اتصالات قديمة أو غير صالحة."""
    for conn in connections.all():
        conn.close_if_unusable_or_obsolete()
    logger.debug("Closed stale DB connections before task run.")

@task_postrun.connect
def on_task_postrun(*args, **kwargs):
    """بعد انتهاء كل مهمة (سواء نجحت أو فشلت)، أغلق الاتصال الحالي بقاعدة البيانات."""
    connection.close()
    logger.debug("Closed DB connection after task run.")


    
# import os
# from celery import Celery

# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eye2_project.settings.development')

# app = Celery('eye2_project')
# app.config_from_object('django.conf:settings', namespace='CELERY')
# app.autodiscover_tasks()