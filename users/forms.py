from django import forms
from django.forms import inlineformset_factory
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import authenticate
from django.forms.widgets import TextInput, Textarea, CheckboxSelectMultiple
from django.utils.safestring import mark_safe
from django.db.models.fields.files import FieldFile
from django.contrib.auth import get_user_model
from django.conf import settings
import os
from .models import CustomUser, Role, AppVariable, Category, CategoryPost, POST_FIELD_CHOICES, Widget, WidgetPost, NewsPost, ExternalSubscriber
from django_summernote.widgets import SummernoteWidget

CustomUser = get_user_model()



def get_field_label(field_name):
    return POST_FIELD_CHOICES.get(field_name, field_name.replace('_', ' ').title())

def delete_old_file(file_path):
    if file_path and os.path.exists(file_path):
        try:
            os.remove(file_path)
        except Exception as e:
            print(f"Error deleting file {file_path}: {e}")


WIDGET_MAPPING = {
    'excerpt': forms.Textarea(attrs={'rows': 5, 'class': 'form-control'}),
    'content': SummernoteWidget(attrs={'rows': 70, 'class': '' }),
    'shortcodes': forms.TextInput(attrs={'rows': 5, 'class': 'form-control'}),
    'address': forms.TextInput(attrs={'rows': 3, 'class': 'form-control'}),
    'event_date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
}

class DynamicPostFormMixin:
    """Mixin to handle dynamic field enabling based on parent child_fields."""

    def dynamic_init_logic(self, parent_instance_id, parent_model, parent_field_name):
        enabled_fields = set()
    
        if parent_instance_id:
            try:
                parent_instance = parent_model.objects.get(pk=parent_instance_id)
                # Ensure child_fields is a list/set
                enabled_fields = set(parent_instance.child_fields or [])
                
                if parent_field_name in self.fields:
                    self.fields[parent_field_name].initial = parent_instance_id
                    self.fields[parent_field_name].widget = forms.HiddenInput()
                    self.initial[parent_field_name] = parent_instance_id
            except parent_model.DoesNotExist:
                pass

        # 1. Define Core Fields (Note: title and slug are the focus here)
        CORE_FIELDS = ['title', 'slug', 'image', 'is_published', parent_field_name]

        for field_name in list(self.fields.keys()):
            # A. FORCE TITLE AND SLUG TO BE REQUIRED
            if field_name in ['title', 'slug']:
                self.fields[field_name].required = True
                # Add HTML5 validation attribute for the browser
                self.fields[field_name].widget.attrs.update({
                    'required': 'required',
                    'class': 'form-control'
                })
                continue

            # B. Style other CORE fields that aren't title/slug
            if field_name in CORE_FIELDS:
                if field_name in self.fields:
                    self.fields[field_name].widget.attrs.setdefault('class', 'form-control')
                continue
                
            # C. Remove fields NOT enabled in the parent (Category/Widget) settings
            if field_name not in enabled_fields:
                self.fields.pop(field_name, None)
                continue

            # D. Handle Dynamic Enabled fields (excerpt, content, etc.)
            self.fields[field_name].label = get_field_label(field_name)
            if field_name in WIDGET_MAPPING:
                self.fields[field_name].widget = WIDGET_MAPPING[field_name]

            # Standard Styling for survival fields
            widget_class = self.fields[field_name].widget.__class__.__name__
            if widget_class not in ('CheckboxInput', 'ClearableFileInput', 'FileInput', 'SummernoteWidget'):
                self.fields[field_name].widget.attrs.setdefault('class', 'form-control')
        
        # 3. Final media styling
        for media in ['image', 'video', 'audio', 'icon']:
            if media in self.fields:
                self.fields[media].widget.attrs.update({'class': 'form-control-file'})

    def dynamic_save_logic(self, commit=True):
        # ... (Your existing save logic is fine)
        old_media_files = {}
        if self.instance.pk:
            for field_name in ['image', 'video', 'audio', 'icon']:
                if field_name in self.cleaned_data:
                    new_file = self.cleaned_data[field_name]
                    current_file = getattr(self.instance, field_name)
                    if current_file and current_file.name:
                        if new_file and new_file != current_file or new_file is False:
                            old_media_files[field_name] = current_file.path

        post = super().save(commit=commit)
        if commit:
            for field_name, old_path in old_media_files.items():
                new_file_obj = getattr(post, field_name)
                if not new_file_obj or (old_path != new_file_obj.path):
                    delete_old_file(old_path)
        return post
    

# =====================================================================
#                           Category Forms
# =====================================================================
   
