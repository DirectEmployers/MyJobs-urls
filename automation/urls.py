from django.conf.urls import patterns, url


urlpatterns = patterns(
    'automation.views',
    url(r'^source-codes/$', 'source_code_upload', name='source_code_upload'),
)