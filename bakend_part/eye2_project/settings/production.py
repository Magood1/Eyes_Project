# production.py
from .base import *


# إعدادات الأمان الخاصة بالإنتاج
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = True

SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# الإنتاج يجب ألا يحتوي DEBUG=True أبداً
DEBUG = False

# إعداد قاعدة البيانات من متغيرات البيئة (يفترض DATABASE_URL معرف في .env)
DATABASES = {
    'default': env.db(),  # مثال: postgres://USER:PASSWORD@HOST:PORT/DBNAME
}

# السماح فقط للعناوين المصرح بها في الإنتاج
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=[])
 

# CORS - اسمح فقط للواجهة الأمامية بالوصول
CORS_ALLOWED_ORIGINS = [
    "*",
]



# eye2_project/settings/production.py

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'json': {
            '()': 'pythonjsonlogger.jsonlogger.JsonFormatter',
            'format': '%(asctime)s %(name)s %(levelname)s %(module)s %(lineno)d %(message)s'
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'json',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
        },
        'apps': { # لجميع تطبيقاتنا
            'handlers': ['console'],
            'level': 'INFO',
        },
    },
}