class CategoryForm(forms.ModelForm):
    child_fields = forms.MultipleChoiceField(
        choices=[(k, v) for k, v in POST_FIELD_CHOICES.items()],
        required=False,
        widget=CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        label="Enable fields for posts in this Category"
    )

    class Meta:
        model = Category
        fields = ['title', 'slug', 'excerpt', 'media_file', 'child_fields']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'slug': forms.TextInput(attrs={'class': 'form-control'}),
            'excerpt': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        # Get the selected fields from the form
        selected_fields = self.cleaned_data.get('child_fields', [])
        
        # 1. Manually add 'title' and 'slug' if they aren't there
        if 'title' not in selected_fields:
            selected_fields.append('title')
        if 'slug' not in selected_fields:
            selected_fields.append('slug')
            
        instance.child_fields = selected_fields
        
        if commit:
            instance.save()
        return instance


class DynamicCategoryPostForm(DynamicPostFormMixin, forms.ModelForm):
    class Meta:
        model = CategoryPost
        fields = list(POST_FIELD_CHOICES.keys()) + ['category']
        exclude = ['author', 'created_at', 'updated_at']

    def __init__(self, *args, **kwargs):
        # 1. Pop custom arguments SAFELY
        # Use .pop(key, None) to ensure it doesn't crash if the key is missing
        cat_id = kwargs.pop('category_id', None)
        kwargs.pop('category_instance', None) # Remove this so super() doesn't see it

        super().__init__(*args, **kwargs)

        # 2. Determine the Category ID for dynamic logic
        # If we are editing (instance exists), get ID from the instance
        if self.instance and self.instance.pk and hasattr(self.instance, 'category'):
            cat_id = self.instance.category.id
        
        # 3. Run dynamic logic
        self.dynamic_init_logic(cat_id, Category, 'category')

        # 4. Make category optional (view handles it)
        if 'category' in self.fields:
            self.fields['category'].required = False



# # =====================================================================
# #                           Widget Forms
# # =====================================================================
    
class WidgetForm(forms.ModelForm):
    child_fields = forms.MultipleChoiceField(
        choices=[(k, v) for k, v in POST_FIELD_CHOICES.items()],
        required=False,
        widget=CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        label="Enable fields for posts in this Category"
    )

    class Meta:
        model = Widget
        fields = ['title', 'slug', 'excerpt', 'media_file', 'child_fields']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'slug': forms.TextInput(attrs={'class': 'form-control'}),
            'excerpt': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def save(self, commit=True):
            instance = super().save(commit=False)
            # Get the selected fields from the form
            selected_fields = self.cleaned_data.get('child_fields', [])
            
            # 1. Manually add 'title' and 'slug' if they aren't there
            if 'title' not in selected_fields:
                selected_fields.append('title')
            if 'slug' not in selected_fields:
                selected_fields.append('slug')
                
            instance.child_fields = selected_fields
            
            if commit:
                instance.save()
            return instance


class DynamicWidgetPostForm(DynamicPostFormMixin, forms.ModelForm):
    class Meta:
        model = WidgetPost
        fields = list(POST_FIELD_CHOICES.keys()) + ['widget']
        exclude = ['author', 'created_at', 'updated_at']

    def __init__(self, *args, **kwargs):
        # 1. Pop custom arguments SAFELY
        # Use .pop(key, None) to ensure it doesn't crash if the key is missing
        wid_id = kwargs.pop('widget_id', None)
        kwargs.pop('widget_instance', None) # Remove this so super() doesn't see it

        super().__init__(*args, **kwargs)

        # 2. Determine the Widget ID for dynamic logic
        # If we are editing (instance exists), get ID from the instance
        if self.instance and self.instance.pk and hasattr(self.instance, 'widget'):
            wid_id = self.instance.widget.id
        
        # 3. Run dynamic logic
        self.dynamic_init_logic(wid_id, Widget, 'widget')

        # 4. Make widget optional (view handles it)
        if 'widget' in self.fields:
            self.fields['widget'].required = False

# =====================================================================
#                          User / Auth Forms
# =====================================================================

class EmailAuthenticationForm(AuthenticationForm):
    model = CustomUser
    fields = ['email', 'username', 'password']

    username = forms.CharField(
        label="Email",
        widget=forms.TextInput(attrs={'autofocus': True})
    )

    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if username and password:
            self.user_cache = authenticate(
                self.request, username=username, password=password
            )

            if self.user_cache is None:
                raise forms.ValidationError(
                    "Invalid username or password."
                )

            self.confirm_login_allowed(self.user_cache)

        return self.cleaned_data


