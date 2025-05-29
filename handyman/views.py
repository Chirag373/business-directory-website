from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib import messages
from django.utils.text import slugify
from django.utils import timezone
from django.urls import reverse
from django.core.mail import send_mail
from django.conf import settings
import uuid
import os
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse
from datetime import timedelta
from django.db.models import Q, Prefetch
from django.views.decorators.cache import cache_page
from django.core.cache import cache

from users.models import User, UserType, UserProfile
from core.models import Address, Category
from users.utils import send_login_email
from .models import Handyman, Service, HandymanService, HandymanPromotion, HandymanJob
import json

# Create your views here.
@cache_page(60 * 15)  # Cache this view for 15 minutes
def handyman_main(request):
    """Main handyman page with search functionality"""
    # Check if it's a POST request - if so, we can't use the cached version
    if request.method == 'POST':
        return _handyman_search(request)
        
    # For GET requests, optimize the query with prefetching
    handymen = Handyman.objects.filter(is_active=True).select_related('user').prefetch_related(
        'service_areas',
        'services',
        Prefetch('promotions', queryset=HandymanPromotion.objects.filter(is_active=True))
    )
    
    # Cache services list for 1 hour
    services = cache.get('all_handyman_services')
    if not services:
        services = list(Service.objects.all())
        cache.set('all_handyman_services', services, 60 * 60)
    
    return render(request, 'handyman/handyman_main.html', {
        'handymen': handymen,
        'services': services,
    })

def _handyman_search(request):
    """Private helper function to handle handyman search submissions"""
    state = request.POST.get('state', '')
    county = request.POST.get('county', '')
    city = request.POST.get('city', '')
    service_description = request.POST.get('service_description', '')
    
    # Start with a base optimized query
    query = Handyman.objects.filter(is_active=True).select_related('user').prefetch_related(
        'service_areas',
        'services',
        Prefetch('promotions', queryset=HandymanPromotion.objects.filter(is_active=True))
    )
    
    # Build query filters incrementally
    filters = Q()
    location_filtered = False
    
    # Filter handymen based on location if provided
    if state:
        filters &= Q(service_areas__state__iexact=state)
        location_filtered = True
    if county:
        filters &= Q(service_areas__county__icontains=county)
        location_filtered = True
    if city:
        filters &= Q(service_areas__city__iexact=city)
        location_filtered = True
        
    # Apply location filters if any were set
    if location_filtered:
        query = query.filter(filters)
    
    # Filter by service description if provided
    if service_description:
        # Use Q objects to optimize OR query
        service_filters = Q(detailed_services_description__icontains=service_description) | \
                        Q(services__name__icontains=service_description)
        query = query.filter(service_filters)
    
    # Always call distinct() to eliminate duplicate results
    handymen = query.distinct()
    
    # Get services (from cache if available)
    services = cache.get('all_handyman_services')
    if not services:
        services = list(Service.objects.all())
        cache.set('all_handyman_services', services, 60 * 60)
    
    return render(request, 'handyman/handyman_main.html', {
        'handymen': handymen,
        'services': services,
    })

