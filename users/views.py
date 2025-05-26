from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate, get_user_model
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.core.mail import send_mail
from django.urls import reverse
from django.conf import settings
from .models import User, ConsumerInterest, UserType, UserProfile
from core.models import Address, Category
from .utils import send_login_email, process_login_token, process_logout
import uuid
import json
from django.utils import timezone

# Create your views here.
def signup(request):
    return render(request, 'users/signup.html')

# consumer signup
def requestor_signup(request):
    if request.method == 'POST':
        # Get form data
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        
        # Address fields
        street_number = request.POST.get('address_number')
        street_name = request.POST.get('street_address')
        street = f"{street_number} {street_name}".strip()
        city = request.POST.get('city')
        state = request.POST.get('state')
        county = request.POST.get('county')
        postal_code = request.POST.get('zip')
        
        
        # Validate required fields
        if not all([first_name, last_name, email, phone, street, city, state, postal_code]):
            messages.error(request, 'Please fill in all required fields.')
            return render(request, 'users/requestor_signup.html')
        
        # Check if user already exists
        if User.objects.filter(email=email).exists():
            messages.error(request, 'A user with that email already exists')
            return render(request, 'users/requestor_signup.html')
        
        try:
            # Create address
            address = Address.objects.create(
                street=street,
                city=city,
                state=state,
                postal_code=postal_code
            )
            
            # Generate a random temporary password
            temp_password = uuid.uuid4().hex[:8]
            
            # Create user
            user = User.objects.create_user(
                email=email,
                first_name=first_name,
                last_name=last_name,
                phone_number=phone,
                address=address,
                user_type=UserType.REQUESTOR,
                password=temp_password
            )
            
            # Handle promotional preferences
            if request.POST.get('promotional_offers'):
                receive_notifications = True
                interests = ConsumerInterest.objects.create(
                    user=user,
                    receive_notifications=receive_notifications
                )
                
                # Add selected categories to interests
                selected_categories = request.POST.getlist('categories')
                if selected_categories:
                    for category_name in selected_categories:
                        category, created = Category.objects.get_or_create(name=category_name, slug=category_name.lower())
                        interests.categories.add(category)
            
            # Send login email with magic link
            send_login_email(request, user, "Consumer")
            
            # Add success message
            messages.success(request, 'Your account has been created successfully! Please check your email (or console for now) to get your login link.')
            
            # Redirect to a "check your email" page
            return render(request, 'users/check_email.html', {'email': email})
        
        except Exception as e:
            messages.error(request, f'An error occurred during registration: {str(e)}')
            return render(request, 'users/requestor_signup.html')
    
    # For GET requests
    return render(request, 'users/requestor_signup.html')

