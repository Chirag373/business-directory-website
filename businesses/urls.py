from django.urls import path
from . import views

urlpatterns = [
    path('card-display-demo/', views.business_card_display_demo, name='business_card_display_demo'),
]