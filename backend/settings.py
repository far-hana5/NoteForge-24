"""
Django settings for backend project.
"""

import os
from pathlib import Path

# ------------------------------------------------
# BASE SETTINGS
# ------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-*selh1o_**lc-kc5oymi=)n8&ke9uo_*^v=986#($^z9=s0312'

#DEBUG = False

#ALLOWED_HOSTS = ["127.0.0.1", "localhost"]
DEBUG = True
ALLOWED_HOSTS = []

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
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
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

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'


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