@login_required
def consumer_dashboard(request):
    """
    Main view for the consumer dashboard
    """
    user = request.user
    
    # If user's token is valid, clear it as they're now logged in
    # This ensures tokens are truly one-time use
    if user.login_token and user.is_token_valid():
        user.clear_token()
    
    # Import needed models
    from promotor.models import PromotionalOffer
    from django.utils import timezone
    from datetime import timedelta
    
    # Get today's date for offer calculations
    today = timezone.now().date()
    
    # Calculate dashboard stats
    # 1. Total active offers
    total_offers = PromotionalOffer.objects.filter(
        is_active=True,
        start_date__lte=today,
        end_date__gte=today
    ).count()
    
    # 2. Offers expiring soon (within 7 days)
    expiry_threshold = today + timedelta(days=7)
    expiring_soon = PromotionalOffer.objects.filter(
        is_active=True,
        start_date__lte=today,
        end_date__gte=today,
        end_date__lte=expiry_threshold
    ).count()
    
    # Get user's interests for preferred categories
    try:
        interests = ConsumerInterest.objects.get(user=user)
        # 3. Active offers matching user's preferred categories
        preferred_categories = interests.categories.all()
        if preferred_categories:
            matching_offers = PromotionalOffer.objects.filter(
                is_active=True,
                start_date__lte=today,
                end_date__gte=today,
                categories__in=preferred_categories
            ).distinct().count()
        else:
            matching_offers = 0
        receive_notifications = interests.receive_notifications
    except ConsumerInterest.DoesNotExist:
        interests = None
        preferred_categories = []
        matching_offers = 0
        receive_notifications = True
    
    # Get specific services from user profile
    specific_services = ""
    if hasattr(user, 'profile') and user.profile and user.profile.bio:
        specific_services = user.profile.bio
    
    # Prepare address data
    address_number = ''
    address_street = ''
    
    if user.address:
        # Split street into number and name if possible
        street_parts = user.address.street.split(' ', 1) if user.address.street else ['', '']
        address_number = street_parts[0] if len(street_parts) > 0 else ''
        address_street = street_parts[1] if len(street_parts) > 1 else ''
    
    # Get all available categories for the form
    from core.models import Category
    all_categories = Category.objects.all()
    
    if not all_categories.exists():
        # Create default categories if none exist
        default_categories = [
            {'name': 'Plumbing', 'slug': 'plumbing', 'description': 'Plumbing services'},
            {'name': 'Electrical', 'slug': 'electrical', 'description': 'Electrical services'},
            {'name': 'General', 'slug': 'general', 'description': 'General services'},
            {'name': 'Foundation Repair', 'slug': 'foundation', 'description': 'Foundation repair services'},
            {'name': 'Drywall/Paint', 'slug': 'drywall', 'description': 'Drywall and painting services'},
            {'name': 'Flooring', 'slug': 'flooring', 'description': 'Flooring services'},
            {'name': 'Moving', 'slug': 'moving', 'description': 'Moving services'},
            {'name': 'Gardening', 'slug': 'gardening', 'description': 'Gardening services'},
            {'name': 'Bathroom Renovation', 'slug': 'bathroom', 'description': 'Bathroom renovation services'},
            {'name': 'Kitchen Cabinet/Countertops', 'slug': 'kitchen', 'description': 'Kitchen renovation services'},
            {'name': 'Concrete', 'slug': 'concrete', 'description': 'Concrete services'},
        ]
        for cat in default_categories:
            Category.objects.create(name=cat['name'], slug=cat['slug'], description=cat['description'])
        all_categories = Category.objects.all()
    
    # Format categories for template
    formatted_categories = [
        {'value': category.slug, 'name': category.name} for category in all_categories
    ]
    
    # Create a list of US states
    states = [
        ('AL', 'Alabama'), ('AK', 'Alaska'), ('AZ', 'Arizona'), ('AR', 'Arkansas'),
        ('CA', 'California'), ('CO', 'Colorado'), ('CT', 'Connecticut'), ('DE', 'Delaware'),
        ('FL', 'Florida'), ('GA', 'Georgia'), ('HI', 'Hawaii'), ('ID', 'Idaho'),
        ('IL', 'Illinois'), ('IN', 'Indiana'), ('IA', 'Iowa'), ('KS', 'Kansas'),
        ('KY', 'Kentucky'), ('LA', 'Louisiana'), ('ME', 'Maine'), ('MD', 'Maryland'),
        ('MA', 'Massachusetts'), ('MI', 'Michigan'), ('MN', 'Minnesota'), ('MS', 'Mississippi'),
        ('MO', 'Missouri'), ('MT', 'Montana'), ('NE', 'Nebraska'), ('NV', 'Nevada'),
        ('NH', 'New Hampshire'), ('NJ', 'New Jersey'), ('NM', 'New Mexico'), ('NY', 'New York'),
        ('NC', 'North Carolina'), ('ND', 'North Dakota'), ('OH', 'Ohio'), ('OK', 'Oklahoma'),
        ('OR', 'Oregon'), ('PA', 'Pennsylvania'), ('RI', 'Rhode Island'), ('SC', 'South Carolina'),
        ('SD', 'South Dakota'), ('TN', 'Tennessee'), ('TX', 'Texas'), ('UT', 'Utah'),
        ('VT', 'Vermont'), ('VA', 'Virginia'), ('WA', 'Washington'), ('WV', 'West Virginia'),
        ('WI', 'Wisconsin'), ('WY', 'Wyoming')
    ]
    
    # Fetch active offers for initial display
    try:
        active_offers = PromotionalOffer.objects.filter(
            is_active=True,
            start_date__lte=today,
            end_date__gte=today
        )
        
        # Process offers data for template
        offers_data = []
        for offer in active_offers:
            days_until_expiry = (offer.end_date - today).days
            expiring_soon_flag = days_until_expiry <= 7 and days_until_expiry >= 0
            
            offer_data = {
                'id': offer.id,
                'title': offer.title if hasattr(offer, 'title') else f"{offer.discount_percentage}% Off",
                'description': offer.description,
                'discount_percentage': offer.discount_percentage,
                'code': offer.code,
                'start_date': offer.start_date,
                'end_date': offer.end_date,
                'business_name': offer.business.name if hasattr(offer, 'business') and hasattr(offer.business, 'name') else "Business Name",
                'business_email': offer.business.email if hasattr(offer, 'business') and hasattr(offer.business, 'email') else "",
                'business_phone': offer.business.phone_number if hasattr(offer, 'business') and hasattr(offer.business, 'phone_number') else "",
                'business_address': str(offer.business.address) if hasattr(offer, 'business') and hasattr(offer.business, 'address') else '',
                'categories': [category.name for category in offer.categories.all()],
                'days_until_expiry': days_until_expiry if days_until_expiry >= 0 else 0,
                'expiring_soon': expiring_soon_flag,
                'expired': today > offer.end_date,
                'categories_match_preferences': any(category in preferred_categories for category in offer.categories.all()) if preferred_categories else False
            }
            offers_data.append(offer_data)
    except Exception as e:
        print(f"Error loading offers: {e}")
        offers_data = []
    
    # Default notification settings
    notification_settings = {
        'notification_preference': 'all',
        'min_discount': 10,
        'time_period': 'week',
        'notification_limit': 3,
        'email_format': 'individual',
    }
    
    # Get user's notification settings if available
    if interests:
        notification_settings.update({
            'notification_preference': getattr(interests, 'notification_preference', 'all'),
            'min_discount': getattr(interests, 'min_discount_threshold', 10),
            'time_period': getattr(interests, 'notification_time_period', 'week'),
            'notification_limit': getattr(interests, 'notification_limit', 3),
            'email_format': getattr(interests, 'email_format', 'individual'),
        })
    
    context = {
        'total_offers': total_offers,
        'active_offers': total_offers,
        'expiring_soon': expiring_soon,
        'matching_offers': matching_offers,
        'all_categories': formatted_categories,
        'selected_categories': preferred_categories,
        'specific_services': specific_services,
        'receive_notifications': receive_notifications,
        'address_number': address_number,
        'address_street': address_street,
        'states': states,
        'cities': [],  # Would be populated dynamically
        'offers': offers_data,
        'categories': all_categories,
        'filter_category': 'all',
        'filter_date': 'newest',
        'filter_discount': 'highest',
        'filter_active_only': True,
    }
    
    # Add notification settings to context
    context.update(notification_settings)
    
    return render(request, 'users/consumer_dashboard.html', context)



