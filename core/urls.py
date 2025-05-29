from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('contact/', views.contact, name='contact'),
    path('premium/', views.premium, name='premium'),
    
    # API endpoints for Country-State-City data
    path('api/countries/', views.get_countries, name='api_countries'),
    path('api/states/<str:country_code>/', views.get_states, name='api_states'),
    path('api/cities/<str:country_code>/<str:state_code>/', views.get_cities, name='api_cities'),
]