from django.http import HttpResponsePermanentRedirect


class MyJobsRedirectMiddleware(object):
    def process_request(self, request):
        host = request.META.get('HTTP_HOST', '')
        if host and 'my.jobs' not in host:
            return HttpResponsePermanentRedirect('http://my.jobs' + request.get_full_path())