@login_required
def offers_tab(request):
    """
    View to handle the offers tab when accessed directly.
    This redirects to the consumer dashboard with the offers tab active.
    """
    return redirect('consumer_dashboard')

@login_required
def filter_offers(request):
    """
    AJAX endpoint to filter promotional offers based on criteria
    """
    user = request.user
    
    # Get filter parameters
    category = request.GET.get('category', 'all')
    date_sort = request.GET.get('date', 'newest')
    discount_sort = request.GET.get('discount', 'highest')
    active_only = request.GET.get('active_only', 'true').lower() == 'true'
    search_query = request.GET.get('search', '').strip()
    
    from django.db.models import Q
    from promotor.models import PromotionalOffer
    from django.utils import timezone
    from datetime import timedelta
    
    # Base query
    today = timezone.now().date()
    offers_query = PromotionalOffer.objects.all()
    
    # Active only filter
    if active_only:
        offers_query = offers_query.filter(
            is_active=True,
            start_date__lte=today,
            end_date__gte=today
        )
    
    # Category filter
    if category != 'all':
        offers_query = offers_query.filter(categories__slug=category)
    
    # Search filter
    if search_query:
        offers_query = offers_query.filter(
            Q(code__icontains=search_query) | 
            Q(description__icontains=search_query) | 
            Q(user__business_name__icontains=search_query) |
            Q(categories__name__icontains=search_query) |
            Q(user__email__icontains=search_query)
        )
    
    # Date sorting
    if date_sort == 'newest':
        offers_query = offers_query.order_by('-start_date')
    else:
        offers_query = offers_query.order_by('start_date')
    
    # Discount sorting (applied after date sorting)
    if discount_sort == 'highest':
        offers_query = offers_query.order_by('-discount_percentage', 'id')
    else:
        offers_query = offers_query.order_by('discount_percentage', 'id')
    
    # Make sure results are distinct (in case of multiple filters)
    offers_query = offers_query.distinct()
    
    # Get user's interests for preferred categories matching
    try:
        interests = ConsumerInterest.objects.get(user=user)
        preferred_categories = interests.categories.all()
    except ConsumerInterest.DoesNotExist:
        preferred_categories = []
    
    # Process offers for response
    offers_data = []
    for offer in offers_query:
        days_until_expiry = (offer.end_date - today).days if offer.end_date >= today else 0
        expiring_soon_flag = days_until_expiry <= 7 and days_until_expiry >= 0
        
        offer_data = {
            'id': offer.id,
            'title': getattr(offer, 'title', f"{offer.discount_percentage}% Off"),
            'description': offer.description,
            'discount_percentage': offer.discount_percentage,
            'code': offer.code,
            'start_date': offer.start_date.strftime("%b %d, %Y"),
            'end_date': offer.end_date.strftime("%b %d, %Y"),
            'business_name': offer.user.business_name if offer.user.business_name else "Business Name",
            'business_email': offer.user.email if offer.user.email else "",
            'business_phone': offer.user.phone_number if offer.user.phone_number else "",
            'business_address': str(offer.user.address) if offer.user.address else '',
            'categories': [category.name for category in offer.categories.all()],
            'days_until_expiry': days_until_expiry,
            'expiring_soon': expiring_soon_flag,
            'expired': today > offer.end_date,
            'categories_match_preferences': any(category in preferred_categories for category in offer.categories.all()) if preferred_categories else False
        }
        offers_data.append(offer_data)
    
    # Calculate stats for response
    total_offers = PromotionalOffer.objects.filter(
        is_active=True,
        start_date__lte=today,
        end_date__gte=today
    ).count()
    
    expiry_threshold = today + timedelta(days=7)
    expiring_soon_count = PromotionalOffer.objects.filter(
        is_active=True, 
        start_date__lte=today,
        end_date__gte=today,
        end_date__lte=expiry_threshold
    ).count()
    
    # Prepare response
    response_data = {
        'status': 'success',
        'offers': offers_data,
        'total_offers': total_offers,
        'expiring_soon_count': expiring_soon_count,
        'active_filters': {
            'category': category,
            'date': date_sort,
            'discount': discount_sort,
            'active_only': active_only,
            'search': search_query
        }
    }
    
    return JsonResponse(response_data)

