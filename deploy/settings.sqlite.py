from default_settings import *


DEBUG = True
TEMPLATE_DEBUG = DEBUG

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'myurls.db',
        'USER': '',
        'PASSWORD': '',
        'HOST': '',
        'PORT': '',
    }
}

# Hosts/domain names that are valid for this site; required if DEBUG is False
# See https://docs.djangoproject.com/en/1.5/ref/settings/#allowed-hosts
ALLOWED_HOSTS = []

# Uncomment for Django Debug Toolbar
#MIDDLEWARE_CLASSES += ('debug_toolbar.middleware.DebugToolbarMiddleware',)
#INSTALLED_APPS += ('debug_toolbar',)

SOLR = {
    # If you are running combined MyJobs/microsites solr, leave as-is
    # If you are still using separate solr versions, remove "/seo"
    'default': 'http://127.0.0.1:8983/solr/seo'
}

# With COMPRESS_ENABLED = True, you must run ./manage.py compress for each
# css change and then restart runserver
COMPRESS_ENABLED = False
