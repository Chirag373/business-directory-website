from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Service, 
    Handyman, 
    HandymanService, 
    HandymanPromotion, 
    HandymanJob,
    PromotionNotification
)

class HandymanServiceInline(admin.TabularInline):
    model = HandymanService
    extra = 0
    fields = ('service', 'hourly_rate', 'flat_rate')
    autocomplete_fields = ['service']

class HandymanPromotionInline(admin.TabularInline):
    model = HandymanPromotion
    extra = 0
    fields = ('service', 'discount_percentage', 'code', 'start_date', 'end_date', 'is_active')
    autocomplete_fields = ['service']

class HandymanJobInline(admin.TabularInline):
    model = HandymanJob
    extra = 0
    fields = ('service', 'client', 'scheduled_date', 'status', 'job_link')
    readonly_fields = ('service', 'client', 'scheduled_date', 'status', 'job_link')
    can_delete = False
    max_num = 0
    
    def job_link(self, obj):
        return format_html('<a href="{}" class="button">View Details</a>', 
                          f'/admin/handyman/handymanjob/{obj.id}/change/')
    
    job_link.short_description = 'Actions'

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'is_active', 'handyman_count')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    
    def handyman_count(self, obj):
        count = obj.handymen.count()
        return format_html('<span style="font-weight: bold;">{}</span>', count)
    
    handyman_count.short_description = 'Handymen'

@admin.register(Handyman)
class HandymanAdmin(admin.ModelAdmin):
    list_display = ('user', 'business_name', 'experience_years', 'license_status', 'verification_status', 'services_count')
    list_filter = ('is_verified', 'is_licensed', 'is_insured', 'offers_promotions')
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'business_name', 'bio')
    inlines = [HandymanServiceInline, HandymanPromotionInline, HandymanJobInline]
    
    def license_status(self, obj):
        if obj.is_licensed:
            return format_html('<span style="color: #4CAF50;"><i class="fas fa-check-circle"></i> Licensed</span>')
        return format_html('<span style="color: #F44336;"><i class="fas fa-times-circle"></i> Not Licensed</span>')
    
    def verification_status(self, obj):
        if obj.is_verified:
            return format_html('<span style="color: #4CAF50;"><i class="fas fa-check-circle"></i> Verified</span>')
        return format_html('<span style="color: #F44336;"><i class="fas fa-times-circle"></i> Not Verified</span>')
    
    def services_count(self, obj):
        return obj.services.count()
    
    license_status.short_description = 'License'
    verification_status.short_description = 'Verification'
    services_count.short_description = 'Services'

@admin.register(HandymanJob)
class HandymanJobAdmin(admin.ModelAdmin):
    list_display = ('id', 'service', 'handyman', 'client', 'scheduled_date', 'status_badge', 'promotion_applied')
    list_filter = ('status', 'scheduled_date', 'service')
    search_fields = ('handyman__user__email', 'client__email', 'description', 'service__name')
    readonly_fields = ('completed_at',)
    date_hierarchy = 'scheduled_date'
    
    def status_badge(self, obj):
        status_colors = {
            'pending': '#FFC107',     # Amber
            'accepted': '#2196F3',    # Blue
            'in_progress': '#9C27B0', # Purple
            'completed': '#4CAF50',   # Green
            'declined': '#F44336',    # Red
            'cancelled': '#9E9E9E',   # Grey
        }
        color = status_colors.get(obj.status, '#757575')
        return format_html('<span style="color: {}; font-weight: bold;">{}</span>', 
                          color, obj.get_status_display())
    
    status_badge.short_description = 'Status'

@admin.register(HandymanPromotion)
class HandymanPromotionAdmin(admin.ModelAdmin):
    list_display = ('code', 'handyman', 'service', 'discount_percentage', 'date_range', 'is_active')
    list_filter = ('is_active', 'discount_percentage', 'start_date', 'end_date')
    search_fields = ('code', 'handyman__user__email', 'handyman__business_name', 'service__name')
    
    def date_range(self, obj):
        return f"{obj.start_date.strftime('%b %d, %Y')} - {obj.end_date.strftime('%b %d, %Y')}"
    
    date_range.short_description = 'Valid Period'

@admin.register(PromotionNotification)
class PromotionNotificationAdmin(admin.ModelAdmin):
    list_display = ('promotion', 'discount_percentage', 'handyman_name', 'recipient_email', 'sent_at', 'opened')
    list_filter = ('sent_at', 'opened', 'promotion__discount_percentage')
    search_fields = ('promotion__code', 'recipient__email', 'promotion__handyman__business_name')
    readonly_fields = ('promotion', 'recipient', 'sent_at', 'opened')
    date_hierarchy = 'sent_at'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'promotion', 
            'promotion__handyman', 
            'promotion__handyman__user', 
            'recipient'
        )
    
    def discount_percentage(self, obj):
        return f"{obj.promotion.discount_percentage}%"
    discount_percentage.short_description = 'Discount'
    discount_percentage.admin_order_field = 'promotion__discount_percentage'
    
    def handyman_name(self, obj):
        return obj.promotion.handyman.business_name or obj.promotion.handyman.user.get_full_name()
    handyman_name.short_description = 'Handyman'
    handyman_name.admin_order_field = 'promotion__handyman__business_name'
    
    def recipient_email(self, obj):
        return obj.recipient.email
    recipient_email.short_description = 'Recipient'
    recipient_email.admin_order_field = 'recipient__email'

@admin.register(HandymanService)
class HandymanServiceAdmin(admin.ModelAdmin):
    list_display = ('handyman', 'service', 'pricing_display')
    list_filter = ('service',)
    search_fields = ('handyman__user__email', 'service__name')
    
    def pricing_display(self, obj):
        pricing = []
        if obj.hourly_rate:
            pricing.append(f"${obj.hourly_rate}/hr")
        if obj.flat_rate:
            pricing.append(f"${obj.flat_rate} flat")
        return ", ".join(pricing) if pricing else "Not specified"
    
    pricing_display.short_description = 'Pricing'
