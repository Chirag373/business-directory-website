from django.shortcuts import render

# Create your views here.
def signup_consumer(request):
    return render(request, 'consumer_signup.html')