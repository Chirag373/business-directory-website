from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _
from core.models import TimeStampedModel, Address
from django.utils import timezone
import uuid
import secrets


class UserManager(BaseUserManager):
    """Define a model manager for User model with no username field."""

    def _create_user(self, email, password=None, **extra_fields):
        """Create and save a User with the given email and password."""
        if not email:
            raise ValueError("The given email must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular User with the given email and password."""
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        """Create and save a SuperUser with the given email and password."""
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(email, password, **extra_fields)


class UserType(models.TextChoices):
    REQUESTOR = "requestor", _("Requestor")
    HANDYMAN = "handyman", _("Handyman")
    PROMOTER = "promoter", _("Promoter")


class User(AbstractUser, TimeStampedModel):
    """Custom User model that uses email as the unique identifier"""

    username = None
    email = models.EmailField(_("email address"), unique=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    profile_picture = models.ImageField(
        upload_to="profile_pictures/", blank=True, null=True
    )
    address = models.ForeignKey(
        Address, on_delete=models.SET_NULL, null=True, blank=True
    )
    user_type = models.CharField(
        max_length=10, choices=UserType.choices, default=UserType.REQUESTOR
    )
    business_name = models.CharField(max_length=255, blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    business_card_front = models.ImageField(
        upload_to="business_cards/", blank=True, null=True
    )
    business_card_back = models.ImageField(
        upload_to="business_cards/", blank=True, null=True
    )
    has_blank_card_back = models.BooleanField(default=False)
    service_description = models.TextField(blank=True, null=True)

    # Business card verification status
    BUSINESS_CARD_STATUS_CHOICES = (
        ("pending_review", "Pending Review"),
        ("accepted", "Accepted"),
        ("rejected", "Rejected"),
    )
    business_card_status = models.CharField(
        max_length=20,
        choices=BUSINESS_CARD_STATUS_CHOICES,
        default="pending_review",
        blank=True,
        null=True,
    )

    # Login token fields for magic link authentication
    login_token = models.CharField(max_length=100, blank=True, null=True)
    token_expiry = models.DateTimeField(blank=True, null=True)

    # Add related_name attributes to fix reverse accessor clashes
    groups = models.ManyToManyField(
        "auth.Group",
        verbose_name=_("groups"),
        blank=True,
        help_text=_(
            "The groups this user belongs to. A user will get all permissions "
            "granted to each of their groups."
        ),
        related_name="custom_user_set",
        related_query_name="user",
    )
    user_permissions = models.ManyToManyField(
        "auth.Permission",
        verbose_name=_("user permissions"),
        blank=True,
        help_text=_("Specific permissions for this user."),
        related_name="custom_user_set",
        related_query_name="user",
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.email

    def generate_login_token(self):
        """Generate a secure login token and set expiry time (24 hours)"""
        self.login_token = secrets.token_urlsafe(32)
        self.token_expiry = timezone.now() + timezone.timedelta(hours=24)
        self.save(update_fields=["login_token", "token_expiry"])
        return self.login_token

    def is_token_valid(self):
        """Check if the current token is valid"""
        if not self.login_token or not self.token_expiry:
            return False
        return timezone.now() < self.token_expiry

    def clear_token(self):
        """Clear the login token after use"""
        self.login_token = None
        self.token_expiry = None
        self.save(update_fields=["login_token", "token_expiry"])


class UserProfile(TimeStampedModel):
    """Extended profile information for users"""

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    bio = models.TextField(blank=True)
    website = models.URLField(blank=True)

    def __str__(self):
        return f"Profile for {self.user.email}"


class ConsumerInterest(TimeStampedModel):
    """Tracks consumer interests for promotional notifications"""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="interests")
    categories = models.ManyToManyField(
        "core.Category", related_name="interested_users"
    )
    receive_notifications = models.BooleanField(default=True)

    # Notification preferences
    NOTIFICATION_PREFERENCES = [
        ("all", "All promotional offers"),
        ("discount", "Only offers above discount threshold"),
        ("categories", "Only offers for selected categories"),
    ]
    notification_preference = models.CharField(
        max_length=15, choices=NOTIFICATION_PREFERENCES, default="all"
    )
    min_discount_threshold = models.IntegerField(default=10)

    # Notification frequency
    TIME_PERIOD_CHOICES = [("day", "Daily"), ("week", "Weekly"), ("month", "Monthly")]
    notification_time_period = models.CharField(
        max_length=10, choices=TIME_PERIOD_CHOICES, default="week"
    )
    notification_limit = models.IntegerField(default=3)

    # Email format
    EMAIL_FORMAT_CHOICES = [
        ("individual", "Individual emails"),
        ("daily", "Daily digest"),
        ("weekly", "Weekly summary"),
    ]
    email_format = models.CharField(
        max_length=15, choices=EMAIL_FORMAT_CHOICES, default="individual"
    )

    def __str__(self):
        return f"Interests for {self.user.email}"


class ServiceCategory(TimeStampedModel):
    """Categories for handyman services"""

    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = "Service Categories"

    def __str__(self):
        return self.name


class HandymanService(TimeStampedModel):
    """Services offered by handymen"""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="services")
    categories = models.ManyToManyField(ServiceCategory, related_name="providers")
    description = models.TextField(help_text="Detailed description of services offered")

    def __str__(self):
        return f"Services by {self.user.email}"


class PromotionalOffer(TimeStampedModel):
    """Promotional offers from businesses/handymen"""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="promotions")
    description = models.TextField()
    code = models.CharField(max_length=20, unique=True)
    discount_percentage = models.IntegerField(
        choices=[
            (3, "3%"),
            (5, "5%"),
            (10, "10%"),
            (15, "15%"),
            (20, "20%"),
            (25, "25%"),
            (30, "30%"),
            (35, "35%"),
            (40, "40%"),
            (45, "45%"),
            (50, "50%"),
            (55, "55%"),
            (60, "60%"),
            (65, "65%"),
            (70, "70%"),
            (75, "75%"),
            (80, "80%"),
            (85, "85%"),
            (90, "90%"),
            (100, "100%"),
        ]
    )
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=True)
    categories = models.ManyToManyField(ServiceCategory, related_name="promotions")

    def __str__(self):
        return f"{self.user.email}'s offer: {self.code}"

    @classmethod
    def generate_promo_code(cls):
        """Generate a unique promotional code"""
        return f"PROMO-{uuid.uuid4().hex[:8].upper()}"


