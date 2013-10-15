from default_settings import *


DEBUG = False
TEMPLATE_DEBUG = DEBUG

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'redirect',
        'USER': 'db_deuser',
        'PASSWORD': PROD_DB_PASSWD,
        'HOST': 'db-redirect.c9shuxvtcmer.us-east-1.rds.amazonaws.com',
        'PORT': '3306',
    }
}

# Hosts/domain names that are valid for this site; required if DEBUG is False
# See https://docs.djangoproject.com/en/1.5/ref/settings/#allowed-hosts
ALLOWED_HOSTS = ['localhost', ]

# Uncomment for Django Debug Toolbar
#MIDDLEWARE_CLASSES += ('debug_toolbar.middleware.DebugToolbarMiddleware',)
#INSTALLED_APPS += ('debug_toolbar',)

NEW_RELIC_TRACKING = True
