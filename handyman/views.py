from django.views.generic import FormView, TemplateView, ListView, UpdateView, View
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.urls import reverse_lazy
from django.conf import settings
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django import forms
from django.http import JsonResponse
from django.utils.text import slugify

from users.models import User, UserType
from users.utils import send_login_email
from .models import Handyman, Service, HandymanService, HandymanPromotion, JobRequest
from core.models import Address

class HandymanSignupForm(forms.Form):
    """Form for handyman signup"""
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    email = forms.EmailField(required=True)
    phone = forms.CharField(max_length=15, required=True)
    business_name = forms.CharField(max_length=100, required=True)
    website = forms.URLField(required=False)
    
    # Address fields
    address_number = forms.CharField(max_length=10, required=True)
    address = forms.CharField(max_length=100, required=True)
    country = forms.CharField(max_length=100, required=True)
    state = forms.CharField(max_length=100, required=True)
    city = forms.CharField(max_length=100, required=True)
    zip = forms.CharField(max_length=20, required=True)
    
    # Service info
    service_description = forms.CharField(widget=forms.Textarea, required=True)
    service_categories = forms.MultipleChoiceField(
        choices=[
            ('Plumbing', 'Plumbing'),
            ('Electrical', 'Electrical'),
            ('Carpentry', 'Carpentry'),
            ('Painting', 'Painting'),
            ('Landscaping', 'Landscaping'),
            ('General Repairs', 'General Repairs'),
            ('HVAC', 'HVAC'),
            ('Roofing', 'Roofing'),
            ('Cleaning', 'Cleaning'),
            ('Flooring', 'Flooring'),
        ],
        widget=forms.CheckboxSelectMultiple,
        required=True
    )
    
    # Promotion options
    run_promotion = forms.BooleanField(required=False)
    discount_percentage = forms.IntegerField(required=False)
    discount_description = forms.CharField(max_length=200, required=False)
    
    # Business card
    card_front = forms.ImageField(required=True)
    card_back = forms.ImageField(required=False)
    blank_back = forms.BooleanField(required=False)
    
    def clean(self):
        cleaned_data = super().clean()
        run_promotion = cleaned_data.get('run_promotion')
        discount_percentage = cleaned_data.get('discount_percentage')
        
        if run_promotion and not discount_percentage:
            self.add_error('discount_percentage', 'Discount percentage is required when running a promotion')
            
        card_back = cleaned_data.get('card_back')
        blank_back = cleaned_data.get('blank_back')
        
        if not card_back and not blank_back:
            self.add_error('card_back', 'Either upload a back side image or check the blank back checkbox')
            
        return cleaned_data

class HandymanSignupView(FormView):
    template_name = 'handyman/handyman_signup.html'
    form_class = HandymanSignupForm
    success_url = reverse_lazy('login')
    
    def form_valid(self, form):
        # Extract data from form
        data = form.cleaned_data
        files = self.request.FILES
        
        # Create user account
        user = User.objects.create(
            email=data['email'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            phone_number=data['phone'],
            user_type=UserType.HANDYMAN,
            business_name=data['business_name'],
            website=data.get('website'),
            service_description=data['service_description']
        )
        
        # Handle business card uploads
        if 'card_front' in files:
            user.business_card_front = files['card_front']
        
        if 'card_back' in files:
            user.business_card_back = files['card_back']
        elif data.get('blank_back'):
            user.has_blank_card_back = True
        
        # Create address for the user
        # Combine address number and street into a single street field
        street_address = f"{data['address_number']} {data['address']}"
        address = Address.objects.create(
            street=street_address,
            city=data['city'],
            state=data['state'],
            country=data['country'],
            postal_code=data['zip']
        )
        user.address = address
        user.save()
        
        # Create handyman profile
        handyman = Handyman.objects.create(
            user=user,
            business_name=data['business_name'],
            bio='',
            detailed_services_description=data['service_description'],
            offers_promotions=data.get('run_promotion', False)
        )
        
        # Add service categories
        service_categories = data['service_categories']
        for category_name in service_categories:
            service, created = Service.objects.get_or_create(name=category_name)
            HandymanService.objects.create(
                handyman=handyman,
                service=service
            )
        
        # Handle promotion if selected
        if data.get('run_promotion'):
            import uuid
            
            HandymanPromotion.objects.create(
                handyman=handyman,
                description=data.get('discount_description', f"{data.get('discount_percentage')}% off for new customers"),
                discount_percentage=int(data.get('discount_percentage')),
                code=f"PROMO-{uuid.uuid4().hex[:8].upper()}",
                start_date=timezone.now().date(),
                end_date=timezone.now().date() + timezone.timedelta(days=90),
                is_active=True
            )
        
        # Generate and send magic login link
        login_url = send_login_email(self.request, user, "Handyman")
        
        messages.success(
            self.request, 
            f"Login link generated: {login_url}"
        )
        return render(self.request, 'users/login_link.html', {'email': user.email})
    
    def form_invalid(self, form):
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f"{field}: {error}")
        return super().form_invalid(form)

