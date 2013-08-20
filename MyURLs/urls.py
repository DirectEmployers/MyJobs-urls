from django.conf.urls import patterns, include, url

from viewsource.views import home

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
    url(r'^(?P<guid>\w{32})$', home, name='home'),
    url(r'^(?P<guid>\w{32})(?P<vsid>\d*)$', home, name='home'),
)
