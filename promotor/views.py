from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib import messages
from django.utils import timezone
from django.urls import reverse
from django.core.mail import send_mail
from django.conf import settings
import uuid
from django.contrib.auth.decorators import login_required

from users.models import User, UserType
from core.models import Address, Category
from users.utils import send_login_email
from businesses.models import Business, BusinessCard
from .models import Plan, Subscription, PromotionalOffer


# Create your views here.
def promotor_signup(request):
    if request.method == "POST":
        # Personal Information
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")

        # Business Information
        business_name = request.POST.get("business_name")
        website = request.POST.get("website")

        # Contact Information
        email = request.POST.get("email")
        phone = request.POST.get("phone")

        # Address fields
        street_number = request.POST.get("address_number")
        street_address = request.POST.get("address")
        street = f"{street_number} {street_address}".strip()
        city = request.POST.get("city")
        state = request.POST.get("state")
        country = request.POST.get("country")
        postal_code = request.POST.get("zip")

        # Product Information
        product_description = request.POST.get("product_description")
        product_categories = request.POST.getlist("product_categories")

        # Promotional Offer
        run_promotion = request.POST.get("run_promotion")
        promotion_description = request.POST.get("promotion_description")
        discount_percentage = request.POST.get("discount_percentage")
        promo_code = request.POST.get("promo_code")
        start_date = request.POST.get("start_date")
        end_date = request.POST.get("end_date")

        # Validate required fields
        if not all(
            [
                first_name,
                last_name,
                email,
                phone,
                business_name,
                street,
                city,
                state,
                country,
                postal_code,
                product_description,
            ]
        ):
            messages.error(request, "Please fill in all required fields.")
            return render(request, "promotor/promotor_signup.html")

        # Check if user already exists
        if User.objects.filter(email=email).exists():
            messages.error(request, "A user with that email already exists.")
            return render(request, "promotor/promotor_signup.html")

        try:
            # Handle file uploads for business cards
            card_front = request.FILES.get("card_front")
            card_back = request.FILES.get("card_back")
            blank_back = request.POST.get("blank_back") == "on"

            # Create address
            address = Address.objects.create(
                street=street,
                city=city,
                state=state,
                postal_code=postal_code,
                country=country,
            )

            # Generate a random temporary password
            temp_password = uuid.uuid4().hex[:8]

            # Create user with promoter user type
            user = User.objects.create_user(
                email=email,
                first_name=first_name,
                last_name=last_name,
                phone_number=phone,
                address=address,
                business_name=business_name,
                website=website,
                user_type=UserType.PROMOTER,
                business_card_front=card_front,
                business_card_back=card_back,
                has_blank_card_back=blank_back,
                service_description=product_description,
                password=temp_password,
            )

            # Create business
            business = Business.objects.create(
                name=business_name,
                owner=user,
                description=product_description,
                address=address,
                email=email,
                phone=phone,
                website=website,
            )

            # Create business card
            if card_front:
                BusinessCard.objects.create(
                    business=business,
                    front_image=card_front,
                    back_image=card_back if not blank_back and card_back else None,
                    back_is_blank=blank_back,
                )

            # Add product categories to business
            if product_categories:
                for category_name in product_categories:
                    # Convert underscore to space in category_name for better display
                    display_name = category_name.replace("_", " ").title()
                    category, created = Category.objects.get_or_create(
                        name=display_name, defaults={"slug": category_name}
                    )
                    business.categories.add(category)

            # Try to get the default plan for promoters
            try:
                default_plan = Plan.objects.filter(is_active=True).first()
                if default_plan:
                    # Create a subscription
                    today = timezone.now().date()
                    end_date_subscription = today + timezone.timedelta(
                        days=30
                    )  # Default 30 days

                    Subscription.objects.create(
                        business=business,
                        plan=default_plan,
                        start_date=today,
                        end_date=end_date_subscription,
                        status="active",
                        auto_renew=False,
                    )
            except (Plan.DoesNotExist, Exception):
                # If there's no default plan or an error occurs, just continue without a subscription
                pass

            # Create promotion if selected
            if run_promotion == "on" and discount_percentage:
                try:
                    # Create promotional offer
                    PromotionalOffer.objects.create(
                        business=business,
                        title=f"{business_name} Special Offer",
                        description=promotion_description
                        or f"Special offer: {discount_percentage}% off",
                        code=promo_code or f"PROMO-{uuid.uuid4().hex[:8].upper()}",
                        discount_percentage=int(discount_percentage),
                        start_date=start_date or timezone.now().date(),
                        end_date=end_date
                        or (timezone.now() + timezone.timedelta(days=30)).date(),
                        is_active=True,
                    )
                except Exception:
                    # If there's an error with the promotion, just log it but continue
                    pass

            # Send login email with magic link
            send_login_email(request, user, "Promotor")

            # Add success message
            messages.success(
                request,
                "Your promotor account has been created successfully! Please check your email (or console for now) to get your login link.",
            )

            # Redirect to a "check your email" page
            return render(request, "users/check_email.html", {"email": email, "user_type": "promoter"})

        except Exception as e:
            messages.error(request, f"An error occurred during registration: {str(e)}")
            return render(request, "promotor/promotor_signup.html")

    # For GET requests
    return render(request, "promotor/promotor_signup.html")


@login_required
def promotor_dashboard(request):
    user = request.user

    # If user's token is valid, clear it as they're now logged in
    # This ensures tokens are truly one-time use
    if user.login_token and user.is_token_valid():
        user.clear_token()

    return render(request, "promotor/promotor_dashboard.html")
