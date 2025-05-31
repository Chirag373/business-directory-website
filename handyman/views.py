from django.views.generic import FormView, TemplateView, View
from django.shortcuts import render, redirect
from django.contrib import messages
from django.urls import reverse_lazy
from django.utils import timezone
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.http import JsonResponse
from django.utils.text import slugify
from users.models import User, UserType
from users.utils import send_login_email, check_handyman_payment_status
from users.views import get_user_profile_data
from .models import Handyman, Service, HandymanService, HandymanPromotion, JobRequest
from core.models import Address
from .forms import (
    HandymanSignupForm,
    HandymanProfileUpdateForm,
    BusinessCardUpdateForm,
    HandymanServicesForm,
    HandymanPromotionForm,
    JobRequestForm,
    JobRequestUpdateForm,
)


class PaymentRequiredMixin:
    """
    Mixin to verify that a handyman user has completed payment
    before accessing protected views.
    """
    
    def dispatch(self, request, *args, **kwargs):
        """Check if user has paid before allowing access"""
        # Skip payment check for non-handyman users
        if request.user.is_authenticated and request.user.user_type == 'handyman':
            if not check_handyman_payment_status(request.user):
                messages.error(request, "Please complete your payment to access this feature.")
                return redirect('handyman_payment')
                
        return super().dispatch(request, *args, **kwargs)


class HandymanSignupView(FormView):
    template_name = "handyman/handyman_signup.html"
    form_class = HandymanSignupForm
    success_url = reverse_lazy("login")

    def form_valid(self, form):
        data = form.cleaned_data
        files = self.request.FILES

        user = User.objects.create(
            email=data["email"],
            first_name=data["first_name"],
            last_name=data["last_name"],
            phone_number=data["phone"],
            user_type=UserType.HANDYMAN,
            business_name=data["business_name"],
            website=data.get("website"),
            service_description=data["service_description"],
            business_card_status=None,
        )

        card_uploaded = False
        if "card_front" in files:
            user.business_card_front = files["card_front"]
            card_uploaded = True

        if "card_back" in files:
            user.business_card_back = files["card_back"]
            card_uploaded = True
        elif data.get("blank_back"):
            user.has_blank_card_back = True

        # Set business card status to pending_review only when a card is uploaded
        if card_uploaded:
            user.business_card_status = "pending_review"

        # Combine address number and street into a single street field
        street = (
            f"{data['address_number']} {data['address']}"
            if data["address_number"]
            else data["address"]
        )

        address = Address.objects.create(
            street=street,
            city=data["city"],
            state=data["state"],
            country=data["country"],
            postal_code=data["zip"],
        )
        user.address = address
        user.save()

        handyman = Handyman.objects.create(
            user=user,
            business_name=data["business_name"],
            bio="",
            detailed_services_description=data["service_description"],
            offers_promotions=data.get("run_promotion", False),
        )

        service_categories = data["service_categories"]
        for category_name in service_categories:
            service, created = Service.objects.get_or_create(name=category_name)
            HandymanService.objects.create(handyman=handyman, service=service)

        if data.get("run_promotion"):
            import uuid

            HandymanPromotion.objects.create(
                handyman=handyman,
                description=data.get(
                    "discount_description",
                    f"{data.get('discount_percentage')}% off for new customers",
                ),
                discount_percentage=int(data.get("discount_percentage")),
                code=f"PROMO-{uuid.uuid4().hex[:8].upper()}",
                start_date=timezone.now().date(),
                end_date=timezone.now().date() + timezone.timedelta(days=90),
                is_active=True,
            )

        login_url = send_login_email(self.request, user, "Handyman")

        messages.success(self.request, f"Login link generated: {login_url}")
        return render(self.request, "users/check_email.html", {"email": user.email, "user_type": "handyman"})

    def form_invalid(self, form):
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f"{field}: {error}")
        return super().form_invalid(form)


