import base64
import datetime
import json
import re
from urllib import unquote
import uuid

from jira.client import JIRA

from django.conf import settings
from django.contrib.auth.models import User
from django.core import mail
from django.core.cache import cache
from django.core.urlresolvers import reverse, NoReverseMatch
from django.test import TestCase
from django.test.client import Client, RequestFactory
from django.utils import text, timezone
from django.utils.http import urlquote_plus

from redirect import helpers
from redirect.models import DestinationManipulation, ExcludedViewSource, CompanyEmail
from redirect.tests.factories import (
    RedirectFactory, CanonicalMicrositeFactory, DestinationManipulationFactory,
    CustomExcludedViewSourceFactory)
from redirect.views import home

GUID_RE = re.compile(r'([{\-}])')


class ViewSourceViewTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.redirect = RedirectFactory()
        self.microsite = CanonicalMicrositeFactory()
        self.manipulation = DestinationManipulationFactory()
        self.redirect_guid = GUID_RE.sub('', self.redirect.guid)

        self.factory = RequestFactory()

    def tearDown(self):
        """
        The cache is not cleared between tests. We need to do it manually.
        """
        cache.clear()

    def test_get_with_bad_vsid(self):
        """
        If no view source id is provided or the given view source id does not
        resolve to a DestinationManipulation instance, default to 0
        """
        for vsid in ['', '1']:
            response = self.client.get(reverse('home',
                                               args=[self.redirect_guid,
                                                     vsid]))

            test_url = '%s%s/job/?vs=%s' % \
                (self.microsite.canonical_microsite_url,
                 self.redirect.uid,
                 vsid or '0')

            self.assertEqual(response['Location'], test_url)

    def test_with_action_type_2(self):
        """
        Sometimes a DestinationManipulation object exists with an action_type
        of 2 but a corresponding object with an action_type of 1 does not
        exist. If one of these is encountered, we should not run the
        manipulation twice.
        """
        self.manipulation.action_type = '2'
        self.manipulation.action = 'sourcecodetag'
        self.manipulation.value_1 = '?src=foo'
        self.manipulation.view_source = 10
        self.redirect.url = 'http://www.directemployers.org'
        self.manipulation.save()
        self.redirect.save()

        with self.assertRaises(DestinationManipulation.DoesNotExist):
            DestinationManipulation.objects.get(
                buid=self.manipulation.buid,
                view_source=self.manipulation.view_source,
                action_type=1)

        response = self.client.get(
            reverse('home',
                    args=[self.redirect_guid,
                          self.manipulation.view_source]))

        self.assertEqual(response.status_code, 301)
        self.assertEqual(response['Location'],
                         self.redirect.url + self.manipulation.value_1)

    def test_get_with_malformed_guid(self):
        """
        Navigating to a url with a malformed guid or a guid that contains
        non-hex characters should display a 404 page
        """
        for guid in [self.redirect_guid[:16],
                     'g' * 32]:
            with self.assertRaises(NoReverseMatch):
                self.client.get(reverse('home', args=[guid]))

    def test_job_does_not_exist(self):
        """
        Nonexistent jobs should display a 404 page.
        """
        response = self.client.get(reverse('home', args=['1' * 32]))
        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed(response, '404.html')
        self.assertTrue('google-analytics' in response.content)

    def test_open_graph_redirect(self):
        """
        Check social bot open graph response
        """
        response = self.client.get(
            reverse('home', args=[self.redirect_guid,
                                  self.manipulation.view_source]),
            HTTP_USER_AGENT='facebookexternalhit')
        self.assertContains(response, 'US.jobs - Programmer - DirectEmployers')
        self.assertTemplateUsed(response, 'redirect/opengraph.html')
        self.assertTrue('google-analytics' not in response.content)

    def test_sourcecodetag_redirect(self):
        """
        Check view that manipulates a url with the sourcecodetag action
        creates the correct redirect url which will have a sourcecode tag on
        the end
        examples: &Codes=DE-DEA, &src=JB-11380, &src=indeed_test
        """
        response = self.client.get(
            reverse('home', args=[self.redirect_guid,
                                  self.manipulation.view_source]))
        #content = json.loads(response.content)
        test_url = '%s?%s' % (self.redirect.url,
                              self.manipulation.value_1[1:])
        self.assertEqual(response['Location'], test_url)

    def test_microsite_redirect(self):
        """
        Ensure that requests for a given GUID + view source redirect to a
        microsite given two criteria:
        - The view source is not an excluded view source
        - The buid that owns the job has a microsite enabled.
        """
        self.manipulation.action = 'sourcecodetag'
        self.manipulation.value_1 = '?src=foo'
        self.manipulation.view_source = 0
        self.manipulation.save()

        response = self.client.get(
            reverse('home', args=[self.redirect_guid,
                                  self.manipulation.view_source]))
        test_url = '%s%s/job/?vs=%s' % (self.microsite.canonical_microsite_url,
                                        self.redirect.uid,
                                        self.manipulation.view_source)
        self.assertEqual(response['Location'], test_url)

    def test_amptoamp_redirect(self):
        """
        Check method that manipulates a url with the amptoamp action
        """
        self.manipulation.action = 'amptoamp'
        self.manipulation.value_1 = 'http://ad.doubleclick.net/clk;2526;8138?'
        self.manipulation.value_2 = '&functionName=viewFromLink&locale=en-us'
        self.manipulation.save()

        self.redirect.url = 'jobsearch.lilly.com/ddddddd/job/&8888888&vs=43'
        self.redirect.save()

        response = self.client.get(
            reverse('home', args=[self.redirect_guid,
                                  self.manipulation.view_source]))
        url = self.redirect.url.split('&')
        test_url = '%s%s%s' % \
            (self.manipulation.value_1, url[1], self.manipulation.value_2)
        self.assertEqual(response['Location'], test_url)

    def test_urlswap_redirect(self):
        """
        Check method that manipulates a url with the cframe action
        """
        self.manipulation.action = 'urlswap'
        self.manipulation.value_1 = 'https://careers.nscorp.com/?sap-client=100'
        self.manipulation.save()

        response = self.client.get(
            reverse('home', args=[self.redirect_guid,
                                  self.manipulation.view_source]))
        test_url = self.manipulation.value_1
        self.assertEqual(response['Location'], test_url)

    def test_cframe_redirect(self):
        """
        Check method that manipulates a url with the cframe action
        """
        self.manipulation.action = 'cframe'
        self.manipulation.value_1 = 'fedex.asp'
        self.manipulation.save()

        response = self.client.get(
            reverse('home', args=[self.redirect_guid,
                                  self.manipulation.view_source]))
        url = urlquote_plus(self.redirect.url, safe='')
        url = url.replace('.', '%2E')
        url = url.replace('-', '%2D')
        url = url.replace('_', '%5F')
        url = '%s?url=%s' % (self.manipulation.value_1, url)
        test_url = 'http://directemployers.us.jobs/companyframe/' + url
        self.assertEqual(response['Location'], test_url)

    def test_anchorredirectissue_redirect(self):
        """
        Check method that manipulates a url with the anchorredirectissue action
        """
        self.manipulation.action = 'anchorredirectissue'
        self.manipulation.value_1 = '&deaanchor='
        self.manipulation.save()

        self.redirect.url = 'directemployers.org/#directemployers#105/'
        self.redirect.save()

        response = self.client.get(
            reverse('home', args=[self.redirect_guid,
                                  self.manipulation.view_source]))
        url = self.redirect.url.split('#')
        test_url = 'http://testserver/' + url[0] + self.manipulation.value_1
        self.assertEqual(response['Location'], test_url)

    def test_replacethenadd_redirect(self):
        """
        Check method that manipulates a url with the replacethenadd action
        """
        self.manipulation.action = 'replacethenadd'
        self.manipulation.value_1 = 'jobdetail.ftl!!!!jobapply.ftl'
        self.manipulation.value_2 = '&src=CWS-12480'
        self.manipulation.save()

        self.redirect.url = 'directemployers.org/'
        self.redirect.save()

        response = self.client.get(
            reverse('home', args=[self.redirect_guid,
                                  self.manipulation.view_source]))
        old, new = self.manipulation.value_1.split('!!!!')
        test_url = 'http://testserver/%s%s' % \
            (self.redirect.url, self.manipulation.value_2.replace('&', '?'))
        self.assertEqual(response['Location'], test_url)

    def test_replacethenaddpre_redirect(self):
        """
        Check method that manipulates a url with the replacethenaddpre action
        """
        self.manipulation.action = 'replacethenaddpre'
        self.manipulation.value_1 = '?ss=paid!!!!?apstr=src%3DJB-10600'
        self.manipulation.value_2 = 'http://ad.doubleclick.net/clk;2613;950;s?'
        self.manipulation.save()

    def test_sourcecodeinsertion_redirect(self):
        """
        Check method that manipulates a url with the sourcecodeinsertion action
        """
        self.manipulation.action = 'sourcecodeinsertion'
        self.manipulation.value_1 = '&src=de'
        self.manipulation.save()

        self.redirect.url = 'directemployers.org/#directemployers/'
        self.redirect.save()

        response = self.client.get(
            reverse('home', args=[self.redirect_guid,
                                  self.manipulation.view_source]))
        url = self.redirect.url.split('#')
        test_url = 'http://testserver/' + ('%s#' %
                                           self.manipulation.value_1).join(url)
        self.assertEqual(response['Location'], test_url)

    def test_sourceurlwrapappend_redirect(self):
        """
        Check method that manipulates a url with the sourceurlwrapappend action
        """
        self.manipulation.action = 'sourceurlwrapappend'
        self.manipulation.value_1 = 'http://bs.serving-sys.com/server.bs?u=$$'
        self.manipulation.value_2 = '$$'
        self.manipulation.save()

        response = self.client.get(
            reverse('home', args=[self.redirect_guid,
                                  self.manipulation.view_source]))
        url = urlquote_plus(self.redirect.url, safe='')
        url = url.replace('.', '%2E')
        url = url.replace('-', '%2D')
        url = url.replace('_', '%5F')
        test_url = self.manipulation.value_1 + url + self.manipulation.value_2
        self.assertEqual(response['Location'], test_url)

    def test_sourceurlwrapunencodedappend_redirect(self):
        """
        Check method that manipulates a url with the
        sourceurlwrapunencodedappend action
        """
        self.manipulation.action = 'sourceurlwrapunencodedappend'
        self.manipulation.value_1 = 'http://ad.doubleclick.net/clk;2593;886;r?'
        self.manipulation.value_2 = '&SID=97'
        self.manipulation.save()

        response = self.client.get(
            reverse('home', args=[self.redirect_guid,
                                  self.manipulation.view_source]))
        #content = json.loads(response.content)
        url = self.manipulation.value_1 + self.redirect.url
        test_url = url + self.manipulation.value_2
        self.assertEqual(response['Location'], test_url)

    def test_sourceurlwrapunencoded_redirect(self):
        """
        Check method that manipulates a url with the sourceurlwrapunencoded
        action
        """
        self.manipulation.action = 'sourceurlwrapunencoded'
        self.manipulation.value_1 = 'http://ad.doubleclick.net/clk;346;154;h?'
        self.manipulation.save()

        response = self.client.get(
            reverse('home', args=[self.redirect_guid,
                                  self.manipulation.view_source]))
        test_url = self.manipulation.value_1 + self.redirect.url
        self.assertEqual(response['Location'], test_url)

    def test_sourceurlwrap_redirect(self):
        """
        Check method that manipulates a url with the sourceurlwrap action
        """
        self.manipulation.action = 'sourceurlwrap'
        self.manipulation.value_1 = 'http://bs.serving-sys.com/?cn=t&rtu=$$'
        self.manipulation.save()

        response = self.client.get(
            reverse('home', args=[self.redirect_guid,
                                  self.manipulation.view_source]))
        url = urlquote_plus(self.redirect.url, safe='')
        url = url.replace('.', '%2E')
        url = url.replace('-', '%2D')
        url = url.replace('_', '%5F')
        test_url = self.manipulation.value_1 + url
        self.assertEqual(response['Location'], test_url)

    def test_switchlastinstance_redirect(self):
        """
        Check method that manipulates a url with the switchlastinstance action
        """
        self.manipulation.action = 'switchlastinstance'
        self.manipulation.value_1 = '/job'
        self.manipulation.value_2 = '/login'
        self.manipulation.save()

        self.redirect.url = 'directemployers.org/job'
        self.redirect.save()

        response = self.client.get(
            reverse('home', args=[self.redirect_guid,
                                  self.manipulation.view_source]))
        old = self.manipulation.value_1
        new = self.manipulation.value_2
        test_url = 'http://testserver/' + new.join(
            self.redirect.url.rsplit(old, 1))
        self.assertEqual(response['Location'], test_url)

    def test_switchlastthenadd_redirect(self):
        """
        Check method that manipulates a url with the switchlastthenadd action
        """
        self.manipulation.action = 'switchlastthenadd'
        self.manipulation.value_1 = '/job!!!!/login'
        self.manipulation.value_2 = '?iis=CareerSiteSEO'
        self.manipulation.save()

        self.redirect.url = 'directemployers.org/job'
        self.redirect.save()

        response = self.client.get(
            reverse('home', args=[self.redirect_guid,
                                  self.manipulation.view_source]))
        old, new = self.manipulation.value_1.split('!!!!')
        new_url = new.join(self.redirect.url.rsplit(old, 1))
        test_url = 'http://testserver/' + new_url + self.manipulation.value_2
        self.assertEqual(response['Location'], test_url)

    def test_state_job(self):
        self.redirect.buid = 1228
        self.redirect.url = 'http://us.jobs/viewjobs.asp?jobid=1234'
        self.redirect.job_location = 'NY-Rochester'
        self.manipulation.delete()
        self.redirect.save()
        response = self.client.get(
            reverse('home', args=[self.redirect_guid,
                                  self.manipulation.view_source]))
        self.assertTrue(self.redirect.url.replace('us.jobs', 'newyork.us.jobs')
                        in response['Location'])

    def test_expired_job(self):
        self.redirect.expired_date = datetime.datetime.now(tz=timezone.utc)
        self.redirect.save()

        response = self.client.get(
            reverse('home', args=[self.redirect_guid,
                                  self.manipulation.view_source]))
        self.assertEqual(response.status_code, 410)
        self.assertTemplateUsed(response, 'redirect/expired.html')
        self.assertTrue('View all current jobs for %s.' %
                        self.redirect.company_name in
                        response.content)
        self.assertTrue('%s (%s)' %
                        (self.redirect.job_title, self.redirect.job_location)
                        in response.content)
        self.assertTrue(self.redirect.url in response.content)
        self.assertTrue('google-analytics' in response.content)

    def test_cookie_domains(self):
        # The value for host is unimportant - if this code does not end up
        # being served on r.my.jobs, it's okay. We're just testing that we
        # properly retrieve the root domain from what is provided.
        for host in ['jcnlx.com', 'my.jobs', 'r.my.jobs']:
            request = self.factory.get(
                reverse('home', args=[self.redirect_guid,
                                      self.manipulation.view_source]),
                HTTP_HOST=host)
            response = home(request, self.redirect_guid,
                            self.manipulation.view_source)

            cookie = response.cookies['aguid']
            if 'my.jobs' in host:
                expected_domain = '.my.jobs'
            else:
                expected_domain = '.jcnlx.com'
            self.assertIn(('domain', expected_domain), cookie.items())
            uuid.UUID(unquote(cookie.value))

    def test_apply_click(self):
        self.apply_manipulation = DestinationManipulationFactory(
            view_source=1234)

        response = self.client.get(reverse('home',
                                           args=[self.redirect_guid]) +
                                   '?vs=%s' %
                                   self.apply_manipulation.view_source)
        self.assertEqual(response.status_code, 301)

        test_url = '%s?%s' % (self.redirect.url,
                              self.apply_manipulation.value_1[1:])

        self.assertEqual(response['Location'], test_url)

    def test_bad_vs_query(self):
        self.apply_manipulation = DestinationManipulationFactory(
            view_source=1234)

        response = self.client.get(reverse('home',
                                           args=[self.redirect_guid]) +
                                   '?vs=%sbad_vs' %
                                   self.apply_manipulation.view_source)

        self.assertTrue(response['Location'].endswith(self.redirect.url))

    def test_source_code_collision(self):
        """
        Test that we never duplicate source codes in the event of a collision

        Tests three circumstances:
        - The source code is the last entry in the query
        - The source code is somewhere in the middle
        - The source code is the first query
        - The source code is the only query
        """
        url = 'directemployers.jobs?%ssrc=de%s'
        for part in [('foo=bar&', ''),  # last
                     ('foo=bar&', '&code=de'),  # middle
                     ('', '&foo=bar'),  # first
                     ('', '')]:  # only
            self.redirect.url = url % part
            self.redirect.save()
            self.manipulation.value_1 = '&src=JB-DE'
            self.manipulation.save()

            response = self.client.get(
                reverse('home',
                        args=[self.redirect_guid,
                              self.manipulation.view_source]))

            self.assertTrue('src=de' not in response['Location'])
            self.assertTrue('src=JB-DE' in response['Location'])

    def test_source_code_with_encoded_parameters(self):
        """
        Sometimes the value that we're adding has %-encoded values already;
        Ensure that we don't accidentally unencode or double-encode those
        values (ie %20->%2520)
        """
        self.manipulation.value_1 = '&src=with%20space'
        self.manipulation.save()

        response = self.client.get(
            reverse('home',
                    args=[self.redirect_guid,
                          self.manipulation.view_source]))

        # We ensure that there is never a & without a preceding ? - that is
        # unlikely, however
        self.assertTrue('?' + self.manipulation.value_1[1:] in
                        response['Location'])

    def test_invalid_sourcecodetag_redirect(self):
        """
        In the event that the desired source code is not present in the
        database somehow, performing a sourcecodetag redirect should result
        in that source code not being added to the final url
        """
        self.manipulation.value_1 = ''
        self.manipulation.save()

        response = self.client.get(
            reverse('home',
                    args=[self.redirect_guid,
                          self.manipulation.view_source]))

        self.assertTrue(response['Location'].endswith(self.redirect.url))

    def test_myjobs_redirects(self):
        paths = ['/terms', '/search?location=Indianapolis']
        for path in paths:
            response = self.client.get(path, follow=True)
            self.assertEqual(response.status_code, 301)
            self.assertTrue(response['Location'].startswith(
                'http://www.my.jobs'))

    def test_debug_parameter(self):
        response = self.client.get(reverse('home',
                                           args=[self.redirect_guid,
                                                 self.manipulation.view_source,
                                                 '+']))
        self.assertTrue(self.redirect.guid in response.content)
        self.assertTrue(self.redirect.url in response.content)
        self.assertEqual(response.status_code, 200)
        self.assertTrue('google-analytics' in response.content)

    def test_redirect_on_new_job(self):
        """
        Ensure that are not done if a job was added
        within the last 30 minutes
        """
        # Make the redirect and manipulation objects look like real data
        self.redirect.new_date = datetime.datetime.now(tz=timezone.utc)
        self.redirect.url = 'http://www.directemployers.org'
        self.redirect.save()
        self.manipulation.action = 'sourcecodetag'
        self.manipulation.value_1 = '?src=foo'
        self.manipulation.view_source = 0
        self.manipulation.save()

        response = self.client.get(reverse('home',
                                           args=[self.redirect_guid]))

        # The job would normally redirect to a microsite, but it should not
        # in this instance
        self.assertFalse(response['Location'].startswith(
            self.microsite.canonical_microsite_url))
        # ... while the result of doing a sourcecodeswitch does.
        self.assertTrue(self.manipulation.value_1 in response['Location'])

        # If a job is 30 minutes old or older, the microsite result is used
        # as expected.
        self.redirect.new_date -= datetime.timedelta(minutes=30)
        self.redirect.save()
        response = self.client.get(reverse('home',
                                           args=[self.redirect_guid]))
        test_url = '%s%s/job/?vs=%s' % (self.microsite.canonical_microsite_url,
                                        self.redirect.uid,
                                        self.manipulation.view_source)
        self.assertEqual(response['Location'], test_url)

    def test_percent_encoded_url_params(self):
        """
        Ensure that query parameters retain their encoding when adding new
        parameters.
        """
        self.redirect.url = 'example.com?%c3%81=%20%3d%2b'
        self.redirect.save()
        response = self.client.get(
            reverse('home',
                    args=[self.redirect_guid,
                          self.manipulation.view_source]))
        self.assertTrue('%c3%81=%20%3d%2b' in response['Location'].lower())

    def test_cache_gets_set_on_view(self):
        """
        Viewing any page when the cache is empty should populate a list of
        excluded view sources
        """
        cache_key = settings.EXCLUDED_VIEW_SOURCE_CACHE_KEY
        cache.delete(cache_key)

        self.assertFalse(cache.get(cache_key))

        self.client.get(reverse('home',
                                args=[self.redirect_guid]))

        self.assertTrue(cache.get(cache_key))

    def test_cache_gets_cleared_on_save(self):
        """
        Saving an ExpiredViewSource object should remove the list of
        excluded view sources, which will be replaced on the next request
        """
        cache_key = settings.EXCLUDED_VIEW_SOURCE_CACHE_KEY
        self.client.get(reverse('home',
                                args=[self.redirect_guid]))

        new_evs = ExcludedViewSource.objects.all().order_by('-view_source')[0]
        new_evs = new_evs.view_source + 1

        self.assertFalse(new_evs in cache.get(cache_key))

        ExcludedViewSource(view_source=new_evs).save()

        self.assertFalse(cache.get(cache_key))

        self.client.get(reverse('home',
                                args=[self.redirect_guid]))

        self.assertTrue(new_evs in cache.get(cache_key))

    def test_custom_microsite_exclusion(self):
        custom_exclusion = CustomExcludedViewSourceFactory()

        response = self.client.get(
            reverse('home',
                    args=[self.redirect_guid,
                          custom_exclusion.view_source]))
        self.assertTrue((custom_exclusion.buid,
                         custom_exclusion.view_source) in
                        settings.CUSTOM_EXCLUSIONS)
        self.assertFalse(response['Location'].startswith(
            self.microsite.canonical_microsite_url))

    def test_custom_parameters(self):
        CustomExcludedViewSourceFactory(
            view_source=self.manipulation.view_source)
        response = self.client.get(
            reverse('home',
                    args=[self.redirect_guid,
                          self.manipulation.view_source]) + '?z=1&foo=bar')
        for part in [self.redirect.url,
                     'foo=bar',
                     self.manipulation.value_1[1:]]:
            self.assertTrue(part in response['Location'])

    def test_custom_parameters_on_microsite(self):
        self.manipulation.view_source = 0
        self.manipulation.save()
        response = self.client.get(
            reverse('home',
                    args=[self.redirect_guid]) + '?z=1&foo=bar')
        test_url = '%s%s/job/?vs=%s&z=1&foo=bar' % \
                   (self.microsite.canonical_microsite_url,
                    self.redirect.uid,
                    self.manipulation.view_source)
        self.assertEqual(response['Location'], test_url)

        response = self.client.get(
            reverse('home',
                    args=[self.redirect_guid]) + '?vs=0&z=1&foo=bar')
        test_url = '%s?%s&foo=bar' % (self.redirect.url,
                                      self.manipulation.value_1[1:])
        self.assertEqual(response['Location'], test_url)

    def test_custom_parameters_on_doubleclick(self):
        self.manipulation.action = 'doubleclickwrap'
        self.manipulation.value_1 = 'http://ad.doubleclick.net/clk;2613;950;s?'
        self.manipulation.save()

        response = self.client.get(
            reverse('home',
                    args=[self.redirect_guid,
                          self.manipulation.view_source]) + '?z=1&foo=bar')
        test_url = '%s%s?foo=bar' % (self.manipulation.value_1,
                                     self.redirect.url)
        self.assertEqual(response['Location'], test_url)


