import uuid, os
import requests
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser, PermissionsMixin
from django.utils.text import slugify
from django.conf import settings
from django.core.mail import send_mail
from django.db.models.signals import post_save
from django.dispatch import receiver
from datetime import timedelta
from django.core.mail import EmailMessage # Required for BCC and HTML
from django.contrib.auth import get_user_model



# ----------------------------------------------------
# 1. GLOBAL UTILITIES & CONSTANTS
# ----------------------------------------------------
def cat_post_upload_path(instance, filename):
    category_slug = slugify(instance.category.title) if instance.category else 'unknown'
    post_slug = slugify(instance.title) or 'untitled'
    return os.path.join('category_posts', category_slug, post_slug, filename)

def cat_image_upload_path(instance, filename):
    return cat_post_upload_path(instance, filename)

def wid_post_upload_path(instance, filename):
    widget_slug = slugify(instance.widget.title) if instance.widget else 'unknown'
    post_slug = slugify(instance.title) or 'untitled'
    return os.path.join('widget_posts', widget_slug, post_slug, filename)

def wid_image_upload_path(instance, filename):
    return wid_post_upload_path(instance, filename)


POST_FIELD_CHOICES = {
    'title': 'Title', 
    'slug': 'Slug', 
    'excerpt': 'Excerpt', 
    'content': 'Content',
    'is_published': 'Publish Now (Toggle)', 
    'author': 'Author', 
    'btn_url': 'btn_URL',
    'btn_text': 'btn_Text', 
    'video': 'Video', 
    'audio': 'Audio', 
    'icon': 'Icon',
    'image': 'Image (Featured)', 
    'image_align': 'Image Align', 
    'tags': 'Tags',
    'event_date': 'Event Date', 
    'address': 'Address', 
    'addfield1': 'Add Field 1',
    'addfield2': 'Add Field 2', 
    'addfield3': 'Add Field 3', 
    'addfield4': 'Add Field 4',
    'subtitle': 'Subtitle', 
    'shortcodes': 'Shortcodes', 
    'progress': 'Progress',
}


# ----------------------------------------------------
# 2. INDEPENDENT MODELS (App Settings)
# ----------------------------------------------------
class AppVariable(models.Model):
    var_name = models.CharField(max_length=100, unique=True)
    var_value = models.CharField(max_length=255, blank=True, null=True)
    description = models.CharField(max_length=250, blank=True, default="")
    isreadonly = models.IntegerField(default=0)
    lastupdated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.var_name}: {self.var_value}"

    @staticmethod
    def get_setting(name, default=''):
        try:
            return AppVariable.objects.get(var_name=name).var_value
        except AppVariable.DoesNotExist:
            return default


# ----------------------------------------------------
# 3. PERMISSIONS & HIERARCHY (Role must come before User)
# ----------------------------------------------------
class Role(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name="Role Name")
    slug = models.SlugField(max_length=50, unique=True, editable=False)
    can_create_user = models.BooleanField(default=False, verbose_name="Can Create Users")
    can_assign_staff = models.BooleanField(default=False, verbose_name="Can Assign Staff (Manager)")

    class Meta:
        verbose_name = "User Role"
        verbose_name_plural = "User Roles"

    def __str__(self):
        return self.name
        
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