class HandymanProfileUpdateForm(forms.Form):
    """Form for updating handyman profile details"""
    # Personal information
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    email = forms.EmailField(required=True, disabled=True)  # Email cannot be changed
    phone_number = forms.CharField(max_length=15, required=True)
    
    # Business information
    business_name = forms.CharField(max_length=100, required=True)
    website = forms.URLField(required=False)
    
    # Bio and experience
    bio = forms.CharField(widget=forms.Textarea, required=False)
    experience_years = forms.IntegerField(min_value=0, required=False)
    license_number = forms.CharField(max_length=50, required=False)
    
    # Additional attributes
    is_insured = forms.BooleanField(required=False)
    is_licensed = forms.BooleanField(required=False)
    
    # Service description
    detailed_services_description = forms.CharField(widget=forms.Textarea, required=True)
    
    # Address fields - split from street to number and street name
    street = forms.CharField(max_length=255, required=True, label="Street Address")
    city = forms.CharField(max_length=100, required=True)
    state = forms.CharField(max_length=100, required=True)
    postal_code = forms.CharField(max_length=20, required=True, label="ZIP/Postal Code")
    country = forms.CharField(max_length=100, required=True, initial="United States")
    
    # Profile picture
    profile_picture = forms.ImageField(required=False)

class HandymanProfileUpdateView(LoginRequiredMixin, FormView):
    """
    View for updating handyman profile details
    """
    template_name = 'handyman/handyman_profile_update.html'
    form_class = HandymanProfileUpdateForm
    success_url = reverse_lazy('handyman_dashboard')
    
    def get_initial(self):
        """Pre-populate form with existing data"""
        initial = super().get_initial()
        user = self.request.user
        
        # Get handyman profile
        try:
            handyman = Handyman.objects.get(user=user)
        except Handyman.DoesNotExist:
            handyman = Handyman.objects.create(
                user=user,
                business_name=user.business_name or user.get_full_name()
            )
        
        # Get address
        address = user.address
        
        # Populate initial data
        initial.update({
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
            'phone_number': user.phone_number,
            'business_name': user.business_name,
            'website': user.website,
            'bio': handyman.bio,
            'experience_years': handyman.experience_years,
            'license_number': handyman.license_number,
            'is_insured': handyman.is_insured,
            'is_licensed': handyman.is_licensed,
            'detailed_services_description': handyman.detailed_services_description,
        })
        
        # Add address if it exists
        if address:
            initial.update({
                'street': address.street,
                'city': address.city,
                'state': address.state,
                'postal_code': address.postal_code,
                'country': address.country,
            })
        
        return initial
    
    def form_valid(self, form):
        """Process the valid form data and update the profile"""
        data = form.cleaned_data
        user = self.request.user
        files = self.request.FILES
        
        # Update User model fields
        user.first_name = data['first_name']
        user.last_name = data['last_name']
        user.phone_number = data['phone_number']
        user.business_name = data['business_name']
        user.website = data.get('website')
        
        # Handle profile picture upload
        if 'profile_picture' in files:
            user.profile_picture = files['profile_picture']
        
        # Update or create address
        if user.address:
            address = user.address
            address.street = data['street']
            address.city = data['city']
            address.state = data['state']
            address.postal_code = data['postal_code']
            address.country = data['country']
            address.save()
        else:
            address = Address.objects.create(
                street=data['street'],
                city=data['city'],
                state=data['state'],
                postal_code=data['postal_code'],
                country=data['country']
            )
            user.address = address
        
        user.save()
        
        # Update Handyman model fields
        handyman = Handyman.objects.get(user=user)
        handyman.business_name = data['business_name']
        handyman.bio = data['bio']
        handyman.detailed_services_description = data['detailed_services_description']
        handyman.experience_years = data['experience_years']
        handyman.license_number = data['license_number']
        handyman.is_insured = data['is_insured']
        handyman.is_licensed = data['is_licensed']
        handyman.save()
        
        messages.success(self.request, "Your profile has been updated successfully!")
        return super().form_valid(form)
    
    def form_invalid(self, form):
        """Handle invalid form submission"""
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f"{field}: {error}")
        return super().form_invalid(form)