class HandymanProfileUpdateView(LoginRequiredMixin, PaymentRequiredMixin, FormView):
    """
    View for updating handyman profile details
    """

    template_name = "handyman/handyman_profile_update.html"
    form_class = HandymanProfileUpdateForm
    success_url = reverse_lazy("handyman_dashboard")

    def get_initial(self):
        """Pre-populate form with existing data"""
        initial = super().get_initial()
        user = self.request.user

        try:
            handyman = Handyman.objects.get(user=user)
        except Handyman.DoesNotExist:
            handyman = Handyman.objects.create(
                user=user, business_name=user.business_name or user.get_full_name()
            )

        address = user.address

        initial.update(
            {
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email,
                "phone_number": user.phone_number,
                "business_name": user.business_name,
                "website": user.website,
                "bio": handyman.bio,
                "experience_years": handyman.experience_years,
                "license_number": handyman.license_number,
                "is_insured": handyman.is_insured,
                "is_licensed": handyman.is_licensed,
                "detailed_services_description": handyman.detailed_services_description,
            }
        )

        if address:
            initial.update(
                {
                    "street": address.street,
                    "city": address.city,
                    "state": address.state,
                    "postal_code": address.postal_code,
                    "country": address.country,
                }
            )

        return initial

    def form_valid(self, form):
        """Process the valid form data and update the profile"""
        data = form.cleaned_data
        user = self.request.user
        files = self.request.FILES

        user.first_name = data["first_name"]
        user.last_name = data["last_name"]
        user.phone_number = data["phone_number"]
        user.business_name = data["business_name"]
        user.website = data.get("website")

        if "profile_picture" in files:
            user.profile_picture = files["profile_picture"]

        if user.address:
            address = user.address
            address.street = data["street"]
            address.city = data["city"]
            address.state = data["state"]
            address.postal_code = data["postal_code"]
            address.country = data["country"]
            address.save()
        else:
            address = Address.objects.create(
                street=data["street"],
                city=data["city"],
                state=data["state"],
                postal_code=data["postal_code"],
                country=data["country"],
            )
            user.address = address

        user.save()

        handyman = Handyman.objects.get(user=user)
        handyman.business_name = data["business_name"]
        handyman.bio = data["bio"]
        handyman.detailed_services_description = data["detailed_services_description"]
        handyman.experience_years = data["experience_years"]
        handyman.license_number = data["license_number"]
        handyman.is_insured = data["is_insured"]
        handyman.is_licensed = data["is_licensed"]
        handyman.save()

        messages.success(self.request, "Your profile has been updated successfully!")
        return super().form_valid(form)

    def form_invalid(self, form):
        """Handle invalid form submission"""
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f"{field}: {error}")
        return super().form_invalid(form)


class HandymanDashboardView(LoginRequiredMixin, PaymentRequiredMixin, TemplateView):
    """
    Display the handyman dashboard page
    """

    template_name = "handyman/handyman_dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        try:
            handyman = Handyman.objects.get(user=self.request.user)
        except Handyman.DoesNotExist:
            handyman = Handyman.objects.create(
                user=self.request.user, business_name=self.request.user.business_name
            )

        services = HandymanService.objects.filter(handyman=handyman)
        total_services = services.count()

        selected_categories = []
        service_description = ""

        if services.exists():
            # Store both the actual name and lowercase version for easier comparison
            selected_categories = [
                {"name": service.service.name, "lower": service.service.name.lower()}
                for service in services
            ]

            service_description = (
                handyman.detailed_services_description
                or self.request.user.service_description
                or ""
            )

        from .models import HandymanPromotion

        promotions = HandymanPromotion.objects.filter(handyman=handyman)
        active_promotions = promotions.filter(is_active=True).count()
        active_promotions_list = promotions.filter(is_active=True).order_by(
            "-start_date"
        )

        all_promotions_list = promotions.order_by("-is_active", "-start_date")

        completion_items = [
            bool(self.request.user.first_name and self.request.user.last_name),
            bool(self.request.user.email),
            bool(self.request.user.phone_number),
            bool(self.request.user.business_name),
            bool(self.request.user.business_card_front),
            bool(self.request.user.address),
            bool(handyman.detailed_services_description),
            bool(services),
        ]
        profile_completion = int((sum(completion_items) / len(completion_items)) * 100)

        # Get address data using the utility function
        address_data = get_user_profile_data(self.request.user)

        context.update(
            {
                "handyman": handyman,
                "total_services": total_services,
                "active_promotions": active_promotions,
                "active_promotions_list": active_promotions_list,
                "all_promotions_list": all_promotions_list,
                "profile_completion": profile_completion,
                "selected_categories": selected_categories,
                "service_description": service_description,
                "address_number": address_data["address_number"],
                "address_street": address_data["address_street"],
            }
        )

        return context