class RoleForm(forms.ModelForm):
    class Meta:
        model = Role
        fields = ['name', 'can_create_user', 'can_assign_staff']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'can_create_user': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'can_assign_staff': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class SiteSettingsKeyForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.settings = AppVariable.objects.all().order_by('var_name')

        for setting in self.settings:
            var_name = setting.var_name

            WidgetType = forms.Textarea if var_name in ['site_description', 'footer_text'] else forms.TextInput

            self.fields[var_name] = forms.CharField(
                label=var_name.replace('_', ' ').title(),
                widget=WidgetType(attrs={'class': 'form-control'}),
                required=False,
                initial=setting.var_value
            )

            self.fields[f'desc_{var_name}'] = forms.CharField(
                label=f"{var_name} Description",
                widget=forms.TextInput(attrs={'class': 'form-control'}),
                required=False,
                initial=setting.description
            )

    def save(self):
        for name, value in self.cleaned_data.items():
            if name.startswith("desc_"):
                AppVariable.objects.filter(var_name=name.replace("desc_", "")).update(description=value)
            else:
                AppVariable.objects.filter(var_name=name).update(var_value=value)


class AdminUserCreationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    password_confirm = forms.CharField(widget=forms.PasswordInput, label="Confirm Password")

    class Meta:
        model = CustomUser
        fields = [
            'email', 'username', 'first_name', 'last_name',
            'role', 'assigned_to', 'religion', 'region',
            'tribe', 'racial_info', 'ip_address', 'is_active', 'is_staff', 'is_manager'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        superior_roles = Role.objects.filter(slug__in=['super_admin', 'general_manager', 'manager', 'staff'])
        superior_users = CustomUser.objects.filter(role__in=superior_roles).order_by('username')

        self.fields['assigned_to'].required = False
        self.fields['assigned_to'].queryset = superior_users
        self.fields['assigned_to'].empty_label = "-- Select Superior --"

    def clean(self):
        data = super().clean()
        if data.get("password") != data.get("password_confirm"):
            raise forms.ValidationError("Passwords do not match.")
        return data

    def save(self, commit=True):
        role_obj = self.cleaned_data.get('role')
        extra_fields = {
            'first_name': self.cleaned_data['first_name'],
            'last_name': self.cleaned_data['last_name'],
            'assigned_to': self.cleaned_data.get('assigned_to'),
            'religion': self.cleaned_data.get('religion'),
            'region': self.cleaned_data.get('region'),
            'tribe': self.cleaned_data.get('tribe'),
            'racial_info': self.cleaned_data.get('racial_info'),
            'ip_address': self.cleaned_data.get('ip_address'),
            'is_active': self.cleaned_data.get('is_active', True),
        }

        user = CustomUser.objects.create_user(
            email=self.cleaned_data['email'],
            username=self.cleaned_data['username'],
            password=self.cleaned_data['password'],
            role_slug=role_obj.slug if role_obj else None,
            **extra_fields
        )
        return user


# class BroadcastForm(forms.ModelForm):
#     class Meta:
#         model = NewsPost
#         fields = ['title', 'subject', 'sender_email', 'content', 'target_audience', 'scheduled_time']
        
#         widgets = {
#             'content': SummernoteWidget(),
#             'scheduled_time': forms.TextInput(attrs={
#                 'class': 'form-control my-datetimepicker', # This class matches our JS
#                 'id': 'datetimepicker',
#                 'autocomplete': 'off',
#                 'placeholder': 'Select Date and Time',
#                 'readonly': 'readonly', # Prevents mobile keyboard from blocking the picker
#             }),
#         }



class BroadcastForm(forms.ModelForm):

    class Meta:
        model = NewsPost
        fields = ['title','subject','sender_email','content','target_audience','scheduled_time'
        ]
        widgets = {
            'content': SummernoteWidget(),
            # 'scheduled_time': forms.DateTimeInput(
            #     attrs={
            #         'type': 'datetime-local',
            #         'class': 'form-control'
            #     },
            #     format='%Y-%m-%dT%H:%M'
            # ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['sender_email'].required = False
        self.fields['scheduled_time'].required = False
        # self.fields['scheduled_time'].input_formats = ['%Y-%m-%dT%H:%M']



class Subcribers(forms.ModelForm):
    class Meta:
        model = ExternalSubscriber
        fields = ['email']
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter email'})
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if ExternalSubscriber.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is already subscribed.")
        return email    
    



class CSVUploadForm(forms.Form):
    csv_file = forms.FileField(label="Select CSV File")