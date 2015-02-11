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

    def test_expired_already_in_archive_table(self):
        """
        Redirects in the Redirect table might've already been put in the
        RedirectArchive and then readded to the Redirect table.
        If this happens the entry from Redirect should overwrite
        the RedirectArchive table when the redirect is re-archived.

        """
        thirty_one = date.today() - timedelta(31)
        expired_redirect = RedirectFactory(job_title='Redirect',
                                           expired_date=thirty_one)
        archive_redirect = RedirectArchiveFactory(job_title='RedirectArchive',
                                                  guid=expired_redirect.guid)
        tasks.expired_to_archive_table()

        # The redirect should've been removed from the Redirect table.
        self.assertRaises(Redirect.DoesNotExist,
                          Redirect.objects.get, guid=expired_redirect.guid)

        # The redirect should be in the RedirectArchive table.
        redirect = RedirectArchive.objects.get(guid=archive_redirect.guid)

        # The redirect should've been updated to match the one that was
        # in the Redirect table.
        self.assertEqual(redirect.job_title, expired_redirect.job_title)