# ----------------------------------------------------
# 4. AUTHENTICATION (Manager then User)
# ----------------------------------------------------
class CustomUserManager(BaseUserManager):
    def create_user(self, email, username, password=None, role_slug='client', **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        try:
            role_instance = Role.objects.get(slug=role_slug)
        except Role.DoesNotExist:
            role_instance, _ = Role.objects.get_or_create(name=role_slug.title(), slug=role_slug)
            
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        user = self.model(email=email, username=username, role=role_instance, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        return self.create_user(email, username, password, role_slug='super_admin', **extra_fields)


class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True, blank=True) 

    class Meta:
        verbose_name = "Department"
        verbose_name_plural = "Departments"

    def __str__(self):
        return self.name
        
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

        

class CustomUser(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=150, unique=True)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    full_name = models.CharField(max_length=60, blank=True, null=True, editable=False)

    is_subscribed = models.BooleanField(default=True, verbose_name="Wants Newsletters")
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_manager = models.BooleanField(default=False)
    is_online = models.BooleanField(default=False)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)

    date_joined = models.DateTimeField(default=timezone.now)
    # Note: Ensure 'Role' is imported or defined above
    role = models.ForeignKey('users.Role', on_delete=models.SET_NULL, null=True, blank=True, related_name='users')
    assigned_to = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='subordinates')
    
    region = models.CharField(max_length=50, blank=True, null=True)
    religion = models.CharField(max_length=50, blank=True, null=True)
    tribe = models.CharField(max_length=50, blank=True, null=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    racial_info = models.CharField(max_length=20, choices=[('black', 'Black'), ('white', 'White'), ('other', 'Other')], blank=True, null=True)
    profile_image = models.ImageField(upload_to='profile_images/', null=True, blank=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']
    
    # CustomUserManager needs to be imported or defined
    objects = CustomUserManager()

    class Meta:
        verbose_name = 'Custom User'
        verbose_name_plural = 'Custom Users'

    def __str__(self):
        return self.email

    def save(self, *args, **kwargs):
        self.full_name = f"{self.first_name} {self.last_name}".strip()
        super().save(*args, **kwargs)



# ----------------------------------------------------
# 5. CONTENT CATEGORIES (Category then CategoryPost)
# ----------------------------------------------------
class Category(models.Model):
    title = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    excerpt = models.TextField(blank=True, null=True)
    media_file = models.FileField(upload_to='category_media/{category}/', blank=True, null=True)
    child_fields = models.JSONField(default=list, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug: self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self): return self.title

    class Meta:
        verbose_name = "Content Type (Category)"
        verbose_name_plural = "Content Types (Categories)"


class CategoryPost(models.Model):
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='posts')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    excerpt = models.TextField(blank=True, null=True)
    content = models.TextField(blank=True, null=True)
    tags = models.CharField(max_length=255, blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    subtitle = models.CharField(max_length=255, blank=True, null=True)
    shortcodes = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to=cat_post_upload_path, blank=True, null=True)
    video = models.FileField(upload_to='cat_post_video/', blank=True, null=True)
    audio = models.FileField(blank=True, null=True)
    icon = models.CharField(max_length=70, blank=True, null=True)
    image_align = models.CharField(max_length=50, blank=True, null=True)
    btn_text = models.CharField(max_length=100, blank=True, null=True, default="Read More")
    btn_url = models.URLField(blank=True, null=True)
    event_date = models.DateTimeField(blank=True, null=True)
    progress = models.IntegerField(blank=True, null=True)
    addfield1 = models.CharField(max_length=255, blank=True, null=True)
    addfield2 = models.CharField(max_length=255, blank=True, null=True)
    addfield3 = models.CharField(max_length=255, blank=True, null=True)
    addfield4 = models.CharField(max_length=255, blank=True, null=True)
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)       

    @property
    def primary_image_url(self):
        return self.image.url if self.image else None

    def save(self, *args, **kwargs):
        if not self.slug: self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['category', '-created_at']


# ----------------------------------------------------
# 6. WIDGETS (Widget then WidgetPost)
# ----------------------------------------------------
class Widget(models.Model):
    title = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    excerpt = models.TextField(blank=True, null=True)
    media_file = models.FileField(upload_to='widget_media/{widget}/', blank=True, null=True)
    child_fields = models.JSONField(default=list, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug: self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self): return self.title


class WidgetPost(models.Model):
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    widget = models.ForeignKey(Widget, on_delete=models.CASCADE, related_name='widget_posts')         
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    excerpt = models.TextField(blank=True, null=True)
    content = models.TextField(blank=True, null=True)
    tags = models.CharField(max_length=255, blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    subtitle = models.CharField(max_length=255, blank=True, null=True)
    shortcodes = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to=wid_post_upload_path, blank=True, null=True)
    video = models.FileField(upload_to='wid_post_video/', blank=True, null=True)
    audio = models.FileField(blank=True, null=True)
    icon = models.CharField(max_length=70, blank=True, null=True)
    image_align = models.CharField(max_length=50, blank=True, null=True)
    btn_text = models.CharField(max_length=100, blank=True, null=True, default="Read More")
    btn_url = models.URLField(blank=True, null=True)
    event_date = models.DateTimeField(blank=True, null=True)
    progress = models.IntegerField(blank=True, null=True)
    addfield1 = models.CharField(max_length=255, blank=True, null=True)
    addfield2 = models.CharField(max_length=255, blank=True, null=True)
    addfield3 = models.CharField(max_length=255, blank=True, null=True)
    addfield4 = models.CharField(max_length=255, blank=True, null=True)
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def primary_image_url(self):
        return self.image.url if self.image else None

    def save(self, *args, **kwargs):
        if not self.slug: self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['widget', '-created_at']




