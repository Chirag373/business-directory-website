from django.contrib import admin
from django.utils.html import format_html
from .models import Business, BusinessHours, BusinessCard, BusinessImage, Review

class BusinessHoursInline(admin.TabularInline):
    model = BusinessHours
    extra = 0
    verbose_name_plural = 'Business Hours'

class BusinessImageInline(admin.TabularInline):
    model = BusinessImage
    extra = 0
    fields = ('image', 'caption', 'is_primary', 'image_preview')
    readonly_fields = ('image_preview',)
    
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" class="admin-thumbnail" />', obj.image.url)
        return '-'
    
    image_preview.short_description = 'Preview'

class BusinessCardInline(admin.StackedInline):
    model = BusinessCard
    extra = 0
    fields = ('front_image', 'front_preview', 'back_image', 'back_preview', 'back_is_blank')
    readonly_fields = ('front_preview', 'back_preview')
    
    def front_preview(self, obj):
        if obj.front_image:
            return format_html('<img src="{}" class="admin-card-preview" />', obj.front_image.url)
        return '-'
    
    def back_preview(self, obj):
        if obj.back_image:
            return format_html('<img src="{}" class="admin-card-preview" />', obj.back_image.url)
        return '-'
    
    front_preview.short_description = 'Front Preview'
    back_preview.short_description = 'Back Preview'

class ReviewInline(admin.TabularInline):
    model = Review
    extra = 0
    readonly_fields = ('user', 'rating', 'comment', 'created_at')
    can_delete = False
    max_num = 0  # Don't allow adding reviews from admin

@admin.register(Business)
class BusinessAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'display_categories', 'city', 'state', 'verified', 'featured')
    list_filter = ('verified', 'featured', 'categories')
    search_fields = ('name', 'description', 'owner__email', 'address__city', 'address__state')
    prepopulated_fields = {'slug': ('name',)}
    filter_horizontal = ('categories',)
    inlines = [BusinessHoursInline, BusinessCardInline, BusinessImageInline, ReviewInline]
    
    def display_categories(self, obj):
        return ", ".join([category.name for category in obj.categories.all()[:3]])
    
    def city(self, obj):
        return obj.address.city if obj.address else '-'
    
    def state(self, obj):
        return obj.address.state if obj.address else '-'
    
    display_categories.short_description = 'Categories'
    city.admin_order_field = 'address__city'
    state.admin_order_field = 'address__state'

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('business', 'user', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('business__name', 'user__email', 'comment')
    readonly_fields = ('created_at',)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('business', 'user')

# Register the remaining models
admin.site.register(BusinessHours)
admin.site.register(BusinessCard)
admin.site.register(BusinessImage)
