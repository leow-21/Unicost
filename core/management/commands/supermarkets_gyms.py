import time
import requests
from django.core.management.base import BaseCommand
from core.models import City, Supermarket, Gym

# using overpass API this time because nominatim was down at the time this was used 
OVERPASS_URL = "https://overpass.kumi.systems/api/interpreter"
# radius searched from the city centre
RADIUS_METRES = 4000 
# header for the API request
HEADERS = {"User-Agent": "university-cost-calculator (student project)"}

# coordinates of city centres
CITY_CENTRES = {
    "Leeds": (53.8008, -1.5491),
    "Manchester": (53.4808, -2.2426),
    "Newcastle upon Tyne": (54.9783, -1.6178),
    "York": (53.9600, -1.0873),
    "Nottingham": (52.9548, -1.1581),
    "Sheffield": (53.3811, -1.4701),
    "Bath": (51.3811, -2.3590),
}

# average costs for common supermarkets + a default average for others
SUPERMARKET_COSTS = {
    "aldi": 22, "lidl": 22, "iceland": 25, "asda": 28,
    "morrisons": 30, "tesco express": 28, "tesco superstore": 35,
    "tesco extra": 36, "tesco": 32, "sainsbury": 33, "co-op": 27,
    "coop": 27, "waitrose": 45, "marks": 40, "m&s": 40,
}
DEFAULT_SUPERMARKET_COST = 30

# costs of common gyms + a default average for others
GYM_COSTS = {
    "puregym": 24.99, "the gym": 20.99, "anytime fitness": 34.99,
    "nuffield health": 65, "david lloyd": 95, "virgin active": 55,
    "everlast": 26.99, "energie": 25, "jd gyms": 22.99,
    "university sport": 0,
}
DEFAULT_GYM_COST = 28

# matches the name of the location to a price from the dictionaries above
def infer_cost(name, cost_map, default):
    lowered = name.lower()
    for key, cost in cost_map.items():
        if key in lowered:
            return cost
    return default

# queries the API for supermarkets and gyms within 4000 metres of the city centre
# retries up to attemps times
def query_overpass(tag_key, tag_value, lat, lon, attempts=3):
    query = f"""
    [out:json][timeout:25];
    (
      node["{tag_key}"="{tag_value}"](around:{RADIUS_METRES},{lat},{lon});
      way["{tag_key}"="{tag_value}"](around:{RADIUS_METRES},{lat},{lon});
    );
    out center tags;
    """
    last_error = None
    for attempt in range(1, attempts + 1):
        try:
            response = requests.post(
                OVERPASS_URL,
                data={"data": query},
                headers=HEADERS,
                timeout=30,
            )
            response.raise_for_status()
            return response.json().get("elements", [])
        except requests.RequestException as e:
            last_error = e
            if attempt < attempts:
                time.sleep(5 * attempt)
    raise last_error

# writes the fetched locations from the API to the SQLie database along with their costs
# existing entries not duplicated
class Command(BaseCommand):
    help = "fetches supermarkets and gyms near each city from OpenStreetMap"

    # since the API used was quite unreliable, i added a function to single out a single city to search if it didn't fill in the first time
    def add_arguments(self, parser):
        parser.add_argument(
            '--city',
            type=str,
            help='only process this city (matches City.name exactly)',
        )

    def handle(self, *args, **options):
        only_city = options.get('city')
        cities = City.objects.all()
        if only_city:
            cities = cities.filter(name=only_city)
            if not cities.exists():
                self.stdout.write(self.style.ERROR(f"No city found matching '{only_city}'."))
                return
        # loops over all cities
        for city in cities:
            centre = CITY_CENTRES.get(city.name)
            if not centre:
                self.stdout.write(self.style.WARNING(f"No known centre coordinates for {city.name}, skipping."))
                continue

            lat, lon = centre
            self.stdout.write(f"\n--- {city.name} ---")
            # fetches ans saves supermarkets for the city
            try:
                elements = query_overpass("shop", "supermarket", lat, lon)
            except requests.RequestException as e:
                self.stdout.write(self.style.ERROR(f"  Supermarket query failed: {e}"))
                elements = []

            added = 0
            for el in elements:
                name = el.get("tags", {}).get("name")
                if not name:
                    continue
                point_lat = el.get("lat") or el.get("center", {}).get("lat")
                point_lon = el.get("lon") or el.get("center", {}).get("lon")
                if point_lat is None or point_lon is None:
                    continue

                _, created = Supermarket.objects.get_or_create(
                    city=city, name=name,
                    defaults={
                        "latitude": point_lat,
                        "longitude": point_lon,
                        "avg_weekly_cost": infer_cost(name, SUPERMARKET_COSTS, DEFAULT_SUPERMARKET_COST),
                    },
                )
                if created:
                    added += 1
            self.stdout.write(self.style.SUCCESS(f"  Supermarkets: added {added}"))
            time.sleep(2) 
            #fetches and saves gyms for the city
            try:
                elements = query_overpass("leisure", "fitness_centre", lat, lon)
            except requests.RequestException as e:
                self.stdout.write(self.style.ERROR(f"  Gym query failed: {e}"))
                elements = []

            added = 0
            for el in elements:
                name = el.get("tags", {}).get("name")
                if not name:
                    continue
                point_lat = el.get("lat") or el.get("center", {}).get("lat")
                point_lon = el.get("lon") or el.get("center", {}).get("lon")
                if point_lat is None or point_lon is None:
                    continue

                _, created = Gym.objects.get_or_create(
                    city=city, name=name,
                    defaults={
                        "latitude": point_lat,
                        "longitude": point_lon,
                        "monthly_cost": infer_cost(name, GYM_COSTS, DEFAULT_GYM_COST),
                    },
                )
                if created:
                    added += 1
            self.stdout.write(self.style.SUCCESS(f"  Gyms: added {added}"))
            time.sleep(2)

        self.stdout.write(self.style.SUCCESS("\nDone."))