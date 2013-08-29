import json
import uuid

from django.test import TestCase
from django.test.client import Client
from django.core.urlresolvers import reverse, NoReverseMatch

from redirect.tests.factories import RedirectFactory, ViewSourceFactory, ATSSourceCodeFactory, RedirectActionFactory


class ViewSourceViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.redirect = RedirectFactory()
        self.vs0 = ViewSourceFactory(view_source_id=0)
        self.vs100 = ViewSourceFactory(view_source_id=100)
        self.atssource = ATSSourceCodeFactory()
        self.redirectaction = RedirectActionFactory()

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

        response = self.client.get(reverse('home',
                                           args=[self.redirect.guid,
                                                 50]))
        self.assertEqual(response.status_code, 404)

    def test_get_with_malformed_guid(self):
        """
        Navigating to a url with a malformed guid or a guid that contains
        non-hex characters should display a 404 page
        """
        for guid in [self.redirect.guid[:16], 'guid should be 32 '
                                              'hex characters']:
            with self.assertRaises(NoReverseMatch):
                self.client.get(reverse('home', args=[guid]))
                
    def test_sourcecodetag(self):           
        site = ATSSourceCodeFactory.build()
        site.save()        
        resp = self.client.get('/indeed/1000/job?src=indeed_test', 
            follow=True, HTTP_HOST='buckconsultants.jobs')
        target_path = u'indianapolis-in/1000/job/?utm_source=indeed&utm_medium=feed&src=indeed_test'
        quoted_path = urlquote(target_path, safe='&:=?/')
        target = u'http://buckconsultants.jobs/{0}'.format(quoted_path)
        self.assertRedirects(resp,target,status_code=301)
        
        
