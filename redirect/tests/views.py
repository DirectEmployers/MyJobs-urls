import json
import uuid
import unittest

from django.test import TestCase
from django.test.client import Client
from django.core.urlresolvers import reverse, NoReverseMatch

from redirect.tests.factories import *


class ViewSourceViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.redirect = RedirectFactory()
        self.vs0 = ViewSourceFactory(view_source_id=0)
        self.vs100 = ViewSourceFactory(view_source_id=100)
        self.atssource = ATSSourceCodeFactory()
        self.redirectaction = RedirectActionFactory()
        self.microsite = CanonicalMicrositeFactory()

    def test_get_with_no_vsid(self):
        """
        Navigating to a url with a guid and no view source id defaults the vsid
        to 0
        """
        response = self.client.get(reverse('home',
                                           args=[self.redirect.guid]))
        content = json.loads(response.content)
        self.assertEqual(content['guid'], self.redirect.guid)
        self.assertEqual(content['vsid'], self.vs0.view_source_id)
        
        print response

    def test_get_with_vsid(self):
        """
        Navigating to a url with both a guid and view source id will use the
        given view source if it exists or display a 404 page
        """
        response = self.client.get(reverse('home',
                                           args=[self.redirect.guid,
                                                 self.vs100.view_source_id]))
        content = json.loads(response.content)
        self.assertEqual(content['guid'], self.redirect.guid)
        self.assertEqual(content['vsid'], self.vs100.view_source_id)
        
        print response
        
        response = self.client.get(reverse('home',
                                           args=[self.redirect.guid,
                                                 50]))
        self.assertEqual(response.status_code, 404)
        
        test_url = self.redirect.url + '/' + self.atssource.parameter_value
        print test_url
        print response

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
        Check view that manipulates a url with the sourcecodetag action creates
        the correct redirect url
        """                      
        response = self.client.get('manipulated_url_view', {'buid': self.atssource.buid, 
                                                            'view_source_id': self.atssource.view_source_id})        
        content = response.content
        test_url = self.redirect.url + '/' + self.atssource.parameter_value
        self.assertEqual(content['url'], test_url)
        # Redirect used in seo
        # self.assertRedirects(resp,target,status_code=301)
        
    
    def test_microsite_redirect(self):
        """
        Check view that manipulates a url with the microsite action creates
        the correct redirect url
        """                      
        response = self.client.get('manipulated_url_view', {'buid': self.microsite.buid, 
                                                            'canonical_microsite_url': self.microsite.canonical_microsite_url})
        content = response.content
        self.assertEqual(content['url'], self.microsite.canonical_microsite_url)
        # Redirect used in seo
        # self.assertRedirects(resp,target,status_code=301)
        
        