def signup_handyman(request):
    if request.method == 'POST':
        # Personal Information
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        
        # Business Information
        business_name = request.POST.get('business_name')
        website = request.POST.get('website')
        
        # Contact Information
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        
        # Address fields
        street_number = request.POST.get('address_number')
        street_address = request.POST.get('address')
        street = f"{street_number} {street_address}".strip()
        city = request.POST.get('city')
        state = request.POST.get('state')
        county = request.POST.get('county')
        postal_code = request.POST.get('zip')
        
        # Service Information
        service_description = request.POST.get('service_description')
        service_categories = request.POST.getlist('service_categories')
        discount_description = request.POST.get('discount_description')
        
        # Promotional Offer
        run_promotion = request.POST.get('run_promotion')
        discount_percentage = request.POST.get('discount_percentage')
        promo_start_date = request.POST.get('start_date')
        promo_end_date = request.POST.get('end_date')
        
        # Validate required fields
        if not all([first_name, last_name, email, phone, business_name, 
                  street, city, state, postal_code, service_description]):
            messages.error(request, 'Please fill in all required fields.')
            return render(request, 'handyman/handyman_signup.html')
        
        # Check if user already exists
        if User.objects.filter(email=email).exists():
            messages.error(request, 'A user with that email already exists.')
            return render(request, 'handyman/handyman_signup.html')
        
        try:
            # Create address independently
            print("Creating address...")
            address = Address.objects.create(
                street=street,
                city=city,
                state=state,
                postal_code=postal_code,
            )
            print(f"Address created: {address.id}")
            
            # Generate a random temporary password
            temp_password = uuid.uuid4().hex[:8]
            
            # Create user independently
            print("Creating user...")
            user = User.objects.create_user(
                email=email,
                first_name=first_name,
                last_name=last_name,
                phone_number=phone,
                address=address,
                business_name=business_name,
                website=website,
                user_type=UserType.HANDYMAN,
                service_description=service_description,
                password=temp_password
            )
            print(f"User created: {user.id}")
            
            # Handle file uploads
            if 'card_front' in request.FILES:
                card_front = request.FILES.get('card_front')
                if card_front:
                    user.business_card_front = card_front
                    user.save()
            
            if 'card_back' in request.FILES:
                card_back = request.FILES.get('card_back')
                if card_back:
                    user.business_card_back = card_back
                    user.save()
            
            blank_back = request.POST.get('blank_back') == 'on'
            if blank_back:
                user.has_blank_card_back = blank_back
                user.save()
            
            # Create user profile
            UserProfile.objects.create(user=user)
            
            # Create handyman profile independently, without ManyToMany fields
            print("Creating handyman profile...")
            handyman = Handyman(
                user=user,
                business_name=business_name,
                bio=service_description or f"Handyman services provided by {business_name}",
                detailed_services_description=service_description or "",
                experience_years=0,
                offers_promotions=run_promotion == 'on'
            )
            # Save handyman object first before adding any ManyToMany relationships
            handyman.save()
            print(f"Handyman created: {handyman.id}")
            
            # AFTER handyman is saved, we can add the service areas
            try:
                print("Adding service area...")
                handyman.service_areas.add(address)
                print("Service area added successfully")
            except Exception as e:
                print(f"Warning: Could not add service area: {str(e)}")
                # Continue anyway - we don't want to fail registration for this
            
            # Add service categories
            added_services = 0
            print(f"Adding service categories: {service_categories}")
            for category_name in service_categories:
                if not category_name:
                    continue
                
                try:    
                    print(f"Creating service: {category_name}")
                    service, created = Service.objects.get_or_create(
                        name=category_name,
                        defaults={'description': f'Services related to {category_name}', 'slug': slugify(category_name)}
                    )
                    print(f"Service created/found: {service.id}, Created: {created}")
                    
                    print("Creating handyman service relationship...")
                    HandymanService.objects.create(
                        handyman=handyman,
                        service=service
                    )
                    added_services += 1
                    print("HandymanService created successfully")
                except Exception as e:
                    print(f"Warning: Could not add service {category_name}: {str(e)}")
                    # Continue with other services
            
            if added_services == 0 and service_categories:
                messages.warning(request, "Could not add any services to your profile. You can add them later from your dashboard.")
            
            # Create promotion if selected
            if run_promotion == 'on' and discount_percentage:
                try:
                    print(f"Creating promotion with discount: {discount_percentage}%")
                    discount_percent = int(discount_percentage)
                    
                    # Ensure discount percent is in valid choices
                    valid_discount_choices = [3, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85, 90, 100]
                    if discount_percent not in valid_discount_choices:
                        # Use nearest valid discount
                        discount_percent = min(valid_discount_choices, key=lambda x: abs(x - discount_percent))
                        print(f"Invalid discount percentage provided, using nearest valid value: {discount_percent}%")
                    
                    # Generate a unique promo code
                    promo_code = f"PROMO-{uuid.uuid4().hex[:8].upper()}"
                    print(f"Promotion code generated: {promo_code}")
                    
                    # Create promotion with proper dates
                    start_date = promo_start_date or timezone.now().date()
                    end_date = promo_end_date or (timezone.now().date() + timezone.timedelta(days=30))
                    
                    if isinstance(start_date, str):
                        start_date = timezone.datetime.strptime(start_date, "%Y-%m-%d").date()
                    
                    if isinstance(end_date, str):
                        end_date = timezone.datetime.strptime(end_date, "%Y-%m-%d").date()
                    
                    print(f"Promotion period: {start_date} to {end_date}")
                    
                    # Make sure we have at least one service to associate with the promotion
                    service_for_promo = None
                    if added_services > 0:
                        first_category = service_categories[0]
                        print(f"Using category for promotion: {first_category}")
                        service_for_promo, _ = Service.objects.get_or_create(
                            name=first_category,
                            defaults={'description': f'Services related to {first_category}', 
                                    'slug': slugify(first_category)}
                        )
                        print(f"Service for promotion: {service_for_promo.id}")
                        
                        # Only create the promotion if we have a valid service
                        if service_for_promo:
                            print("Creating promotion...")
                            try:
                                HandymanPromotion.objects.create(
                                    handyman=handyman,
                                    service=service_for_promo,  # Add the service to the promotion
                                    description=discount_description or f"Special offer: {discount_percent}% off services",
                                    discount_percentage=discount_percent,
                                    code=promo_code,
                                    start_date=start_date,
                                    end_date=end_date,
                                    is_active=True
                                )
                                print("Promotion created successfully")
                            except Exception as e:
                                print(f"Error creating promotion: {str(e)}")
                                # Don't fail the whole signup if just the promotion fails
                                messages.warning(request, f'Your account was created, but there was an error setting up the promotion: {str(e)}')
                        else:
                            print("No service for promotion, skipping creation")
                            messages.warning(request, 'Your account was created, but the promotion could not be added because no service category was selected.')
                    else:
                        messages.warning(request, 'Your account was created, but the promotion could not be added because no services were available.')
                except Exception as e:
                    print(f"Error with promotion setup: {str(e)}")
                    # Don't fail the whole signup if just the promotion fails
                    messages.warning(request, f'Your account was created, but there was an error setting up the promotion: {str(e)}')
            
            # Send login email with magic link
            print("Sending login email...")
            send_login_email(request, user, "Handyman")
            print("Login email sent")
            
            # Add success message
            messages.success(request, 'Your handyman account has been created successfully! Please check your email (or console for now) to get your login link.')
            
            print("Registration complete, redirecting to check_email page")
            # Redirect to a "check your email" page
            return render(request, 'users/check_email.html', {'email': email})
            
        except Exception as e:
            import traceback
            print(f"ERROR DURING REGISTRATION: {str(e)}")
            print("TRACEBACK:")
            traceback.print_exc()
            messages.error(request, f'An error occurred during registration: {str(e)}')
            return render(request, 'handyman/handyman_signup.html')
    
    # For GET requests
    return render(request, 'handyman/handyman_signup.html')

