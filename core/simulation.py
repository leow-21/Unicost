import math
import random
import statistics
from decimal import Decimal

# average adult walking pace used to convert the max walking time preference into a distance to compare to the supermarkets and gyms
WALKING_SPEED_KMH = 4.8 

WALKING_MINUTES_BY_BAND = {
    'under_10': 10,
    'under_20': 20,
    'under_30': 30,
    'under_40': 40,
}

# minimum wage in the uk for 18-20 year olds as that covers the majority of undergads
HOURLY_WAGE_18_20 = Decimal('10.85')
DEFAULT_HOURLY_WAGE = HOURLY_WAGE_18_20

# the number of weeks in a typical uni year
ACADEMIC_YEAR_WEEKS = 32

NIGHT_OUT_BUDGET_RANGES = {
    'under_10': (5, 10),
    '10_30': (10, 30),
    '30_50': (30, 50),
}

# the straight line distance in kilometers between two latitude longitude points
def haversine_km(lat1, lon1, lat2, lon2):
    r = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)
    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))

# converts the walking time preference into a distance
def max_walking_distance_km(walking_band):
    minutes = WALKING_MINUTES_BY_BAND.get(walking_band, 20)
    return (minutes / 60) * WALKING_SPEED_KMH


# works out which gyms or supermarkets fall within the users walking distance preference and gives each one a probability of being picked in
# order of how close they are, using inverse distance as the weight 
# it is capped to the nearest max_candidates so a city centre with an unreasonable amount of supermarkets or gyms 
# doesn't create an unrealistically long amount of very low probability options
def weighted_amenities(accommodation, amenities, walking_band, max_candidates=6):
    if accommodation.latitude is None or accommodation.longitude is None:
        return []

    max_km = max_walking_distance_km(walking_band)

    scored = []
    for amenity in amenities:
        if amenity.latitude is None or amenity.longitude is None:
            continue
        distance = haversine_km(
            accommodation.latitude, accommodation.longitude,
            amenity.latitude, amenity.longitude,
        )
        scored.append((amenity, distance))

    if not scored:
        return []

    in_range = [(a, d) for a, d in scored if d <= max_km]
    if not in_range:
        nearest = min(scored, key=lambda pair: pair[1])
        return [(nearest[0], 1.0)]

    in_range.sort(key=lambda pair: pair[1])
    in_range = in_range[:max_candidates]

    weights = [(a, 1 / (d + 0.1)) for a, d in in_range]
    total_weight = sum(w for _, w in weights)
    return [(a, w / total_weight) for a, w in weights]

# samples one location for a single trial using the probability weightings from weighted_amenities
def sample_amenity(weighted_choices):
    if not weighted_choices:
        return None
    amenities, probabilities = zip(*weighted_choices)
    return random.choices(amenities, weights=probabilities, k=1)[0]

# applies the uks maintenance loan taper
# full amount given below the income threshold then reduced by £1 per taper_divisor of income
# above it down to a guaranteed minimum
# final year students get 75% of this since the loan doesnt cover the summer after finishing
def calculate_maintenance_loan(loan_band, household_income, year_of_study):
    income = Decimal(household_income)
    if income <= loan_band.income_threshold:
        loan = loan_band.max_loan
    else:
        excess = income - loan_band.income_threshold
        reduction = excess / loan_band.taper_divisor
        loan = max(loan_band.max_loan - reduction, loan_band.min_loan)

    if year_of_study == 'final':
        loan = loan * Decimal('0.75')

    return loan

