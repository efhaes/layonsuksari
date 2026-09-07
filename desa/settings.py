from pathlib import Path
from decouple import config, Csv
import os
import sys

BASE_DIR = Path(__file__).resolve().parent.parent

# ===== Kunci rahasia
SECRET_KEY = config('SECRET_KEY')

# ===== Mode
DEBUG = config('DEBUG', default=False, cast=bool)

# ===== Host
ALLOWED_HOSTS = config(
    'ALLOWED_HOSTS',
    default='127.0.0.1,localhost',
    cast=Csv()
)


CSRF_TRUSTED_ORIGINS = [
    # HTTP (sebelum HTTPS aktif)
    "http://168.231.123.63",
    "http://techo.id", "http://www.techo.id",
    "http://layonsukasari.techo.id",
    # HTTPS (setelah TLS)
    "https://techo.id", "https://www.techo.id",
    "https://layonsukasari.techo.id",
]

# ===== Aplikasi
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'kembang',
    'widget_tweaks',
]

# ===== Middleware
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # untuk static hashed (backup selain Nginx)
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'desa.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'kembang.context_processors.notifikasi_admin',
                'kembang.context_processors.popupwhatsapp',
            ],
        },
    },
]

WSGI_APPLICATION = 'desa.wsgi.application'

# ===== Database (SQLite)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# ===== Validasi password
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ===== Bahasa & Zona Waktu
LANGUAGE_CODE = 'id'
TIME_ZONE = 'Asia/Jakarta'
USE_I18N = True
USE_TZ = True

# ===== Static & Media
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'      # hasil collectstatic untuk Nginx
STATICFILES_DIRS = [BASE_DIR / 'static']    # sumber asset projek

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# WhiteNoise (hash + compress)
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
# WHITENOISE_MAX_AGE = 60 * 60 * 24 * 30  # optional cache 30 hari

# reverse proxy header (Nginx)
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# ===== Default PK
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ===== Auth
LOGIN_URL = '/login/'

# ===== Keamanan (aktif otomatis kalau USE_HTTPS=1 di environment)
USE_HTTPS = os.getenv('USE_HTTPS', '0') == '1'

SECURE_SSL_REDIRECT = USE_HTTPS
SESSION_COOKIE_SECURE = USE_HTTPS
CSRF_COOKIE_SECURE = USE_HTTPS
SECURE_HSTS_SECONDS = 31536000 if USE_HTTPS else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = USE_HTTPS
SECURE_HSTS_PRELOAD = USE_HTTPS
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
X_FRAME_OPTIONS = "DENY"

# ===== Logging ke console (buat systemd journal)
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {'class': 'logging.StreamHandler', 'stream': sys.stdout},
    },
    'root': {'handlers': ['console'], 'level': 'WARNING'},
}