@login_required
def dashboard(request):
    """View function for the handyman dashboard."""
    user = request.user
    
    # If user's token is valid, clear it as they're now logged in
    # This ensures tokens are truly one-time use
    if user.login_token and user.is_token_valid():
        user.clear_token()
        
    # Verify this user is supposed to be a handyman
    if user.user_type != UserType.HANDYMAN:
        messages.error(request, "Your account is not registered as a handyman. Please contact support.")
        return redirect('login')
    
    # Early cache check for frequently accessed data
    cache_key = f'handyman_dashboard_{user.id}'
    cached_data = cache.get(cache_key)
    if cached_data:
        return render(request, 'handyman/handyman_dashboard.html', cached_data)
        
    # Get the handyman profile
    try:
        # Use select_related to get user data in the same query
        handyman = Handyman.objects.select_related('user').get(user=user)
    except Handyman.DoesNotExist:
        # Instead of trying to create a profile automatically, redirect to a setup page
        messages.info(request, "Please complete your handyman profile setup.")
        return redirect('handyman_setup')
    
    # Get today's date for calculations
    today = timezone.now().date()
    
    # Calculate dashboard stats using optimized queries
    # 1. Get active promotions with a single query
    active_promotions = HandymanPromotion.objects.filter(
        handyman=handyman,
        is_active=True,
        start_date__lte=today,
        end_date__gte=today
    ).select_related('service').order_by('-created_at')
    
    # 2. Calculate profile views (placeholder for now)
    profile_views = 0  # This would be implemented with a tracking system
    
    # 3. Calculate promotional matches (placeholder)
    promotional_matches = 0
    
    # 4. Calculate notifications sent (placeholder)
    notifications_sent = 0
    
    # 5. Calculate website clicks (placeholder) 
    website_clicks = 0
    
    # Get the handyman's services with a more efficient query
    handyman_services = HandymanService.objects.filter(
        handyman=handyman
    ).select_related('service')
    
    # Format services for the template - Reuse this data for multiple sections
    services_data = []
    for hs in handyman_services:
        service = hs.service
        services_data.append({
            'id': service.id,
            'name': service.name,
            'hourly_rate': hs.hourly_rate,
            'flat_rate': hs.flat_rate,
        })
    
    # Get promotions in a single optimized query
    all_promotions = HandymanPromotion.objects.filter(
        handyman=handyman
    ).select_related('service').order_by('-created_at')
    
    # Format promotions data
    promotions_data = []
    for promo in all_promotions:
        service_name = promo.service.name if promo.service else "General Service"
        promotions_data.append({
            'id': promo.id,
            'discount': promo.discount_percentage,
            'service': service_name, 
            'code': promo.code,
            'start_date': promo.start_date,
            'end_date': promo.end_date,
            'is_active': promo.is_active and promo.start_date <= today and promo.end_date >= today,
        })
    
    # Get recent jobs with status info
    recent_jobs = HandymanJob.objects.filter(
        handyman=handyman
    ).select_related('service', 'client', 'address').order_by('-created_at')[:5]
    
    # Format jobs data
    jobs_data = []
    for job in recent_jobs:
        jobs_data.append({
            'id': job.id,
            'client': job.client.get_full_name() or job.client.email,
            'service': job.service.name,
            'status': job.get_status_display(),
            'date': job.scheduled_date,
            'raw_status': job.status,
        })
    
    # Process address data
    address = user.address
    address_number = ""
    address_street = ""
    
    if address and address.street:
        # Split address into number and street
        address_parts = address.street.split(' ', 1)
        if len(address_parts) > 1:
            address_number = address_parts[0]
            address_street = address_parts[1]
        else:
            address_street = address.street
    
    # Get service categories efficiently 
    categories = list(Category.objects.filter(is_active=True).order_by('name'))
    
    # Format categories data
    formatted_categories = []
    for category in categories:
        formatted_categories.append({
            'id': category.id,
            'name': category.name,
        })
    
    # Get all services - use cached data if available
    services = cache.get('all_handyman_services')
    if not services:
        services = list(Service.objects.all())
        cache.set('all_handyman_services', services, 60 * 60)
    
    # Get US states from cached data
    states = cache.get('us_states')
    if not states:
        states = [
            "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
            "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
            "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
            "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
            "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY"
        ]
        cache.set('us_states', states, 60 * 60 * 24)  # Cache for 24 hours
    
    context = {
        'handyman': handyman,
        'profile_views': profile_views,
        'promotional_matches': promotional_matches,
        'notifications_sent': notifications_sent,
        'website_clicks': website_clicks,
        'services': services_data,
        'promotions': promotions_data,
        'jobs': jobs_data,
        'address_number': address_number,
        'address_street': address_street,
        'all_categories': formatted_categories,
        'all_services': services,
        'states': states,
        'has_active_promotion': active_promotions.exists(),
        'active_promotion': active_promotions.first() if active_promotions.exists() else None,
        'service_description': handyman.detailed_services_description or handyman.bio
    }
    
    # Cache the dashboard data for 5 minutes to reduce database load
    cache.set(cache_key, context, 60 * 5)
    
    return render(request, 'handyman/handyman_dashboard.html', context)

