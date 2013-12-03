import datetime
import re
from urllib import unquote
import uuid

from django.test import TestCase
from django.test.client import Client, RequestFactory
from django.core.urlresolvers import reverse, NoReverseMatch
from django.utils import timezone
from django.utils.http import urlquote_plus

from redirect import helpers
from redirect.models import DestinationManipulation
from redirect.tests.factories import (
    RedirectFactory, CanonicalMicrositeFactory, DestinationManipulationFactory)
from redirect.views import home


class ViewSourceViewTests(TestCase):
    guid_re = re.compile(r'([{\-}])')

    def setUp(self):
        self.client = Client()
        self.redirect = RedirectFactory()
        self.microsite = CanonicalMicrositeFactory()
        self.manipulation = DestinationManipulationFactory()
        self.redirect_guid = self.guid_re.sub('', self.redirect.guid)

        self.factory = RequestFactory()

    def test_get_with_bad_vsid(self):
        """
        If no view source id is provided or the given view source id does not
        resolve to a DestinationManipulation instance, default to 0
        """
        for vsid in ['', '1']:
            response = self.client.get(reverse('home',
                                               args=[self.redirect_guid,
                                                     vsid]))
            # In this case, view source id 0 is a sourcecodetag redirect
            test_url = 'http://testserver/%s%s' % \
                (self.redirect.url, self.manipulation.value_1.replace('&','?'))
            self.assertEqual(response['Location'], test_url)

    def test_with_action_type_2(self):
        """
        Sometimes a DestinationManipulation object exists with an action_type
        of 2 but a corresponding object with an action_type of 1 does not
        exist. If one of these is encountered, we should not run the
        manipulation twice.
        """
        self.manipulation.action_type = '2'
        self.manipulation.action = 'micrositetag'
        self.redirect.url = 'www.my.jobs/[Unique_ID]/job/'
        self.manipulation.save()
        self.redirect.save()

        with self.assertRaises(DestinationManipulation.DoesNotExist):
            DestinationManipulation.objects.get(buid=self.manipulation.buid,
                                                view_source=self.manipulation.view_source,
                                                action_type=1)

        response = self.client.get(reverse('home',
                                           args=[self.redirect_guid,
                                                 self.manipulation.view_source]))
        self.assertEqual(response.status_code, 301)
        self.assertTrue(response['Location'].endswith(
            self.redirect.url.replace('[Unique_ID]', str(self.redirect.uid))))

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
        response = self.client.get(reverse('home', args=['1'*32]))
        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed(response, '404.html')

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
        test_url = 'http://testserver/%s%s' % \
            (self.redirect.url, self.manipulation.value_1.replace('&','?'))
        self.assertEqual(response['Location'], test_url)

    def test_micrositetag_redirect(self):
        """
        Check view that manipulates a url with the micrositetag action creates
        the correct redirect url which should be to the microsite with the
        unique ID
        """
        self.manipulation.action = 'micrositetag'
        self.manipulation.save()

        self.redirect.uid = '37945336'
        self.redirect.url = 'jobs.jobs/[Unique_ID]/job'
        self.redirect.save()

        response = self.client.get(
            reverse('home', args=[self.redirect_guid,
                                  self.manipulation.view_source]))
        test_url = 'http://testserver/%s' % \
            self.microsite.canonical_microsite_url.replace(
                '[Unique_ID]', str(self.redirect.uid))
        self.assertEqual(response['Location'], test_url)

    def test_microsite_redirect(self):
        """
        Check view that manipulates a url with the microsite action creates
        the correct redirect url similar to micrositetag but adds '?vs=' on
        the end
        example: http://cadence.jobs/noida-ind/smcs/37945336/job/?vs=274
        """
        self.manipulation.action = 'microsite'
        self.manipulation.value_1 = 'jobsearch.lilly.com/[Unique_ID]/job/'
        self.manipulation.save()

        self.redirect.url = 'jobsearch.lilly.com/[Unique_ID]/job/'
        self.redirect.save()

        response = self.client.get(
            reverse('home', args=[self.redirect_guid,
                                  self.manipulation.view_source]))
        test_url = 'http://testserver/' + self.manipulation.value_1
        test_url = test_url.replace('[Unique_ID]', str(self.redirect.uid))
        test_url += '?vs=%s' % self.manipulation.view_source
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
            (self.redirect.url, self.manipulation.value_2)
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

    def test_expired_facebook_job(self):
        self.manipulation.view_source = 294
        self.manipulation.save()

        self.redirect.expired_date = datetime.datetime.now(tz=timezone.utc)
        self.redirect.save()

        response = self.client.get(
            reverse('home', args=[self.redirect_guid,
                                  self.manipulation.view_source]))
        self.assertEqual(response.status_code, 410)
        self.assertTemplateUsed(response, 'redirect/expired.html')
        self.assertTrue('Please <a href="http://us.jobs/"' in response.content)
        self.assertTrue('%s (%s)' %
                        (self.redirect.job_title, self.redirect.job_location)
                        in response.content)
        self.assertTrue('facebook.com/us-jobs/?jvid=%s%s' %
                        (self.redirect_guid, self.manipulation.view_source)
                        in response.content)
        self.assertFalse('National Labor Exchange' in response.content)

    def test_expired_state_job(self):
        self.manipulation.buid = self.redirect.buid = 1228
        self.redirect.expired_date = datetime.datetime.now(tz=timezone.utc)
        self.redirect.job_location = 'NY-Rochester'
        self.manipulation.save()
        self.redirect.save()

        response = self.client.get(
            reverse('home', args=[self.redirect_guid,
                                  self.manipulation.view_source]))
        self.assertEqual(response.status_code, 410)
        self.assertTemplateUsed(response, 'redirect/expired.html')
        self.assertTrue('Please <a href="#" onclick' in response.content)
        self.assertTrue('%s (%s)' %
                        (self.redirect.job_title, self.redirect.job_location)
                        in response.content)
        self.assertTrue(self.redirect.url in response.content)
        self.assertFalse('National Labor Exchange' in response.content)

    def test_other_expired_job(self):
        self.redirect.expired_date = datetime.datetime.now(tz=timezone.utc)
        self.redirect.save()

        response = self.client.get(
            reverse('home', args=[self.redirect_guid,
                                  self.manipulation.view_source]))
        self.assertEqual(response.status_code, 410)
        self.assertTemplateUsed(response, 'redirect/expired.html')
        self.assertTrue('Please <a href="#" onclick' in response.content)
        self.assertTrue('%s (%s)' %
                        (self.redirect.job_title, self.redirect.job_location)
                        in response.content)
        self.assertTrue(self.redirect.url in response.content)
        self.assertTrue('National Labor Exchange' in response.content)
        self.assertTrue('bu=%s">%s' %
                        (self.redirect.buid, self.redirect.company_name)
                        in response.content)

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
        self.assertTrue(response['Location'].endswith(self.redirect.url))

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

            response = self.client.get(reverse('home',
                                               args=[self.redirect_guid]))
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

        response = self.client.get(reverse('home',
                                           args=[self.redirect_guid]))
        # We ensure that there is never a & without a preceding ? - that is
        # unlikely, however
        self.assertTrue('?' + self.manipulation.value_1[1:] in response['Location'])

    def test_invalid_sourcecodetag_redirect(self):
        """
        In the event that the desired source code is not present in the
        database somehow, performing a sourcecodetag redirect should result
        in that source code not being added to the final url
        """
        self.manipulation.value_1 = ''
        self.manipulation.save()

        response = self.client.get(reverse('home',
                                           args=[self.redirect_guid]))
        self.assertTrue(response['Location'].endswith(self.redirect.url))

    def test_myjobs_redirects(self):
        paths = ['/terms', '/search?location=Indianapolis']
        for path in paths:
            response = self.client.get(path, follow=True)
            self.assertEqual(response.status_code, 301)
            self.assertTrue(response['Location'].startswith('http://www.my.jobs'))

    def test_debug_parameter(self):
        response = self.client.get(reverse('home',
                                           args=[self.redirect_guid,
                                                 self.manipulation.view_source,
                                                 '+']))
        self.assertTrue(self.redirect.guid in response.content)
        self.assertTrue(self.redirect.url in response.content)
        self.assertEqual(response.status_code, 200)

    def test_microsite_redirect_on_new_job(self):
        """
        Ensure that microsite manipulations are not done if a job was added
        within the last 30 minutes
        """
        # Make the redirect and manipulation objects look like real data
        self.redirect.new_date = datetime.datetime.now(tz=timezone.utc)
        self.redirect.url = 'example.com/jobdetail.ftl'
        self.redirect.save()
        self.manipulation.action = 'microsite'
        self.manipulation.value_1 = 'www.my.jobs/[Unique_ID]/job/'
        self.manipulation.save()

        # Create a new DestinationManipulation object which should be
        # the only manipulation done
        DestinationManipulationFactory(action='sourcecodeswitch',
                                       buid=self.manipulation.buid,
                                       view_source=self.manipulation.view_source,
                                       value_1='jobdetail.ftl',
                                       value_2='jobapply.ftl',
                                       action_type=2)
        response = self.client.get(reverse('home',
                                           args=[self.redirect_guid]))

        # We know how the code *should* behave when doing just a microsite
        # redirect and what *should* happen if a job is older than 30 minutes.
        url = helpers.microsite(self.redirect, self.manipulation)

        # The result of doing a microsite manipulation does not appear
        # in the response headers...
        self.assertFalse(url in response['Location'])
        # ... while the result of doing a sourcecodeswitch does.
        self.assertTrue('jobapply.ftl' in response['Location'])

        # If a job is 30 minutes old or older, the microsite result is used
        # as expected.
        self.redirect.new_date -= datetime.timedelta(minutes=30)
        self.redirect.save()
        response = self.client.get(reverse('home',
                                           args=[self.redirect_guid]))
        self.assertTrue(url in response['Location'])

    def test_percent_encoded_url_params(self):
        """
        Ensure that query parameters retain their encoding when adding new
        parameters.
        """
        self.redirect.url = 'example.com?%2b=%20%3d%2b'
        self.redirect.save()
        response = self.client.get(reverse('home',
                                           args=[self.redirect_guid]))
        self.assertTrue('%2b=%20%3d%2b' in response['Location'].lower())