@login_required
def notifications_tab(request):
    """
    Handle notification settings tab
    """
    user = request.user
    
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # Get form data
        notification_preference = request.POST.get('notification_preference', 'all')
        min_discount = int(request.POST.get('min_discount', 10))
        time_period = request.POST.get('time_period', 'week')
        notification_limit = int(request.POST.get('notification_limit', 3))
        email_format = request.POST.get('email_format', 'individual')
        
        # Get or create the user's consumer interest record
        consumer_interest, created = ConsumerInterest.objects.get_or_create(
            user=user
        )
        
        # Update the notification settings
        consumer_interest.notification_preference = notification_preference
        consumer_interest.min_discount_threshold = min_discount
        consumer_interest.notification_time_period = time_period
        consumer_interest.notification_limit = notification_limit
        consumer_interest.email_format = email_format
        consumer_interest.save()
        
        return JsonResponse({
            'status': 'success',
            'message': 'Notification settings updated successfully!'
        })
    
    # For GET requests or non-AJAX POST requests, return current notification settings
    try:
        consumer_interest = ConsumerInterest.objects.get(user=user)
        notification_settings = {
            'notification_preference': consumer_interest.notification_preference,
            'min_discount': consumer_interest.min_discount_threshold,
            'time_period': consumer_interest.notification_time_period,
            'notification_limit': consumer_interest.notification_limit,
            'email_format': consumer_interest.email_format,
            'status': 'success'
        }
    except ConsumerInterest.DoesNotExist:
        notification_settings = {
            'notification_preference': 'all',
            'min_discount': 10,
            'time_period': 'week',
            'notification_limit': 3,
            'email_format': 'individual',
            'status': 'success'
        }
    
    return JsonResponse(notification_settings)

