from django.core.management.base import BaseCommand
from parcel.pathao_integration import PathaoAPIClient
import logging
import time

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Populate Pathao cities, zones, and areas from API'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force update existing records',
        )

    def handle(self, *args, **options):
        self.stdout.write('Starting Pathao locations population...')

        try:
            client = PathaoAPIClient()

            # Populate cities
            self.stdout.write('Fetching cities...')
            cities = client.get_cities()
            self.stdout.write(f'Found {len(cities)} cities')

            # Populate zones for each city
            for city in cities:
                self.stdout.write(f'Fetching zones for city: {city.get("city_name")}')
                zones = client.get_zones(city['city_id'])
                self.stdout.write(f'Found {len(zones)} zones')
                time.sleep(1)  # Delay to avoid rate limiting

                # Populate areas for each zone
                for zone in zones:
                    self.stdout.write(f'Fetching areas for zone: {zone.get("zone_name")}')
                    areas = client.get_areas(zone['zone_id'])
                    self.stdout.write(f'Found {len(areas)} areas')
                    time.sleep(1)  # Delay to avoid rate limiting

            self.stdout.write(
                self.style.SUCCESS('Successfully populated Pathao locations')
            )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error populating locations: {str(e)}')
            )
            logger.exception('Error in populate_pathao_locations command')