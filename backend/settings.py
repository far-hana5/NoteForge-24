"""
Django settings for backend project.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

ENVIRONMENT=os.getenv('ENVIRONMENT',default='production')  

# ------------------------------------------------
# BASE SETTINGS
# ------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent




SECRET_KEY = os.getenv("SECRET_KEY")
if ENVIRONMENT=='deployment': 
    DEBUG=True
else:
    DEBUG = False

ALLOWED_HOSTS = ["127.0.0.1", "*"]
#ALLOWED_HOSTS = os.getenv(["*"])

#ALLOWED_HOSTS = []

EMAIL_HOST = 'smtp.gmail.com'
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD") 
EMAIL_PORT = 587
EMAIL_USE_TLS = True  
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
 
# ------------------------------------------------
# APPLICATIONS
# ------------------------------------------------
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party
    'rest_framework',

    #  app(s)
    'core',
    'category',
    'accounts',
    'courses',
    'image_enhancer',
]


# ------------------------------------------------
# MIDDLEWARE
# ------------------------------------------------
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    "whitenoise.middleware.WhiteNoiseMiddleware",
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


# ------------------------------------------------
# URLS / WSGI
# ------------------------------------------------
ROOT_URLCONF = 'backend.urls'
WSGI_APPLICATION = 'backend.wsgi.application'
AUTH_USER_MODEL = 'accounts.Account'

# ------------------------------------------------
# TEMPLATES
# ------------------------------------------------
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
                'category.context_processors.menu_links',
            ],
        },
    },
]


# ------------------------------------------------
# DATABASE
# ------------------------------------------------
DB_LIVE = os.getenv('DB_LIVE')
if DB_LIVE in ["False",False]:
      

      
      DATABASES = {
          'default': {
              'ENGINE': 'django.db.backends.sqlite3',
              'NAME': BASE_DIR / 'db.sqlite3',
          }
      }

else:

      DATABASES={
          'default':{
              'ENGINE':'django.db.backends.postgresql',
              'NAME':os.getenv('DB_NAME'),
              'USER':os.getenv('DB_USER'),
              'PASSWORD':os.getenv('DB_PASSWORD'),
              'HOST': os.getenv('DB_HOST', 'localhost'),
              #'HOST':os.getenv('DB_HOST'),
              'PORT':os.getenv('DB_PORT'),
          }
      }


# ------------------------------------------------
# PASSWORD VALIDATION
# ------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# ------------------------------------------------
# INTERNATIONALIZATION
# ------------------------------------------------
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True


# ------------------------------------------------
# STATIC & MEDIA FILES
# ------------------------------------------------
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'backend' / 'static']  # ✅ points to backend/static
STATIC_ROOT = BASE_DIR / 'staticfiles'
STORAGES = {
    # ...
    "staticfiles": {
        'BACKEND' : 'whitenoise.storage.CompressedStaticFilesStorage',

    },
}


TIME_ZONE = "Asia/Dhaka"
USE_TZ = True

#CELERY_BROKER_URL = "redis://localhost:6379/0"
#CELERY_RESULT_BACKEND = "redis://localhost:6379/1"
# Celery settings
#CELERY_BROKER_URL = os.getenv("REDIS_URL")
#CELERY_RESULT_BACKEND = os.getenv("REDIS_URL")

CELERY_BEAT_SCHEDULE = {
    "process_due_lectures_every_5_minutes": {
        "task": "courses.tasks.process_due_lectures_task",
        "schedule": 3600.0,
    },
}

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# ------------------------------------------------
# REST FRAMEWORK
# ------------------------------------------------
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ]
}


# ------------------------------------------------
# DEFAULT PRIMARY KEY FIELD TYPE
# ------------------------------------------------
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

from django.contrib.messages import constants as messages

MESSAGE_TAGS = {
    messages.INFO: "",
    
}