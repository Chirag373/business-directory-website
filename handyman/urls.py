from django.urls import path
from . import views


urlpatterns = [
    path("signup/", views.HandymanSignupView.as_view(), name="signup_handyman"),
    path(
        "dashboard/", views.HandymanDashboardView.as_view(), name="handyman_dashboard"
    ),
    path(
        "update-profile/",
        views.HandymanProfileUpdateFormView.as_view(),
        name="handyman_update_profile",
    ),
    path(
        "update-business-card/",
        views.HandymanBusinessCardUpdateView.as_view(),
        name="handyman_update_business_card",
    ),
    path(
        "update-profile/",
        views.HandymanProfileUpdateFormView.as_view(),
        name="handyman_update_profile",
    ),
    path(
        "update-services/",
        views.HandymanServicesUpdateView.as_view(),
        name="handyman_update_services",
    ),
    path(
        "services-tab/",
        views.HandymanServicesTabView.as_view(),
        name="handyman_services_tab",
    ),
    path("jobs-tab/", views.HandymanJobsTabView.as_view(), name="handyman_jobs_tab"),
    path(
        "create-promotion/",
        views.HandymanPromotionCreateView.as_view(),
        name="handyman_create_promotion",
    ),
    path(
        "toggle-promotion/",
        views.HandymanTogglePromotionView.as_view(),
        name="handyman_toggle_promotion",
    ),
    path(
        "job-requests/",
        views.HandymanJobRequestsView.as_view(),
        name="handyman_job_requests",
    ),
    path("payment/", views.HandymanPaymentView.as_view(), name="handyman_payment"),
    path("", views.HandymanMainView.as_view(), name="handyman_main"),
    path("", views.HandymanMainView.as_view(), name="handyman"),
    path('notifications/', views.get_user_notifications, name='user_notifications'),
    path('notifications/<int:notification_id>/read/', views.mark_notification_read, name='mark_notification_read'),
]
