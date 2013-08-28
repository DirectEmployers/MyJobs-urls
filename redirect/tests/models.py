from datetime import datetime, timedelta
import unittest

import pytz
import uuid

from django.test import TestCase

from redirect.models import ViewSource
from redirect.tests.factories import RedirectFactory, ViewSourceFactory


class ViewSourceTests(TestCase):
    def test_set_viewsource_id(self):
        self.assertEqual(ViewSource.objects.count(), 0)

        # Creating a ViewSource when none exist sets the viewsource_id to 0
        vs = ViewSourceFactory()
        self.assertEqual(vs.view_source_id, 0)

        # Creating new ViewSource instances without providing a viewsource_id
        # does not fill in missing ids
        ViewSourceFactory(view_source_id=5)
        vs = ViewSourceFactory()
        self.assertEqual(vs.view_source_id, 6)

        # This holds true even if an instance is manually created within
        # an empty block
        ViewSourceFactory(view_source_id=3)
        vs = ViewSourceFactory()
        self.assertEqual(vs.view_source_id, 7)

        self.assertEqual(ViewSource.objects.count(), 5)
