from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate, get_user_model
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import uuid
import json

from .models import User, ConsumerInterest, UserType, UserProfile, ServiceCategory
from core.models import Address, Category
from .utils import send_login_email, process_login_token, process_logout

# Authentication Views
def login_view(request):
    """Handle user login with password or redirect to magic link"""
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, email=email, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, 'Login successful!')
            return redirect(get_user_dashboard_url(user))
        else:
            messages.error(request, 'Invalid email or password.')
    
    return render(request, 'users/login.html')

def register_view(request):
    """Display account type selection page"""
    return render(request, 'users/signup.html')

def generate_login_link(request):
    """Generate and send magic login link"""
    if request.method == 'POST':
        email = request.POST.get('email')
        
        try:
            user = User.objects.get(email=email)
            login_url = send_login_email(request, user)
            messages.info(request, f'Login link generated: {login_url}')
            return render(request, 'users/login_link.html', {'email': email})
        except User.DoesNotExist:
            messages.error(request, 'No account found with this email.')
            return redirect('login')
    
    return redirect('login')

def verify_token(request, token):
    """Verify magic link token and log user in"""
    success, redirect_url, error_message = process_login_token(request, token)
    
    if success:
        messages.success(request, 'Login successful!')
        return redirect(redirect_url)
    else:
        if error_message:
            messages.error(request, error_message)
        return redirect('login')

def magic_link_login(request, token):
    """Alias for verify_token for backward compatibility"""
    return verify_token(request, token)

# Registration Views
def requestor_signup(request):
    """Handle consumer/requestor registration"""
    if request.method == 'POST':
        return process_requestor_registration(request)
    
    return render(request, 'users/requestor_signup.html')

def process_requestor_registration(request):
    """Process consumer registration form submission"""
    # Extract form data
    form_data = extract_registration_data(request)
    
    # Validate form data
    errors = validate_registration_data(form_data)
    if errors:
        for error in errors:
            messages.error(request, error)
        return render(request, 'users/requestor_signup.html')
    
    try:
        # Create user and related objects
        user = create_consumer_user(form_data)
        
        # Handle promotional preferences
        if form_data['promotional_offers']:
            setup_consumer_interests(user, form_data['categories'])
        
        # Send login email
        send_login_email(request, user, "Consumer")
        
        messages.success(request, 'Account created successfully! Check your email for login link.')
        return render(request, 'users/check_email.html', {'email': form_data['email']})
        
    except Exception as e:
        messages.error(request, f'Registration error: {str(e)}')
        return render(request, 'users/requestor_signup.html')

# Dashboard Views
@login_required
def consumer_dashboard(request):
    """Main consumer dashboard view"""
    user = request.user
    
    # Clear token if still valid (ensures one-time use)
    if user.login_token and user.is_token_valid():
        user.clear_token()
    
    # Gather dashboard data
    context = {
        'user': user,
        **get_dashboard_stats(user),
        **get_user_profile_data(user),
        **get_user_preferences_data(user),
        **get_offers_data(user),
        **get_notification_settings(user),
        'states': get_us_states(),
        'all_categories': get_formatted_categories(),
    }
    
    return render(request, 'users/consumer_dashboard.html', context)

@login_required
@require_http_methods(["POST"])
def user_profile(request):
    """Handle profile updates via AJAX"""
    if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'status': 'error', 'message': 'Invalid request'})
    
    user = request.user
    
    try:
        # Update user basic info
        update_user_info(user, request.POST)
        
        # Update or create address
        update_user_address(user, request.POST)
        
        user.save()
        
        return JsonResponse({
            'status': 'success',
            'message': 'Profile updated successfully!'
        })
        
    except ValueError as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        })

@login_required
@require_http_methods(["POST"])
def user_preferences(request):
    """Handle service preferences updates via AJAX"""
    if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'status': 'error', 'message': 'Invalid request'})
    
    user = request.user
    
    try:
        # Update preferences
        update_user_preferences(user, request.POST)
        
        return JsonResponse({
            'status': 'success',
            'message': 'Preferences updated successfully!'
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Error updating preferences: {str(e)}'
        })

@login_required
def filter_offers(request):
    """Filter promotional offers based on criteria"""
    if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return redirect('consumer_dashboard')
    
    # Get filter parameters
    filters = {
        'category': request.GET.get('category', 'all'),
        'date_sort': request.GET.get('date', 'newest'),
        'discount_sort': request.GET.get('discount', 'highest'),
        'active_only': request.GET.get('active_only', 'true').lower() == 'true',
        'search_query': request.GET.get('search', '').strip()
    }
    
    # Get filtered offers
    offers = get_filtered_offers(request.user, filters)
    
    # Get stats
    stats = get_offers_stats()
    
    return JsonResponse({
        'status': 'success',
        'offers': offers,
        'total_offers': stats['total'],
        'expiring_soon_count': stats['expiring_soon'],
        'active_filters': filters
    })

