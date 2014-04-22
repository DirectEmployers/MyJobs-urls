from default_settings import *


DEBUG = True
TEMPLATE_DEBUG = DEBUG

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'redirect',
        'USER': 'de_dbuser',
        'PASSWORD': PROD_DB_PASSWD,
        'HOST': 'db-redirectstaging.c9shuxvtcmer.us-east-1.rds.amazonaws.com',
        'PORT': '3306',
    }
}

# Hosts/domain names that are valid for this site; required if DEBUG is False
# See https://docs.djangoproject.com/en/1.5/ref/settings/#allowed-hosts
ALLOWED_HOSTS = []

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

SOLR = {
    'default': 'http://23.21.242.45:8983/solr'
}

