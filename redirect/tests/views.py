import json
import uuid
import unittest

from django.test import TestCase
from django.test.client import Client
from django.core.urlresolvers import reverse, NoReverseMatch

from redirect.models import *
from redirect.tests.factories import *


class ViewSourceViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.redirect = RedirectFactory()
        self.view_source = ViewSourceFactory(view_source_id=0)
        self.microsite = CanonicalMicrositeFactory()
        self.redirect_action = RedirectActionFactory(
            buid=self.redirect.buid,
            view_source_id=self.view_source.pk,
            action=RedirectAction.SOURCECODETAG_ACTION)

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
        the correct redirect url which will have a sourcecode tag on the end
        examples: &Codes=DE-DEA, &src=JB-11380, &src=indeed_test
        """
        ats_source = ATSSourceCodeFactory(parameter_name='src',
                                          parameter_value='indeed_test')

        response = self.client.get(reverse('home',
                                           args=[self.redirect.guid,
                                                 self.view_source.pk]))
        content = json.loads(response.content)
        test_url = self.redirect.url + u'?%s=%s' % \
            (ats_source.parameter_name, ats_source.parameter_value)
        self.assertEqual(content['url'], test_url)
        # Redirect used in seo
        # self.assertRedirects(resp,target,status_code=301)
        
    def test_micrositetag_redirect(self):
        """
        Check view that manipulates a url with the micrositetag action creates
        the correct redirect url which should be to the microsite with the
        unique ID        
        """
        self.redirect_action.action = RedirectAction.MICROSITETAG_ACTION
        self.redirect_action.save()

        response = self.client.get(reverse('home', 
                                           args=[self.redirect.guid, 
                                                 self.view_source.pk]))
        content = json.loads(response.content)
        test_url = self.microsite.canonical_microsite_url % self.redirect.uid
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
        self.redirect_action.action = RedirectAction.MICROSITE_ACTION
        self.redirect_action.save()
        ATSSourceCodeFactory()

        response = self.client.get(reverse('home', 
                                           args=[self.redirect.guid,
                                                 self.view_source.pk]))
        content = json.loads(response.content)
        test_url = (self.microsite.canonical_microsite_url + '?vs=%s') % \
            (self.redirect.uid, str(self.view_source.pk))
        self.assertEqual(content['url'], test_url)
        # Redirect used in seo
        # self.assertRedirects(resp,target,status_code=301)

    def test_passthrough_redirect(self):
        pass

    def test_amptoamp_redirect(self):
        """
        Information about test
        """
        pass 
    
    def test_cframe_redirect(self):
        """
        Information about test
        """
        pass

    def test_sourceurlwrapappend_redirect(self):
        """
        Information about test
        """
        pass

    def test_anchorredirectissue_redirect(self):
        """
        Information about test
        """
        pass
    
    def test_replacethenaddpre_redirect(self):
        """
        Information about test
        """
        pass
    
    def test_sourcecodeinsertion_redirect(self):
        """
        Information about test
        """
        pass
    
    def test_sourceurlwrapunencodedappend_redirect(self):
        """
        Information about test
        """
        pass
    
    def test_sourceurlwrapunencoded_redirect(self):
        """
        Information about test
        """
        pass 