def magic_link_login(request, token):
    """
    Handle login via magic link tokens
    """
    success, redirect_url, error_message = process_login_token(request, token)
    
    if success:
        return redirect(redirect_url)
    else:
        if error_message:
            messages.error(request, error_message)
        return redirect(redirect_url)

def user_logout(request):
    """
    Log the user out and redirect to home
    """
    redirect_url = process_logout(request)
    messages.info(request, 'You have been logged out successfully.')
    return redirect(redirect_url)

def login_view(request):
    """Handle user login"""
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, email=email, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, 'Login successful!')
            
            # Redirect based on user type
            if user.user_type == 'requestor':
                return redirect('consumer_dashboard')
            elif user.user_type == 'handyman':
                return redirect('handyman_dashboard')
            elif user.user_type == 'promoter':
                return redirect('promoter_dashboard')
            else:
                return redirect('consumer_dashboard')
        else:
            messages.error(request, 'Invalid email or password.')
    
    return render(request, 'users/login.html')

def register_view(request):
    """Handle user registration"""
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        user_type = request.POST.get('user_type', 'requestor')
        
        # Validate data
        if password != confirm_password:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'users/signup.html')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email is already registered.')
            return render(request, 'users/signup.html')
        
        # Create user
        user = User.objects.create_user(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            user_type=user_type
        )
        
        # Create user profile
        UserProfile.objects.create(user=user)
        
        # Create consumer interest if user type is requestor
        if user_type == 'requestor':
            ConsumerInterest.objects.create(user=user)
        
        # Log the user in
        login(request, user)
        messages.success(request, 'Registration successful!')
        
        # Redirect based on user type
        if user_type == 'requestor':
            return redirect('consumer_dashboard')
        elif user_type == 'handyman':
            return redirect('handyman_dashboard')
        elif user_type == 'promoter':
            return redirect('promoter_dashboard')
        
    return render(request, 'users/signup.html')