class HandymanDashboardView(LoginRequiredMixin, TemplateView):
    """
    Display the handyman dashboard page
    """
    template_name = 'handyman/handyman_dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get the handyman profile
        try:
            handyman = Handyman.objects.get(user=self.request.user)
        except Handyman.DoesNotExist:
            # If handyman profile doesn't exist, create one
            handyman = Handyman.objects.create(
                user=self.request.user,
                business_name=self.request.user.business_name
            )
        
        # Get services, promotions, etc.
        services = HandymanService.objects.filter(handyman=handyman)
        total_services = services.count()
        
        # Get selected service categories for the services tab
        selected_categories = []
        service_description = ''
        
        if services.exists():
            # Get service names in lowercase for easy comparison in the template
            selected_categories = [service.service.name.lower() for service in services]
            
            # Get service description
            service_description = handyman.detailed_services_description or self.request.user.service_description or ''
        
        from .models import HandymanPromotion
        promotions = HandymanPromotion.objects.filter(handyman=handyman)
        active_promotions = promotions.filter(is_active=True).count()
        active_promotions_list = promotions.filter(is_active=True).order_by('-start_date')
        
        # Get all promotions (both active and inactive) for display
        all_promotions_list = promotions.order_by('-is_active', '-start_date')
        
        # Calculate profile completion percentage
        completion_items = [
            bool(self.request.user.first_name and self.request.user.last_name),
            bool(self.request.user.email),
            bool(self.request.user.phone_number),
            bool(self.request.user.business_name),
            bool(self.request.user.business_card_front),
            bool(self.request.user.address),
            bool(handyman.detailed_services_description),
            bool(services)
        ]
        profile_completion = int((sum(completion_items) / len(completion_items)) * 100)
        
        # Add to context
        context.update({
            'handyman': handyman,
            'total_services': total_services,
            'active_promotions': active_promotions,
            'active_promotions_list': active_promotions_list,
            'all_promotions_list': all_promotions_list,
            'profile_completion': profile_completion,
            'selected_categories': selected_categories,
            'service_description': service_description,
        })
        
        return context

class HandymanMainView(TemplateView):
    """
    Display the handyman main landing page
    """
    template_name = 'handyman/handyman_main.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get featured handymen
        featured_handymen = Handyman.objects.filter(
            user__is_active=True
        ).order_by('?')[:6]  # Random selection for featured
        
        # Get service categories
        service_categories = Service.objects.all().distinct()[:10]
        
        # Add to context
        context.update({
            'featured_handymen': featured_handymen,
            'service_categories': service_categories,
        })
        
        return context
    
    def post(self, request, *args, **kwargs):
        """Handle search form submission"""
        # Extract search parameters
        country = request.POST.get('country', '')
        state = request.POST.get('state', '')
        city = request.POST.get('city', '')
        service_description = request.POST.get('service_description', '')
        
        # Build query
        handymen = Handyman.objects.filter(user__is_active=True)
        
        # Filter by location if provided
        location_filters = Q()
        if country:
            location_filters &= Q(user__address__country=country)
        if state:
            location_filters &= Q(user__address__state=state)
        if city:
            location_filters &= Q(user__address__city=city)
        
        if location_filters:
            handymen = handymen.filter(location_filters)
        
        # Filter by service description if provided
        if service_description:
            service_filters = (
                Q(detailed_services_description__icontains=service_description) |
                Q(user__service_description__icontains=service_description) |
                Q(services__service__name__icontains=service_description)
            )
            handymen = handymen.filter(service_filters).distinct()
        
        # Render the same template with search results
        context = self.get_context_data(**kwargs)
        context['search_results'] = handymen
        context['search_query'] = {
            'country': country,
            'state': state,
            'city': city,
            'service_description': service_description
        }
        
        return render(request, self.template_name, context)

class HandymanBusinessCardUpdateView(LoginRequiredMixin, View):
    """
    View for updating handyman business card images
    """
    success_url = reverse_lazy('handyman_dashboard')
    
    def post(self, request, *args, **kwargs):
        """Handle POST request with file uploads"""
        user = request.user
        files = request.FILES
        
        # Handle front side upload
        if 'card_front' in files:
            user.business_card_front = files['card_front']
        
        # Handle back side upload or blank back checkbox
        if 'card_back' in files:
            user.business_card_back = files['card_back']
            user.has_blank_card_back = False
        elif request.POST.get('blank_back'):
            user.has_blank_card_back = True
            # Clear existing back image if blank back is checked
            if user.business_card_back:
                user.business_card_back = None
        
        # Set status to pending_review when card is updated
        user.business_card_status = 'pending_review'
        
        user.save()
        
        # Check if this is an AJAX request
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        
        if is_ajax:
            return JsonResponse({
                'status': 'success',
                'message': 'Your business card has been updated successfully!'
            })
        else:
            messages.success(request, "Your business card has been updated successfully!")
            return redirect(self.success_url)

