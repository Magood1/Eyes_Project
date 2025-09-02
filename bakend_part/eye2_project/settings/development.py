# development.py
from .base import *

# قاعدة بيانات SQLite لتطوير محلي
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# السماح بكل العناوين في بيئة التطوير
ALLOWED_HOSTS = ["*"]
CORS_ALLOW_ALL_ORIGINS = True
# إظهار رسائل الأخطاء التفصيلية
DEBUG = True
 
