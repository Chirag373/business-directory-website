from django.db import models
from django.utils.text import slugify
from django.conf import settings

from core.models import TimeStampedModel, Address


class Service(TimeStampedModel):
    """
    Model for handyman services
    """
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    description = models.TextField()
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Handyman(TimeStampedModel):
    """
    Model for handyman professionals
    """
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='handyman_profile')
    business_name = models.CharField(max_length=200, blank=True, null=True)
    services = models.ManyToManyField(Service, through='HandymanService', related_name='handymen')
    bio = models.TextField()
    detailed_services_description = models.TextField(
        help_text="Detailed description of your services. Include specific keywords for better search results.",
        blank=True
    )
    experience_years = models.PositiveIntegerField(default=0)
    license_number = models.CharField(max_length=50, blank=True, null=True)
    service_areas = models.ManyToManyField(Address, related_name='handymen')
    is_insured = models.BooleanField(default=False)
    is_licensed = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    offers_promotions = models.BooleanField(default=False, 
                                            help_text="Check if you want to offer promotional discounts")
    
    class Meta:
        verbose_name_plural = "Handymen"
    
    def __str__(self):
        return self.user.get_full_name() or self.user.email


class HandymanService(TimeStampedModel):
    """
    Linking model between Handyman and Service with pricing
    """
    handyman = models.ForeignKey(Handyman, on_delete=models.CASCADE, related_name='handyman_services')
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='handyman_services')
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    flat_rate = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    class Meta:
        unique_together = ['handyman', 'service']
    
    def __str__(self):
        return f"{self.handyman} - {self.service.name}"


class HandymanPromotion(TimeStampedModel):
    """
    Promotional offers for handyman services
    """
    handyman = models.ForeignKey(Handyman, on_delete=models.CASCADE, related_name='promotions')
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='promotions', null=True, blank=True)
    description = models.TextField()
    discount_percentage = models.PositiveIntegerField(
        choices=[(i, f"{i}%") for i in (3, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85, 90, 100)]
    )
    code = models.CharField(max_length=20, unique=True)
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"Promotion by {self.handyman} - {self.discount_percentage}% off"


class HandymanJob(TimeStampedModel):
    """
    Model for handyman job requests
    """
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )
    
    handyman = models.ForeignKey(Handyman, on_delete=models.CASCADE, related_name='jobs')
    client = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='handyman_requests')
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='jobs')
    address = models.ForeignKey(Address, on_delete=models.CASCADE)
    description = models.TextField()
    scheduled_date = models.DateField()
    scheduled_time = models.TimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    estimated_hours = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    promotion_applied = models.ForeignKey(HandymanPromotion, on_delete=models.SET_NULL, null=True, blank=True, related_name='jobs')
    
    def __str__(self):
        return f"Job #{self.id}: {self.service.name} for {self.client.get_full_name() or self.client.email}"


class PromotionNotification(TimeStampedModel):
    """
    Tracks handyman promotion notifications sent to consumers
    """
    promotion = models.ForeignKey(HandymanPromotion, on_delete=models.CASCADE, related_name='notifications')
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='handyman_promotion_notifications')
    sent_at = models.DateTimeField(auto_now_add=True)
    opened = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Notification to {self.recipient.email} for promotion by {self.promotion.handyman}"
