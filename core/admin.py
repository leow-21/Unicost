from django.contrib import admin
from .models import University, Course, Accommodation
from .models import City, Supermarket, Gym
from .models import MaintenanceLoanBand, Report

# each class below registers a model so it shows up in admin and controls which fields are visible and editable from the list view

@admin.register(University)
class UniversityAdmin(admin.ModelAdmin):
    list_display = ('name', 'city')
    list_filter = ('city',)

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('name', 'university')
    list_filter = ('university',)

@admin.register(Accommodation)
class AccommodationAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'university', 'latitude', 'longitude',
        'offers_catered', 'offers_self_catered',
        'offers_en_suite', 'offers_shared_bathroom',
        'rent_catered_ensuite', 'rent_catered_shared',
        'rent_self_catered_ensuite', 'rent_self_catered_shared',
    )
    list_filter = ('university', 'offers_catered', 'offers_self_catered', 'offers_en_suite', 'offers_shared_bathroom')
    list_editable = (
        'latitude', 'longitude',
        'offers_catered', 'offers_self_catered', 'offers_en_suite', 'offers_shared_bathroom',
        'rent_catered_ensuite', 'rent_catered_shared',
        'rent_self_catered_ensuite', 'rent_self_catered_shared',
    )

@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ('name',)

@admin.register(Supermarket)
class SupermarketAdmin(admin.ModelAdmin):
    list_display = ('name', 'city', 'latitude', 'longitude', 'avg_weekly_cost')
    list_filter = ('city',)
    list_editable = ('latitude', 'longitude', 'avg_weekly_cost')

@admin.register(Gym)
class GymAdmin(admin.ModelAdmin):
    list_display = ('name', 'city', 'latitude', 'longitude', 'monthly_cost')
    list_filter = ('city',)
    list_editable = ('latitude', 'longitude', 'monthly_cost')

@admin.register(MaintenanceLoanBand)
class MaintenanceLoanBandAdmin(admin.ModelAdmin):
    list_display = ('living_situation', 'max_loan', 'min_loan', 'income_threshold', 'taper_divisor')
    list_editable = ('max_loan', 'min_loan', 'income_threshold', 'taper_divisor')


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'university', 'accommodation', 'household_income', 'created_at')
    list_filter = ('university', 'living_situation', 'year_of_study')
    readonly_fields = [f.name for f in Report._meta.fields]