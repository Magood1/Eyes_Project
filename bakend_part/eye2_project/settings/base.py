
from datetime import timedelta
import environ
from pathlib import Path

# المسارات الأساسية
BASE_DIR = Path(__file__).resolve().parent.parent.parent


# تحميل متغيرات البيئة من ملف .env
env = environ.Env()
environ.Env.read_env(BASE_DIR / ".env")

# إعدادات الأمان
SECRET_KEY = env("SECRET_KEY")
DEBUG = env.bool("DEBUG", default=False)
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=[])


# التطبيقات
INSTALLED_APPS = [
    # Django Apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-Party Apps
    'rest_framework',
    'rest_framework_simplejwt',
    'drf_spectacular',
    'corsheaders', 

    # Local Apps
    'apps.core',
    'apps.users',
    'apps.diagnosis',
]



# الوسائط الوسيطة (Middleware)
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


ROOT_URLCONF = 'eye2_project.urls'
WSGI_APPLICATION = 'eye2_project.wsgi.application'
ASGI_APPLICATION = 'eye2_project.asgi.application'

# القوالب
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'], 
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]
"""

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=600),    # مدة صلاحية توكن الوصول (يمكن زيادتها حسب حاجتك)
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),       # مدة صلاحية توكن التحديث (مثلاً أسبوع)
    "ROTATE_REFRESH_TOKENS": True,                      # توليد توكن تحديث جديد عند عملية التجديد
    "BLACKLIST_AFTER_ROTATION": True,                   # حظر التوكن القديم بعد التدوير (يتطلب blacklist app)
}

"""

DATABASES = {
    'default': env.db(),  #{'ENGINE': 'django.db.backends.sqlite3', 'NAME': BASE_DIR / 'db.sqlite3',}
}

# إعدادات التحقق من كلمات المرور
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# إعدادات المصادقة
AUTH_USER_MODEL = 'users.User'  # نموذج مخصص للمستخدم



# إعدادات REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/day',
        'user': '1000/day',
    }, 
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema', 
    
}

MEDIA_ROOT = BASE_DIR / 'media'
MEDIA_URL = '/media/'



# اللغة والمنطقة الزمنية
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# الملفات الثابتة
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# نوع المفتاح الأساسي الافتراضي
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# CELERY SETTINGS
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/1'
CELERY_ACCEPT_CONTENT = ['application/json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE

# --- إعدادات الإنتاج الموصى بها ---
# 🔴 تحذير: يجب أن يكون هذا FALSE دائمًا في الإنتاج أو عند الاختبار الحقيقي
# قم بتعطيله في development.py إذا كنت تريد اختبار سلوك العامل الحقيقي
CELERY_TASK_ALWAYS_EAGER = False 

# يضمن أن المهمة لن تُقر (acknowledged) إلا بعد نجاحها أو فشلها
CELERY_TASK_ACKS_LATE = True

# يعيد جدولة المهمة إذا فُقد العامل (Worker) بشكل غير متوقع
CELERY_TASK_REJECT_ON_WORKER_LOST = True

# يمنع العامل من سحب مهام كثيرة دفعة واحدة، وهو أمر حيوي للمهام طويلة الأمد
CELERY_WORKER_PREFETCH_MULTIPLIER = 1

# حدود زمنية للمهام لمنع تعليقها إلى الأبد
CELERY_TASK_TIME_LIMIT = 600  # 10 دقائق (حد قاسي)
CELERY_TASK_SOFT_TIME_LIMIT = 540 # 9 دقائق (حد ناعم، يثير استثناء)


# CELERY_TASK_ALWAYS_EAGER = True
# CELERY_TASK_EAGER_PROPAGATES = True




LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'audit_file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs/audit.log',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
        },
        'audit': {
            'handlers': ['audit_file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}


SPECTACULAR_SETTINGS = {
    'TITLE': 'Eye2 Diagnostic API',
    'DESCRIPTION': 'API for retinal disease diagnosis using a multi-modal AI pipeline.',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False, # لا تخدم ملف schema.yml الخام
}



# AI PIPELINE SETTINGS
AI_MODELS_BASE_DIR = BASE_DIR / "ai_models"
AI_MULTI_CLASS_MODEL_PATH = AI_MODELS_BASE_DIR / "multi_class_model.keras"
AI_TABULAR_MODEL_PATH = AI_MODELS_BASE_DIR / "tabular_model.keras"

# EXPERT MODELS
AI_EXPERT_CATARACT_MODEL_PATH = AI_MODELS_BASE_DIR / "expert_glaucoma.keras"
AI_EXPERT_DIABETES_MODEL_PATH = AI_MODELS_BASE_DIR / "expert_diabetes.keras"
AI_EXPERT_GLAUCOMA_MODEL_PATH = AI_MODELS_BASE_DIR / "expert_glaucoma.keras"
AI_EXPERT_HYPERTENSION_MODEL_PATH = AI_MODELS_BASE_DIR / "expert_hypertension.keras"
AI_EXPERT_MYOPIA_MODEL_PATH = AI_MODELS_BASE_DIR / "expert_myopia.keras"
AI_EXPERT_AGE_MODEL_PATH = AI_MODELS_BASE_DIR / "expert_age.keras"
