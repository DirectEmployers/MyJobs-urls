from django.db import IntegrityError
from django.test import TestCase

from redirect.models import ViewSource, ViewSourceGroup
from redirect.tests.factories import ViewSourceFactory, ViewSourceGroupFactory


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


class ViewSourceGroupTests(TestCase):
    def test_view_source_group_without_view_source(self):
        with self.assertRaises(IntegrityError):
            ViewSourceGroup(name='foo').save()

    def test_one_view_source_multiple_groups(self):
        view_source = ViewSourceFactory()
        groups = []
        for i in range(2):
            groups.append(ViewSourceGroupFactory(view_source=view_source))
