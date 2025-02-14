from .base import *
import dj_database_url

DEBUG = False

DATABASES = {
    'default': dj_database_url.parse(env('DATABASE_URL'), conn_max_age=600),
}


# Override static files storage setting for production
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
