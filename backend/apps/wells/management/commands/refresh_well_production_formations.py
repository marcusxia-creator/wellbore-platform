from django.core.management.base import BaseCommand

from apps.wells import writes


class Command(BaseCommand):
    help = "Refresh sliced production/injection formation values for fast filtering."

    def handle(self, *args, **options):
        mapping_count, formation_count = writes.refresh_well_production_formations()
        self.stdout.write(
            self.style.SUCCESS(
                f"Refreshed {mapping_count} well-formation mappings across {formation_count} unique formations."
            )
        )
