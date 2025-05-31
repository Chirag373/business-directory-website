from django.contrib import admin
from django.utils.html import format_html
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (
    User, 
    UserProfile, 
    ConsumerInterest, 
    ServiceCategory, 
    HandymanService, 
    PromotionalOffer,
    PromotionalEmailSent,
    SubscriptionPlan,
    Subscription,
    Payment
)

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'
    fk_name = 'user'

class HandymanServiceInline(admin.StackedInline):
    model = HandymanService
    extra = 0
    verbose_name_plural = 'Handyman Services'
    fk_name = 'user'

class PromotionalOfferInline(admin.TabularInline):
    model = PromotionalOffer
    extra = 0
    verbose_name_plural = 'Promotional Offers'
    fk_name = 'user'

class SubscriptionInline(admin.TabularInline):
    model = Subscription
    extra = 0
    verbose_name_plural = 'Subscriptions'
    fk_name = 'user'

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'phone_number', 'profile_picture', 'address')}),
        ('Business Info', {'fields': ('user_type', 'business_name', 'website', 'service_description',
                                      'business_card_front', 'business_card_back', 'has_blank_card_back',
                                      'business_card_status')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2'),
        }),
    )
    list_display = ('email', 'first_name', 'last_name', 'user_type', 'is_staff', 'card_status')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'user_type', 'business_card_status')
    search_fields = ('email', 'first_name', 'last_name', 'business_name')
    ordering = ('email',)
    inlines = [UserProfileInline, HandymanServiceInline, PromotionalOfferInline, SubscriptionInline]
    
    def card_status(self, obj):
        status_classes = {
            'pending_review': 'status-pending',
            'accepted': 'status-accepted',
            'rejected': 'status-rejected',
        }
        
        if obj.business_card_status:
            css_class = status_classes.get(obj.business_card_status, '')
            label = obj.get_business_card_status_display()
            return format_html('<span class="{}">{}</span>', css_class, label)
        return '-'
    
    card_status.short_description = 'Card Status'

@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)

@admin.register(PromotionalOffer)
class PromotionalOfferAdmin(admin.ModelAdmin):
    list_display = ('code', 'user', 'discount_percentage', 'start_date', 'end_date', 'is_active')
    list_filter = ('is_active', 'discount_percentage', 'start_date', 'end_date')
    search_fields = ('code', 'description', 'user__email', 'user__business_name')
    autocomplete_fields = ['user']
    filter_horizontal = ('categories',)
    
    def get_discount(self, obj):
        return f"{obj.discount_percentage}%"
    get_discount.short_description = 'Discount'

@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'user_type', 'setup_fee', 'monthly_fee', 'is_active')
    list_filter = ('is_active', 'user_type')
    search_fields = ('name', 'description')

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'plan', 'start_date', 'end_date', 'is_active', 'auto_renew')
    list_filter = ('is_active', 'auto_renew', 'is_free', 'start_date')
    search_fields = ('user__email', 'user__business_name')
    autocomplete_fields = ['user', 'plan']

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('subscription', 'amount', 'payment_date', 'payment_method', 'is_setup_fee')
    list_filter = ('payment_date', 'payment_method', 'is_setup_fee')
    search_fields = ('transaction_id', 'subscription__user__email')
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('subscription__user', 'subscription__plan')

@admin.register(PromotionalEmailSent)
class PromotionalEmailSentAdmin(admin.ModelAdmin):
    list_display = ('promotion', 'recipient', 'sent_date')
    list_filter = ('sent_date',)
    search_fields = ('promotion__code', 'recipient__email')
    autocomplete_fields = ['promotion', 'recipient']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('promotion', 'recipient')

@admin.register(ConsumerInterest)
class ConsumerInterestAdmin(admin.ModelAdmin):
    list_display = ('user', 'notification_preference', 'notification_time_period', 'receive_notifications')
    list_filter = ('receive_notifications', 'notification_preference', 'notification_time_period')
    search_fields = ('user__email',)
    autocomplete_fields = ['user']
    filter_horizontal = ('categories',)