class HandymanMainView(TemplateView):
    """
    Display the handyman main landing page
    """

    template_name = "handyman/handyman_main.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        featured_handymen = Handyman.objects.filter(user__is_active=True).order_by("?")[
            :6
        ]

        service_categories = Service.objects.all().distinct()[:10]

        context.update(
            {
                "featured_handymen": featured_handymen,
                "service_categories": service_categories,
            }
        )

        return context

    def post(self, request, *args, **kwargs):
        """Handle search form submission"""
        country = request.POST.get("country", "")
        state = request.POST.get("state", "")
        city = request.POST.get("city", "")
        service_description = request.POST.get("service_description", "")

        handymen = Handyman.objects.filter(user__is_active=True)

        location_filters = Q()
        if country:
            location_filters &= Q(user__address__country=country)
        if state:
            location_filters &= Q(user__address__state=state)
        if city:
            location_filters &= Q(user__address__city=city)

        if location_filters:
            handymen = handymen.filter(location_filters)

        if service_description:
            service_filters = (
                Q(detailed_services_description__icontains=service_description)
                | Q(user__service_description__icontains=service_description)
                | Q(services__service__name__icontains=service_description)
            )
            handymen = handymen.filter(service_filters).distinct()

        context = self.get_context_data(**kwargs)
        context["search_results"] = handymen
        context["search_query"] = {
            "country": country,
            "state": state,
            "city": city,
            "service_description": service_description,
        }

        return render(request, self.template_name, context)


class HandymanBusinessCardUpdateView(LoginRequiredMixin, PaymentRequiredMixin, FormView):
    """
    View for updating handyman business card images
    """

    template_name = "handyman/handyman_dashboard.html"
    form_class = BusinessCardUpdateForm
    success_url = reverse_lazy("handyman_dashboard")

    def form_valid(self, form):
        user = self.request.user
        files = self.request.FILES
        data = form.cleaned_data

        card_updated = False

        if "card_front" in files:
            user.business_card_front = files["card_front"]
            card_updated = True

        if "card_back" in files:
            user.business_card_back = files["card_back"]
            user.has_blank_card_back = False
            card_updated = True
        elif data.get("blank_back"):
            user.has_blank_card_back = True
            if user.business_card_back:
                user.business_card_back = None
                card_updated = True

        # Set status to pending_review only when cards are updated
        if card_updated:
            user.business_card_status = "pending_review"
        # If user has a business card but no status, ensure it has a status
        elif user.business_card_front and user.business_card_status is None:
            user.business_card_status = None

        user.save()

        is_ajax = self.request.headers.get("X-Requested-With") == "XMLHttpRequest"

        if is_ajax:
            return JsonResponse(
                {
                    "status": "success",
                    "message": "Your business card has been updated successfully!",
                }
            )
        else:
            messages.success(
                self.request, "Your business card has been updated successfully!"
            )
            return redirect(self.success_url)

    def form_invalid(self, form):
        is_ajax = self.request.headers.get("X-Requested-With") == "XMLHttpRequest"

        if is_ajax:
            errors = {field: error for field, error in form.errors.items()}
            return JsonResponse(
                {
                    "status": "error",
                    "message": "Please fix the form errors.",
                    "errors": errors,
                }
            )
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(self.request, f"{field}: {error}")
            return redirect(self.success_url)


