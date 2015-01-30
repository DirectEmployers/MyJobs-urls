from datetime import date, timedelta
from uuid import uuid4

from django.test import TestCase

from redirect.tests.factories import RedirectFactory, RedirectArchiveFactory
from redirect.models import Redirect, RedirectArchive
from redirect import tasks


class TaskTests(TestCase):
    def test_expired_to_archive_table(self):
        """
        Redirects that have been expired for 30 or more days should be moved
        from the Redirect table to the RedirectArchive table.

        """
        twenty_nine = date.today() - timedelta(29)
        thirty = date.today() - timedelta(30)
        thirty_one = date.today() - timedelta(31)

        not_expired = RedirectFactory(guid=uuid4())
        twenty_nine_days_expired = RedirectFactory(expired_date=twenty_nine,
                                                   guid=uuid4())
        thirty_days_expired = RedirectFactory(expired_date=thirty,
                                              guid=uuid4())
        thirty_one_days_expired = RedirectFactory(expired_date=thirty_one,
                                                  guid=uuid4())

        tasks.expired_to_archive_table()

        # Confirm the redirects that haven't been expired for thirty or more
        # days are still in the Redirect table.
        for redirect in [not_expired, twenty_nine_days_expired]:
            Redirect.objects.get(guid=redirect.guid)

        # Confirm that the redirects that have been expired for thirty
        # days or more are no longer in the Redirect table.
        for redirect in [thirty_days_expired, thirty_one_days_expired]:
            self.assertRaises(Redirect.DoesNotExist,
                              Redirect.objects.get, guid=redirect.guid)

        # Confirm that expired redirects have been correctly move to the
        # RedirectArchive table.
        for redirect in [thirty_days_expired, thirty_one_days_expired]:
            RedirectArchive.objects.get(guid=redirect.guid)

        # Confirm that unexpired redirects and redirects expired
        # for less than thirty days are not in the RedirectArchive table.
        for redirect in [not_expired, twenty_nine_days_expired]:
            self.assertRaises(RedirectArchive.DoesNotExist,
                              RedirectArchive.objects.get, guid=redirect.guid)

    def test_unexpired_to_active_table(self):
        """
        Redirects that aren't actually expired should be moved from
        the RedirectArchive table to the Redirect table.

        """
        expired = RedirectArchiveFactory(guid=uuid4())
        unexpired = RedirectArchiveFactory(expired_date=None, guid=uuid4())

        tasks.unexpired_to_active_table()

        # Expired jobs should still be in the RedirectArchive table.
        RedirectArchive.objects.get(guid=expired.guid)

        # Unexpired jobs (i.e. jobs with no expired_date) should not
        # be kept in the RedirectArchive table.
        self.assertRaises(RedirectArchive.DoesNotExist,
                          RedirectArchive.objects.get, guid=unexpired.guid)

        # Unexpired jobs should be moved to the Redirect table.
        Redirect.objects.get(guid=unexpired.guid)

        # Expired jobs should not be moved back to the Redirect table.
        self.assertRaises(Redirect.DoesNotExist,
                          Redirect.objects.get, guid=expired.guid)

    def test_remove_duplicates(self):
        """
        Duplicates guids across the Redirect - RedirectArchive tables should
        be removed from the RedirectArchive table but not the Redirect table.

        """
        unexpired = RedirectFactory(guid=uuid4())
        expired_duplicate = RedirectArchiveFactory(guid=unexpired.guid)
        expired_not_duplicate = RedirectArchiveFactory(guid=uuid4())

        tasks.remove_duplicates()

        # Duplicates should not be removed from the Redirect table.
        # Non-duplicates should be left alone.
        # Redirect.objects.get(guid=unexpired.guid)
        # RedirectArchiveFactory.objects.get(guid=expired_not_duplicate.guid)
        #
        # # Duplicates should be removed from the RedirectArchive table.
        # self.assertRaises(RedirectArchive.DoesNotExist,
        #                   RedirectArchive.objects.get,
        #                   guid=expired_duplicate.guid)