@login_required
def profile_tab(request):
    """View function for the profile tab in handyman dashboard."""
    user = request.user
    
    # Check if we have cached data
    cache_key = f'handyman_profile_tab_{user.id}'
    cached_content = cache.get(cache_key)
    if cached_content:
        return cached_content
    
    try:
        # Use select_related for more efficient query
        handyman = Handyman.objects.select_related('user', 'user__address').get(user=user)
    except Handyman.DoesNotExist:
        return redirect('handyman_dashboard')
    
    context = {
        'handyman': handyman,
        'address': user.address,
    }
    
    response = render(request, 'handyman/handyman_dashboard_profile.html', context)
    
    # Cache the response for 10 minutes
    cache.set(cache_key, response, 60 * 10)
    
    return response

@login_required
def promotions_tab(request):
    """View function for the promotions tab in handyman dashboard."""
    user = request.user
    today = timezone.now().date()
    
    try:
        handyman = Handyman.objects.select_related('user').get(user=user)
    except Handyman.DoesNotExist:
        return redirect('handyman_dashboard')
    
    # Get all promotions in a single optimized query
    all_promotions = HandymanPromotion.objects.filter(
        handyman=handyman
    ).select_related('service').order_by('-created_at')
    
    # Get active promotions
    active_promotions = [
        promo for promo in all_promotions 
        if promo.is_active and promo.start_date <= today and promo.end_date >= today
    ]
    
    # Get all available services efficiently
    services = cache.get('all_handyman_services')
    if not services:
        services = list(Service.objects.all())
        cache.set('all_handyman_services', services, 60 * 60)
    
    # Get discount choices from the model
    discount_choices = HandymanPromotion._meta.get_field('discount_percentage').choices
    
    context = {
        'handyman': handyman,
        'promotions': all_promotions,
        'active_promotions': active_promotions,
        'services': services,
        'discount_choices': [choice[0] for choice in discount_choices],
    }
    
    return render(request, 'handyman/handyman_dashboard_promotions.html', context)

@login_required
def services_tab(request):
    """View function for the services tab in handyman dashboard."""
    user = request.user
    
    try:
        handyman = Handyman.objects.select_related('user').get(user=user)
    except Handyman.DoesNotExist:
        return redirect('handyman_dashboard')
    
    # Get all services offered by this handyman efficiently
    handyman_services = HandymanService.objects.filter(
        handyman=handyman
    ).select_related('service')
    
    # Get all available services from cache
    all_services = cache.get('all_handyman_services')
    if not all_services:
        all_services = list(Service.objects.all())
        cache.set('all_handyman_services', all_services, 60 * 60)
    
    # Get service categories efficiently
    categories = list(Category.objects.filter(is_active=True).order_by('name'))
    
    context = {
        'handyman': handyman,
        'handyman_services': handyman_services,
        'all_services': all_services,
        'categories': categories,
        'service_description': handyman.detailed_services_description or handyman.bio
    }
    
    return render(request, 'handyman/handyman_dashboard_services.html', context)