class HandymanProfileUpdateFormView(LoginRequiredMixin, PaymentRequiredMixin, View):
    """
    View for handling the personal details form submission in the dashboard
    """

    success_url = reverse_lazy("handyman_dashboard")

    def post(self, request, *args, **kwargs):
        """Handle POST request with form data"""
        user = request.user
        data = request.POST
        files = request.FILES
        errors = {}

        required_fields = ["first_name", "last_name", "phone_number", "business_name"]
        for field in required_fields:
            if not data.get(field):
                errors[field] = f"{field.replace('_', ' ').title()} is required."

        if errors:
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse(
                    {
                        "status": "error",
                        "message": "Please fix the form errors.",
                        "errors": errors,
                    }
                )
            else:
                for field, error in errors.items():
                    messages.error(request, error)
                return redirect(self.success_url)

        try:
            handyman = Handyman.objects.get(user=user)
        except Handyman.DoesNotExist:
            handyman = Handyman.objects.create(
                user=user, business_name=user.business_name or user.get_full_name()
            )

        user.first_name = data.get("first_name")
        user.last_name = data.get("last_name")
        user.phone_number = data.get("phone_number")
        user.business_name = data.get("business_name")
        user.website = data.get("website")

        address_number = data.get("address_number", "")
        address_street = data.get("address_street", "")
        if address_number and address_street:
            street_address = f"{address_number} {address_street}"

            if user.address:
                address = user.address
                address.street = street_address
                address.city = data.get("city")
                address.state = data.get("state")
                address.postal_code = data.get("zip")
                address.country = data.get("country")
                address.save()
            else:
                address = Address.objects.create(
                    street=street_address,
                    city=data.get("city"),
                    state=data.get("state"),
                    postal_code=data.get("zip"),
                    country=data.get("country"),
                )
                user.address = address

        user.save()

        handyman.business_name = data.get("business_name")

        if data.get("bio"):
            handyman.bio = data.get("bio")
        if data.get("detailed_services_description"):
            handyman.detailed_services_description = data.get(
                "detailed_services_description"
            )
        if data.get("experience_years"):
            try:
                handyman.experience_years = int(data.get("experience_years"))
            except (ValueError, TypeError):
                pass
        if data.get("license_number"):
            handyman.license_number = data.get("license_number")

        handyman.is_insured = data.get("is_insured") == "on"
        handyman.is_licensed = data.get("is_licensed") == "on"

        handyman.save()

        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse(
                {
                    "status": "success",
                    "message": "Your profile has been updated successfully!",
                }
            )
        else:
            messages.success(request, "Your profile has been updated successfully!")
            return redirect(self.success_url)


class HandymanServicesUpdateView(LoginRequiredMixin, PaymentRequiredMixin, FormView):
    """
    View for updating handyman services categories and description
    """

    template_name = "handyman/handyman_dashboard.html"
    form_class = HandymanServicesForm
    success_url = reverse_lazy("handyman_dashboard")

    def get_initial(self):
        initial = super().get_initial()
        user = self.request.user

        try:
            handyman = Handyman.objects.get(user=user)
            services = HandymanService.objects.filter(handyman=handyman)
            service_categories = [service.service.name for service in services]

            initial.update(
                {
                    "service_description": handyman.detailed_services_description
                    or user.service_description
                    or "",
                    "service_categories": service_categories,
                }
            )

        except Handyman.DoesNotExist:
            pass

        return initial

    def form_valid(self, form):
        user = self.request.user
        data = form.cleaned_data

        try:
            handyman = Handyman.objects.get(user=user)
        except Handyman.DoesNotExist:
            handyman = Handyman.objects.create(
                user=user, business_name=user.business_name or user.get_full_name()
            )

        service_description = data.get("service_description")
        user.service_description = service_description
        handyman.detailed_services_description = service_description

        user.save()
        handyman.save()

        # Delete existing services
        HandymanService.objects.filter(handyman=handyman).delete()

        # Add new services
        service_categories = data.get("service_categories", [])
        if not service_categories:
            is_ajax = self.request.headers.get("X-Requested-With") == "XMLHttpRequest"
            error_msg = "Please select at least one service category."
            if is_ajax:
                return JsonResponse(
                    {
                        "status": "error",
                        "message": error_msg,
                        "errors": {"service_categories": error_msg},
                    }
                )
            else:
                messages.error(self.request, error_msg)
                return redirect(self.success_url)

        for category_name in service_categories:
            # Try to find service by case-insensitive name comparison first
            try:
                service = Service.objects.get(name__iexact=category_name)
            except Service.DoesNotExist:
                # Create with a unique slug
                base_slug = slugify(category_name)
                slug = base_slug
                counter = 1

                # Check if slug exists and make it unique by appending a counter
                while Service.objects.filter(slug=slug).exists():
                    slug = f"{base_slug}-{counter}"
                    counter += 1

                service = Service.objects.create(
                    name=category_name,
                    slug=slug,
                    description=f"Services related to {category_name}",
                )

            # Create the handyman service relationship
            HandymanService.objects.create(handyman=handyman, service=service)

        is_ajax = self.request.headers.get("X-Requested-With") == "XMLHttpRequest"

        if is_ajax:
            return JsonResponse(
                {
                    "status": "success",
                    "message": "Your services have been updated successfully!",
                    "total_services": len(service_categories),
                }
            )
        else:
            messages.success(
                self.request, "Your services have been updated successfully!"
            )
            return redirect(self.success_url)

    def form_invalid(self, form):
        is_ajax = self.request.headers.get("X-Requested-With") == "XMLHttpRequest"

        if is_ajax:
            errors = {}
            for field, error_list in form.errors.items():
                errors[field] = [str(error) for error in error_list]

            return JsonResponse(
                {
                    "status": "error",
                    "message": "Please fix the form errors.",
                    "errors": errors,
                },
                status=400,
            )
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(self.request, f"{field}: {error}")
            return redirect(self.success_url)


