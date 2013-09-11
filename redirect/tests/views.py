import json
import uuid
import unittest
import urllib

from django.test import TestCase
from django.test.client import Client
from django.core.urlresolvers import reverse, NoReverseMatch

from redirect import helpers
from redirect.models import *
from redirect.tests.factories import *


class ViewSourceViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.redirect = RedirectFactory()
        self.microsite = CanonicalMicrositeFactory()
        self.manipulation = DestinationManipulationFactory()

    def test_get_with_no_vsid(self):
        """
        If no view source id is provided, default to 0
        """
        response = self.client.get(reverse('home', args=[self.redirect.guid]))
        content = json.loads(response.content)
        # In this case, view source id 0 is a sourcecodetag redirect
        test_url = self.redirect.url + self.manipulation.value_1
        self.assertEqual(content['url'], test_url)

    def test_get_with_nonexistent_vsid(self):
        """
        If a view source does not exist for the given view source id,
        redirect to the job url with no manipulation
        """
        response = self.client.get(reverse('home',
                                           args=[self.redirect.guid, 5]))
        content = json.loads(response.content)
        self.assertEqual(content['url'],
                         helpers.sourcecodetag(self.redirect,
                                               self.manipulation))

    def test_get_with_malformed_guid(self):
        """
        Navigating to a url with a malformed guid or a guid that contains
        non-hex characters should display a 404 page
        """
        for guid in [self.redirect.guid[:16], 'guid should be 32 '
                                              'hex characters']:
            with self.assertRaises(NoReverseMatch):
                self.client.get(reverse('home', args=[guid]))

    def test_sourcecodetag_redirect(self):
        """
        Check view that manipulates a url with the sourcecodetag action
        creates the correct redirect url which will have a sourcecode tag on
        the end
        examples: &Codes=DE-DEA, &src=JB-11380, &src=indeed_test
        """
        response = self.client.get(
            reverse('home', args=[self.redirect.guid,
                                  self.manipulation.view_source]))
        content = json.loads(response.content)
        test_url = self.redirect.url + self.manipulation.value_1
        self.assertEqual(content['url'], test_url)
        # Redirect used in seo
        # self.assertRedirects(resp,target,status_code=301)

    def test_micrositetag_redirect(self):
        """
        Check view that manipulates a url with the micrositetag action creates
        the correct redirect url which should be to the microsite with the
        unique ID
        """
        self.manipulation.action = 'micrositetag'
        self.manipulation.save()

        response = self.client.get(
            reverse('home', args=[self.redirect.guid,
                                  self.manipulation.view_source]))
        content = json.loads(response.content)
        test_url = self.microsite.canonical_microsite_url.replace(
            '[blank_MS1]', str(self.redirect.uid))
        self.assertEqual(content['url'], test_url)
        # Redirect used in seo
        # self.assertRedirects(resp,target,status_code=301)

    def test_microsite_redirect(self):
        """
        Check view that manipulates a url with the microsite action creates
        the correct redirect url similar to micrositetag but adds '?vs=' on
        the end
        example: http://cadence.jobs/noida-ind/smcs/37945336/job/?vs=274
        """
        self.manipulation.action = 'microsite'
        self.manipulation.save()

        response = self.client.get(
            reverse('home', args=[self.redirect.guid,
                                  self.manipulation.view_source]))
        content = json.loads(response.content)
        test_url = self.microsite.canonical_microsite_url.replace(
            '[Unique_ID]', str(self.redirect.uid))
        test_url += '?vs=%s' % self.manipulation.view_source
        self.assertEqual(content['url'], test_url)
        # Redirect used in seo
        # self.assertRedirects(resp,target,status_code=301)

    def test_amptoamp_redirect(self):
        """
        Check method that manipulates a url with the amptoamp action
        """
        self.manipulation.action = 'amptoamp'
        #self.manipulation.view_source = 0
        self.manipulation.value_1 = 'http://ad.doubleclick.net/clk;2526;8138?'
        self.manipulation.value_2 = '&functionName=viewFromLink&locale=en-us'
        self.manipulation.save()
        
        #response = self.client.get(
            #reverse('home', args=[self.redirect.guid,
                                  #self.manipulation.view_source]))
        #content = json.loads(response.content)
        
        pass
    
    
    def test_urlswap_redirect(self):
        """
        Check method that manipulates a url with the cframe action
        """
        self.manipulation.action = 'urlswap'
        self.manipulation.value_1 = 'https://careers.nscorp.com/?sap-client=100'
        self.manipulation.save()
        
        response = self.client.get(
            reverse('home', args=[self.redirect.guid,
                                  self.manipulation.view_source]))
        content = json.loads(response.content)
        test_url = self.manipulation.value_1
        self.assertEqual(content['url'], test_url)
        
        
    def test_cframe_redirect(self):
        """
        Check method that manipulates a url with the cframe action
        """
        self.manipulation.action = 'cframe'
        self.manipulation.value_1 = 'fedex.asp'
        self.manipulation.save()
        
        response = self.client.get(
            reverse('home', args=[self.redirect.guid,
                                  self.manipulation.view_source]))
        content = json.loads(response.content)
        url = urllib.quote(self.redirect.url)
        url = '%s?url=%s' % (self.manipulation.value_1, url)        
        test_url = 'http://directemployers.us.jobs/companyframe/' + url
        self.assertEqual(content['url'], test_url)
        

    def test_sourceurlwrapappend_redirect(self):
        """
        Check method that manipulates a url with the sourceurlwrapappend action
        """
        self.manipulation.action = 'sourceurlwrapappend'
        self.manipulation.save()
        
        response = self.client.get(
            reverse('home', args=[self.redirect.guid,
                                  self.manipulation.view_source]))
        content = json.loads(response.content)
        
        pass
    

    def test_anchorredirectissue_redirect(self):
        """
        Check method that manipulates a url with the anchorredirectissue action
        """
        self.manipulation.action = 'anchorredirectissue'
        self.manipulation.save()
        
        response = self.client.get(
            reverse('home', args=[self.redirect.guid,
                                  self.manipulation.view_source]))
        content = json.loads(response.content)
        
        pass
    
    
    def test_replacethenaddpre_redirect(self):
        """
        Check method that manipulates a url with the replacethenaddpre action
        """
        self.manipulation.action = 'replacethenaddpre'
        self.manipulation.value_1 = '?ss=paid!!!!?apstr=src%3DJB-10600'
        self.manipulation.save()
        
        response = self.client.get(
            reverse('home', args=[self.redirect.guid,
                                  self.manipulation.view_source]))
        content = json.loads(response.content)
        
        pass
    
    
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
            reverse('home', args=[self.redirect.guid,
                                  self.manipulation.view_source]))
        content = json.loads(response.content)
        url = self.redirect.url.split('#')
        test_url = ('%s#' % self.manipulation.value_1).join(url)
        self.assertEqual(content['url'], test_url)
        
    
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
            reverse('home', args=[self.redirect.guid,
                                  self.manipulation.view_source]))
        content = json.loads(response.content)
        url = self.manipulation.value_1 + self.redirect.url
        test_url = url + self.manipulation.value_2
        self.assertEqual(content['url'], test_url)
        
    
    def test_sourceurlwrapunencoded_redirect(self):
        """
        Check method that manipulates a url with the sourceurlwrapunencoded 
        action
        """
        self.manipulation.action = 'sourceurlwrapunencoded'
        self.manipulation.value_1 = 'http://ad.doubleclick.net/clk;346;154;h?'
        self.manipulation.save()
        
        response = self.client.get(
            reverse('home', args=[self.redirect.guid,
                                  self.manipulation.view_source]))
        content = json.loads(response.content)        
        test_url = self.manipulation.value_1 + self.redirect.url        
        self.assertEqual(content['url'], test_url)
                
    
    def test_sourceurlwrap_redirect(self):
        """
        Check method that manipulates a url with the sourceurlwrap action
        """
        self.manipulation.action = 'sourceurlwrap'
        self.manipulation.value_1 = 'http://bs.serving-sys.com/?cn=t&rtu=$$'
        self.manipulation.save()
        
        response = self.client.get(
            reverse('home', args=[self.redirect.guid,
                                  self.manipulation.view_source]))
        content = json.loads(response.content)
        url = urllib.quote(self.redirect.url)
        test_url = self.manipulation.value_1 + url
        self.assertEqual(content['url'], test_url)
        
        
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
            reverse('home', args=[self.redirect.guid,
                                  self.manipulation.view_source]))
        content = json.loads(response.content)
        old = self.manipulation.value_1
        new = self.manipulation.value_2
        test_url = new.join(self.redirect.url.rsplit(old, 1))        
        self.assertEqual(content['url'], test_url)        
        
