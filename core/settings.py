# -*- encoding: utf-8 -*-
"""
License: MIT
Copyright (c) 2019 - present AppSeed.us
"""

import os
from decouple import config
from unipath import Path

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_DIR = Path(__file__).parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG')
# SECURITY WARNING: keep the secret key used in production secret!
# Try to read SECRET_KEY from env, fallback to a safe placeholder for dev
SECRET_KEY = config('SECRET_KEY', default='dev-secret-change-me')

# DEBUG flag (cast to bool via decouple)
DEBUG = config('DEBUG', default=False, cast=bool)

# ALLOWED_HOSTS can be a comma-separated list in env
ALLOWED_HOSTS = [h.strip() for h in config('ALLOWED_HOSTS', default='').split(',') if h.strip()]

# Add development hosts when in DEBUG mode
if DEBUG:
    ALLOWED_HOSTS.extend(['localhost', '127.0.0.1', '[::1]', '.localhost', 'testserver'])

# Production security recommendations (override in env/settings)
if not DEBUG:
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    X_FRAME_OPTIONS = 'DENY'

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'core',  # Add core app for management commands
    'app',  # Enable the inner app 
    'grants',  # Newly created grants app
    'accounts',  # Accounts app for signup/login
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Add WhiteNoise for static files
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    # 'core.middleware.HideAdminMiddleware',  # Temporarily disabled for debugging
    # 'core.admin.admin_view_middleware',  # Temporarily disabled for debugging
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# CSRF Settings - Allow same-origin requests and handle CSRF properly
CSRF_COOKIE_SECURE = not DEBUG  # Use secure cookies in production
CSRF_COOKIE_HTTPONLY = False  # Allow JavaScript access if needed
CSRF_COOKIE_SAMESITE = 'Lax'

# CSRF Trusted Origins - Update for production
CSRF_TRUSTED_ORIGINS = [
    'http://localhost:8000', 
    'http://127.0.0.1:8000',
    'https://*.onrender.com',  # Add Render domains
]

# Add your Render domain when you get it
if not DEBUG:
    render_domain = config('RENDER_EXTERNAL_URL', default='')
    if render_domain:
        CSRF_TRUSTED_ORIGINS.append(render_domain)

ROOT_URLCONF = 'core.urls'
LOGIN_REDIRECT_URL = "grants:dashboard"   # Redirect to grants dashboard after login
LOGIN_URL = "/accounts/login/"   # URL for login page
LOGOUT_REDIRECT_URL = "home"  # Route defined in app/urls.py
TEMPLATE_DIR = os.path.join(BASE_DIR, "core/templates")  # ROOT dir for templates

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [TEMPLATE_DIR],
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

WSGI_APPLICATION = 'core.wsgi.application'

# Database
# https://docs.djangoproject.com/en/3.0/ref/settings/#databases

# Use dj-database-url to configure database from environment variables
import dj_database_url

DATABASES = {
    'default': dj_database_url.config(
        default=f'sqlite:///{os.path.join(BASE_DIR, "db.sqlite3")}',
        conn_max_age=600,
        conn_health_checks=True,
    )
}

# Password validation
# https://docs.djangoproject.com/en/3.0/ref/settings/#auth-password-validators

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


# Internationalization
# https://docs.djangoproject.com/en/3.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.0/howto/static-files/

STATIC_URL = '/static/'

# STATIC_ROOT production load 
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# STATIC_ROOT development load 
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "core/static"),
]

# WhiteNoise configuration for static files - Use simpler storage for production
if DEBUG:
    STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'
else:
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'

# WhiteNoise settings
WHITENOISE_USE_FINDERS = True
WHITENOISE_AUTOREFRESH = True
WHITENOISE_SKIP_COMPRESS_EXTENSIONS = ['jpg', 'jpeg', 'png', 'gif', 'webp', 'zip', 'gz', 'tgz', 'bz2', 'tbz', 'xz', 'br', 'map']

# Media files (uploaded files)
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# File Upload Settings
FILE_UPLOAD_MAX_MEMORY_SIZE = 10485760  # 10MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 10485760  # 10MB
FILE_UPLOAD_PERMISSIONS = 0o644

# Email Configuration
# For production, change to SMTP backend: 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_BACKEND = config('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = config('EMAIL_HOST', default='localhost')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='Dave Johnson Foundation <grantdavejohnsonfoundation@gmail.com>')

# Grant System Specific Settings
GRANT_SYSTEM_SETTINGS = {
    'MAX_APPLICATIONS_PER_USER': 1,
    'DOCUMENT_UPLOAD_PATH': 'grant_documents/',
    'MAX_DOCUMENT_SIZE': 10485760,  # 10MB
    'ALLOWED_DOCUMENT_TYPES': ['pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png', 'txt'],
    'ANALYTICS_RETENTION_DAYS': 365,
    'MANUAL_REVIEW_ONLY': True,  # Production setting: all grants require manual review
}

# Development-friendly email backend (prints emails to console)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
