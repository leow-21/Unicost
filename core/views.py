from decimal import Decimal, InvalidOperation

from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm, AuthenticationForm
from django.contrib import messages
from django.db.models.functions import Lower
from django.shortcuts import render, redirect, get_object_or_404

from .models import (
    University, Course, Accommodation, MaintenanceLoanBand, Report, SimulationRun,
)
from .simulation import run_simulation
from .forms import CreateAccountForm

# the ID of the saved report i chose to use as the example report
EXAMPLE_REPORT_ID = 50

def home(request):
    return render(request, 'home.html')

# lets the user build a report and runs it through the monte carlo simulation when submitted
# then refreshes the same page with the results shown at the bottom
def create_report(request):
    universities = University.objects.order_by(Lower('name'))

    accommodations_by_university = {}
    courses_by_university = {}

    # creates the JSON data the dropdown javascript needs for every university
    for uni in universities:
        accommodations = sorted(
            uni.accommodations.all(),
            key=lambda acc: (acc.name != "Living at home", acc.name.lower())
        )
        accommodations_by_university[str(uni.id)] = [
            {
                'id': acc.id,
                'name': acc.name,
                'catering': (
                    (['catered'] if acc.offers_catered else [])
                    + (['self_catered'] if acc.offers_self_catered else [])
                ),
                'bathroom': (
                    (['en_suite'] if acc.offers_en_suite else [])
                    + (['shared'] if acc.offers_shared_bathroom else [])
                ),
            }
            for acc in accommodations
        ]
        courses_by_university[str(uni.id)] = [
            {'id': course.id, 'name': course.name}
            for course in uni.courses.all().order_by(Lower('name'))
        ]

    context = {
        'universities': universities,
        'accommodations_by_university': accommodations_by_university,
        'courses_by_university': courses_by_university,
    }

    if request.method == 'POST':
        # keeps whatever the user submitted so the form can be filled again if something below fails
        context['submitted'] = request.POST
        try:
            university = University.objects.get(pk=request.POST.get('university'))
            accommodation = Accommodation.objects.get(pk=request.POST.get('accommodation'))
        except (University.DoesNotExist, Accommodation.DoesNotExist, ValueError, TypeError):
            messages.error(request, 'Select a valid university and accommodation.')
            return render(request, 'create_report.html', context)

        catering = request.POST.get('catering', '')
        bathroom = request.POST.get('bathroom', '')
        rent_per_week = accommodation.get_rent(catering, bathroom)

        # refuses to run the simulation with no real rent data
        if rent_per_week is None:
            messages.error(
                request,
                f'"{accommodation.name}" doesn\'t have a rent figure set for that combination yet — add one in /admin/ under Accommodations.',
            )
            return render(request, 'create_report.html', context)

        course = Course.objects.filter(pk=request.POST.get('course')).first()
        living_situation = request.POST.get('living_situation')
        loan_band = MaintenanceLoanBand.objects.filter(living_situation=living_situation).first()

        if loan_band is None:
            messages.error(
                request,
                'Maintenance loan figures haven\'t been set up for this living situation yet — add them in /admin/ under Maintenance Loan Bands.',
            )
            return render(request, 'create_report.html', context)

        try:
            household_income = Decimal(request.POST.get('household_income') or 0)
            savings = Decimal(request.POST.get('savings') or 0)
            part_time_hours = Decimal(request.POST.get('part_time_hours') or 0)
            scholarship_amount = Decimal(request.POST.get('scholarship_amount') or 0)
            other_subscriptions_amount = Decimal(request.POST.get('other_subscriptions_amount') or 0)
            nights_out_per_week = int(request.POST.get('nights_out_per_week') or 0)
        except (InvalidOperation, ValueError):
            messages.error(request, 'Check the numeric fields and try again.')
            return render(request, 'create_report.html', context)

        if household_income > Decimal('5000000'):
            messages.error(request, 'household income looks unusually high')
            return render(request, 'create_report.html', context)

        # saves what was submitted
        report = Report.objects.create(
            user=request.user if request.user.is_authenticated else None,
            university=university,
            course=course,
            accommodation=accommodation,
            catering=catering,
            bathroom=bathroom,
            gym_membership=request.POST.get('gym_membership', 'no'),
            walking_distance=request.POST.get('walking_distance', 'under_20'),
            nights_out_per_week=nights_out_per_week,
            night_out_budget=request.POST.get('night_out_budget', 'under_10'),
            other_subscriptions_amount=other_subscriptions_amount,
            household_income=household_income,
            living_situation=living_situation,
            year_of_study=request.POST.get('year_of_study', 'first_or_middle'),
            savings=savings,
            spend_savings=request.POST.get('spend_savings', 'no'),
            loan_spread=request.POST.get('loan_spread', 'term_time'),
            part_time_hours=part_time_hours,
            scholarship_amount=scholarship_amount,
        )

        # runs the monte carlo simulation using the report data
        sim = run_simulation({
            'accommodation': accommodation,
            'rent_per_week': rent_per_week,
            'walking_distance': report.walking_distance,
            'gym_membership': report.gym_membership,
            'nights_out_per_week': report.nights_out_per_week,
            'night_out_budget': report.night_out_budget,
            'part_time_hours': report.part_time_hours,
            'household_income': report.household_income,
            'year_of_study': report.year_of_study,
            'loan_band': loan_band,
            'scholarship_amount': report.scholarship_amount,
            'other_subscriptions_amount': report.other_subscriptions_amount,
            'savings': report.savings,
            'spend_savings': report.spend_savings,
            'loan_spread': report.loan_spread,
        })

        # the simulation output is saved and permanently linked to this specific report
        simulation_run = SimulationRun.objects.create(
            report=report,
            trials=sim['trials'],
            weekly_cost_results=sim['cost']['results'],
            median_cost_per_week=sim['cost']['median'],
            p10_cost_per_week=sim['cost']['p10'],
            p90_cost_per_week=sim['cost']['p90'],
            mean_cost_per_week=sim['cost']['mean'],
            stdev_cost_per_week=sim['cost']['stdev'],
            weekly_income=sim['weekly_income'],
        )

        context['report'] = report
        context['simulation'] = simulation_run
        return render(request, 'create_report.html', context)

    return render(request, 'create_report.html', context)

