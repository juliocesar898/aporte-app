from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Tenant, User

@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    """
    Administrative layout configuration for the Multi-tenant root entity.
    """
    list_display = ('name', 'subdomain', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'subdomain')
    ordering = ('-created_at',)


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """
    Administrative layout configuration for the Custom User entity,
    safely expanding the native Django UserAdmin to support roles and tenants.
    """
    # Fields to display in the main list view
    list_display = ('username', 'email', 'role', 'tenant', 'is_staff', 'is_active')
    
    # Sidebar filters for rapid database sorting
    list_filter = ('role', 'is_staff', 'is_active', 'tenant')
    
    # Search constraints across text fields
    search_fields = ('username', 'first_name', 'last_name', 'email', 'phone_number')
    
    # Expose our custom platform fields inside the detailed editing view
    fieldsets = UserAdmin.fieldsets + (
        ('Aporte Platform Custom Core Keys', {
            'fields': ('role', 'tenant', 'phone_number'),
        }),
    )
    
    # Expose custom fields during manual user creation within the admin panel
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Aporte Platform Custom Core Keys', {
            'fields': ('role', 'tenant', 'phone_number'),
        }),
    )