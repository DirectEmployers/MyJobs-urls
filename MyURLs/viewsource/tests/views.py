import json
import uuid

from django.test import TestCase
from django.test.client import Client
from django.core.urlresolvers import reverse, NoReverseMatch


class ViewSourceViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.guid = uuid.uuid4()
        self.guid_str = str(self.guid)
        self.guid_no_dash = self.guid_str.replace('-', '')

    def test_get_with_no_vsid(self):
        response = self.client.get(reverse('home',
                                           args=[self.guid_no_dash]))
        content = json.loads(response.content)
        self.assertEqual(content['guid'], self.guid_str)
        self.assertEqual(content['vsid'], '0')

    def test_get_with_vsid(self):
        vsid = '100'
        response = self.client.get(reverse('home',
                                           args=[self.guid_no_dash,
                                                 vsid]))
        content = json.loads(response.content)
        self.assertEqual(content['guid'], self.guid_str)
        self.assertEqual(content['vsid'], vsid)

    def test_get_with_malformed_guid(self):
        with self.assertRaises(NoReverseMatch):
            self.client.get(reverse('home',
                                    args=[self.guid_no_dash[:16]]))