class HandymanPromotionCreateView(LoginRequiredMixin, PaymentRequiredMixin, FormView):
    """
    View for creating handyman promotional offers
    """

    template_name = "handyman/handyman_dashboard.html"
    form_class = HandymanPromotionForm
    success_url = reverse_lazy("handyman_dashboard")

    def form_valid(self, form):
        user = self.request.user
        data = form.cleaned_data

        run_campaign = data.get("run_campaign")

        if not run_campaign:
            if self.request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse(
                    {"status": "success", "message": "Promotion settings saved."}
                )
            else:
                messages.info(
                    self.request, "You've chosen not to run a promotional campaign."
                )
                return redirect(self.success_url)

        try:
            handyman = Handyman.objects.get(user=user)
        except Handyman.DoesNotExist:
            handyman = Handyman.objects.create(
                user=user, business_name=user.business_name or user.get_full_name()
            )

        handyman.offers_promotions = True
        handyman.save()

        discount_percentage = data.get("discount_percentage", 0)

        promotion = HandymanPromotion.objects.create(
            handyman=handyman,
            description=data.get("discount_description"),
            discount_percentage=discount_percentage,
            code=data.get("promo_code"),
            start_date=data.get("start_date"),
            end_date=data.get("stop_date"),
            is_active=True,
        )

        if self.request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse(
                {
                    "status": "success",
                    "message": "Your promotional campaign has been created successfully!",
                }
            )
        else:
            messages.success(
                self.request, "Your promotional campaign has been created successfully!"
            )
            return redirect(self.success_url)

    def form_invalid(self, form):
        is_ajax = self.request.headers.get("X-Requested-With") == "XMLHttpRequest"

        if is_ajax:
            errors = {field: error for field, error in form.errors.items()}
            return JsonResponse(
                {
                    "status": "error",
                    "message": "Please fix the form errors.",
                    "errors": errors,
                }
            )
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(self.request, f"{field}: {error}")
            return redirect(self.success_url)


