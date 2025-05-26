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
    login_url = request.build_absolute_uri(reverse('magic_link_login', args=[token]))
    
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
    print("\n" + "="*80)
    print(f"MAGIC LOGIN LINK GENERATED")
    print(f"User Type: {user_type_display}")
    print(f"Email: {user.email}")
    print(f"URL: {login_url}")
    print("Copy and paste this URL into your browser to login")
    print("="*80 + "\n")
    
    # Send the email (currently configured to output to console)
    send_mail(
        email_subject,
        email_message,
        settings.DEFAULT_FROM_EMAIL or 'noreply@businessdirectory.com',
        [user.email],
        fail_silently=False,
    )
    
    return login_url

def process_login_token(request, token):
    """
    Process a login token, authenticate the user, and determine redirect URL.
    
    Args:
        request: The HTTP request object
        token: The login token string
    
    Returns:
        tuple: (success, redirect_url, error_message)
            - success: Boolean indicating if login was successful
            - redirect_url: URL to redirect to after processing
            - error_message: Error message if login failed
    """
    try:
        # Find user with this token
        user = User.objects.get(login_token=token)
        
        # Check if token is valid
        if user.is_token_valid():
            # Clear the token (one-time use)
            user.clear_token()
            
            # Log the user in
            login(request, user)
            
            # Determine redirect URL based on user type
            if user.user_type == UserType.REQUESTOR:
                redirect_url = 'consumer_dashboard'
            elif user.user_type == UserType.HANDYMAN:
                redirect_url = 'handyman_dashboard'
            elif user.user_type == UserType.PROMOTER:
                redirect_url = 'promotor_dashboard'
            else:
                # Default redirect
                redirect_url = 'consumer_dashboard'
            
            return True, redirect_url, None
        else:
            return False, 'login', 'This login link has expired. Please request a new one.'
    
    except User.DoesNotExist:
        return False, 'login', 'Invalid login link. Please request a new one.'

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
    return '/' 