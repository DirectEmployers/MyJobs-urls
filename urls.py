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

    # secure.my.jobs redirects
    url(r'^about/?$',
        RedirectView.as_view(url='https://secure.my.jobs/about')),
    url(r'^account/?',
        RedirectView.as_view(url='https://secure.my.jobs/account/edit')),
    url(r'^candidates/?',
        RedirectView.as_view(url='https://secure.my.jobs/candidates/view')),
    url(r'^contact/?$',
        RedirectView.as_view(url='https://secure.my.jobs/contact/')),
    url(r'^privacy/?$',
        RedirectView.as_view(url='https://secure.my.jobs/privacy/')),
    url(r'^profile/?',
        RedirectView.as_view(url='https://secure.my.jobs/profile/view')),
    url(r'^saved-search/?',
        RedirectView.as_view(url='https://secure.my.jobs/saved-search/view')),
    url(r'^terms/?$',
        RedirectView.as_view(url='https://secure.my.jobs/terms/')),

    # Potential www.my.jobs redirects
    url(r'^$',
        RedirectView.as_view(url='http://www.my.jobs')),
    url(r'^.*/?$', myjobs_redirect),
)
