import json
import uuid
import unittest

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
        Information about test
        """
        self.manipulation.action = 'amptoamp'
        self.manipulation.save()
        
        pass 
    
    def test_cframe_redirect(self):
        """
        Information about test
        """
        self.manipulation.action = 'cframe'
        self.manipulation.save()
        
        pass

    def test_sourceurlwrapappend_redirect(self):
        """
        Information about test
        """
        self.manipulation.action = 'sourceurlwrapappend'
        self.manipulation.save()
        
        pass

    def test_anchorredirectissue_redirect(self):
        """
        Information about test
        """
        self.manipulation.action = 'anchorredirectissue'
        self.manipulation.save()
        
        pass
    
    def test_replacethenaddpre_redirect(self):
        """
        Information about test
        """
        self.manipulation.action = 'replacethenaddpre'
        self.manipulation.save()
        
        pass
    
    def test_sourcecodeinsertion_redirect(self):
        """
        Information about test
        """
        self.manipulation.action = 'sourcecodeinsertion'
        self.manipulation.save()
        
        pass
    
    def test_sourceurlwrapunencodedappend_redirect(self):
        """
        Information about test
        """
        self.manipulation.action = 'sourceurlwrapunencodedappend'
        self.manipulation.save()
        
        pass
    
    def test_sourceurlwrapunencoded_redirect(self):
        """
        Information about test
        """
        self.manipulation.action = 'sourceurlwrapunencoded'
        self.manipulation.save()
        
        pass 