class HandymanJobRequestsView(LoginRequiredMixin, PaymentRequiredMixin, View):
    """
    View for handling handyman job requests
    Returns job requests for the authenticated handyman via AJAX
    """

    def get(self, request, *args, **kwargs):
        """Handle GET request to retrieve job requests"""
        user = request.user

        try:
            handyman = Handyman.objects.get(user=user)
        except Handyman.DoesNotExist:
            return JsonResponse({"jobs": []})

        job_requests = JobRequest.objects.filter(handyman=handyman).order_by(
            "-created_at"
        )

        jobs_data = []
        for job in job_requests:
            job_data = {
                "id": job.id,
                "service_name": job.service_name,
                "client_name": (
                    f"{job.client.first_name} {job.client.last_name}"
                    if job.client
                    else "Anonymous"
                ),
                "scheduled_date": (
                    job.scheduled_date.strftime("%Y-%m-%d")
                    if job.scheduled_date
                    else None
                ),
                "scheduled_time": (
                    job.scheduled_time.strftime("%H:%M") if job.scheduled_time else None
                ),
                "address": str(job.address) if job.address else "No address provided",
                "description": job.description,
                "status": job.status,
                "created_at": job.created_at.strftime("%Y-%m-%d %H:%M"),
            }
            jobs_data.append(job_data)

        return JsonResponse({"jobs": jobs_data})

    def post(self, request, *args, **kwargs):
        """Handle POST request to update job request status"""
        user = request.user
        form = JobRequestUpdateForm(request.POST)

        if not form.is_valid():
            return JsonResponse(
                {
                    "status": "error",
                    "message": "Invalid form data",
                    "errors": form.errors,
                }
            )

        data = form.cleaned_data
        job_id = data.get("job_id")
        action = data.get("action")

        test_mode = request.POST.get("test_mode", "false").lower() == "true"

        if test_mode:
            valid_actions = ["accept", "decline", "complete"]
            if action not in valid_actions:
                return JsonResponse(
                    {"status": "error", "message": f"Invalid action: {action}"}
                )

            action_messages = {
                "accept": "Job request accepted",
                "decline": "Job request declined",
                "complete": "Job marked as completed",
            }

            return JsonResponse(
                {
                    "status": "success",
                    "message": action_messages.get(
                        action, "Status updated successfully"
                    ),
                }
            )

        try:
            handyman = Handyman.objects.get(user=user)
            job = JobRequest.objects.get(id=job_id, handyman=handyman)

            if action == "accept":
                job.status = "accepted"
                message = "Job request accepted"
            elif action == "decline":
                job.status = "declined"
                message = "Job request declined"
            elif action == "complete":
                job.status = "completed"
                job.completed_at = timezone.now()
                message = "Job marked as completed"
            else:
                return JsonResponse(
                    {"status": "error", "message": f"Invalid action: {action}"}
                )

            job.save()

            return JsonResponse({"status": "success", "message": message})

        except Handyman.DoesNotExist:
            return JsonResponse(
                {"status": "error", "message": "Handyman profile not found"}
            )
        except JobRequest.DoesNotExist:
            return JsonResponse({"status": "error", "message": "Job request not found"})
        except Exception as e:
            return JsonResponse(
                {"status": "error", "message": f"Error updating job status: {str(e)}"}
            )


class HandymanServicesTabView(LoginRequiredMixin, PaymentRequiredMixin, View):
    """
    View for handling AJAX loading of the services tab in dashboard
    """

    def get(self, request, *args, **kwargs):
        """Handle GET request to load services data"""
        user = request.user

        try:
            handyman = Handyman.objects.get(user=user)
        except Handyman.DoesNotExist:
            handyman = Handyman.objects.create(
                user=user, business_name=user.business_name or user.get_full_name()
            )

        services = HandymanService.objects.filter(handyman=handyman)

        selected_categories = []
        if services.exists():
            # Store both the actual name and lowercase version
            selected_categories_data = [
                {"name": service.service.name, "lower": service.service.name.lower()}
                for service in services
            ]
            # For JSON response, just send the names
            selected_categories = [item["name"] for item in selected_categories_data]

        service_description = (
            handyman.detailed_services_description or user.service_description or ""
        )

        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse(
                {
                    "status": "success",
                    "selected_categories": selected_categories,
                    "service_description": service_description,
                    "total_services": services.count(),
                },
                content_type="application/json",
            )

        return redirect(f"{reverse_lazy('handyman_dashboard')}#services")


