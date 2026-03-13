from .base import *

DEBUG = True

INSTALLED_APPS += ['django_extensions']

INTERNAL_IPS = ['127.0.0.1']

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Allow all origins in dev
CORS_ALLOW_ALL_ORIGINS = True

# Simpler password validation in dev
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
     'OPTIONS': {'min_length': 6}},
]
