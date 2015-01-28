from django.core.exceptions import ObjectDoesNotExist
from django.test import TestCase

from redirect import models
from redirect.tests import factories


class ViewSourceTests(TestCase):
    def test_set_viewsource_id(self):
        self.assertEqual(models.ViewSource.objects.count(), 0)

        # Creating a ViewSource when none exist sets the viewsource_id to 0
        vs = factories.ViewSourceFactory()
        self.assertEqual(vs.view_source_id, 0)

        # Creating new ViewSource instances without providing a viewsource_id
        # does not fill in missing ids
        factories.ViewSourceFactory(view_source_id=5)
        vs = factories.ViewSourceFactory()
        self.assertEqual(vs.view_source_id, 6)

        # This holds true even if an instance is manually created within
        # an empty block
        factories.ViewSourceFactory(view_source_id=3)
        vs = factories.ViewSourceFactory()
        self.assertEqual(vs.view_source_id, 7)

        self.assertEqual(models.ViewSource.objects.count(), 5)


class ViewSourceGroupTests(TestCase):
    def test_one_view_source_multiple_groups(self):
        view_source = factories.ViewSourceFactory()
        for i in range(2):
            factories.ViewSourceGroupFactory(view_sources=(view_source, ))
        self.assertEqual(models.ViewSourceGroup.objects.count(), 2)


class BaseRedirectTests(TestCase):
    def test_get_any(self):
        redirect = factories.RedirectFactory()
        archived_redirect = factories.RedirectArchiveFactory()

        models.Redirect.objects.get_any(guid=redirect.guid)
        models.Redirect.objects.get_any(guid=archived_redirect.guid)

        self.assertRaises(ObjectDoesNotExist,
                          models.Redirect.objects.get_any, guid='a')

        models.RedirectArchive.objects.get_any(guid=redirect.guid)
        models.RedirectArchive.objects.get_any(guid=archived_redirect.guid)

        self.assertRaises(ObjectDoesNotExist,
                          models.RedirectArchive.objects.get_any, guid='a')