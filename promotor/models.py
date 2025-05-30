from django.db import models
from django.conf import settings
import uuid
import string
import random

from core.models import TimeStampedModel
from businesses.models import Business


def generate_promo_code(length=8):
    """Generate a unique promotional code"""
    chars = string.ascii_uppercase + string.digits
    return "BD-" + "".join(random.choice(chars) for _ in range(length))


class Plan(TimeStampedModel):
    """
    Subscription plans for business promotion
    """

    name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration_days = models.PositiveIntegerField()
    featured_listing = models.BooleanField(default=False)
    priority_search = models.BooleanField(default=False)
    max_images = models.PositiveIntegerField(default=5)

    def __str__(self):
        return self.name


class Subscription(TimeStampedModel):
    """
    Business subscriptions to promotion plans
    """

    STATUS_CHOICES = (
        ("active", "Active"),
        ("expired", "Expired"),
        ("cancelled", "Cancelled"),
    )

    business = models.ForeignKey(
        Business, on_delete=models.CASCADE, related_name="subscriptions"
    )
    plan = models.ForeignKey(
        Plan, on_delete=models.CASCADE, related_name="subscriptions"
    )
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    auto_renew = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.business.name} - {self.plan.name}"


class PromotionalOffer(TimeStampedModel):
    """
    Special promotional offers with discount information
    """

    business = models.ForeignKey(
        Business, on_delete=models.CASCADE, related_name="promotional_offers"
    )
    title = models.CharField(max_length=200)
    description = models.TextField()
    code = models.CharField(max_length=20, unique=True, default=generate_promo_code)
    discount_percentage = models.PositiveIntegerField(
        choices=[
            (i, f"{i}%")
            for i in (
                3,
                5,
                10,
                15,
                20,
                25,
                30,
                35,
                40,
                45,
                50,
                55,
                60,
                65,
                70,
                75,
                80,
                85,
                90,
                100,
            )
        ]
    )
    start_date = models.DateField()
    end_date = models.DateField()
    categories = models.ManyToManyField(
        "core.Category", related_name="promotional_offers"
    )
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.title} ({self.business.name})"


class PromotionalNotification(TimeStampedModel):
    """
    Tracks promotional notifications sent to consumers
    """

    offer = models.ForeignKey(
        PromotionalOffer, on_delete=models.CASCADE, related_name="notifications"
    )
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="received_promotions",
    )
    sent_at = models.DateTimeField(auto_now_add=True)
    opened = models.BooleanField(default=False)

    def __str__(self):
        return f"Notification to {self.recipient.email} for {self.offer.title}"


class Promotion(TimeStampedModel):
    """
    Special promotions for businesses
    """

    TYPE_CHOICES = (
        ("banner", "Banner Ad"),
        ("featured", "Featured Listing"),
        ("popup", "Popup Promotion"),
        ("email", "Email Campaign"),
    )

    business = models.ForeignKey(
        Business, on_delete=models.CASCADE, related_name="promotions"
    )
    title = models.CharField(max_length=200)
    description = models.TextField()
    promo_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    start_date = models.DateField()
    end_date = models.DateField()
    image = models.ImageField(upload_to="promotions/", blank=True, null=True)
    link = models.URLField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    budget = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.title} ({self.business.name})"


class PromotionClick(TimeStampedModel):
    """
    Tracks clicks on promotions
    """

    promotion = models.ForeignKey(
        Promotion, on_delete=models.CASCADE, related_name="clicks"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True, null=True)
    referrer = models.URLField(blank=True, null=True)

    def __str__(self):
        return f"Click on {self.promotion.title}"


class Coupon(TimeStampedModel):
    """
    Discount coupons for businesses
    """

    business = models.ForeignKey(
        Business, on_delete=models.CASCADE, related_name="coupons"
    )
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField()
    discount_percentage = models.PositiveIntegerField(null=True, blank=True)
    discount_amount = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    start_date = models.DateField()
    end_date = models.DateField()
    max_uses = models.PositiveIntegerField(null=True, blank=True)
    current_uses = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.code} - {self.business.name}"
