from datetime import datetime, timedelta
import pytz
import uuid

from django.test import TestCase

from viewsource.models import ViewSource
from viewsource.tests.factories import ViewSourceFactory


class ViewSourceTests(TestCase):
    def test_set_viewsource_id(self):
        self.assertEqual(ViewSource.objects.count(), 0)

        # Creating a ViewSource when none exist sets the viewsource_id to 0
        vs = ViewSourceFactory()
        self.assertEqual(vs.viewsource_id, 0)

        # Creating new ViewSource instances without providing a viewsource_id
        # does not fill in missing ids
        ViewSourceFactory(viewsource_id=5)
        vs = ViewSourceFactory()
        self.assertEqual(vs.viewsource_id, 6)

        # This holds true even if an instance is manually created within
        # an empty block
        ViewSourceFactory(viewsource_id=3)
        vs = ViewSourceFactory()
        self.assertEqual(vs.viewsource_id, 7)

        self.assertEqual(ViewSource.objects.count(), 5)

    def test_get_url(self):
        fake_guid = str(uuid.uuid4()).replace('-', '')
        vs = ViewSourceFactory()
        self.assertEqual(vs.get_url(fake_guid), vs.redirect_url)

        vs.date_new = datetime.now(tz=pytz.utc) - timedelta(minutes=30)
        vs.save()
        with self.assertRaises(NotImplementedError):
            vs.get_url(fake_guid)