@login_required
def jobs_tab(request):
    """View function for the jobs tab in handyman dashboard."""
    user = request.user
    
    try:
        handyman = Handyman.objects.select_related('user').get(user=user)
    except Handyman.DoesNotExist:
        return redirect('handyman_dashboard')
    
    # Get jobs with all necessary related objects in a single query
    jobs = HandymanJob.objects.filter(
        handyman=handyman
    ).select_related(
        'service', 
        'client',
        'address',
        'promotion_applied'
    ).order_by('-created_at')
    
    context = {
        'handyman': handyman,
        'jobs': jobs,
    }
    
    return render(request, 'handyman/handyman_dashboard_jobs.html', context)

@login_required
@transaction.atomic
def update_profile(request):
    """Update the handyman's profile information."""
    user = request.user
    
    # Verify this user is a handyman
    if user.user_type != UserType.HANDYMAN:
        messages.error(request, "Your account is not registered as a handyman.")
        return redirect('login')
    
    if request.method == 'POST':
        try:
            # Get both user and handyman in a single transaction to ensure consistency
            with transaction.atomic():
                handyman = Handyman.objects.select_related('user').get(user=user)
                
                # Update basic information
                user.first_name = request.POST.get('first_name', user.first_name)
                user.last_name = request.POST.get('last_name', user.last_name)
                user.phone_number = request.POST.get('phone_number', user.phone_number)
                user.website = request.POST.get('website', user.website)
                handyman.business_name = request.POST.get('business_name', handyman.business_name)
                
                # Process experience years
                experience = request.POST.get('experience_years')
                if experience and experience.isdigit():
                    handyman.experience_years = int(experience)
                
                # Process license information
                license_number = request.POST.get('license_number')
                if license_number:
                    handyman.license_number = license_number
                    handyman.is_licensed = True
                
                # Handle insurance checkbox
                handyman.is_insured = request.POST.get('is_insured') == 'on'
                
                # Update bio if provided
                bio = request.POST.get('bio')
                if bio:
                    handyman.bio = bio
                
                # Handle address updates efficiently
                address_number = request.POST.get('address_number', '')
                address_street = request.POST.get('address_street', '')
                city = request.POST.get('city', '')
                state = request.POST.get('state', '')
                postal_code = request.POST.get('zip', '')
                
                if address_number or address_street or city or state or postal_code:
                    # Combine street number and name
                    full_street = f"{address_number} {address_street}".strip()
                    
                    # Get or create address with all fields at once
                    if user.address:
                        # Update existing address
                        address = user.address
                        if full_street:
                            address.street = full_street
                        if city:
                            address.city = city
                        if state:
                            address.state = state
                        if postal_code:
                            address.postal_code = postal_code
                        address.save()
                    else:
                        # Create new address
                        address = Address.objects.create(
                            street=full_street,
                            city=city,
                            state=state,
                            postal_code=postal_code
                        )
                        user.address = address
                
                # Save all changes at once
                user.save()
                handyman.save()
                
                # Clear any cached data for this user
                cache_keys = [
                    f'handyman_dashboard_{user.id}',
                    f'handyman_profile_tab_{user.id}'
                ]
                for key in cache_keys:
                    cache.delete(key)
                
                messages.success(request, "Your profile has been updated successfully!")
                
        except Exception as e:
            messages.error(request, f"Could not update your profile: {str(e)}")
        
        return redirect('handyman_dashboard_profile')
    
    # GET requests shouldn't reach here, redirect to profile tab
    return redirect('handyman_dashboard_profile')

@login_required
def update_service_description(request):
    """Update handyman service description."""
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        user = request.user
        
        try:
            handyman = Handyman.objects.get(user=user)
        except Handyman.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Handyman profile not found'})
        
        # Get new description
        service_description = request.POST.get('service_description')
        
        if service_description:
            handyman.detailed_services_description = service_description
            handyman.bio = service_description
            handyman.save()
            
            # Also update in user model if it exists there
            user.service_description = service_description
            user.save()
            
            return JsonResponse({'status': 'success', 'message': 'Service description updated successfully'})
        
        return JsonResponse({'status': 'error', 'message': 'Service description cannot be empty'})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request'})

