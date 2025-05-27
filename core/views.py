from django.shortcuts import render
from businesses.models import Business

# Create your views here.
def home(request):
    return render(request, 'core/home.html')

def contact(request):
    return render(request, 'core/contact.html')

def premium(request):
    # Get featured (premium) businesses
    premium_businesses = Business.objects.filter(featured=True)
    return render(request, 'core/premium.html', {'premium_businesses': premium_businesses})