def get_default_sender():
    # You can change this to your actual default domain
    return "noreply@bgtech.com"


# ----------------------------------------------------
# SUBSCRIPTION
# ----------------------------------------------------
class ExternalSubscriber(models.Model):
    email = models.EmailField(unique=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    region = models.CharField(max_length=100, null=True, blank=True)
    date_subscribed = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        # TRIGGER CELERY: Offload IP lookup to background
        # Import inside the method to prevent Circular Import errors
        if is_new and self.ip_address:
            try:
                from .tasks import get_subscriber_location_task
                get_subscriber_location_task.delay(self.id)
            except ImportError:
                pass




class NewsPost(models.Model):
    AUDIENCE_CHOICES = [
        ('all', 'All Audience'),
        ('staff_only', 'Staff Only'),
        ('external_only', 'External Subscribers Only'),
        ('clients', 'Company Users (Clients)'),
        ('super_admin', 'Super Admins Only'),
        ('is_manager', 'Managers Only'),
        ('administrator', 'Administrators Only'),
    ]

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('scheduled', 'Scheduled'),
        ('sending', 'Sending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
    ]

    # Content Fields
    title = models.CharField(max_length=255)
    subject = models.CharField(max_length=255, blank=True)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    content = models.TextField()
    
    # Configuration Fields
    # We keep sender_email optional here so the View can fill it later
    sender_email = models.EmailField(blank=True, null=True)
    target_audience = models.CharField(max_length=50, choices=AUDIENCE_CHOICES, default='all')
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='draft')
    scheduled_time = models.DateTimeField(null=True, blank=True)

    # Tracking Fields
    last_sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    def gather_emails(self):
        """
        Returns a unique list of email addresses based on the target_audience.
        This is used by the View to know who the recipients are.
        """
        CustomUser = get_user_model()
        from users.models import ExternalSubscriber  # Local import to avoid circular dependency

        emails = set()

        if self.target_audience == 'all':
            emails.update(CustomUser.objects.filter(is_active=True).values_list('email', flat=True))
            emails.update(ExternalSubscriber.objects.values_list('email', flat=True))
        elif self.target_audience == 'staff_only':
            emails.update(CustomUser.objects.filter(is_staff=True, is_active=True).values_list('email', flat=True))
        elif self.target_audience == 'external_only':
            emails.update(ExternalSubscriber.objects.values_list('email', flat=True))
        elif self.target_audience == 'clients':
            emails.update(CustomUser.objects.filter(role__name__iexact='Clients', is_active=True).values_list('email', flat=True))
        elif self.target_audience == 'super_admin':
            emails.update(CustomUser.objects.filter(is_superuser=True, is_active=True).values_list('email', flat=True))
        elif self.target_audience == 'is_manager':
            emails.update(CustomUser.objects.filter(is_manager=True, is_active=True).values_list('email', flat=True))
        elif self.target_audience == 'administrator':
            emails.update(CustomUser.objects.filter(role__name__iexact='Administrator', is_active=True).values_list('email', flat=True))

        return list(filter(None, emails))

    def is_due(self):
        """Returns True if it's time to send (or no time was set)."""
        if not self.scheduled_time:
            return True
        return self.scheduled_time <= timezone.now()

    def save(self, *args, **kwargs):
        # Auto-fill subject if empty
        if not self.subject:
            self.subject = self.title

        # Auto-generate slug if empty
        if not self.slug:
            base_slug = slugify(self.title)
            self.slug = base_slug
            while NewsPost.objects.filter(slug=self.slug).exists():
                self.slug = f"{base_slug}-{uuid.uuid4().hex[:4]}"

        super().save(*args, **kwargs)