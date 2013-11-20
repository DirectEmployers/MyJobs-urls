from django.test import TestCase
from django.test.client import RequestFactory


from redirect.middleware import MyJobsRedirectMiddleware


class MyJobsMiddlewareTests(TestCase):
    def setUp(self):
        self.middleware = MyJobsRedirectMiddleware()
        self.factory = RequestFactory()

    def test_redirects_to_myjobs(self):
        """
        A request for any domain other than my.jobs should get redirected
        to the same path on my.jobs.
        """
        for path in ['/', '/search?foo=bar']:
            request = self.factory.get(path,
                                       HTTP_HOST='jcnlx.com')
            response = self.middleware.process_request(request)
            self.assertEqual(response['Location'], 'http://my.jobs' + path)
