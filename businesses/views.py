from django.shortcuts import render

# Create your views here.
def business_card_display_demo(request):
    return render(request, 'businesses/business_card_display_demo.html')
