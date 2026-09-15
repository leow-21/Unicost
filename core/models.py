from django.conf import settings
from django.db import models

# links universities to their city, so the supermarket and gym data can be used for multiple unis in the same city
class City(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class University(models.Model):
    name = models.CharField(max_length=200, unique=True)
    city = models.ForeignKey(City, on_delete=models.PROTECT, related_name='universities', null=True, blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Course(models.Model):
    university = models.ForeignKey(University, on_delete=models.CASCADE, related_name='courses')
    name = models.CharField(max_length=200)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.university.name})"

# the accommodation class splits rent into four possible outcomes dependent on the catering and bathroom situation
class Accommodation(models.Model):
    university = models.ForeignKey(University, on_delete=models.CASCADE, related_name='accommodations')
    name = models.CharField(max_length=200)

    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    offers_catered = models.BooleanField(default=False)
    offers_self_catered = models.BooleanField(default=True)
    offers_en_suite = models.BooleanField(default=False)
    offers_shared_bathroom = models.BooleanField(default=False)

    rent_catered_ensuite = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True)
    rent_catered_shared = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True)
    rent_self_catered_ensuite = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True)
    rent_self_catered_shared = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True)

    # fetches the correct rent for what the user entered 
    def get_rent(self, catering, bathroom):
        field_map = {
            ('catered', 'en_suite'): self.rent_catered_ensuite,
            ('catered', 'shared'): self.rent_catered_shared,
            ('self_catered', 'en_suite'): self.rent_self_catered_ensuite,
            ('self_catered', 'shared'): self.rent_self_catered_shared,
        }
        exact = field_map.get((catering, bathroom))
        if exact is not None:
            return exact
        for value in field_map.values():
            if value is not None:
                return value
        return None

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.university.name})"


class Supermarket(models.Model):
    city = models.ForeignKey(City, on_delete=models.CASCADE, related_name='supermarkets')
    name = models.CharField(max_length=200)
    latitude = models.FloatField()
    longitude = models.FloatField()
    avg_weekly_cost = models.DecimalField(max_digits=6, decimal_places=2)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.city.name})"


class Gym(models.Model):
    city = models.ForeignKey(City, on_delete=models.CASCADE, related_name='gyms')
    name = models.CharField(max_length=200)
    latitude = models.FloatField()
    longitude = models.FloatField()
    monthly_cost = models.DecimalField(max_digits=6, decimal_places=2)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.city.name})"

# based on the uk governments maintenance loan requirements
class MaintenanceLoanBand(models.Model):
    AT_HOME = 'at_home'
    AWAY_OUTSIDE_LONDON = 'away_outside_london'
    AWAY_IN_LONDON = 'away_in_london'
    LIVING_SITUATION_CHOICES = [
        (AT_HOME, 'Living with parents/guardians'),
        (AWAY_OUTSIDE_LONDON, 'Away from home, outside London'),
        (AWAY_IN_LONDON, 'Away from home, in London'),
    ]

    living_situation = models.CharField(max_length=30, choices=LIVING_SITUATION_CHOICES, unique=True)
    max_loan = models.DecimalField(max_digits=8, decimal_places=2)
    min_loan = models.DecimalField(max_digits=8, decimal_places=2)
    income_threshold = models.DecimalField(max_digits=8, decimal_places=2)
    taper_divisor = models.DecimalField(max_digits=6, decimal_places=2)

    def __str__(self):
        return self.get_living_situation_display()

# everything the user entered on create report
class Report(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reports', null=True, blank=True)
    university = models.ForeignKey(University, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.SET_NULL, null=True, blank=True)
    accommodation = models.ForeignKey(Accommodation, on_delete=models.CASCADE)

    catering = models.CharField(max_length=20)
    bathroom = models.CharField(max_length=20)

    gym_membership = models.CharField(max_length=3)
    walking_distance = models.CharField(max_length=20)
    nights_out_per_week = models.PositiveSmallIntegerField()
    night_out_budget = models.CharField(max_length=20)
    other_subscriptions_amount = models.DecimalField(max_digits=7, decimal_places=2, default=0)

    household_income = models.DecimalField(max_digits=20, decimal_places=2)
    living_situation = models.CharField(max_length=30)
    year_of_study = models.CharField(max_length=20)
    savings = models.DecimalField(max_digits=9, decimal_places=2, default=0)
    spend_savings = models.CharField(max_length=3, default='no')
    loan_spread = models.CharField(max_length=10, default='term_time')
    part_time_hours = models.DecimalField(max_digits=4, decimal_places=1, default=0)
    scholarship_amount = models.DecimalField(max_digits=9, decimal_places=2, default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Report for {self.university.name} ({self.created_at:%Y-%m-%d})"

# the actual monte carlo output for a report 
# every trials cost is stored in weekly_cost_results
class SimulationRun(models.Model):
    report = models.OneToOneField(Report, on_delete=models.CASCADE, related_name='simulation_run')
    trials = models.PositiveIntegerField()

    weekly_cost_results = models.JSONField()

    median_cost_per_week = models.DecimalField(max_digits=8, decimal_places=2)
    p10_cost_per_week = models.DecimalField(max_digits=8, decimal_places=2)
    p90_cost_per_week = models.DecimalField(max_digits=8, decimal_places=2)
    mean_cost_per_week = models.DecimalField(max_digits=8, decimal_places=2)
    stdev_cost_per_week = models.DecimalField(max_digits=8, decimal_places=2)

    weekly_income = models.DecimalField(max_digits=8, decimal_places=2)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Simulation for {self.report}"