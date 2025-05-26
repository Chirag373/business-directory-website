from django.urls import path
from . import views


urlpatterns = [
        path('signup/', views.signup_handyman, name='signup_handyman'),
        path('dashboard/', views.dashboard, name='handyman_dashboard'),
        path('dashboard/profile/', views.profile_tab, name='handyman_dashboard_profile'),
        path('dashboard/promotions/', views.promotions_tab, name='handyman_dashboard_promotions'),
        path('dashboard/services/', views.services_tab, name='handyman_dashboard_services'),
        path('dashboard/jobs/', views.jobs_tab, name='handyman_dashboard_jobs'),
        path('update-profile/', views.update_profile, name='handyman_update_profile'),
        path('update-service-description/', views.update_service_description, name='handyman_update_service_description'),
        path('add-service/', views.add_service, name='handyman_add_service'),
        path('create-promotion/', views.create_promotion, name='handyman_create_promotion'),
        path('deactivate-promotion/<int:promotion_id>/', views.deactivate_promotion, name='handyman_deactivate_promotion'),
        path('update-job-status/<int:job_id>/', views.update_job_status, name='handyman_update_job_status'),
        path('setup/', views.handyman_setup, name='handyman_setup'),
]