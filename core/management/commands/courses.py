from django.core.management.base import BaseCommand
from core.models import University, Course

# courses in alphabetical order 
COURSE_NAMES = [
    "Accounting & Finance",
    "Business",
    "Civil Engineering",
    "Economics",
    "Geography",
    "History",
    "Mathematics",
    "Politics",
    "Psychology",
]

# writes the courses to each university in the SQLite database
class Command(BaseCommand):
    help = "Add the standard course list to every university currently in the database."

    def handle(self, *args, **options):
        universities = University.objects.all()
        if not universities.exists():
            # error message if there are no universities to actually attach the courses to
            self.stdout.write(self.style.WARNING("No universities in the database yet"))
            return

        total_added = 0
        # loop to add every course to every university
        for university in universities:
            for name in COURSE_NAMES:
                _, was_created = Course.objects.get_or_create(university=university, name=name)
                if was_created:
                    total_added += 1

        self.stdout.write(self.style.SUCCESS(f"Added {total_added} course entries across {universities.count()} universities."))