class PromotionalEmailSent(TimeStampedModel):
    """Track promotional emails sent to consumers"""

    promotion = models.ForeignKey(
        PromotionalOffer, on_delete=models.CASCADE, related_name="emails_sent"
    )
    recipient = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="promo_emails_received"
    )
    sent_date = models.DateTimeField(auto_now_add=True)
    matched_categories = models.ManyToManyField(ServiceCategory)

    def __str__(self):
        return f"Promo email to {self.recipient.email} for {self.promotion.code}"


class SubscriptionPlan(TimeStampedModel):
    """Subscription plans for different user types"""

    name = models.CharField(max_length=100)
    user_type = models.CharField(max_length=10, choices=UserType.choices)
    setup_fee = models.DecimalField(max_digits=10, decimal_places=2)
    monthly_fee = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} for {self.get_user_type_display()}"


class Subscription(TimeStampedModel):
    """User subscriptions"""

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="subscriptions"
    )
    plan = models.ForeignKey(
        SubscriptionPlan,
        on_delete=models.SET_NULL,
        null=True,
        related_name="subscribers",
    )
    start_date = models.DateField(auto_now_add=True)
    end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    auto_renew = models.BooleanField(default=False)
    is_free = models.BooleanField(
        default=False, help_text="Admin can grant free subscriptions"
    )

    def __str__(self):
        return f"{self.user.email}'s subscription to {self.plan.name}"


class Payment(TimeStampedModel):
    """Payment records for subscriptions"""

    subscription = models.ForeignKey(
        Subscription, on_delete=models.CASCADE, related_name="payments"
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateTimeField(auto_now_add=True)
    payment_method = models.CharField(max_length=50)
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    is_setup_fee = models.BooleanField(default=False)

    def __str__(self):
        return f"Payment of ${self.amount} for {self.subscription.user.email}"