class HandymanProfileUpdateFormView(LoginRequiredMixin, View):
    """
    View for handling the personal details form submission in the dashboard
    """
    success_url = reverse_lazy('handyman_dashboard')
    
    def post(self, request, *args, **kwargs):
        """Handle POST request with form data"""
        user = request.user
        data = request.POST
        files = request.FILES
        errors = {}
        
        # Validate required fields
        required_fields = ['first_name', 'last_name', 'phone_number', 'business_name']
        for field in required_fields:
            if not data.get(field):
                errors[field] = f"{field.replace('_', ' ').title()} is required."
        
        # If validation errors, return early
        if errors:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'error',
                    'message': 'Please fix the form errors.',
                    'errors': errors
                })
            else:
                for field, error in errors.items():
                    messages.error(request, error)
                return redirect(self.success_url)
        
        # Get or create handyman profile
        try:
            handyman = Handyman.objects.get(user=user)
        except Handyman.DoesNotExist:
            handyman = Handyman.objects.create(
                user=user,
                business_name=user.business_name or user.get_full_name()
            )
        
        # Update User model fields
        user.first_name = data.get('first_name')
        user.last_name = data.get('last_name')
        user.phone_number = data.get('phone_number')
        user.business_name = data.get('business_name')
        user.website = data.get('website')
        
        # Handle address information
        address_number = data.get('address_number', '')
        address_street = data.get('address_street', '')
        if address_number and address_street:
            street_address = f"{address_number} {address_street}"
            
            if user.address:
                # Update existing address
                address = user.address
                address.street = street_address
                address.city = data.get('city')
                address.state = data.get('state')
                address.postal_code = data.get('zip')
                address.country = data.get('country')
                address.save()
            else:
                # Create new address
                address = Address.objects.create(
                    street=street_address,
                    city=data.get('city'),
                    state=data.get('state'),
                    postal_code=data.get('zip'),
                    country=data.get('country')
                )
                user.address = address
        
        # Save user changes
        user.save()
        
        # Update handyman profile fields
        handyman.business_name = data.get('business_name')
        
        # Additional profile fields if provided
        if data.get('bio'):
            handyman.bio = data.get('bio')
        if data.get('detailed_services_description'):
            handyman.detailed_services_description = data.get('detailed_services_description')
        if data.get('experience_years'):
            try:
                handyman.experience_years = int(data.get('experience_years'))
            except (ValueError, TypeError):
                pass
        if data.get('license_number'):
            handyman.license_number = data.get('license_number')
        
        # Boolean fields
        handyman.is_insured = data.get('is_insured') == 'on'
        handyman.is_licensed = data.get('is_licensed') == 'on'
        
        # Save handyman changes
        handyman.save()
        
        # Check if this is an AJAX request
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'success',
                'message': 'Your profile has been updated successfully!'
            })
        else:
            messages.success(request, "Your profile has been updated successfully!")
            return redirect(self.success_url)

class HandymanServicesUpdateView(LoginRequiredMixin, View):
    """
    View for updating handyman services categories and description
    """
    success_url = reverse_lazy('handyman_dashboard')
    
    def post(self, request, *args, **kwargs):
        """Handle POST request with service form data"""
        user = request.user
        data = request.POST
        errors = {}
        
        # Validate required fields
        if not data.get('service_description'):
            errors['service_description'] = "Service description is required."
            
        service_categories = request.POST.getlist('service_categories')
        if not service_categories:
            errors['service_categories'] = "Please select at least one service category."
        
        # If validation errors, return early
        if errors:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'error',
                    'message': 'Please fix the form errors.',
                    'errors': errors
                })
            else:
                for field, error in errors.items():
                    messages.error(request, error)
                return redirect(self.success_url)
        
        # Get or create handyman profile
        try:
            handyman = Handyman.objects.get(user=user)
        except Handyman.DoesNotExist:
            handyman = Handyman.objects.create(
                user=user,
                business_name=user.business_name or user.get_full_name()
            )
        
        # Update service description
        service_description = data.get('service_description')
        user.service_description = service_description
        handyman.detailed_services_description = service_description
        
        # Save changes
        user.save()
        handyman.save()
        
        # Update service categories
        # First, remove all current services
        HandymanService.objects.filter(handyman=handyman).delete()
        
        # Add selected service categories
        for category_name in service_categories:
            try:
                # First try to get the service by name
                service = Service.objects.get(name__iexact=category_name)
            except Service.DoesNotExist:
                # If not found, create one with a unique slug
                base_slug = slugify(category_name)
                slug = base_slug
                counter = 1
                
                # Keep trying with incremented counters until we find a unique slug
                while Service.objects.filter(slug=slug).exists():
                    slug = f"{base_slug}-{counter}"
                    counter += 1
                
                # Create the service with the unique slug
                service = Service.objects.create(
                    name=category_name,
                    slug=slug,
                    description=f"Services related to {category_name}"
                )
            
            # Create the handyman-service relationship
            HandymanService.objects.create(
                handyman=handyman,
                service=service
            )
        
        # Check if this is an AJAX request
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'success',
                'message': 'Your services have been updated successfully!'
            })
        else:
            messages.success(request, "Your services have been updated successfully!")
            return redirect(self.success_url)

