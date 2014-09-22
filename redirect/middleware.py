from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponsePermanentRedirect

from redirect.models import ExcludedViewSource, CustomExcludedViewSource


class MyJobsRedirectMiddleware(object):
    """
    Ensures that all requests are for my.jobs
    """
    def process_request(self, request):
        host = request.META.get('HTTP_HOST', '')
        if host and not any(domain in host
                            for domain in settings.ALLOWED_HOSTS):
            return HttpResponsePermanentRedirect(
                'http://my.jobs' + request.get_full_path())


class ExcludedViewSourceMiddleware:
    """
    Caches excluded view sources (both global and custom) if they are not
    cached already.
    """
    def process_request(self, request):
        # Globally excluded view sources
        global_cache_key = settings.EXCLUDED_VIEW_SOURCE_CACHE_KEY
        excluded = cache.get(global_cache_key)
        if not excluded:
            excluded = set(
                ExcludedViewSource.objects.all().values_list('view_source',
                                                             flat=True))
            cache.set(global_cache_key, excluded)
        settings.EXCLUDED_VIEW_SOURCES = excluded

        # BUID-specific excluded view sources
        custom_cache_key = settings.CUSTOM_EXCLUSION_CACHE_KEY
        custom = cache.get(custom_cache_key)
        if not custom:
            custom = set(
                CustomExcludedViewSource.objects.all().values_list('buid',
                                                                   'view_source'))
            cache.set(custom_cache_key, custom)
        settings.CUSTOM_EXCLUSIONS = custom
