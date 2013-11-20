from django.conf.urls import patterns, include, url
from django.views.generic.base import RedirectView

from redirect.views import myjobs_redirect, home

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),

    # Redirect views
    url(r'^(?P<guid>[0-9A-Fa-f]{32})$', home, name='home'),
    url(r'^(?P<guid>[0-9A-Fa-f]{32})(?P<vsid>\d*)$', home, name='home'),

    # Potential www.my.jobs redirect, catches root and anything not caught
    # previously
    url(r'^(?:.*/)?$', myjobs_redirect),
)
