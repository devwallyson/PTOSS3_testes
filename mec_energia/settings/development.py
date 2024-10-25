# flake8: noqa
# pylint: skip-file

import environ

from .common import *


env = environ.Env()
ENV_FILE = BASE_DIR / ".envs" / ".env.dev"
env.read_env(ENV_FILE)

ENVIRONMENT = env("ENVIRONMENT")
SECRET_KEY = "django-insecure-#123!@#$%^&*()_+"
DEBUG = True

ALLOWED_HOSTS = ["mepa-api", "localhost", "127.0.0.1", "0.0.0.0", "[::1]"]
CSRF_TRUSTED_ORIGINS = ["http://mepa-web:3000", "http://localhost:3000"]
CORS_ALLOW_ALL_ORIGINS = True

LOG_LEVEL = env("LOG_LEVEL", default="DEBUG")
LOGGING['loggers']['apps']['level'] = LOG_LEVEL



# DATABASES
# ------------------------------------------------------------------------------------------------
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "HOST": env("POSTGRES_HOST"),
        "PORT": env("POSTGRES_PORT"),
        "NAME": env("POSTGRES_DB"),
        "USER": env("POSTGRES_USER"),
        "PASSWORD": env("POSTGRES_PASSWORD"),
    }
}


# BACKEND CACHE (MOCK CACHE)
# ------------------------------------------------------------------------------------------------
CACHES = {
    "default": {
        "BACKEND": "tests.test_mock_cache.MockCacheTest",
        "LOCATION": "",
    },
}


# MEC ENERGIA
# ------------------------------------------------------------------------------------------------
MEPA_FRONT_END_URL = env("FRONT_END_URL")
RECOMMENDATION_METHOD = env("RECOMMENDATION_METHOD")

# Password reset
RESET_PASSWORD_TOKEN_TIMEOUT = env.int("RESET_PASSWORD_TOKEN_TIMEOUT")
RESEND_EMAIL_RESET_PASSWORD_TIMEOUT = env.int("RESEND_EMAIL_RESET_PASSWORD_TIMEOUT")

# Configurações do servidor SMTP
SMTP_EMAIL_SERVER = env("SMTP_EMAIL_SERVER")
SMTP_EMAIL_PORT = env("SMTP_EMAIL_PORT")
SMTP_EMAIL_USER = env("SMTP_EMAIL_USER")
SMTP_EMAIL_PASSWORD = env("SMTP_EMAIL_PASSWORD")


# DEBUG TOOLBAR
# ------------------------------------------------------------------------------------------------
MIDDLEWARE += ["debug_toolbar.middleware.DebugToolbarMiddleware"]
INSTALLED_APPS += ["debug_toolbar"]
DEBUG_TOOLBAR_CONFIG = {
    "SHOW_TOOLBAR_CALLBACK": lambda request: True,
    "INTERCEPT_REDIRECTS": False,
    "ALLOWED_HOSTS": ["*"],
}


# DJANGO EXTENSIONS
# ------------------------------------------------------------------------------------------------
INSTALLED_APPS += ["django_extensions"]


# SECURITY DISABLED FOR DEVELOPMENT
# ------------------------------------------------------------------------------------------------
SECURE_BROWSER_XSS_FILTER = False
SECURE_CONTENT_TYPE_NOSNIFF = False
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
