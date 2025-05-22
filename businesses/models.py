from django.db import models
from django.utils.text import slugify
from django.conf import settings

from core.models import TimeStampedModel, Address, Category


class Business(TimeStampedModel):
    """
    Model for business listings
    """
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='businesses')
    description = models.TextField()
    categories = models.ManyToManyField(Category, related_name='businesses')
    address = models.ForeignKey(Address, on_delete=models.CASCADE, related_name='businesses')
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    website = models.URLField(blank=True, null=True)
    logo = models.ImageField(upload_to='business_logos/', blank=True, null=True)
    featured = models.BooleanField(default=False)
    verified = models.BooleanField(default=False)
    
    class Meta:
        verbose_name_plural = "Businesses"
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class BusinessHours(models.Model):
    """
    Model for business operating hours
    """
    DAYS_OF_WEEK = (
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    )
    
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='business_hours')
    day = models.IntegerField(choices=DAYS_OF_WEEK)
    opening_time = models.TimeField()
    closing_time = models.TimeField()
    is_closed = models.BooleanField(default=False)
    
    class Meta:
        verbose_name_plural = "Business Hours"
        ordering = ['day']
        unique_together = ['business', 'day']
    
    def __str__(self):
        return f"{self.business.name} - {self.get_day_display()}"


class BusinessCard(TimeStampedModel):
    """
    Model for business card images (front and back)
    """
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='business_cards')
    front_image = models.ImageField(upload_to='business_cards/front/')
    back_image = models.ImageField(upload_to='business_cards/back/', blank=True, null=True)
    back_is_blank = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Business Card for {self.business.name}"


class BusinessImage(TimeStampedModel):
    """
    Model for business photos
    """
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='business_images/')
    caption = models.CharField(max_length=255, blank=True)
    is_primary = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Image for {self.business.name}"


class Review(TimeStampedModel):
    """
    Model for business reviews
    """
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reviews')
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField()
    
    class Meta:
        unique_together = ['business', 'user']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Review by {self.user.email} for {self.business.name}"
