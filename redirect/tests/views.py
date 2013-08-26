import json
import uuid

from django.test import TestCase
from django.test.client import Client
from django.core.urlresolvers import reverse, NoReverseMatch

from redirect.tests.factories import RedirectFactory, ViewSourceFactory


class ViewSourceViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.redirect = RedirectFactory()
        self.viewsource = ViewSourceFactory(viewsource_id=100)

    def test_get_with_no_vsid(self):
        response = self.client.get(reverse('home',
                                           args=[self.redirect.guid]))
        content = json.loads(response.content)
        self.assertEqual(content['guid'], self.redirect.guid)
        self.assertEqual(content['vsid'], 0)

    def test_get_with_vsid(self):
        response = self.client.get(reverse('home',
                                           args=[self.redirect.guid,
                                                 self.viewsource.viewsource_id]))
        content = json.loads(response.content)
        self.assertEqual(content['guid'], self.redirect.guid)
        self.assertEqual(content['vsid'], self.viewsource.viewsource_id)

    def test_get_with_malformed_guid(self):
        with self.assertRaises(NoReverseMatch):
            self.client.get(reverse('home',
                                    args=[self.redirect.guid[:16]]))
