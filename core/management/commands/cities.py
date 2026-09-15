from django.core.management.base import BaseCommand
from core.models import City, University

# maps each university to its city
# useful for when the supermarkets and gyms are pulled

UNIVERSITY_CITIES = {
    "University of Leeds": "Leeds",
    "University of Manchester": "Manchester",
    "Newcastle University": "Newcastle upon Tyne",
    "Northumbria University": "Newcastle upon Tyne",
    "University of York": "York",
    "University of Nottingham": "Nottingham",
    "University of Sheffield": "Sheffield",
    "University of Bath": "Bath",
}

# links the city data to the SQLite database
class Command(BaseCommand):
    help = "Create cities and link each university to its city."

    def handle(self, *args, **options):
        # loops over each university 
        for uni_name, city_name in UNIVERSITY_CITIES.items():
            city, _ = City.objects.get_or_create(name=city_name)
            try:
                university = University.objects.get(name=uni_name)
            except University.DoesNotExist:
                # if the university is not in the database it is skipped
                self.stdout.write(self.style.WARNING(f"Skipped {uni_name} — not found in database."))
                continue
            # writes to the database if not already there
            if university.city_id != city.id:
                university.city = city
                university.save(update_fields=['city'])
                self.stdout.write(self.style.SUCCESS(f"Linked {uni_name} → {city_name}"))

        self.stdout.write(self.style.SUCCESS("Done."))