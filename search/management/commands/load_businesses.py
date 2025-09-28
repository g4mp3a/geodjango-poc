import json
import os
from django.contrib.gis.geos import Point
from django.core.management.base import BaseCommand
from django.conf import settings
from search.models import Business

class Command(BaseCommand):
    help = 'Load business data from businesses.json file into the database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default='businesses.json',
            help='Path to the JSON file containing business data (default: businesses.json in project root)'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing business data before loading'
        )

    def handle(self, *args, **options):
        file_path = options['file']
        clear_existing = options['clear']
        
        # If path is not absolute, assume it's relative to the project root
        if not os.path.isabs(file_path):
            file_path = os.path.join(settings.BASE_DIR, file_path)
        
        if not os.path.exists(file_path):
            self.stderr.write(self.style.ERROR(f'File not found: {file_path}'))
            return
        
        if clear_existing:
            deleted_count, _ = Business.objects.all().delete()
            self.stdout.write(
                self.style.WARNING(f'Deleted {deleted_count} existing businesses')
            )
        
        try:
            with open(file_path, 'r') as f:
                businesses_data = json.load(f)

            created_count = 0
            skipped_count = 0

            for biz_data in businesses_data:
                # Skip if business with same name, city and state
                if Business.objects.filter(
                        name=biz_data['name'],
                        city=biz_data['city'],
                        state=biz_data['state']
                ).exists():
                    skipped_count += 1
                    continue

                # Create Point from latitude and longitude
                location = Point(
                    float(biz_data['longitude']),
                    float(biz_data['latitude']),
                    srid=4326  # WGS84
                )

                # Create and save business
                Business.objects.create(
                    name=biz_data['name'],
                    city=biz_data['city'],
                    state=biz_data['state'],
                    location=location
                )
                created_count += 1

            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully loaded {created_count} businesses. '
                    f'Skipped {skipped_count} duplicates.'
                )
            )
            
        except json.JSONDecodeError:
            self.stderr.write(self.style.ERROR('Error: Invalid JSON file'))
        except KeyError as e:
            self.stderr.write(self.style.ERROR(f'Missing required field: {e}'))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'An error occurred: {str(e)}'))
