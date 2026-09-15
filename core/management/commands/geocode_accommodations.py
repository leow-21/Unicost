import time
import requests
from django.core.management.base import BaseCommand
from core.models import Accommodation

# external geocoding API nominatim
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"

# user agent header for the nomanatim request
HEADERS = {"User-Agent": "university-cost-calculator (student project)"}

# fetches the latitude and longitude of every accommodation by querying the API above
# only processes accommodations currently without latitudes and longitudes filled in
class Command(BaseCommand):
    help = "Geocode every Accommodation missing lat/lon using OpenStreetMap Nominatim."

    def handle(self, *args, **options):
        # only fetch if coordinates are missing
        accommodations = Accommodation.objects.filter(latitude__isnull=True)
        total = accommodations.count()
        self.stdout.write(f"Found {total} accommodations without coordinates.")

        found = 0
        skipped = 0

        # loop to geocode every accommodation
        for acc in accommodations:
            # these aren't actual places so they are skipped
            # note - i manually entered the coordinates for these to just be the coordinates of each university themselves
            if acc.name.lower() in ("living at home", "shared houses"):
                skipped += 1
                continue

            city_name = acc.university.city.name if acc.university.city else ""
            query = f"{acc.name}, {city_name}, UK"

            # sends the request to nominatim
            try:
                response = requests.get(
                    NOMINATIM_URL,
                    params={"q": query, "format": "json", "limit": 1},
                    headers=HEADERS,
                    timeout=10,
                )
                results = response.json()
            except requests.RequestException as e:
                # skips if there is an API or network failure
                self.stdout.write(self.style.ERROR(f"  request failed for {acc.name}: {e}"))
                time.sleep(1)
                continue

            # write the coordinates into the SQLite if nominatim found them
            if results:
                acc.latitude = float(results[0]["lat"])
                acc.longitude = float(results[0]["lon"])
                acc.save(update_fields=["latitude", "longitude"])
                found += 1
                self.stdout.write(self.style.SUCCESS(f"  {acc.name}: {acc.latitude}, {acc.longitude}"))
            else:
                skipped += 1
                self.stdout.write(self.style.WARNING(f"  No match found for: {query}"))

            # max amount of requests per second is 1 because of nominatims API usage policy
            time.sleep(1)

        self.stdout.write(self.style.SUCCESS(f"\nDone. Geocoded {found}, skipped {skipped} of {total}."))