class ClientJobRequestCreateView(LoginRequiredMixin, FormView):
    """
    View for handling job requests from clients to handymen
    """

    form_class = JobRequestForm
    success_url = reverse_lazy("handyman_main")
    template_name = "handyman/handyman_job_request.html"  # You might need to create this template or use a different one

    def form_valid(self, form):
        user = self.request.user
        data = form.cleaned_data

        try:
            handyman = Handyman.objects.get(id=data.get("handyman_id"))
            service = Service.objects.get(id=data.get("service_id"))

            address_data = {
                "street": f"{data.get('address_number')} {data.get('address_street')}",
                "city": data.get("address_city", ""),
                "state": data.get("address_state", ""),
                "postal_code": data.get("address_zip", ""),
                "country": data.get("address_country", "USA"),
            }

            # Create a new address or use the user's address
            if user.address and not all(address_data.values()):
                address = user.address
            else:
                address = Address.objects.create(**address_data)

            promotion = None
            promo_code = data.get("promo_code")
            if promo_code:
                try:
                    promotion = HandymanPromotion.objects.get(
                        handyman=handyman,
                        code=promo_code,
                        is_active=True,
                        start_date__lte=timezone.now().date(),
                        end_date__gte=timezone.now().date(),
                    )
                except HandymanPromotion.DoesNotExist:
                    pass

            job = JobRequest.objects.create(
                handyman=handyman,
                client=user,
                service=service,
                address=address,
                description=data.get("description"),
                scheduled_date=data.get("scheduled_date"),
                scheduled_time=data.get("scheduled_time"),
                status="pending",
                promotion_applied=promotion,
            )

            success_message = "Your job request has been sent to the handyman!"
            if self.request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse(
                    {"status": "success", "message": success_message, "job_id": job.id}
                )
            else:
                messages.success(self.request, success_message)
                return redirect(self.request.META.get("HTTP_REFERER", "/"))

        except Handyman.DoesNotExist:
            error_message = "Handyman not found"
            if self.request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse({"status": "error", "message": error_message})
            else:
                messages.error(self.request, error_message)
                return redirect(self.request.META.get("HTTP_REFERER", "/"))

        except Service.DoesNotExist:
            error_message = "Service not found"
            if self.request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse({"status": "error", "message": error_message})
            else:
                messages.error(self.request, error_message)
                return redirect(self.request.META.get("HTTP_REFERER", "/"))

        except Exception as e:
            error_message = f"Error creating job request: {str(e)}"
            if self.request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse({"status": "error", "message": error_message})
            else:
                messages.error(self.request, error_message)
                return redirect(self.request.META.get("HTTP_REFERER", "/"))

    def form_invalid(self, form):
        is_ajax = self.request.headers.get("X-Requested-With") == "XMLHttpRequest"

        if is_ajax:
            errors = {field: error for field, error in form.errors.items()}
            return JsonResponse(
                {
                    "status": "error",
                    "message": "Please fix the form errors.",
                    "errors": errors,
                }
            )
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(self.request, f"{field}: {error}")
            return redirect(self.request.META.get("HTTP_REFERER", "/"))


class HandymanTogglePromotionView(LoginRequiredMixin, PaymentRequiredMixin, View):
    """
    View for toggling the active status of a promotion
    """

    success_url = reverse_lazy("handyman_dashboard")

    def post(self, request, *args, **kwargs):
        """Handle POST request to toggle promotion status"""
        user = request.user
        data = request.POST

        promotion_id = data.get("promotion_id")
        action = data.get("action")

        if not promotion_id or not action:
            messages.error(request, "Missing required information.")
            return redirect(self.success_url + "#promotions")

        try:
            handyman = Handyman.objects.get(user=user)

            from .models import HandymanPromotion

            promotion = HandymanPromotion.objects.get(
                id=promotion_id, handyman=handyman
            )

            if action == "activate":
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
            messages.error(
                request,
                "Promotion not found or you don't have permission to modify it.",
            )
        except Exception as e:
            messages.error(request, f"Error updating promotion: {str(e)}")

        return redirect(self.success_url + "#promotions")


