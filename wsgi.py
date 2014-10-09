import os, sys

import newrelic.agent
newrelic.agent.initialize('/home/web/MyJobs/MyJobs-urls/newrelic.ini')


os.environ['DJANGO_SETTINGS_MODULE'] = 'MyJobs-urls.settings'

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.join(PROJECT_DIR, '../')

if PROJECT_DIR not in sys.path:
    sys.path.append(PROJECT_DIR)
if PARENT_DIR not in sys.path:
    sys.path.append(PARENT_DIR)

import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()
application = newrelic.agent.wsgi_application()(application)
