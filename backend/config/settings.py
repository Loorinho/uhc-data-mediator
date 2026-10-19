"""
Django settings for the uhc data mediator project.
"""

from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Read environment variables

import os

SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]

DEBUG = os.environ.get("DJANGO_DEBUG", "False").lower() == "true"

ALLOWED_HOSTS = [
    host.strip()
    for host in os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost").split(",")
    if host.strip()
]

# Allowed origins especially for the frontend of the uhc data mediator application

CORS_ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get("CORS_ALLOWED_ORIGINS", "").split(",")
    if origin.strip()
]


# DHIS2 configuration settings


def env_list(name, default=""):
    """
    Read semicolon-separated environment variables.
    """
    raw = os.getenv(name, default)
    return [item.strip() for item in raw.split(";") if item.strip()]


DHIS2_BASE_URL = os.getenv(
    "DHIS2_BASE_URL",
    "https://play.im.dhis2.org/stable-2-43-2",
).rstrip("/")

DHIS2_USERNAME = os.getenv("DHIS2_USERNAME", "")
DHIS2_PASSWORD = os.getenv("DHIS2_PASSWORD", "")

DHIS2_CONNECT_TIMEOUT = int(os.getenv("DHIS2_CONNECT_TIMEOUT", "5"))

DHIS2_READ_TIMEOUT = int(os.getenv("DHIS2_READ_TIMEOUT", "60"))

DHIS2_DX_IDS = env_list("DHIS2_DX_IDS")
DHIS2_PERIODS = env_list("DHIS2_PERIODS")
DHIS2_ORG_UNIT_IDS = env_list("DHIS2_ORG_UNIT_IDS")


ACQUISITION_POLL_SECONDS = int(os.getenv("ACQUISITION_POLL_SECONDS", "3"))

DHIS2_MAX_ATTEMPTS = int(os.getenv("DHIS2_MAX_ATTEMPTS", "3"))

DHIS2_RETRY_BACKOFF_SECONDS = int(os.getenv("DHIS2_RETRY_BACKOFF_SECONDS", "2"))

if not DHIS2_DX_IDS:
    raise ValueError("DHIS2_DX_IDS cannot be empty")

if not DHIS2_PERIODS:
    raise ValueError("DHIS2_PERIODS cannot be empty")

if not DHIS2_ORG_UNIT_IDS:
    raise ValueError("DHIS2_ORG_UNIT_IDS cannot be empty")


# FHIR
FHIR_CANONICAL_BASE_URL = os.getenv("FHIR_CANONICAL_BASE_URL")

if not FHIR_CANONICAL_BASE_URL:
    raise ValueError("FHIR_CANONICAL_BASE_URL cannot be empty")

FHIR_VALIDATOR_VERSION = os.getenv("FHIR_VALIDATOR_VERSION")
FHIR_VALIDATOR_JAR = os.getenv("FHIR_VALIDATOR_JAR")
FHIR_JAVA_COMMAND = os.getenv("FHIR_JAVA_COMMAND", "java")
FHIR_VALIDATOR_TIMEOUT = int(os.getenv("FHIR_VALIDATOR_TIMEOUT", "300"))
FHIR_WORKER_POLL_SECONDS = int(os.getenv("FHIR_WORKER_POLL_SECONDS", "3"))

if not FHIR_VALIDATOR_VERSION:
    raise ValueError("FHIR_VALIDATOR_VERSION cannot be empty")

if not FHIR_VALIDATOR_JAR:
    raise ValueError("FHIR_VALIDATOR_JAR cannot be empty")

if not FHIR_JAVA_COMMAND:
    raise ValueError("FHIR_JAVA_COMMAND cannot be empty")

if not FHIR_VALIDATOR_TIMEOUT:
    raise ValueError("FHIR_VALIDATOR_TIMEOUT cannot be empty")

if not FHIR_WORKER_POLL_SECONDS:
    raise ValueError("FHIR_WORKER_POLL_SECONDS cannot be empty")

# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Adding my rest framework and cors headers
    "rest_framework",
    "corsheaders",
    # Include the core app for the uhc data mediator
    "core",
]

# Custom user model provided by the core app
AUTH_USER_MODEL = "core.User"

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    # The CORS middleware being placed as high as possible,
    # especially before any middleware that can generate responses.
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"


# Database

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ["POSTGRES_DB"],
        "USER": os.environ["POSTGRES_USER"],
        "PASSWORD": os.environ["POSTGRES_PASSWORD"],
        "HOST": os.environ.get("DB_HOST", "uhc-db"),
        "PORT": os.environ.get("DB_PORT", "5432"),
        "CONN_MAX_AGE": 60,
    }
}


# Django REST Framework + JWT authentication

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "EXCEPTION_HANDLER": "core.responses.custom_exception_handler",
}

from datetime import timedelta

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=30),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
}


# Password validation
# https://docs.djangoproject.com/en/6.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/6.1/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/6.1/howto/static-files/

STATIC_URL = "static/"


# Email
# https://docs.djangoproject.com/en/6.1/topics/email/#topic-email-configuration

MAILERS = {
    "default": {
        "BACKEND": "django.core.mail.backends.console.EmailBackend",
    },
}