@login_required
def notifications_tab(request):
    """Handle notification settings"""
    user = request.user
    
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            update_notification_settings(user, request.POST)
            return JsonResponse({
                'status': 'success',
                'message': 'Notification settings updated!'
            })
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            })
    
    # GET request - return current settings
    return JsonResponse(get_notification_settings(user))

# Helper Functions
def get_user_dashboard_url(user):
    """Get appropriate dashboard URL based on user type"""
    dashboard_urls = {
        UserType.REQUESTOR: 'consumer_dashboard',
        UserType.HANDYMAN: 'handyman_dashboard',
        UserType.PROMOTER: 'promoter_dashboard'
    }
    return dashboard_urls.get(user.user_type, 'consumer_dashboard')

def extract_registration_data(request):
    """Extract and organize registration form data"""
    return {
        'first_name': request.POST.get('first_name', '').strip(),
        'last_name': request.POST.get('last_name', '').strip(),
        'email': request.POST.get('email', '').strip().lower(),
        'phone': request.POST.get('phone', '').strip(),
        'street_number': request.POST.get('address_number', '').strip(),
        'street_name': request.POST.get('street_address', '').strip(),
        'city': request.POST.get('city', '').strip(),
        'state': request.POST.get('state', '').strip(),
        'county': request.POST.get('county', '').strip(),
        'postal_code': request.POST.get('zip', '').strip(),
        'promotional_offers': request.POST.get('promotional_offers') == 'on',
        'categories': request.POST.getlist('categories')
    }

def validate_registration_data(data):
    """Validate registration form data"""
    errors = []
    
    # Check required fields
    required_fields = ['first_name', 'last_name', 'email', 'phone', 
                      'city', 'state', 'postal_code']
    
    for field in required_fields:
        if not data.get(field):
            errors.append(f'{field.replace("_", " ").title()} is required.')
    
    # Check if street address is provided
    if not data['street_number'] and not data['street_name']:
        errors.append('Street address is required.')
    
    # Check email uniqueness
    if data['email'] and User.objects.filter(email=data['email']).exists():
        errors.append('An account with this email already exists.')
    
    return errors

def create_consumer_user(data):
    """Create a new consumer user with address"""
    # Create address
    street = f"{data['street_number']} {data['street_name']}".strip()
    address = Address.objects.create(
        street=street,
        city=data['city'],
        state=data['state'],
        postal_code=data['postal_code']
    )
    
    # Create user with temporary password
    temp_password = uuid.uuid4().hex[:8]
    user = User.objects.create_user(
        email=data['email'],
        first_name=data['first_name'],
        last_name=data['last_name'],
        phone_number=data['phone'],
        address=address,
        user_type=UserType.REQUESTOR,
        password=temp_password
    )
    
    return user

def setup_consumer_interests(user, selected_categories):
    """Set up consumer interests and categories"""
    interests = ConsumerInterest.objects.create(
        user=user,
        receive_notifications=True
    )
    
    # Add selected categories
    for category_name in selected_categories:
        category, _ = Category.objects.get_or_create(
            name=category_name.title(),
            slug=category_name.lower().replace(' ', '-')
        )
        interests.categories.add(category)
    
    return interests

def get_dashboard_stats(user):
    """Get dashboard statistics"""
    from promotor.models import PromotionalOffer
    today = timezone.now().date()
    
    # Active offers count
    active_offers = PromotionalOffer.objects.filter(
        is_active=True,
        start_date__lte=today,
        end_date__gte=today
    )
    
    # Expiring soon (within 7 days)
    expiry_threshold = today + timedelta(days=7)
    expiring_soon = active_offers.filter(end_date__lte=expiry_threshold).count()
    
    # Matching preferences
    try:
        interests = ConsumerInterest.objects.get(user=user)
        preferred_categories = interests.categories.all()
        matching_offers = active_offers.filter(
            categories__in=preferred_categories
        ).distinct().count() if preferred_categories else 0
    except ConsumerInterest.DoesNotExist:
        matching_offers = 0
    
    return {
        'total_offers': active_offers.count(),
        'active_offers': active_offers.count(),
        'expiring_soon': expiring_soon,
        'matching_offers': matching_offers
    }

def get_user_profile_data(user):
    """Get user profile data for dashboard"""
    address_number = ''
    address_street = ''
    
    if user.address and user.address.street:
        parts = user.address.street.split(' ', 1)
        address_number = parts[0] if len(parts) > 0 else ''
        address_street = parts[1] if len(parts) > 1 else ''
    
    return {
        'address_number': address_number,
        'address_street': address_street
    }