# only shows if the user is logged in
# they can pick two of their own saved reports and see them side by side
@login_required
def compare(request):
    reports = Report.objects.filter(user=request.user).select_related(
        'university', 'course', 'accommodation', 'simulation_run'
    )

    selected_a = request.GET.get('report_a')
    selected_b = request.GET.get('report_b')
    comparison = None

    if selected_a and selected_b:
        report_a = reports.filter(pk=selected_a).first()
        report_b = reports.filter(pk=selected_b).first()

        if (report_a and report_b
                and hasattr(report_a, 'simulation_run')
                and hasattr(report_b, 'simulation_run')):
            # builds the data for one side of the comparison table
            def build_side(report):
                sim = report.simulation_run
                rent = report.accommodation.get_rent(report.catering, report.bathroom) or Decimal('0')
                return {
                    'label': f"{report.university.name} — {report.accommodation.name}",
                    'university': report.university.name,
                    'course': report.course.name if report.course else '—',
                    'accommodation': report.accommodation.name,
                    'rent': rent,
                    'median_cost': sim.median_cost_per_week,
                    'weekly_income': sim.weekly_income,
                    'net': sim.weekly_income - sim.median_cost_per_week,
                }

            comparison = {
                'a': build_side(report_a),
                'b': build_side(report_b),
            }

    return render(request, 'compare.html', {
        'reports': reports,
        'selected_a': selected_a,
        'selected_b': selected_b,
        'comparison': comparison,
    })


# page showing one fixed pre generated report that gives an example of what will be outputted to the user
def example_report(request):
    report = Report.objects.filter(pk=EXAMPLE_REPORT_ID).first()
    simulation = getattr(report, 'simulation_run', None) if report else None
    return render(request, 'example_report.html', {'report': report, 'simulation': simulation})

# lists every report the logged in user has created
@login_required
def saved_reports(request):
    reports = Report.objects.filter(user=request.user)
    return render(request, 'saved_reports.html', {'reports': reports})

# shows one specific saved report in full when 'view' is clicked
@login_required
def report_detail(request, pk):
    report = get_object_or_404(Report, pk=pk, user=request.user)
    simulation = getattr(report, 'simulation_run', None)
    return render(request, 'report_detail.html', {'report': report, 'simulation': simulation})

# uses djangos built in authenticationform
def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            next_url = request.POST.get('next') or request.GET.get('next')
            return redirect(next_url or 'home')
    else:
        form = AuthenticationForm(request)

    return render(request, 'login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('home')

# uses the custom createaccountform which adds email and duplicate email checks on top of djangos signup form)
def create_account(request):
    if request.method == 'POST':
        form = CreateAccountForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Welcome, {user.username}! Your account has been created.')
            return redirect('home')
    else:
        form = CreateAccountForm()

    return render(request, 'create_account.html', {'form': form})

# lets a logged in user update their username and email
@login_required
def user_info(request):
    if request.method == 'POST':
        request.user.email = request.POST.get('email', request.user.email)
        request.user.save()
        messages.success(request, 'Your details were updated.')
        return redirect('user_info')

    return render(request, 'user_info.html')

# djangos built in password change flow
@login_required
def password_change_view(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Your password was updated.')
            return redirect('user_info')
        messages.error(request, 'Check the highlighted fields and try again.')

    return redirect('user_info')