class HandymanPromotionCreateView(LoginRequiredMixin, View):
    """
    View for creating handyman promotional offers
    """
    success_url = reverse_lazy('handyman_dashboard')
    
    def post(self, request, *args, **kwargs):
        """Handle POST request with promotion form data"""
        user = request.user
        
        data = request.POST
        errors = {}
        
        # Check if user wants to run a campaign
        run_campaign = data.get('run_campaign') == 'yes'
        
        # If not running a campaign, just redirect
        if not run_campaign:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'success',
                    'message': 'Promotion settings saved.'
                })
            else:
                messages.info(request, "You've chosen not to run a promotional campaign.")
                return redirect(self.success_url)
        
        # Validate required fields for campaign
        required_fields = {
            'discount_description': 'Promotion description is required.',
            'discount_percentage': 'Discount percentage is required.',
            'promo_code': 'Promotional code is required.',
            'start_date': 'Start date is required.',
            'stop_date': 'Stop date is required.'
        }
        
        for field, error_msg in required_fields.items():
            if not data.get(field):
                errors[field] = error_msg
        
        # Validate dates
        start_date = None
        stop_date = None
        
        try:
            if data.get('start_date'):
                start_date = timezone.datetime.strptime(data.get('start_date'), '%Y-%m-%d').date()
            if data.get('stop_date'):
                stop_date = timezone.datetime.strptime(data.get('stop_date'), '%Y-%m-%d').date()
                
            if start_date and stop_date and start_date >= stop_date:
                errors['stop_date'] = "Stop date must be after start date."
                
        except ValueError:
            errors['date_format'] = "Invalid date format. Please use YYYY-MM-DD format."
        
        # If validation errors, return early
        if errors:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'error',
                    'message': 'Please fix the form errors.',
                    'errors': errors
                })
            else:
                for field, error in errors.items():
                    messages.error(request, error)
                return redirect(self.success_url)
        
        # Get or create handyman profile
        try:
            handyman = Handyman.objects.get(user=user)
        except Handyman.DoesNotExist:
            handyman = Handyman.objects.create(
                user=user,
                business_name=user.business_name or user.get_full_name()
            )
        
        # Update handyman to indicate they offer promotions
        handyman.offers_promotions = True
        handyman.save()
        
        # Create the promotion
        from .models import HandymanPromotion
        
        # Parse discount percentage
        try:
            discount_percentage = int(data.get('discount_percentage', 0))
        except ValueError:
            discount_percentage = 0
            
        # Create new promotion
        promotion = HandymanPromotion.objects.create(
            handyman=handyman,
            description=data.get('discount_description'),
            discount_percentage=discount_percentage,
            code=data.get('promo_code'),
            start_date=start_date,
            end_date=stop_date,
            is_active=True
        )
        
        # Check if this is an AJAX request
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'success',
                'message': 'Your promotional campaign has been created successfully!'
            })
        else:
            messages.success(request, "Your promotional campaign has been created successfully!")
            return redirect(self.success_url)