class EmailForwardTests(TestCase):
    def setUp(self):
        self.redirect = RedirectFactory(buid=1)
        self.redirect_guid = GUID_RE.sub('', self.redirect.guid)

        self.password = 'secret'
        self.user = User.objects.create(username='accounts@my.jobs')
        self.user.set_password(self.password)
        self.user.save()

        self.contact = CompanyEmail.objects.create(
            buid=self.redirect.buid,
            email=self.user.username)

        self.email = self.user.username.replace('@', '%40')
        self.auth = {
            'bad': [
                '',
                'Basic %s' % base64.b64encode('bad%40email:wrong_pass')],
            'good':
                'Basic %s' % base64.b64encode('%s:%s' % (self.user.username.\
                                                         replace('@', '%40'),
                                                         self.password))}
        self.post_dict = {'to': 'to@example.com',
                          'from': 'from@example.com',
                          'text': 'This address does not contain a valid guid',
                          'html': '',
                          'subject': 'Bad Email',
                          'attachments': 0}


    def test_jira_login(self):
        jira = JIRA(options=settings.JIRA_OPTIONS, basic_auth=settings.JIRA_AUTH)
        self.assertIsNotNone(jira)

    def test_bad_authorization(self):
        for auth in self.auth.get('bad'):
            kwargs = {}
            if auth:
                # auth_value has a value, so we can pass an HTTP_AUTHORIZATION
                #    header
                kwargs['HTTP_AUTHORIZATION'] = auth
            response = self.client.post(reverse('email_redirect'),
                                        **kwargs)
            self.assertTrue(response.status_code, 403)

    def test_good_authorization(self):
        auth_value = self.auth.get('good')
        response = self.client.post(reverse('email_redirect'),
                                    HTTP_AUTHORIZATION=auth_value)
        self.assertEqual(response.status_code, 200)

    def test_bad_email(self):
        auth = self.auth.get('good')
        response = self.client.post(reverse('email_redirect'),
                                    HTTP_AUTHORIZATION=auth,
                                    data=self.post_dict)
        self.assertEqual(response.status_code, 200)
        email = mail.outbox.pop()
        for field in [self.post_dict['to'][0], self.post_dict['from']]:
            self.assertTrue(field in email.body)

        self.assertEqual(email.from_email, self.post_dict['from'])
        self.assertEqual(email.to, [settings.EMAIL_TO_ADMIN])
        self.assertEqual(email.subject, 'My.jobs contact email')
        self.assertTrue(self.post_dict['text'] in email.body)

    def test_bad_guid_email(self):
        self.post_dict['to'] = '%s@my.jobs' % ('1'*32)
        self.post_dict['text'] = 'This address is not in the database'

        auth = self.auth.get('good')
        response = self.client.post(reverse('email_redirect'),
                                    HTTP_AUTHORIZATION=auth,
                                    data=self.post_dict)
        self.assertEqual(response.status_code, 200)
        # TODO: Test that an email gets sent once that functionality is added

    def test_good_guid_email(self):
        self.post_dict['to'] = ['%s@my.jobs' % self.redirect_guid]
        self.post_dict['text'] = 'Questions about stuff and things'
        self.post_dict['subject'] = 'Compliance'

        auth = self.auth.get('good')
        response = self.client.post(reverse('email_redirect'),
                                    HTTP_AUTHORIZATION=auth,
                                    data=self.post_dict)
        self.assertEqual(response.status_code, 200)

        email = mail.outbox.pop()
        self.assertEqual(email.from_email, self.post_dict['from'])
        self.assertEqual(email.to, [self.contact.email])
        self.assertEqual(email.subject, self.post_dict['subject'])
        self.assertEqual(email.body, self.post_dict['text'])

    def test_email_with_name(self):
        self.post_dict['to'] = 'User <%s@my.jobs>' % self.redirect_guid
        self.post_dict['text'] = 'Questions about stuff and things'
        self.post_dict['subject'] = 'Compliance'

        auth = self.auth.get('good')
        response = self.client.post(reverse('email_redirect'),
                                    HTTP_AUTHORIZATION=auth,
                                    data=self.post_dict)
        self.assertEqual(response.status_code, 200)

        email = mail.outbox.pop()

    def test_creating_mj_user(self):
        response = helpers.create_myjobs_account(self.user.username)
        for parameter in ['username=%s' % settings.MJ_API['username'].replace('@', '%40'),
                          'api_key=%s' % settings.MJ_API['key'],
                          'email=%s' % self.user.username.replace('@', '%40')]:
            self.assertTrue(parameter in response)

    def test_no_emails(self):
        self.post_dict.pop('to')
        auth = self.auth.get('good')
        response = self.client.post(reverse('email_redirect'),
                                    HTTP_AUTHORIZATION=auth,
                                    data=self.post_dict)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)

        email = mail.outbox.pop()
        self.assertTrue('My.jobs contact email' in email.subject)

    def test_too_many_emails(self):
        self.post_dict['to'] = 'test@example.com, foo@mail.my.jobs'
        auth = self.auth.get('good')
        response = self.client.post(reverse('email_redirect'),
                                    HTTP_AUTHORIZATION=auth,
                                    data=self.post_dict)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)

        email = mail.outbox.pop()
        self.assertTrue('My.jobs contact email' in email.subject)

    def test_prm_email(self):
        """
        If prm@my.jobs is included as a recipient, we repost this email to
        My.jobs. This is a straight post, which we don't want to do in a
        testing environment. If we receive a 200 status code and no emails
        were sent, this was reasonably likely to have completed successfully.
        """
        for email in ['prm@my.jobs', 'PRM@MY.JOBS']:
            self.post_dict['to'] = email
            auth = self.auth.get('good')
            response = self.client.post(reverse('email_redirect'),
                                        HTTP_AUTHORIZATION=auth,
                                        data=self.post_dict)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(len(mail.outbox), 0)