@login_required
def add_service(request):
    """Add a new service for the handyman."""
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        user = request.user
        
        try:
            handyman = Handyman.objects.get(user=user)
        except Handyman.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Handyman profile not found'})
        
        # Get form data
        service_id = request.POST.get('service_id')
        hourly_rate = request.POST.get('hourly_rate')
        flat_rate = request.POST.get('flat_rate')
        
        # Validate data
        if not service_id:
            return JsonResponse({'status': 'error', 'message': 'Service selection is required'})
        
        try:
            service = Service.objects.get(id=service_id)
        except Service.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Selected service does not exist'})
        
        # Check if this service is already added
        if HandymanService.objects.filter(handyman=handyman, service=service).exists():
            return JsonResponse({'status': 'error', 'message': 'You already offer this service'})
        
        # Create new handyman service
        handyman_service = HandymanService.objects.create(
            handyman=handyman,
            service=service,
            hourly_rate=hourly_rate if hourly_rate else None,
            flat_rate=flat_rate if flat_rate else None
        )
        
        return JsonResponse({
            'status': 'success',
            'message': 'Service added successfully',
            'service': {
                'id': handyman_service.id,
                'name': service.name,
                'hourly_rate': handyman_service.hourly_rate,
                'flat_rate': handyman_service.flat_rate
            }
        })
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request'})

@login_required
@transaction.atomic
def create_promotion(request):
    """Create a new promotion for the handyman's services."""
    user = request.user
    
    # Verify this user is a handyman
    if user.user_type != UserType.HANDYMAN:
        messages.error(request, "Your account is not registered as a handyman.")
        return redirect('login')
    
    # Only accept POST requests
    if request.method != 'POST':
        return redirect('handyman_dashboard_promotions')
    
    # Check if request is AJAX
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    
    try:
        # Get handyman profile
        handyman = Handyman.objects.get(user=user)
        
        # Extract form data
        service_id = request.POST.get('service')
        discount_percentage = request.POST.get('discount_percentage')
        promotion_description = request.POST.get('description')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        
        # Validate required fields
        if not all([discount_percentage, promotion_description, start_date, end_date]):
            error_msg = "Please fill in all required fields."
            if is_ajax:
                return JsonResponse({'status': 'error', 'message': error_msg})
            messages.error(request, error_msg)
            return redirect('handyman_dashboard_promotions')
        
        # Convert dates to proper format
        try:
            start_date = timezone.datetime.strptime(start_date, "%Y-%m-%d").date()
            end_date = timezone.datetime.strptime(end_date, "%Y-%m-%d").date()
            
            # Validate date range
            today = timezone.now().date()
            if start_date < today:
                error_msg = "Start date cannot be in the past."
                if is_ajax:
                    return JsonResponse({'status': 'error', 'message': error_msg})
                messages.error(request, error_msg)
                return redirect('handyman_dashboard_promotions')
            
            if end_date <= start_date:
                error_msg = "End date must be after start date."
                if is_ajax:
                    return JsonResponse({'status': 'error', 'message': error_msg})
                messages.error(request, error_msg)
                return redirect('handyman_dashboard_promotions')
        except ValueError:
            error_msg = "Invalid date format."
            if is_ajax:
                return JsonResponse({'status': 'error', 'message': error_msg})
            messages.error(request, error_msg)
            return redirect('handyman_dashboard_promotions')
        
        # Get service if provided
        service = None
        if service_id:
            try:
                service = Service.objects.get(id=service_id)
            except Service.DoesNotExist:
                # Non-critical error, can continue without service
                pass
        
        # Generate unique promo code
        promo_code = f"{handyman.business_name[:5] or 'PROMO'}-{uuid.uuid4().hex[:6].upper()}"
        
        # Create the promotion
        with transaction.atomic():
            # Mark handyman as offering promotions
            handyman.offers_promotions = True
            handyman.save(update_fields=['offers_promotions'])
            
            # Create the promotion
            promotion = HandymanPromotion.objects.create(
                handyman=handyman,
                service=service,
                description=promotion_description,
                discount_percentage=int(discount_percentage),
                code=promo_code,
                start_date=start_date,
                end_date=end_date,
                is_active=True
            )
            
            # Clear any cached data related to promotions
            cache_keys = [
                f'handyman_dashboard_{user.id}',
                'all_handyman_services'  # This might be overkill but ensures consistency
            ]
            for key in cache_keys:
                cache.delete(key)
            
        success_msg = "Promotion created successfully!"
        if is_ajax:
            return JsonResponse({
                'status': 'success',
                'message': success_msg,
                'promotion': {
                    'id': promotion.id,
                    'code': promotion.code,
                    'discount': promotion.discount_percentage,
                    'start_date': promotion.start_date.strftime('%Y-%m-%d'),
                    'end_date': promotion.end_date.strftime('%Y-%m-%d'),
                    'service': service.name if service else 'All Services'
                }
            })
        
        messages.success(request, success_msg)
    
    except Exception as e:
        error_msg = f"Error creating promotion: {str(e)}"
        if is_ajax:
            return JsonResponse({'status': 'error', 'message': error_msg})
        messages.error(request, error_msg)
    
    return redirect('handyman_dashboard_promotions')

