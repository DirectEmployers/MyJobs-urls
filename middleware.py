from django.http import HttpResponsePermanentRedirect


class MyJobsRedirectMiddleware(object):
    def process_request(self, request):
        if 'my.jobs' not in request.META['HTTP_HOST']:
            print request.get_full_path()
            return HttpResponsePermanentRedirect('http://my.jobs' + request.get_full_path())