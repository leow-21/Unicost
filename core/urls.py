from django.urls import path
from . import views

# assigns each URL path to the view function that handles it and gives each one a name so templates can link to them with 
# {% url 'name' %} instead of hardcoding the path
urlpatterns = [
    path('', views.home, name='home'),
    path('create-report/', views.create_report, name='create_report'),
    path('compare/', views.compare, name='compare'),
    path('example-report/', views.example_report, name='example_report'),
    path('saved-reports/', views.saved_reports, name='saved_reports'),
    path('reports/<int:pk>/', views.report_detail, name='report_detail'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('create-account/', views.create_account, name='create_account'),
    path('account/', views.user_info, name='user_info'),
    path('account/password/', views.password_change_view, name='password_change'),
]