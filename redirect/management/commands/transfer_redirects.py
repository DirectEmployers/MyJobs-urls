from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.db import Error

from redirect.tasks import expired_to_archive_table


class Command(BaseCommand):
    help = 'Moves expired jobs from Redirect to RedirectArchive'

    def handle(self, *args, **options):
        try:
            expired_to_archive_table()
        except Error, e:
            # Error is the parent to all of Django's database-related
            # exceptions.
            send_mail('transfer_redirects failed',
                      str(e),
                      'monitoring@my.jobs',
                      ['aws@directemployers.org'],
                      fail_silently=False)
