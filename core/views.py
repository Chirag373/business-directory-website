from django.shortcuts import render
from django.http import JsonResponse
from django.conf import settings
from businesses.models import Business
from .api_utils import CountryStateCityAPI

# Initialize the API client
api_client = None


def init_api_client():
    global api_client
    if api_client is None and settings.COUNTRY_STATE_CITY_API_KEY:
        api_client = CountryStateCityAPI(settings.COUNTRY_STATE_CITY_API_KEY)
    return api_client


# Create your views here.
def home(request):
    return render(request, "core/home.html")


def contact(request):
    return render(request, "core/contact.html")


def premium(request):
    # Get featured (premium) businesses
    premium_businesses = Business.objects.filter(featured=True)
    return render(
        request, "core/premium.html", {"premium_businesses": premium_businesses}
    )


# API endpoints for Country-State-City data
def get_countries(request):
    """API endpoint to get all countries"""
    client = init_api_client()
    if not client:
        return JsonResponse({"error": "API key not configured"}, status=500)

    countries = client.get_countries()
    return JsonResponse(countries, safe=False)


def get_states(request, country_code):
    """API endpoint to get all states for a country"""
    client = init_api_client()
    if not client:
        return JsonResponse({"error": "API key not configured"}, status=500)

    states = client.get_states(country_code)
    return JsonResponse(states, safe=False)


def get_cities(request, country_code, state_code):
    """API endpoint to get all cities for a state"""
    client = init_api_client()
    if not client:
        return JsonResponse({"error": "API key not configured"}, status=500)

    cities = client.get_cities(country_code, state_code)
    return JsonResponse(cities, safe=False)