class HandymanJobRequestsView(LoginRequiredMixin, View):
    """
    View for handling handyman job requests
    Returns job requests for the authenticated handyman via AJAX
    """
    
    def get(self, request, *args, **kwargs):
        """Handle GET request to retrieve job requests"""
        user = request.user
        
        # Get handyman profile
        try:
            handyman = Handyman.objects.get(user=user)
        except Handyman.DoesNotExist:
            # If no handyman profile exists, return empty list
            return JsonResponse({'jobs': []})
        
        # Get job requests for this handyman
        from .models import JobRequest
        
        # Check for a test mode parameter
        use_test_data = request.GET.get('test', 'false').lower() == 'true'
        
        if use_test_data:
            # Return example data for testing/development
            jobs_data = [
                {
                    'id': 1,
                    'service_name': 'Plumbing Repair',
                    'client_name': 'John Smith',
                    'scheduled_date': '2025-06-15',
                    'scheduled_time': '10:00',
                    'address': '123 Main St, Anytown, CA',
                    'description': 'Leaking pipe under kitchen sink. Water is collecting in the cabinet below. Need urgent repair.',
                    'status': 'pending',
                    'created_at': '2025-06-10 14:30'
                },
                {
                    'id': 2,
                    'service_name': 'Electrical Installation',
                    'client_name': 'Mary Johnson',
                    'scheduled_date': '2025-06-18',
                    'scheduled_time': '14:00',
                    'address': '456 Oak Ave, Anytown, CA',
                    'description': 'Install new light fixtures in living room. Three ceiling lights need to be replaced. Customer has purchased the fixtures already.',
                    'status': 'pending',
                    'created_at': '2025-06-11 09:15'
                },
                {
                    'id': 3,
                    'service_name': 'Cabinet Installation',
                    'client_name': 'Robert Davis',
                    'scheduled_date': '2025-06-20',
                    'scheduled_time': '09:00',
                    'address': '789 Pine St, Anytown, CA',
                    'description': 'Install new kitchen cabinets. Full kitchen renovation, cabinets already delivered to the site.',
                    'status': 'accepted',
                    'created_at': '2025-06-12 11:45'
                },
                {
                    'id': 4,
                    'service_name': 'Painting',
                    'client_name': 'Emily Wilson',
                    'scheduled_date': '2025-06-10',
                    'scheduled_time': '11:00',
                    'address': '321 Elm St, Anytown, CA',
                    'description': 'Paint master bedroom - walls and ceiling. Color: Soft Blue (Benjamin Moore #2065-70).',
                    'status': 'completed',
                    'created_at': '2025-06-05 16:20'
                },
                {
                    'id': 5,
                    'service_name': 'Fence Repair',
                    'client_name': 'Thomas Brown',
                    'scheduled_date': '2025-06-12',
                    'scheduled_time': '16:00',
                    'address': '567 Maple Dr, Anytown, CA',
                    'description': 'Repair damaged backyard fence. Approximately 20 feet of wooden fence damaged by storm.',
                    'status': 'declined',
                    'created_at': '2025-06-08 10:30'
                }
            ]
        else:
            # Get actual job requests from the database
            job_requests = JobRequest.objects.filter(
                handyman=handyman
            ).order_by('-created_at')  # Most recent first
            
            # Serialize the job requests for JSON response
            jobs_data = []
            for job in job_requests:
                job_data = {
                    'id': job.id,
                    'service_name': job.service_name,
                    'client_name': f"{job.client.first_name} {job.client.last_name}" if job.client else "Anonymous",
                    'scheduled_date': job.scheduled_date.strftime('%Y-%m-%d') if job.scheduled_date else None,
                    'scheduled_time': job.scheduled_time.strftime('%H:%M') if job.scheduled_time else None,
                    'address': str(job.address) if job.address else "No address provided",
                    'description': job.description,
                    'status': job.status,
                    'created_at': job.created_at.strftime('%Y-%m-%d %H:%M')
                }
                jobs_data.append(job_data)
        
        # Return the job requests as JSON
        return JsonResponse({'jobs': jobs_data})
    
    def post(self, request, *args, **kwargs):
        """Handle POST request to update job request status"""
        user = request.user
        data = request.POST
        job_id = data.get('job_id')
        action = data.get('action')
        
        # Check for test mode
        test_mode = data.get('test_mode', 'false').lower() == 'true'
        
        if not job_id or not action:
            return JsonResponse({
                'status': 'error',
                'message': 'Job ID and action are required'
            })
        
        # If in test mode, simulate a successful response
        if test_mode:
            valid_actions = ['accept', 'decline', 'complete']
            if action not in valid_actions:
                return JsonResponse({
                    'status': 'error',
                    'message': f'Invalid action: {action}'
                })
                
            # Return success for test mode
            action_messages = {
                'accept': 'Job request accepted',
                'decline': 'Job request declined',
                'complete': 'Job marked as completed'
            }
            
            return JsonResponse({
                'status': 'success',
                'message': action_messages.get(action, 'Status updated successfully')
            })
            
        # Real processing mode
        try:
            # Get handyman profile
            handyman = Handyman.objects.get(user=user)
            
            # Get the job request model
            from .models import JobRequest
            
            # Get the specific job request
            job = JobRequest.objects.get(id=job_id, handyman=handyman)
            
            # Update job status based on action
            if action == 'accept':
                job.status = 'accepted'
                message = 'Job request accepted'
            elif action == 'decline':
                job.status = 'declined'
                message = 'Job request declined'
            elif action == 'complete':
                job.status = 'completed'
                # Set completed_at timestamp
                job.completed_at = timezone.now()
                message = 'Job marked as completed'
            else:
                return JsonResponse({
                    'status': 'error',
                    'message': f'Invalid action: {action}'
                })
            
            # Save the updated job
            job.save()
            
            return JsonResponse({
                'status': 'success',
                'message': message
            })
            
        except Handyman.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': 'Handyman profile not found'
            })
        except JobRequest.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': 'Job request not found'
            })
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'Error updating job status: {str(e)}'
            })

