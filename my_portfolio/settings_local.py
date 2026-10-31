"""Local development only; no AWS or real email credentials required."""
import getpass
from .settings import *

DEBUG = True
ALLOWED_HOSTS = ["localhost", "127.0.0.1", "testserver"]
SECRET_KEY = "local-development-only-not-for-production"
DATABASES = {"default": dj_database_url.parse(os.getenv(
    "DATABASE_URL", f"postgres://{getpass.getuser()}@127.0.0.1:55432/studyflux_local"
))}
AWS = False
STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"
MEDIA_URL = "/media/"
MEDIA_ROOT = os.getenv("STUDYFLUX_MEDIA_ROOT", os.path.join(BASE_DIR, "media"))
DEFAULT_FILE_STORAGE = "django.core.files.storage.FileSystemStorage"
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
CORS_ORIGIN_ALLOW_ALL = False
SESSION_COOKIE_HTTPONLY = True

# Pagination is configured explicitly by the feed view.
SILENCED_SYSTEM_CHECKS = ["rest_framework.W001"]
