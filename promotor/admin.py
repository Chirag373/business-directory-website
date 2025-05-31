from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Plan, 
    Subscription, 
    PromotionalOffer, 
    PromotionalNotification, 
    Promotion, 
    PromotionClick, 
    Coupon
)

@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'duration_days', 'features_list', 'is_active')
    list_filter = ('is_active', 'featured_listing', 'priority_search')
    search_fields = ('name', 'description')
    
    def features_list(self, obj):
        features = []
        if obj.featured_listing:
            features.append('<span style="color: #4CAF50;"><i class="fas fa-check"></i> Featured</span>')
        if obj.priority_search:
            features.append('<span style="color: #4CAF50;"><i class="fas fa-check"></i> Priority Search</span>')
        features.append(f'<span><i class="fas fa-images"></i> {obj.max_images} Images</span>')
        
        return format_html(' | '.join(features))
    
    features_list.short_description = 'Features'

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('business', 'plan', 'date_range', 'status_badge', 'auto_renew')
    list_filter = ('status', 'auto_renew', 'start_date')
    search_fields = ('business__name', 'plan__name')
    date_hierarchy = 'start_date'
    
    def date_range(self, obj):
        return f"{obj.start_date.strftime('%b %d, %Y')} - {obj.end_date.strftime('%b %d, %Y')}"
    
    def status_badge(self, obj):
        status_colors = {
            'active': '#4CAF50',    # Green
            'expired': '#F44336',   # Red
            'cancelled': '#9E9E9E', # Grey
        }
        color = status_colors.get(obj.status, '#757575')
        return format_html('<span style="color: {}; font-weight: bold;">{}</span>', 
                          color, obj.get_status_display())
    
    date_range.short_description = 'Subscription Period'
    status_badge.short_description = 'Status'

class PromotionalNotificationInline(admin.TabularInline):
    model = PromotionalNotification
    extra = 0
    fields = ('recipient', 'sent_at', 'opened')
    readonly_fields = ('recipient', 'sent_at', 'opened')
    can_delete = False
    max_num = 0

@admin.register(PromotionalOffer)
class PromotionalOfferAdmin(admin.ModelAdmin):
    list_display = ('title', 'business', 'code', 'discount', 'date_range', 'is_active')
    list_filter = ('is_active', 'discount_percentage', 'start_date', 'end_date')
    search_fields = ('title', 'description', 'code', 'business__name')
    filter_horizontal = ('categories',)
    inlines = [PromotionalNotificationInline]
    
    def discount(self, obj):
        return f"{obj.discount_percentage}%"
    
    def date_range(self, obj):
        return f"{obj.start_date.strftime('%b %d, %Y')} - {obj.end_date.strftime('%b %d, %Y')}"
    
    discount.short_description = 'Discount'
    date_range.short_description = 'Valid Period'

@admin.register(PromotionalNotification)
class PromotionalNotificationAdmin(admin.ModelAdmin):
    list_display = ('offer', 'recipient', 'sent_at', 'opened')
    list_filter = ('sent_at', 'opened')
    search_fields = ('offer__title', 'recipient__email')
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('offer', 'recipient')

class PromotionClickInline(admin.TabularInline):
    model = PromotionClick
    extra = 0
    fields = ('user', 'ip_address', 'created_at')
    readonly_fields = ('user', 'ip_address', 'created_at')
    can_delete = False
    max_num = 0

@admin.register(Promotion)
class PromotionAdmin(admin.ModelAdmin):
    list_display = ('title', 'business', 'promo_type', 'date_range', 'is_active', 'budget', 'clicks_count')
    list_filter = ('is_active', 'promo_type', 'start_date', 'end_date')
    search_fields = ('title', 'description', 'business__name')
    inlines = [PromotionClickInline]
    
    def date_range(self, obj):
        return f"{obj.start_date.strftime('%b %d, %Y')} - {obj.end_date.strftime('%b %d, %Y')}"
    
    def clicks_count(self, obj):
        count = obj.clicks.count()
        return format_html('<span style="font-weight: bold;">{}</span>', count)
    
    date_range.short_description = 'Active Period'
    clicks_count.short_description = 'Clicks'

@admin.register(PromotionClick)
class PromotionClickAdmin(admin.ModelAdmin):
    list_display = ('promotion', 'user', 'ip_address', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('promotion__title', 'user__email', 'ip_address')
    date_hierarchy = 'created_at'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('promotion', 'user')

@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ('code', 'business', 'discount_display', 'date_range', 'usage_count')
    list_filter = ('start_date', 'end_date')
    search_fields = ('code', 'description', 'business__name')
    
    def discount_display(self, obj):
        if obj.discount_percentage:
            return f"{obj.discount_percentage}%"
        elif obj.discount_amount:
            return f"${obj.discount_amount}"
        return "No discount"
    
    def date_range(self, obj):
        return f"{obj.start_date.strftime('%b %d, %Y')} - {obj.end_date.strftime('%b %d, %Y')}"
    
    def usage_count(self, obj):
        if obj.max_uses:
            return f"{obj.current_uses}/{obj.max_uses}"
        return f"{obj.current_uses}/∞"
    
    discount_display.short_description = 'Discount'
    date_range.short_description = 'Valid Period'
    usage_count.short_description = 'Usage'
