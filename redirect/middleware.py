from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponsePermanentRedirect

from redirect.models import ExcludedViewSource


class MyJobsRedirectMiddleware(object):
    """
    Ensures that all requests are for my.jobs
    """
    def process_request(self, request):
        host = request.META.get('HTTP_HOST', '')
        if host and 'my.jobs' not in host:
            return HttpResponsePermanentRedirect(
                'http://my.jobs' + request.get_full_path())

class ExcludedViewSourceMiddleware:
    def process_request(self, request):
        cache_key = settings.EXCLUDED_VIEW_SOURCE_CACHE_KEY
        excluded = cache.get(cache_key)
        if not excluded:
            excluded = set(ExcludedViewSource.objects.all().values_list('view_source', flat=True))
            cache.set(cache_key, excluded)
        settings.EXCLUDED_VIEW_SOURCES = excluded