class HandymanServicesTabView(LoginRequiredMixin, View):
    """
    View for handling AJAX loading of the services tab in dashboard
    """
    
    def get(self, request, *args, **kwargs):
        """Handle GET request to load services data"""
        user = request.user
        
        # Get handyman profile
        try:
            handyman = Handyman.objects.get(user=user)
        except Handyman.DoesNotExist:
            handyman = Handyman.objects.create(
                user=user,
                business_name=user.business_name or user.get_full_name()
            )
        
        # Get services
        services = HandymanService.objects.filter(handyman=handyman)
        
        # Get selected service categories
        selected_categories = []
        if services.exists():
            selected_categories = [service.service.name.lower() for service in services]
        
        # Get service description
        service_description = handyman.detailed_services_description or user.service_description or ''
        
        # Handle AJAX request
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'success',
                'selected_categories': selected_categories,
                'service_description': service_description,
                'total_services': services.count()
            })
        
        # If not AJAX, redirect to dashboard with services tab
        return redirect(f"{reverse_lazy('handyman_dashboard')}#services")

class ClientJobRequestCreateView(LoginRequiredMixin, View):
    """
    View for handling job requests from clients to handymen
    """
    
    def post(self, request, *args, **kwargs):
        """Handle POST request to create a job request"""
        user = request.user
        data = request.POST
        errors = {}
        
        # Validate required fields
        required_fields = {
            'handyman_id': 'Handyman is required',
            'service_id': 'Service is required',
            'description': 'Job description is required',
            'scheduled_date': 'Scheduled date is required',
            'scheduled_time': 'Scheduled time is required',
        }
        
        for field, error_msg in required_fields.items():
            if not data.get(field):
                errors[field] = error_msg
        
        # If validation errors, return early
        if errors:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'error',
                    'message': 'Please fix the form errors.',
                    'errors': errors
                })
            else:
                for field, error in errors.items():
                    messages.error(request, error)
                return redirect(request.META.get('HTTP_REFERER', '/'))
        
        try:
            # Get the handyman
            handyman = Handyman.objects.get(id=data.get('handyman_id'))
            
            # Get the service
            service = Service.objects.get(id=data.get('service_id'))
            
            # Get or create address for the job
            address_data = {
                'number': data.get('address_number', ''),
                'street': data.get('address_street', ''),
                'city': data.get('address_city', ''),
                'state': data.get('address_state', ''),
                'zip_code': data.get('address_zip', ''),
                'country': data.get('address_country', 'USA'),
            }
            
            # Check if user has an address
            if user.address:
                # Use user's address if no specific job address provided
                address = user.address
                
                # Update with job-specific address if provided
                if all(address_data.values()):
                    address = Address.objects.create(**address_data)
            else:
                # Create new address if user doesn't have one
                if all(address_data.values()):
                    address = Address.objects.create(**address_data)
                else:
                    # Return error if no address is provided
                    error_msg = 'Address information is required'
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({
                            'status': 'error',
                            'message': error_msg,
                            'errors': {'address': error_msg}
                        })
                    else:
                        messages.error(request, error_msg)
                        return redirect(request.META.get('HTTP_REFERER', '/'))
            
            # Parse date and time
            try:
                scheduled_date = timezone.datetime.strptime(data.get('scheduled_date'), '%Y-%m-%d').date()
                scheduled_time = timezone.datetime.strptime(data.get('scheduled_time'), '%H:%M').time()
            except ValueError:
                error_msg = 'Invalid date or time format'
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'status': 'error',
                        'message': error_msg,
                        'errors': {'date': 'Invalid date format', 'time': 'Invalid time format'}
                    })
                else:
                    messages.error(request, error_msg)
                    return redirect(request.META.get('HTTP_REFERER', '/'))
            
            # Check if a promotion code was provided
            promotion = None
            promo_code = data.get('promo_code')
            if promo_code:
                try:
                    promotion = HandymanPromotion.objects.get(
                        handyman=handyman,
                        promo_code=promo_code,
                        is_active=True,
                        start_date__lte=timezone.now().date(),
                        stop_date__gte=timezone.now().date()
                    )
                except HandymanPromotion.DoesNotExist:
                    # Optional: Return error if promo code is invalid
                    pass
            
            # Create the job request
            job = JobRequest.objects.create(
                handyman=handyman,
                client=user,
                service=service,
                address=address,
                description=data.get('description'),
                scheduled_date=scheduled_date,
                scheduled_time=scheduled_time,
                status='pending',
                promotion_applied=promotion
            )
            
            # Optional: Send notification to handyman
            
            # Return success response
            success_message = 'Your job request has been sent to the handyman!'
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'success',
                    'message': success_message,
                    'job_id': job.id
                })
            else:
                messages.success(request, success_message)
                return redirect(request.META.get('HTTP_REFERER', '/'))
                
        except Handyman.DoesNotExist:
            error_message = 'Handyman not found'
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'error',
                    'message': error_message
                })
            else:
                messages.error(request, error_message)
                return redirect(request.META.get('HTTP_REFERER', '/'))
                
        except Service.DoesNotExist:
            error_message = 'Service not found'
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'error',
                    'message': error_message
                })
            else:
                messages.error(request, error_message)
                return redirect(request.META.get('HTTP_REFERER', '/'))
                
        except Exception as e:
            error_message = f'Error creating job request: {str(e)}'
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'error',
                    'message': error_message
                })
            else:
                messages.error(request, error_message)
                return redirect(request.META.get('HTTP_REFERER', '/'))

