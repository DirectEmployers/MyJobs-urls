from django.test import TestCase

from redirect import helpers


class HelperTests(TestCase):
    def setUp(self):
        self.params = {'key': 'key',
                       'value': 'value',
                       'separator': ', '}

    def add_part(self, body=''):
        return helpers.add_part(body, self.params['key'],
                                self.params['value'], self.params['separator'])

    def test_add_body_part(self):
        body = self.add_part()
        expected = '%s: %s\n' % (self.params['key'], self.params['value'])
        self.assertEqual(body, expected)

        self.params['value'] = ['multiple', 'values']
        expected = '%s: %s\n' % (self.params['key'],
                                 self.params['separator'].join(
                                     self.params['value']))
        body = self.add_part()
        self.assertEqual(body, expected)
