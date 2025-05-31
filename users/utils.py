from django.conf import settings
from django.core.mail import send_mail
from django.urls import reverse
from django.contrib.auth import login, logout
from django.shortcuts import redirect
from .models import User, UserType


def send_login_email(request, user, user_type=None):
    """
    Send a login email with a magic link to the user.

    Args:
        request: The HTTP request object
        user: The user object to send the email to
        user_type: Optional string to customize the email based on user type

    Returns:
        The login URL that was sent to the user
    """
    # Generate login token
    token = user.generate_login_token()
    login_url = request.build_absolute_uri(reverse("magic_link_login", args=[token]))

    # Determine user type for email customization
    user_type_display = user_type or user.get_user_type_display() or "User"

    # Create email subject and message
    email_subject = f"Welcome to Business Directory - Your Login Link"

    email_message = f"""
Hello {user.first_name},

Thank you for registering with Business Directory{f" as a {user_type_display}" if user_type else ""}!

Click the link below to access your dashboard:
{login_url}

This link will expire in 24 hours.

Thank you,
Business Directory Team
"""

    # For development, print the link to console
    print("\n" + "=" * 80)
    print(f"MAGIC LOGIN LINK GENERATED")
    print(f"User Type: {user_type_display}")
    print(f"Email: {user.email}")
    print(f"URL: {login_url}")
    print("Copy and paste this URL into your browser to login")
    print("=" * 80 + "\n")

    # Send the email (currently configured to output to console)
    send_mail(
        email_subject,
        email_message,
        settings.DEFAULT_FROM_EMAIL or "noreply@businessdirectory.com",
        [user.email],
        fail_silently=False,
    )

    return login_url


def process_login_token(request, token):
    """
    Process a login token from a magic link.

    Args:
        request: The HTTP request object
        token: The token to verify

    Returns:
        (success, redirect_url, error_message)
    """
    try:
        user = User.objects.get(login_token=token)

        if not user.is_token_valid():
            return False, "/", "This login link has expired. Please request a new one."

        # Log the user in
        login(request, user)

        # Clear the token after use
        user.clear_token()

        # Determine the appropriate dashboard URL based on user type and payment status
        redirect_url = get_redirect_url_after_login(user)
        
        return True, redirect_url, None

    except User.DoesNotExist:
        return False, "/", "Invalid login link. Please request a new one."
    except Exception as e:
        return False, "/", f"An error occurred: {str(e)}"


def process_logout(request):
    """
    Process user logout and determine redirect URL.

    Args:
        request: The HTTP request object

    Returns:
        redirect_url: URL to redirect to after logout
    """
    # Perform logout
    logout(request)

    # Return home URL
    return "/"


def process_helcium_payment(user, amount, payment_method, card_info=None):
    """
    Process a payment through Helcium API.
    
    Args:
        user: The user making the payment
        amount: Payment amount as decimal
        payment_method: The payment method (credit_card, bank_account, etc.)
        card_info: Dictionary with card information if using credit_card method
        
    Returns:
        (success, transaction_id, error_message)
    """
    # This is a placeholder implementation. You should implement the actual
    # Helcium API integration here using their documentation.
    
    # For development/testing purposes, we'll simulate a successful payment
    try:
        # In production, replace this with actual Helcium API call
        # Example structure of what you might need to implement:
        '''
        import requests
        
        helcium_url = "https://api.helcim.com/v2/payment"
        headers = {
            "Authorization": f"Bearer {settings.HELCIUM_API_KEY}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "amount": str(amount),
            "currency": "USD",
            "payment_method": payment_method,
            "card_info": card_info,
            "customer": {
                "email": user.email,
                "name": f"{user.first_name} {user.last_name}",
            }
        }
        
        response = requests.post(helcium_url, json=payload, headers=headers)
        if response.status_code == 200:
            data = response.json()
            return True, data.get("transaction_id"), None
        else:
            return False, None, f"Payment failed: {response.text}"
        '''
        
        # Simulated successful payment
        import uuid
        transaction_id = f"sim-{uuid.uuid4().hex[:12]}"
        
        # Create a subscription for the user if they don't have one
        from .models import SubscriptionPlan, Subscription, Payment
        
        # Find appropriate subscription plan for user type
        plan = SubscriptionPlan.objects.filter(
            user_type=user.user_type,
            is_active=True
        ).first()
        
        if not plan:
            # Create a default plan if none exists
            plan = SubscriptionPlan.objects.create(
                name=f"Default {user.get_user_type_display()} Plan",
                user_type=user.user_type,
                setup_fee=0.00,
                monthly_fee=float(amount),
                description="Default subscription plan",
                is_active=True
            )
        
        # Create or update subscription
        subscription, created = Subscription.objects.get_or_create(
            user=user,
            defaults={
                'plan': plan,
                'is_active': True,
                'auto_renew': True,
                'is_free': False
            }
        )
        
        if not created:
            subscription.is_active = True
            subscription.plan = plan
            subscription.save()
        
        # Record the payment
        payment = Payment.objects.create(
            subscription=subscription,
            amount=amount,
            payment_method=payment_method,
            transaction_id=transaction_id,
            is_setup_fee=True
        )
        
        print(f"[PAYMENT SIMULATION] Processed payment of ${amount} for {user.email} with transaction ID: {transaction_id}")
        
        return True, transaction_id, None
    
    except Exception as e:
        print(f"[PAYMENT ERROR] {str(e)}")
        return False, None, str(e)


def check_handyman_payment_status(user):
    """
    Check if a handyman user has an active subscription from a payment.
    
    Args:
        user: The user to check
        
    Returns:
        Boolean indicating if user has an active paid subscription
    """
    if user.user_type != 'handyman':
        return True  # Non-handyman users don't need to pay
        
    from .models import Subscription
    
    # Check if user has any active subscription
    return Subscription.objects.filter(
        user=user,
        is_active=True,
        is_free=False  # Must be a paid subscription
    ).exists()


def get_redirect_url_after_login(user):
    """
    Determine where to redirect the user after login based on user type
    and payment status.
    
    Args:
        user: The authenticated user
        
    Returns:
        URL to redirect user to
    """
    from django.urls import reverse
    
    if user.user_type == 'handyman':
        # Check if handyman has paid
        if check_handyman_payment_status(user):
            return reverse('handyman_dashboard')
        else:
            # Redirect to payment page
            return reverse('handyman_payment')
    
    elif user.user_type == 'promoter':
        return reverse('promoter_dashboard')
    else:  # Default to consumer/requestor
        return reverse('consumer_dashboard')
