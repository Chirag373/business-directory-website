from django.urls import path
from . import views
from django.views.generic import RedirectView
from django.contrib.auth import views as auth_views

urlpatterns = [
    path("", RedirectView.as_view(url="/login/")),
    path("login/", views.login_view, name="login"),
    path("logout/", auth_views.LogoutView.as_view(next_page="/login/"), name="logout"),
    path("register/", views.register_view, name="register"),
    path(
        "signup/", RedirectView.as_view(url="/users/register/"), name="signup"
    ),  # Redirect for backward compatibility
    path(
        "requestor-signup/", views.requestor_signup, name="requestor_signup"
    ),  # Add URL for requestor signup
    # Magic link authentication
    path("generate-login-link/", views.generate_login_link, name="generate_login_link"),
    path("verify-token/<str:token>/", views.verify_token, name="verify_token"),
    path(
        "magic-link/<str:token>/", views.magic_link_login, name="magic_link_login"
    ),  # Add URL for magic link login
    # Dashboard views
    path("consumer-dashboard/", views.consumer_dashboard, name="consumer_dashboard"),
    path("consumer-dashboard/profile/", views.user_profile, name="user_profile"),
    path(
        "consumer-dashboard/preferences/",
        views.user_preferences,
        name="user_preferences",
    ),
    path("consumer-dashboard/offers/", views.offers_tab, name="offers_tab"),
    path(
        "consumer-dashboard/filter-offers/", views.filter_offers, name="filter_offers"
    ),
    path(
        "consumer-dashboard/notifications/",
        views.notifications_tab,
        name="user_notifications",
    ),
    # Handyman/Provider Dashboard
    path("provider-dashboard/", views.provider_dashboard, name="provider_dashboard"),
    # Promoter Dashboard
    path("promoter-dashboard/", views.promoter_dashboard, name="promoter_dashboard"),
]
