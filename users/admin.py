from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from .models import Role, CustomUser, AppVariable, Category, CategoryPost, Widget, WidgetPost, ExternalSubscriber, NewsPost


# ----------------------------------------------------
# ACTIONS & UTILITIES
# ----------------------------------------------------

@admin.action(description="Resend/Reuse selected News")
def resend_news_action(modeladmin, request, queryset):
    """Triggers the send_broadcast method on selected old posts."""
    for post in queryset:
        # Note: Ensure your NewsPost model has a send_broadcast method 
        # that uses the new target_audience logic.
        post.send_broadcast()
    modeladmin.message_user(request, "Selected emails have been resent to the target audience.")

# ----------------------------------------------------
# 1. CORE SYSTEM SETTINGS
# ----------------------------------------------------
@admin.register(AppVariable)
class AppVariableAdmin(admin.ModelAdmin):
    list_display = ('var_name', 'var_value', 'description', 'lastupdated')
    search_fields = ('var_name',)

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'can_assign_staff', 'can_create_user')
    readonly_fields = ('slug',)

# ----------------------------------------------------
# 2. USER & COMMUNITY MANAGEMENT
# ----------------------------------------------------
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ('email', 'username', 'full_name', 'role', 'assigned_to', 'is_active')
    list_filter = ('role', 'is_active', 'region')
    fieldsets = UserAdmin.fieldsets + (
        ('Community Information', {
            'fields': ('role', 'assigned_to', 'is_subscribed', 'region', 'profile_image')
        }),
        ('Additional Data', {
            'fields': ('religion', 'tribe', 'racial_info', 'ip_address')
        }),
    )
    search_fields = ('email', 'username', 'first_name', 'last_name')
    ordering = ('email',)

admin.site.register(CustomUser, CustomUserAdmin)

# ----------------------------------------------------
# 3. NEWS & BROADCASTING (CLEANED)
# ----------------------------------------------------
@admin.register(NewsPost)
class NewsPostAdmin(admin.ModelAdmin):
    # Removed deleted ManyToMany fields from list_display and fieldsets
    list_display = ('title', 'display_status', 'target_audience', 'created_at')
    list_filter = ('target_audience', 'created_at')
    
    # Removed 'filter_horizontal' because ManyToMany fields are gone
    prepopulated_fields = {"slug": ("title",)}
    actions = [resend_news_action]
    
    fieldsets = (
        ('Announcement Content', {
            'fields': ('title', 'slug', 'content', 'sender_email')
        }),
        ('Audience Targeting', {
            'fields': ('target_audience',),
            'description': "Displays the audience group selected during the broadcast dispatch."
        }),
    )

    def display_status(self, obj):
        """Visual notification system for the admin list view."""
        # Using a fallback if status_notification isn't a property/field
        status = getattr(obj, 'status_notification', 'Stored')
        
        if "CRITICAL" in status or "5 mins" in status:
            return format_html(
                '''<span style="color: white; background: #d9534f; padding: 4px 8px; border-radius: 4px; font-weight: bold; animation: blinker 1s linear infinite;">{}</span>
                   <style>@keyframes blinker {{ 50% {{ opacity: 0; }} }}</style>''', 
                status
            )
        elif "WARNING" in status or "10 mins" in status:
            return format_html(
                '<span style="color: black; background: #f0ad4e; padding: 4px 8px; border-radius: 4px; font-weight: bold;">{}</span>', 
                status
            )
        elif "Sent" in status:
            return format_html('<span style="color: #5cb85c; font-weight: bold;">{}</span>', status)
            
        return status
    
    display_status.short_description = "Delivery Status"

@admin.register(ExternalSubscriber)
class ExternalSubscriberAdmin(admin.ModelAdmin):
    list_display = ('email', 'region', 'ip_address', 'date_subscribed')
    readonly_fields = ('date_subscribed', 'region', 'ip_address')
    search_fields = ('email', 'region')

# ----------------------------------------------------
# 4. CONTENT & WIDGET MANAGEMENT
# ----------------------------------------------------
class CategoryPostInline(admin.StackedInline):
    model = CategoryPost
    extra = 1

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug')
    prepopulated_fields = {"slug": ("title",)}
    inlines = [CategoryPostInline]

@admin.register(CategoryPost)
class CategoryPostAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'author', 'is_published', 'created_at')
    list_filter = ('category', 'is_published')
    search_fields = ('title', 'content')

@admin.register(Widget)
class WidgetAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug')

@admin.register(WidgetPost)
class WidgetPostAdmin(admin.ModelAdmin):
    list_display = ('title', 'widget', 'is_published')