class UpdateBUIDTests(TestCase):
    def setUp(self):
        self.key = settings.BUID_API_KEY
        self.cm = CanonicalMicrositeFactory(buid=1)
        self.dm = DestinationManipulationFactory(buid=1)

    def test_key(self):
        resp = self.client.get(reverse('update_buid'))
        self.assertEqual(resp.status_code, 401)

        bad_key = '12345'
        resp = self.client.get(reverse('update_buid') + '?key=%s' % bad_key)
        self.assertEqual(resp.status_code, 401)

        resp = self.client.get(reverse('update_buid') + '?key=%s' % self.key)
        self.assertEqual(resp.content, '{"error": "Invalid format for old business unit"}')

    def test_no_new_buid(self):
        resp = self.client.get(reverse('update_buid') + '?key=%s&old_buid=%s' % (
            self.key, self.cm.buid))
        self.assertEqual(resp.content, '{"error": "Invalid format for new business unit"}')

    def test_existing_buid(self):
        resp = self.client.get(reverse('update_buid') + \
                               '?key=%s&old_buid=%s&new_buid=%s' % \
                               (self.key, self.cm.buid, self.cm.buid))
        self.assertEqual(resp.content, '{"error": "New business unit already exists"}')

    def test_no_old_buid(self):
        resp = self.client.get(reverse('update_buid') + '?key=%s&new_buid=%s' % \
                               (self.key, self.cm.buid + 1))
        self.assertEqual(resp.content, '{"error": "Invalid format for old business unit"}')

    def test_new_buid(self):
        resp = self.client.get(reverse('update_buid') + '?key=%s&old_buid=%s&new_buid=%s' % \
                               (self.key, self.cm.buid, self.cm.buid + 1))
        content = json.loads(resp.content)
        self.assertEqual(content['new_bu'], self.cm.buid + 1)
        self.assertEqual(content['updated'], 2)