@login_required
def deactivate_promotion(request, promotion_id):
    """Deactivate a promotion."""
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        user = request.user
        
        try:
            handyman = Handyman.objects.get(user=user)
            promotion = HandymanPromotion.objects.get(id=promotion_id, handyman=handyman)
        except (Handyman.DoesNotExist, HandymanPromotion.DoesNotExist):
            return JsonResponse({'status': 'error', 'message': 'Promotion not found'})
        
        promotion.is_active = False
        promotion.save()
        
        return JsonResponse({'status': 'success', 'message': 'Promotion deactivated successfully'})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request'})

@login_required
def update_job_status(request, job_id):
    """Update the status of a job."""
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        user = request.user
        new_status = request.POST.get('status')
        
        if not new_status:
            return JsonResponse({'status': 'error', 'message': 'New status is required'})
        
        try:
            handyman = Handyman.objects.get(user=user)
            job = HandymanJob.objects.get(id=job_id, handyman=handyman)
        except (Handyman.DoesNotExist, HandymanJob.DoesNotExist):
            return JsonResponse({'status': 'error', 'message': 'Job not found'})
        
        # Validate status transition
        valid_statuses = ['pending', 'accepted', 'in_progress', 'completed', 'cancelled']
        if new_status not in valid_statuses:
            return JsonResponse({'status': 'error', 'message': 'Invalid status'})
        
        # Update job status
        job.status = new_status
        if new_status == 'completed':
            job.completed_at = timezone.now()
        job.save()
        
        return JsonResponse({'status': 'success', 'message': f'Job status updated to {new_status}'})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request'})

@login_required
def handyman_setup(request):
    """View for setting up a handyman profile for existing users."""
    user = request.user
    
    # Ensure the user doesn't already have a handyman profile
    try:
        handyman = Handyman.objects.get(user=user)
        # If profile exists, redirect to dashboard
        messages.info(request, "Your handyman profile is already set up.")
        return redirect('handyman_dashboard')
    except Handyman.DoesNotExist:
        pass
    
    if request.method == 'POST':
        business_name = request.POST.get('business_name') or f"{user.first_name}'s Services"
        bio = request.POST.get('bio') or user.service_description or "Handyman services"
        
        print(f"DEBUG: Creating handyman for user ID: {user.id}")
        print(f"DEBUG: User type: {user.user_type}")
        print(f"DEBUG: Business name: {business_name}")
        
        try:
            # Create a minimal handyman record with only required fields
            print("DEBUG: Creating handyman with minimal fields")
            handyman = Handyman()
            handyman.user = user
            handyman.business_name = business_name 
            handyman.bio = bio
            # Skip all other fields for now - we can add them later
            
            # Save the record
            print("DEBUG: Calling handyman.save()")
            handyman.save()
            print(f"DEBUG: Handyman saved successfully with ID {handyman.id}")
            
            messages.success(request, "Your handyman profile has been created successfully!")
            return redirect('handyman_dashboard')
            
        except Exception as e:
            import traceback
            print(f"ERROR creating handyman profile: {str(e)}")
            print("TRACEBACK:")
            traceback.print_exc()
            
            # Check Django model fields
            print("DEBUG: Checking Handyman model fields")
            for field in Handyman._meta.fields:
                print(f"Field: {field.name}, Required: {not field.null and not field.blank}, Type: {field.get_internal_type()}")
            
            messages.error(request, f"There was an error setting up your profile: {str(e)}")
    
    # For GET requests, prepare any prefilled data
    context = {
        'business_name': user.business_name or f"{user.first_name}'s Services",
        'bio': user.service_description or "",
        'service_description': user.service_description or ""
    }
    
    return render(request, 'handyman/handyman_setup.html', context)

@login_required
def update_business_card(request):
    """Update the handyman's business card (front and back)."""
    user = request.user
    
    # Verify this user is supposed to be a handyman
    if user.user_type != UserType.HANDYMAN:
        messages.error(request, "Your account is not registered as a handyman. Please contact support.")
        return redirect('login')
    
    if request.method == 'POST':
        # Handle front side of business card
        if 'card_front' in request.FILES:
            card_front = request.FILES.get('card_front')
            if card_front:
                user.business_card_front = card_front
                user.save()
                messages.success(request, "Business card front side has been updated successfully.")
        
        # Handle back side of business card
        if 'card_back' in request.FILES:
            card_back = request.FILES.get('card_back')
            if card_back:
                user.business_card_back = card_back
                user.save()
                messages.success(request, "Business card back side has been updated successfully.")
        
        # Handle blank back checkbox
        blank_back = request.POST.get('blank_back') == 'on'
        user.has_blank_card_back = blank_back
        user.save()
        
        # If no specific success message was added, add a general one
        if not any(m.level == messages.SUCCESS for m in messages.get_messages(request)):
            messages.success(request, "Business card information has been updated successfully.")
        
        # Redirect back to the dashboard business card section
        return redirect('handyman_dashboard_profile')
    
    # For GET requests, this should not be called directly
    return redirect('handyman_dashboard_profile')