class HandymanJobsTabView(LoginRequiredMixin, PaymentRequiredMixin, TemplateView):
    """
    View for displaying and handling job requests in the dashboard
    """

    template_name = "handyman/handyman_dashboard_jobs.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        try:
            handyman = Handyman.objects.get(user=user)
        except Handyman.DoesNotExist:
            context["jobs"] = []
            context["pending_count"] = 0
            return context

        from .models import JobRequest

        job_requests = JobRequest.objects.filter(handyman=handyman).order_by(
            "-created_at"
        )

        jobs = []
        for job in job_requests:
            job_data = {
                "id": job.id,
                "service_name": job.service_name,
                "client_name": (
                    f"{job.client.first_name} {job.client.last_name}"
                    if job.client
                    else "Anonymous"
                ),
                "scheduled_date": (
                    job.scheduled_date.strftime("%Y-%m-%d")
                    if job.scheduled_date
                    else None
                ),
                "scheduled_time": (
                    job.scheduled_time.strftime("%H:%M") if job.scheduled_time else None
                ),
                "address": str(job.address) if job.address else "No address provided",
                "description": job.description,
                "status": job.status,
                "created_at": job.created_at.strftime("%Y-%m-%d %H:%M"),
            }
            jobs.append(job_data)

        pending_count = sum(1 for job in jobs if job["status"] == "pending")

        context["jobs"] = jobs
        context["pending_count"] = pending_count
        return context


class HandymanPaymentView(View):
    """
    View for handling Helcium payments for handyman account activation
    """
    template_name = "handyman/handyman_payment.html"
    
    def get(self, request, *args, **kwargs):
        """Display the payment form"""
        if request.user.is_anonymous:
            messages.error(request, "You must be logged in to access this page.")
            return redirect('login')
            
        if request.user.user_type != 'handyman':
            messages.error(request, "This page is only for handyman accounts.")
            return redirect('login')
        
        # Check if user already has a subscription
        if check_handyman_payment_status(request.user):
            messages.info(request, "You already have an active subscription.")
            return redirect('handyman_dashboard')
        
        # Get subscription plans for handymen
        from users.models import SubscriptionPlan, UserType
        
        plans = SubscriptionPlan.objects.filter(
            user_type=UserType.HANDYMAN,
            is_active=True
        ).order_by('monthly_fee')
        
        # If no plans exist, create a default one
        if not plans.exists():
            default_plan = SubscriptionPlan.objects.create(
                name="Handyman Basic Plan",
                user_type=UserType.HANDYMAN,
                setup_fee=25.00,
                monthly_fee=19.99,
                description="Access to all handyman features and dashboard",
                is_active=True
            )
            plans = [default_plan]
        
        context = {
            'plans': plans,
            'user': request.user,
        }
        
        return render(request, self.template_name, context)
    
    def post(self, request, *args, **kwargs):
        """Process the payment submission"""
        if request.user.is_anonymous:
            messages.error(request, "You must be logged in to make a payment.")
            return redirect('login')
            
        if request.user.user_type != 'handyman':
            messages.error(request, "This payment option is only for handyman accounts.")
            return redirect('login')
        
        # Extract payment information
        plan_id = request.POST.get('plan_id')
        card_number = request.POST.get('card_number')
        card_expiry = request.POST.get('card_expiry')
        card_cvv = request.POST.get('card_cvv')
        
        # Basic validation
        if not all([plan_id, card_number, card_expiry, card_cvv]):
            messages.error(request, "Please provide all required payment information.")
            return redirect('handyman_payment')
        
        # Get the plan
        from users.models import SubscriptionPlan
        
        try:
            plan = SubscriptionPlan.objects.get(id=plan_id, is_active=True)
        except SubscriptionPlan.DoesNotExist:
            messages.error(request, "Selected plan is not available.")
            return redirect('handyman_payment')
        
        # Calculate amount (setup fee + first month)
        amount = plan.setup_fee + plan.monthly_fee
        
        # Create card info object
        card_info = {
            'number': card_number,
            'expiry': card_expiry,
            'cvv': card_cvv
        }
        
        # Process the payment
        from users.utils import process_helcium_payment
        
        success, transaction_id, error_message = process_helcium_payment(
            user=request.user,
            amount=amount,
            payment_method='credit_card',
            card_info=card_info
        )
        
        if success:
            messages.success(
                request, 
                f"Payment successful! Your handyman account is now active. Transaction ID: {transaction_id}"
            )
            return redirect('handyman_dashboard')
        else:
            messages.error(
                request, 
                f"Payment failed: {error_message or 'Unknown error occurred.'}"
            )
            return redirect('handyman_payment')
