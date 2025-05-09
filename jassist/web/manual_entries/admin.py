from django.contrib import admin
from .models import ManualEntry

@admin.register(ManualEntry)
class ManualEntryAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'classification', 'short_content', 'created_at', 'updated_at')
    list_filter = ('classification', 'created_at', 'user')
    search_fields = ('content', 'user__username')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'created_at'
    
    def short_content(self, obj):
        return obj.content[:50] + "..." if len(obj.content) > 50 else obj.content
    
    short_content.short_description = "Content Preview"