@login_required
def update_services(request):
    """Update the handyman's offered services."""
    user = request.user
    
    # Verify this user is supposed to be a handyman
    if user.user_type != UserType.HANDYMAN:
        messages.error(request, "Your account is not registered as a handyman. Please contact support.")
        return redirect('login')
    
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # Get the handyman profile
        try:
            handyman = Handyman.objects.get(user=user)
        except Handyman.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Handyman profile not found'})
        
        # Get service description and selected categories
        service_description = request.POST.get('service_description')
        service_categories = request.POST.getlist('service_categories')
        
        # Update service description
        if service_description:
            handyman.detailed_services_description = service_description
            handyman.save()
            
            # Also update in user model if it exists there
            user.service_description = service_description
            user.save()
        
        # Handle service categories
        if service_categories:
            # First, remove all existing services
            HandymanService.objects.filter(handyman=handyman).delete()
            
            # Add new services
            added_services = 0
            for category_name in service_categories:
                if not category_name:
                    continue
                
                try:
                    service, created = Service.objects.get_or_create(
                        name=category_name,
                        defaults={'description': f'Services related to {category_name}', 'slug': slugify(category_name)}
                    )
                    
                    HandymanService.objects.create(
                        handyman=handyman,
                        service=service
                    )
                    added_services += 1
                except Exception as e:
                    # Continue with other services
                    pass
            
            return JsonResponse({
                'status': 'success', 
                'message': f'Services updated successfully. Added {added_services} service categories.'
            })
        
        return JsonResponse({'status': 'success', 'message': 'Service information updated successfully'})
    
    # Handle non-AJAX POST requests (fallback)
    elif request.method == 'POST':
        # Process the form data
        service_description = request.POST.get('service_description')
        service_categories = request.POST.getlist('service_categories')
        
        try:
            handyman = Handyman.objects.get(user=user)
            
            # Update service description
            if service_description:
                handyman.detailed_services_description = service_description
                handyman.save()
                
                # Also update in user model if it exists there
                user.service_description = service_description
                user.save()
            
            # Handle service categories
            if service_categories:
                # First, remove all existing services
                HandymanService.objects.filter(handyman=handyman).delete()
                
                # Add new services
                for category_name in service_categories:
                    if not category_name:
                        continue
                    
                    try:
                        service, created = Service.objects.get_or_create(
                            name=category_name,
                            defaults={'description': f'Services related to {category_name}', 'slug': slugify(category_name)}
                        )
                        
                        HandymanService.objects.create(
                            handyman=handyman,
                            service=service
                        )
                    except Exception as e:
                        # Continue with other services
                        pass
            
            messages.success(request, "Services updated successfully")
        except Handyman.DoesNotExist:
            messages.error(request, "Handyman profile not found")
        
        return redirect('handyman_dashboard_services')
    
    # For GET requests, redirect to the services tab
    return redirect('handyman_dashboard_services')

@login_required
def job_requests(request):
    """API endpoint to get handyman job requests for the dashboard."""
    if request.headers.get('X-Requested-With') != 'XMLHttpRequest':
        return redirect('handyman_dashboard')
    
    user = request.user
    
    # Verify this user is supposed to be a handyman
    if user.user_type != UserType.HANDYMAN:
        return JsonResponse({'status': 'error', 'message': 'Access denied'})
        
    # Get the handyman profile
    try:
        handyman = Handyman.objects.get(user=user)
    except Handyman.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Handyman profile not found'})
    
    # Get all jobs for this handyman
    all_jobs = HandymanJob.objects.filter(handyman=handyman).order_by('-created_at')
    
    # Format jobs data
    jobs_data = []
    for job in all_jobs:
        jobs_data.append({
            'id': job.id,
            'client_name': job.client.get_full_name() or job.client.email,
            'service': job.service.name,
            'scheduled_date': job.scheduled_date.strftime('%Y-%m-%d'),
            'scheduled_time': job.scheduled_time.strftime('%H:%M'),
            'status': job.status,
            'address': str(job.address),
            'estimated_hours': job.estimated_hours,
            'completed_at': job.completed_at.strftime('%Y-%m-%d %H:%M') if job.completed_at else None
        })
    
    return JsonResponse({
        'status': 'success',
        'jobs': jobs_data,
        'pending_count': all_jobs.filter(status='pending').count(),
        'active_count': all_jobs.filter(status='in_progress').count(),
        'completed_count': all_jobs.filter(status='completed').count()
    })