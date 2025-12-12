"""
Django settings for backend project.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

# ------------------------------------------------
# ENVIRONMENT
# ------------------------------------------------
ENVIRONMENT = os.getenv("ENVIRONMENT", "production")

# BASE DIR
BASE_DIR = Path(__file__).resolve().parent.parent

# ------------------------------------------------
# SECURITY
# ------------------------------------------------
SECRET_KEY = os.getenv("SECRET_KEY")

# DEBUG = False in Railway
DEBUG = True if ENVIRONMENT == "deployment" else False

SITE_DOMAIN = os.getenv("RAILWAY_PUBLIC_DOMAIN", "")

ALLOWED_HOSTS = [
    "127.0.0.1",
    "localhost",
    SITE_DOMAIN,
]

CSRF_TRUSTED_ORIGINS = [
    f"https://{SITE_DOMAIN}",
    f"http://{SITE_DOMAIN}",
]
WHITENOISE_USE_FINDERS = True

# ------------------------------------------------
# INSTALLED APPS
# ------------------------------------------------
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'cloudinary',
    'cloudinary_storage',

    'rest_framework',

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
    "django.middleware.security.SecurityMiddleware",

    # WhiteNoise must be here
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
        'DIRS': [BASE_DIR / "templates"],
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

DB_LIVE = os.getenv("DB_LIVE")
  


if DB_LIVE in ["False", False, None]:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.getenv('DB_NAME'),
            'USER': os.getenv('DB_USER'),
            'PASSWORD': os.getenv('DB_PASSWORD'),
            'HOST': os.getenv('DB_HOST'),
            'PORT': os.getenv('DB_PORT'),
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
# STATIC FILES
# ------------------------------------------------
STATIC_URL = "/static/"

# Your folder is backend/static
STATICFILES_DIRS = [
    BASE_DIR / "backend" / "static"
]

STATIC_ROOT = BASE_DIR / "staticfiles"

STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
WHITENOISE_USE_FINDERS = True

# ------------------------------------------------
# MEDIA FILES (Cloudinary)
# ------------------------------------------------
DEFAULT_FILE_STORAGE = "cloudinary_storage.storage.MediaCloudinaryStorage"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# ------------------------------------------------
# CLOUDINARY CONFIG
# ------------------------------------------------
import cloudinary
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
)

# ------------------------------------------------
# CELERY
# ------------------------------------------------
if DB_LIVE in ["False", False]:
    CELERY_BROKER_URL = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND = "redis://localhost:6379/1"
else:
    CELERY_BROKER_URL = os.getenv("REDIS_URL")
    CELERY_RESULT_BACKEND = os.getenv("REDIS_URL")

CELERY_BEAT_SCHEDULE = {
    "process_due_lectures_every_hour": {
        "task": "courses.tasks.process_due_lectures_task",
        "schedule": 3600.0,
    },
}

# ------------------------------------------------
# REST FRAMEWORK
# ------------------------------------------------
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ]
}

# ------------------------------------------------
# MISC
# ------------------------------------------------
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

from django.contrib.messages import constants as messages
MESSAGE_TAGS = {
    messages.INFO: "",
}
