import datetime
import re

from django.test import TestCase
from django.test.client import Client
from django.core.urlresolvers import reverse, NoReverseMatch
from django.utils import timezone
from django.utils.http import urlquote_plus

from redirect.models import DestinationManipulation
from redirect.tests.factories import (
    RedirectFactory, CanonicalMicrositeFactory, DestinationManipulationFactory)


class ViewSourceViewTests(TestCase):
    guid_re = re.compile(r'([{\-}])')

    def setUp(self):
        self.client = Client()
        self.redirect = RedirectFactory()
        self.microsite = CanonicalMicrositeFactory()
        self.manipulation = DestinationManipulationFactory()
        self.redirect_guid = self.guid_re.sub('', self.redirect.guid)

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
                (self.redirect.url, self.manipulation.value_1)
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

        response = self.client.get(reverse('home',
                                           args=[self.redirect_guid,
                                                 self.manipulation.view_source]))
        self.assertEqual(response.status_code, 301)
        self.assertTrue(response['Location'].endswith(
            self.redirect.url.replace('[Unique_ID]', str(self.redirect.uid))))

    def test_action_types(self):
        """
        DestinationManipulation.action_type is an integer that can be either
        1 or 2. Sometimes a DestinationManipulation object exists with
        action_type 2 but no corresponding object exists for action_type 1.
        The correct object should be retrieved regardless.
        """
        old_action_type = self.manipulation.action_type
        self.manipulation.action_type = old_action_type + 1
        self.manipulation.save()

        with self.assertRaises(DestinationManipulation.DoesNotExist):
            DestinationManipulation.objects.get(buid=self.manipulation.buid,
                                                view_source=self.manipulation.view_source,
                                                action_type=old_action_type)

        response = self.client.get(reverse('home',
                                           args=[self.redirect_guid,
                                                 self.manipulation.view_source]))
        self.assertEqual(response.status_code, 301)

    def test_get_with_malformed_guid(self):
        """
        Navigating to a url with a malformed guid or a guid that contains
        non-hex characters should display a 404 page
        """
        for guid in [self.redirect_guid[:16], 'guid should be 32 '
                                              'hex characters']:
            with self.assertRaises(NoReverseMatch):
                self.client.get(reverse('home', args=[guid]))

    def test_open_graph_redirect(self):
        """
        Check social bot open graph response
        """
        response = self.client.get(
            reverse('home', args=[self.redirect_guid,
                                  self.manipulation.view_source]),
            HTTP_USER_AGENT='facebookexternalhit')
        self.assertContains(response, 'US.jobs - Programmer - DirectEmployers')

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
            (self.redirect.url, self.manipulation.value_1)
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
