"""
Django settings base for core project.
"""

import logging
import os
import sys
from pathlib import Path
from urllib.parse import unquote, urlparse

from dotenv import load_dotenv

try:
    import dj_database_url
except ModuleNotFoundError:  # pragma: no cover
    dj_database_url = None


def _postgres_driver_available() -> bool:
    try:
        import psycopg  # type: ignore # noqa: F401

        return True
    except ModuleNotFoundError:
        try:
            import psycopg2  # type: ignore # noqa: F401

            return True
        except ModuleNotFoundError:
            return False


def _parse_database_url_fallback(database_url: str) -> dict:
    parsed = urlparse(database_url)
    scheme = (parsed.scheme or "").lower()

    if scheme in {"postgres", "postgresql"}:
        return {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": unquote((parsed.path or "").lstrip("/")),
            "USER": unquote(parsed.username or ""),
            "PASSWORD": unquote(parsed.password or ""),
            "HOST": parsed.hostname or "",
            "PORT": str(parsed.port) if parsed.port else "",
        }

    if scheme == "sqlite":
        if parsed.netloc == ":memory:" or (parsed.path or "").lstrip("/") == ":memory:":
            return {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}

        path = parsed.path or ""
        if database_url.startswith("sqlite:////"):
            name = path[1:]
        else:
            name = path
            if len(name) >= 3 and name[0] == "/" and name[2] == ":":
                name = name[1:]

        return {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": name or str(BASE_DIR / "db.sqlite3"),
        }

    raise RuntimeError(
        f"Unsupported DATABASE_URL scheme '{scheme}'. "
        "Install dj_database_url or use sqlite/postgresql."
    )


def _parse_database_url(database_url: str) -> dict:
    if dj_database_url is not None:
        return dj_database_url.parse(database_url)

    return _parse_database_url_fallback(database_url)


BASE_DIR = Path(__file__).resolve().parent.parent.parent

load_dotenv(BASE_DIR / ".env")

SECRET_KEY = os.getenv("SECRET_KEY")

DEBUG = False

ALLOWED_HOSTS = []

INSTALLED_APPS = [
    "corsheaders",
    "django_prometheus",
    "daphne",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sites",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",
    "rest_framework",
    "drf_spectacular",
    "channels",
    "users",
    "rooms.apps.RoomsConfig",
    "sync",
    "chat",
    "providers",
    "common",
]

MIDDLEWARE = [
    "django_prometheus.middleware.PrometheusBeforeMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "common.middleware.request_id.RequestIDMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "allauth.account.middleware.AccountMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django_prometheus.middleware.PrometheusAfterMiddleware",
]

ROOT_URLCONF = "core.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "core.wsgi.application"
ASGI_APPLICATION = "core.asgi.application"

DATABASE_URL = os.getenv("DATABASE_URL")

IS_TESTING = "test" in sys.argv

_default_db = _parse_database_url(DATABASE_URL) if DATABASE_URL else {}

if (
    _default_db.get("ENGINE") == "django.db.backends.postgresql"
    and not _postgres_driver_available()
):
    if IS_TESTING:
        _default_db = {}
    else:
        raise RuntimeError(
            "PostgreSQL DATABASE_URL is configured but no psycopg/psycopg2 driver is installed. "
            "Install backend requirements."
        )

if not _default_db:
    _default_db = {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": str(BASE_DIR / "db.sqlite3"),
    }

DATABASES = {"default": _default_db}

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

AUTH_USER_MODEL = "users.User"

SITE_ID = 1

AUTHENTICATION_BACKENDS = (
    "django.contrib.auth.backends.ModelBackend",
    "users.auth_backends.EmailAuthBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
)

ACCOUNT_ADAPTER = "users.adapters.CustomAccountAdapter"

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True

STATIC_URL = "static/"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REDIS_URL = os.getenv("REDIS_URL")

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [REDIS_URL],
        },
    },
}

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "standard",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "INFO",
        },
        "rooms": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "chat": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}

# --------------------------------------------------
# Security hardening
# --------------------------------------------------

SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

SECURE_REFERRER_POLICY = "same-origin"

# Cookies (enabled in production)
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# --------------------------------------------------
# CORS configuration
# --------------------------------------------------

CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

CORS_ALLOW_CREDENTIALS = True
