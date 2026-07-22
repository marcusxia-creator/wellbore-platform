from django.core.management.base import BaseCommand

from apps.wells import writes


class Command(BaseCommand):
    help = "Refresh derived well status categories for fast dashboard filtering."

    def handle(self, *args, **options):
        count = writes.refresh_well_status_categories()
        self.stdout.write(self.style.SUCCESS(f"Refreshed {count} well status categories."))