def get_user_preferences_data(user):
    """Get user service preferences"""
    try:
        interests = ConsumerInterest.objects.get(user=user)
        selected_categories = list(interests.categories.all())
        receive_notifications = interests.receive_notifications
        
        # Get specific services from profile
        specific_services = ""
        if hasattr(user, 'profile') and user.profile:
            specific_services = user.profile.bio or ""
            
    except ConsumerInterest.DoesNotExist:
        selected_categories = []
        receive_notifications = True
        specific_services = ""
    
    return {
        'selected_categories': selected_categories,
        'receive_notifications': receive_notifications,
        'specific_services': specific_services
    }

def get_offers_data(user, limit=None):
    """Get promotional offers data"""
    from promotor.models import PromotionalOffer
    today = timezone.now().date()
    
    offers_query = PromotionalOffer.objects.filter(
        is_active=True,
        start_date__lte=today,
        end_date__gte=today
    ).order_by('-discount_percentage')
    
    if limit:
        offers_query = offers_query[:limit]
    
    # Get user's preferred categories
    try:
        interests = ConsumerInterest.objects.get(user=user)
        preferred_categories = interests.categories.all()
    except ConsumerInterest.DoesNotExist:
        preferred_categories = []
    
    offers_data = []
    for offer in offers_query:
        offers_data.append(format_offer_data(offer, today, preferred_categories))
    
    return {
        'offers': offers_data,
        'filter_category': 'all',
        'filter_date': 'newest',
        'filter_discount': 'highest',
        'filter_active_only': True
    }

def format_offer_data(offer, today, preferred_categories):
    """Format single offer data for frontend"""
    days_until_expiry = (offer.end_date - today).days if offer.end_date >= today else 0
    
    # Get business info safely
    business_info = {
        'name': 'Business Name',
        'email': '',
        'phone': '',
        'address': ''
    }
    
    if hasattr(offer, 'user') and offer.user:
        business_info.update({
            'name': offer.user.business_name or f"{offer.user.first_name} {offer.user.last_name}",
            'email': offer.user.email,
            'phone': offer.user.phone_number or '',
            'address': str(offer.user.address) if offer.user.address else ''
        })
    
    return {
        'id': offer.id,
        'title': getattr(offer, 'title', f"{offer.discount_percentage}% Off"),
        'description': offer.description,
        'discount_percentage': offer.discount_percentage,
        'code': offer.code,
        'start_date': offer.start_date.strftime("%b %d, %Y"),
        'end_date': offer.end_date.strftime("%b %d, %Y"),
        'business_name': business_info['name'],
        'business_email': business_info['email'],
        'business_phone': business_info['phone'],
        'business_address': business_info['address'],
        'categories': [cat.name for cat in offer.categories.all()],
        'days_until_expiry': max(0, days_until_expiry),
        'expiring_soon': 0 <= days_until_expiry <= 7,
        'expired': days_until_expiry < 0,
        'categories_match_preferences': any(
            cat in preferred_categories for cat in offer.categories.all()
        ) if preferred_categories else False
    }

def get_notification_settings(user):
    """Get user's notification settings"""
    try:
        interests = ConsumerInterest.objects.get(user=user)
        return {
            'notification_preference': interests.notification_preference,
            'min_discount': interests.min_discount_threshold,
            'time_period': interests.notification_time_period,
            'notification_limit': interests.notification_limit,
            'email_format': interests.email_format,
            'status': 'success'
        }
    except ConsumerInterest.DoesNotExist:
        return {
            'notification_preference': 'all',
            'min_discount': 10,
            'time_period': 'week',
            'notification_limit': 3,
            'email_format': 'individual',
            'status': 'success'
        }

def update_user_info(user, post_data):
    """Update user basic information"""
    user.first_name = post_data.get('first_name', '')
    user.last_name = post_data.get('last_name', '')
    user.phone_number = post_data.get('phone', '')
    
    # Handle email change
    new_email = post_data.get('email', '').lower()
    if new_email != user.email:
        if User.objects.filter(email=new_email).exists():
            raise ValueError('This email is already registered to another account.')
        user.email = new_email

def update_user_address(user, post_data):
    """Update or create user address"""
    address_number = post_data.get('address_number', '')
    address_street = post_data.get('address_street', '')
    street = f"{address_number} {address_street}".strip() if address_number else address_street
    
    address_data = {
        'street': street,
        'city': post_data.get('city', ''),
        'state': post_data.get('state', ''),
        'postal_code': post_data.get('zip', '')
    }
    
    if user.address:
        for key, value in address_data.items():
            setattr(user.address, key, value)
        user.address.save()
    else:
        user.address = Address.objects.create(**address_data)

