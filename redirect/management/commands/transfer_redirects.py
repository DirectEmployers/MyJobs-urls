from django.core.management.base import BaseCommand

from redirect.tasks import expired_to_archive_table


class Command(BaseCommand):
    help = 'Moves expired jobs from Redirect to RedirectArchive'

    def handle(self, *args, **options):
        expired_to_archive_table()