class HandymanTogglePromotionView(LoginRequiredMixin, View):
    """
    View for toggling the active status of a promotion
    """
    success_url = reverse_lazy('handyman_dashboard')
    
    def post(self, request, *args, **kwargs):
        """Handle POST request to toggle promotion status"""
        user = request.user
        data = request.POST
        
        promotion_id = data.get('promotion_id')
        action = data.get('action')
        
        if not promotion_id or not action:
            messages.error(request, "Missing required information.")
            return redirect(self.success_url + '#promotions')
        
        try:
            # Get handyman profile
            handyman = Handyman.objects.get(user=user)
            
            # Get the promotion and verify ownership
            from .models import HandymanPromotion
            promotion = HandymanPromotion.objects.get(id=promotion_id, handyman=handyman)
            
            # Toggle active status
            if action == 'activate':
                promotion.is_active = True
                status_message = "Promotion activated successfully!"
            else:
                promotion.is_active = False
                status_message = "Promotion deactivated successfully!"
                
            promotion.save()
            
            messages.success(request, status_message)
            
        except Handyman.DoesNotExist:
            messages.error(request, "Handyman profile not found.")
        except HandymanPromotion.DoesNotExist:
            messages.error(request, "Promotion not found or you don't have permission to modify it.")
        except Exception as e:
            messages.error(request, f"Error updating promotion: {str(e)}")
        
        # Redirect back to the promotions tab
        return redirect(self.success_url + '#promotions')

class HandymanJobsTabView(LoginRequiredMixin, TemplateView):
    """
    View for displaying and handling job requests in the dashboard
    """
    template_name = 'handyman/handyman_dashboard_jobs.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Get handyman profile
        try:
            handyman = Handyman.objects.get(user=user)
        except Handyman.DoesNotExist:
            # If no handyman profile exists, return empty context
            context['jobs'] = []
            context['pending_count'] = 0
            return context
        
        # Get job requests for this handyman
        from .models import JobRequest
        job_requests = JobRequest.objects.filter(handyman=handyman).order_by('-created_at')
        
        # Prepare jobs data for the template
        jobs = []
        for job in job_requests:
            job_data = {
                'id': job.id,
                'service_name': job.service_name,
                'client_name': f"{job.client.first_name} {job.client.last_name}" if job.client else "Anonymous",
                'scheduled_date': job.scheduled_date.strftime('%Y-%m-%d') if job.scheduled_date else None,
                'scheduled_time': job.scheduled_time.strftime('%H:%M') if job.scheduled_time else None,
                'address': str(job.address) if job.address else "No address provided",
                'description': job.description,
                'status': job.status,
                'created_at': job.created_at.strftime('%Y-%m-%d %H:%M')
            }
            jobs.append(job_data)
        
        # Count pending jobs
        pending_count = sum(1 for job in jobs if job['status'] == 'pending')
        
        context['jobs'] = jobs
        context['pending_count'] = pending_count
        return context