def update_user_preferences(user, post_data):
    """Update user service preferences"""
    # Get or create interests
    interests, _ = ConsumerInterest.objects.get_or_create(user=user)
    interests.receive_notifications = post_data.get('receive_promotions') == 'on'
    interests.save()
    
    # Update categories
    selected_categories = post_data.getlist('service_category')
    interests.categories.clear()
    
    for category_slug in selected_categories:
        try:
            category = Category.objects.get(slug=category_slug)
            interests.categories.add(category)
        except Category.DoesNotExist:
            continue
    
    # Update specific services in profile
    profile, _ = UserProfile.objects.get_or_create(user=user)
    profile.bio = post_data.get('specific_services', '')
    profile.save()

def update_notification_settings(user, post_data):
    """Update notification settings"""
    interests, _ = ConsumerInterest.objects.get_or_create(user=user)
    
    interests.notification_preference = post_data.get('notification_preference', 'all')
    interests.min_discount_threshold = int(post_data.get('min_discount', 10))
    interests.notification_time_period = post_data.get('time_period', 'week')
    interests.notification_limit = int(post_data.get('notification_limit', 3))
    interests.email_format = post_data.get('email_format', 'individual')
    
    interests.save()

def get_filtered_offers(user, filters):
    """Get filtered promotional offers"""
    from promotor.models import PromotionalOffer
    today = timezone.now().date()
    
    # Base query
    offers_query = PromotionalOffer.objects.all()
    
    # Apply filters
    if filters['active_only']:
        offers_query = offers_query.filter(
            is_active=True,
            start_date__lte=today,
            end_date__gte=today
        )
    
    if filters['category'] != 'all':
        offers_query = offers_query.filter(categories__slug=filters['category'])
    
    if filters['search_query']:
        offers_query = offers_query.filter(
            Q(code__icontains=filters['search_query']) |
            Q(description__icontains=filters['search_query']) |
            Q(user__business_name__icontains=filters['search_query']) |
            Q(categories__name__icontains=filters['search_query'])
        )
    
    # Apply sorting
    if filters['date_sort'] == 'newest':
        offers_query = offers_query.order_by('-start_date')
    else:
        offers_query = offers_query.order_by('start_date')
    
    if filters['discount_sort'] == 'highest':
        offers_query = offers_query.order_by('-discount_percentage', 'id')
    else:
        offers_query = offers_query.order_by('discount_percentage', 'id')
    
    offers_query = offers_query.distinct()
    
    # Get user's preferred categories
    try:
        interests = ConsumerInterest.objects.get(user=user)
        preferred_categories = interests.categories.all()
    except ConsumerInterest.DoesNotExist:
        preferred_categories = []
    
    # Format offers
    return [format_offer_data(offer, today, preferred_categories) for offer in offers_query]

def get_offers_stats():
    """Get offer statistics"""
    from promotor.models import PromotionalOffer
    today = timezone.now().date()
    
    active_offers = PromotionalOffer.objects.filter(
        is_active=True,
        start_date__lte=today,
        end_date__gte=today
    )
    
    expiry_threshold = today + timedelta(days=7)
    expiring_soon = active_offers.filter(end_date__lte=expiry_threshold).count()
    
    return {
        'total': active_offers.count(),
        'expiring_soon': expiring_soon
    }

def get_formatted_categories():
    """Get all categories formatted for frontend"""
    categories = Category.objects.all()
    
    if not categories.exists():
        # Create default categories
        create_default_categories()
        categories = Category.objects.all()
    
    return [
        {'value': cat.slug, 'name': cat.name}
        for cat in categories
    ]

def create_default_categories():
    """Create default service categories"""
    default_categories = [
        ('Plumbing', 'plumbing'),
        ('Electrical', 'electrical'),
        ('General', 'general'),
        ('Foundation Repair', 'foundation'),
        ('Drywall/Paint', 'drywall'),
        ('Flooring', 'flooring'),
        ('Moving', 'moving'),
        ('Gardening', 'gardening'),
        ('Bathroom Renovation', 'bathroom'),
        ('Kitchen Cabinet/Countertops', 'kitchen'),
        ('Concrete', 'concrete'),
        ('HVAC', 'hvac'),
        ('Roofing', 'roofing'),
        ('Landscaping', 'landscaping')
    ]
    
    for name, slug in default_categories:
        Category.objects.create(
            name=name,
            slug=slug,
            description=f"{name} services"
        )

def get_us_states():
    """Get list of US states"""
    return [
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

# Redirect views for other user types
@login_required
def provider_dashboard(request):
    """Redirect to handyman dashboard"""
    return redirect('handyman_dashboard')

@login_required
def promoter_dashboard(request):
    """Redirect to promoter dashboard"""
    return redirect('promotor_dashboard')

@login_required
def offers_tab(request):
    """Redirect to consumer dashboard with offers tab active"""
    return redirect('consumer_dashboard')

# Alias for backward compatibility
def signup(request):
    """Alias for register_view"""
    return register_view(request)