def generate_login_link(request):
    """Generate a magic login link and email it to the user"""
    if request.method == 'POST':
        email = request.POST.get('email')
        
        try:
            user = User.objects.get(email=email)
            token = user.generate_login_token()
            
            # Here you would send an email with the token link
            # For now we'll just show it on the page
            login_url = request.build_absolute_uri(f'/users/verify-token/{token}/')
            messages.info(request, f'Login link generated: {login_url}')
            
        except User.DoesNotExist:
            messages.error(request, 'No account found with this email.')
    
    return render(request, 'users/login_link.html')

def verify_token(request, token):
    """Verify a login token and log the user in"""
    User = get_user_model()
    
    try:
        user = User.objects.get(login_token=token)
        
        if user.is_token_valid():
            # Log the user in
            user.backend = 'django.contrib.auth.backends.ModelBackend'
            login(request, user)
            
            # Clear the token so it can't be used again
            user.clear_token()
            
            messages.success(request, 'Login successful!')
            
            # Redirect based on user type
            if user.user_type == 'requestor':
                return redirect('consumer_dashboard')
            elif user.user_type == 'handyman':
                return redirect('handyman_dashboard')
            elif user.user_type == 'promoter':
                return redirect('promoter_dashboard')
            else:
                return redirect('consumer_dashboard')
        else:
            messages.error(request, 'The login link has expired.')
    except User.DoesNotExist:
        messages.error(request, 'Invalid login link.')
    
    return redirect('login')

@login_required
def provider_dashboard(request):
    """
    Dashboard view for service providers
    """
    # Redirect to the proper handyman dashboard in handyman app
    return redirect('handyman_dashboard')

@login_required
def promoter_dashboard(request):
    """
    Dashboard view for promoters
    """
    return redirect('promotor_dashboard')

@login_required
def user_profile(request):
    """
    Handle user profile updates
    """
    user = request.user
    
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # Get form data
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        address_number = request.POST.get('address_number')
        address_street = request.POST.get('address_street')
        state = request.POST.get('state')
        city = request.POST.get('city')
        zip_code = request.POST.get('zip')
        
        # Update user information
        user.first_name = first_name
        user.last_name = last_name
        user.phone_number = phone
        
        # Only update email if it's different and not already taken
        if email != user.email:
            if User.objects.filter(email=email).exists():
                return JsonResponse({
                    'status': 'error', 
                    'message': 'This email is already registered to another account.'
                })
            user.email = email
        
        # Update or create address
        from core.models import Address
        if user.address:
            address = user.address
            address.street = f"{address_number} {address_street}" if address_number else address_street
            address.city = city
            address.state = state
            address.postal_code = zip_code
            address.save()
        else:
            address = Address.objects.create(
                street=f"{address_number} {address_street}" if address_number else address_street,
                city=city,
                state=state,
                postal_code=zip_code
            )
            user.address = address
        
        # Save user
        user.save()
        
        return JsonResponse({
            'status': 'success',
            'message': 'Profile updated successfully!'
        })
    
    return JsonResponse({
        'status': 'error',
        'message': 'Invalid request'
    })

@login_required
def user_preferences(request):
    """
    Handle user service preferences updates
    """
    user = request.user
    
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # Get form data
        selected_categories = request.POST.getlist('service_category')
        specific_services = request.POST.get('specific_services', '')
        receive_promotions = request.POST.get('receive_promotions', '') == 'on'
        
        # Update or create interests
        from core.models import Category
        interests, created = ConsumerInterest.objects.get_or_create(user=user)
        interests.receive_notifications = receive_promotions
        interests.save()
        
        # Clear previous categories and add new ones
        interests.categories.clear()
        for category_slug in selected_categories:
            try:
                category = Category.objects.get(slug=category_slug)
                interests.categories.add(category)
            except Category.DoesNotExist:
                pass
        
        # Update specific services in user profile
        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.bio = specific_services
        profile.save()
        
        return JsonResponse({
            'status': 'success',
            'message': 'Preferences updated successfully!'
        })
    
    return JsonResponse({
        'status': 'error',
        'message': 'Invalid request'
    })