# the monte carlo simulation where each trial represents one week of spending 
# rent is fixed, but the supermarkets and gym chosen, their costs, and the night out spend vary randomly each trial, 
# based on the probabilities and ranges set up above
# this is ran thousands of times to get the final distribution shown to the user
# income is fixed so it is not part of the monte carlo
def run_simulation(report_inputs, trials=20000):

    accommodation = report_inputs['accommodation']
    city = accommodation.university.city

    supermarkets = list(city.supermarkets.all()) if city else []
    gyms = list(city.gyms.all()) if city else []

    walking_band = report_inputs['walking_distance']
    weighted_supermarkets = weighted_amenities(accommodation, supermarkets, walking_band)
    weighted_gyms = weighted_amenities(accommodation, gyms, walking_band) if report_inputs['gym_membership'] == 'yes' else []

    rent_per_week = report_inputs.get('rent_per_week') or Decimal('0')

    nights_out_per_week = int(report_inputs['nights_out_per_week'])
    budget_low, budget_high = NIGHT_OUT_BUDGET_RANGES.get(report_inputs['night_out_budget'], (0, 0))

    other_subscriptions_per_week = Decimal(report_inputs.get('other_subscriptions_amount') or 0) * Decimal('12') / Decimal('52')

    hourly_wage = DEFAULT_HOURLY_WAGE
    part_time_hours = Decimal(report_inputs.get('part_time_hours') or 0)
    part_time_income_per_week = part_time_hours * hourly_wage

    maintenance_loan_annual = calculate_maintenance_loan(
        report_inputs['loan_band'],
        report_inputs['household_income'],
        report_inputs['year_of_study'],
    )

    # loan is spread over either 32 weeks or 52 weeks depending on what the user picked on the form
    loan_weeks = 52 if report_inputs.get('loan_spread') == 'year_round' else 32
    maintenance_loan_per_week = maintenance_loan_annual / loan_weeks

    scholarship_per_week = Decimal(report_inputs.get('scholarship_amount') or 0) / ACADEMIC_YEAR_WEEKS

    # savings only count as income if the user said they are willing to spend it during term time
    savings_per_week = Decimal(0)
    if report_inputs.get('spend_savings') == 'yes':
        savings_per_week = Decimal(report_inputs.get('savings') or 0) / ACADEMIC_YEAR_WEEKS

    weekly_income = part_time_income_per_week + maintenance_loan_per_week + scholarship_per_week + savings_per_week

    cost_results = []

    # runs the monte carlo trials where each loop is one simulated week
    for _ in range(trials):
        weekly_cost = rent_per_week

        # picks a supermarket for this trial and adds its cost with some random jitter 
        # this is because in real life the cost of a weekly shop will vary slightly each week
        supermarket = sample_amenity(weighted_supermarkets)
        if supermarket:
            base_cost = float(supermarket.avg_weekly_cost)
            jittered = random.gauss(base_cost, base_cost * 0.12)
            weekly_cost += Decimal(str(max(0, jittered)))

        # some jitter with the gyms too but less so because memberships are more stable
        gym = sample_amenity(weighted_gyms)
        if gym:
            base_cost = float(gym.monthly_cost) * 12 / 52
            jittered = random.gauss(base_cost, base_cost * 0.05)
            weekly_cost += Decimal(str(max(0, jittered)))

        if nights_out_per_week > 0 and budget_high > 0:
            night_out_spend = Decimal(random.uniform(budget_low, budget_high))
            weekly_cost += night_out_spend * nights_out_per_week

        weekly_cost += other_subscriptions_per_week
        cost_results.append(float(weekly_cost))

    cost_results.sort()
    n = len(cost_results)

    # summary stats used for the stat boxes and to fit the normal curve on the chart
    # the full results list is also returned so the histogram can be built from the real trial data
    return {
        'trials': trials,
        'weeks_per_year': ACADEMIC_YEAR_WEEKS,
        'cost': {
            'results': cost_results,
            'median': cost_results[n // 2],
            'p10': cost_results[int(n * 0.10)],
            'p90': cost_results[int(n * 0.90)],
            'min': cost_results[0],
            'max': cost_results[-1],
            'mean': statistics.mean(cost_results),
            'stdev': statistics.stdev(cost_results) if n > 1 else 0.0,
        },
        'weekly_income': float(weekly_income),
        'maintenance_loan_per_week': float(maintenance_loan_per_week),
        'part_time_income_per_week': float(part_time_income_per_week),
        'scholarship_per_week': float(scholarship_per_week),
    }