from django.contrib import admin
from django.contrib.admin import AdminSite
from django.utils.html import format_html
from .models import Address, Category

# Customize the admin site
admin.site.site_header = 'Business Directory 2.0 Admin'
admin.site.site_title = 'BD2 Admin Portal'
admin.site.index_title = 'Business Directory Management'

@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ('formatted_address', 'city', 'state', 'postal_code', 'country', 'has_coordinates')
    list_filter = ('state', 'country')
    search_fields = ('street', 'city', 'state', 'postal_code', 'country')
    
    def formatted_address(self, obj):
        return f"{obj.street}"
    
    def has_coordinates(self, obj):
        if obj.latitude and obj.longitude:
            return format_html('<span class="icon-yes"><i class="fas fa-check-circle"></i> Yes</span>')
        return format_html('<span class="icon-no"><i class="fas fa-times-circle"></i> No</span>')
    
    formatted_address.short_description = 'Street Address'
    has_coordinates.short_description = 'Has Coordinates'

class CategoryChildrenInline(admin.TabularInline):
    model = Category
    fk_name = 'parent'
    extra = 0
    fields = ('name', 'slug', 'is_active')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent', 'is_active', 'business_count')
    list_filter = ('is_active', 'parent')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [CategoryChildrenInline]
    
    def business_count(self, obj):
        count = obj.businesses.count()
        return format_html('<span class="bold">{}</span>', count)
    
    business_count.short_description = 'Businesses'
