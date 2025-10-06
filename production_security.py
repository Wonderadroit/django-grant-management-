# Production Security Configuration for Django Admin
# Add these settings to your production settings.py file

# Admin Security Settings
ADMIN_URL = 'secure-admin-panel/'  # Change from 'admin/' for security
ADMIN_FORCE_ALLAUTH = False

# Session Security
SESSION_COOKIE_SECURE = True  # Only send cookies over HTTPS
SESSION_COOKIE_HTTPONLY = True  # Prevent XSS attacks
SESSION_COOKIE_AGE = 3600  # 1 hour session timeout
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# CSRF Protection
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Strict'

# Security Headers
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
X_FRAME_OPTIONS = 'DENY'

# Admin IP Whitelist (uncomment and add your IPs)
# ALLOWED_ADMIN_IPS = [
#     '192.168.1.100',  # Your office IP
#     '203.0.113.10',   # Your VPN IP
# ]

# Logging Configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'logs/admin_actions.log',
            'formatter': 'verbose',
        },
        'security_file': {
            'level': 'WARNING',
            'class': 'logging.FileHandler',
            'filename': 'logs/security.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'loggers': {
        'django.security': {
            'handlers': ['security_file', 'console'],
            'level': 'WARNING',
            'propagate': True,
        },
        'grants.admin': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
        'authentication.admin': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}

# Database Security
DATABASES = {
    'default': {
        # Use environment variables for database credentials
        'ENGINE': 'django.db.backends.postgresql',  # Use PostgreSQL in production
        'NAME': os.environ.get('DB_NAME'),
        'USER': os.environ.get('DB_USER'),
        'PASSWORD': os.environ.get('DB_PASSWORD'),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
        'OPTIONS': {
            'sslmode': 'require',  # Require SSL for database connections
        },
    }
}

# Password Validation (already configured but ensure these are in production)
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 12,  # Increase minimum length for admin users
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Email Security for admin notifications
EMAIL_USE_TLS = True
EMAIL_PORT = 587
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')

# Two-Factor Authentication (optional but recommended)
# Install: pip install django-otp qrcode[pil]
# Add to INSTALLED_APPS: 'django_otp', 'django_otp.plugins.otp_totp', 'django_otp.plugins.otp_static'
# Add to MIDDLEWARE: 'django_otp.middleware.OTPMiddleware'

# Rate Limiting (install django-ratelimit)
# pip install django-ratelimit

# Cache Security
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': os.environ.get('REDIS_URL', 'redis://127.0.0.1:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        'KEY_PREFIX': 'djf_admin',
    }
}

# File Upload Security
FILE_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB
DATA_UPLOAD_MAX_NUMBER_FIELDS = 1000

# Content Security Policy (install django-csp)
# pip install django-csp
# CSP_DEFAULT_SRC = ("'self'",)
# CSP_SCRIPT_SRC = ("'self'", "'unsafe-inline'", "cdn.jsdelivr.net")
# CSP_STYLE_SRC = ("'self'", "'unsafe-inline'", "cdn.jsdelivr.net")

# Admin Customization for Security
ADMIN_SITE_HEADER = "David Johnson Foundation - Secure Admin"
ADMIN_SITE_TITLE = "DJF Admin"
ADMIN_INDEX_TITLE = "Grant Management System"

# Disable Debug in Production
DEBUG = False
TEMPLATE_DEBUG = False

# Allowed Hosts (configure for your domain)
ALLOWED_HOSTS = [
    'yourdomain.com',
    'www.yourdomain.com',
    'admin.yourdomain.com',  # Subdomain for admin
]

# Static and Media Files Security
STATIC_URL = '/static/'
MEDIA_URL = '/media/'
SECURE_STATIC_URL = '/secure-static/'  # Different path for security

# Backup Configuration (implement regular backups)
BACKUP_STORAGE = {
    'ENGINE': 'storages.backends.s3boto3.S3Boto3Storage',
    'OPTIONS': {
        'bucket_name': os.environ.get('BACKUP_BUCKET'),
        'access_key': os.environ.get('AWS_ACCESS_KEY_ID'),
        'secret_key': os.environ.get('AWS_SECRET_ACCESS_KEY'),
    }
}

# Environment Variables Template (create .env file)
"""
# Database
DB_NAME=your_database_name
DB_USER=your_database_user
DB_PASSWORD=your_secure_password
DB_HOST=your_database_host
DB_PORT=5432

# Email
EMAIL_HOST_USER=your_email@domain.com
EMAIL_HOST_PASSWORD=your_email_password
EMAIL_HOST=smtp.your-provider.com

# Security
SECRET_KEY=your_very_long_random_secret_key_here
ADMIN_URL=your-custom-admin-path/

# AWS (for backups)
AWS_ACCESS_KEY_ID=your_aws_key
AWS_SECRET_ACCESS_KEY=your_aws_secret
BACKUP_BUCKET=your-backup-bucket

# Redis
REDIS_URL=redis://localhost:6379/1
"""