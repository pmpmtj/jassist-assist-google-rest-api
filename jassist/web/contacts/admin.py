from django.contrib import admin
from .models import Contact

@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('id', 'full_name', 'alias', 'user', 'email', 'phone', 'category', 'created_at')
    list_filter = ('category', 'created_at', 'user')
    search_fields = (
        'first_name', 'last_name', 'alias', 
        'email', 'private_email', 'professional_email',
        'phone', 'private_phone', 'professional_phone',
        'notes', 'user__username'
    )
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'first_name', 'last_name', 'alias', 'category')
        }),
        ('Main Contact Details', {
            'fields': ('email', 'phone')
        }),
        ('Private Contact Details', {
            'fields': ('private_email', 'private_phone')
        }),
        ('Professional Contact Details', {
            'fields': ('professional_email', 'professional_phone')
        }),
        ('Additional Details', {
            'fields': ('address', 'notes')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def full_name(self, obj):
        return obj.full_name
    
    full_name.short_description = "Name" 