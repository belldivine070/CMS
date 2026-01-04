import csv, io, datetime
from zoneinfo import ZoneInfo
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponseRedirect, Http404, JsonResponse, HttpResponse
from django.urls import reverse_lazy, reverse
from django.views import View
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, FormView, DetailView
from django.conf import settings
from django.db import transaction
from django.db.models import Count, Q
from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from django.utils import timezone
from django.utils.timezone import make_aware, is_naive, now as timezone_now
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from .mixins import RolePermissionRequiredMixin, role_permission_required, is_super_admin
from .models import Category, CategoryPost, Widget, WidgetPost, CustomUser, AppVariable, Role, POST_FIELD_CHOICES, NewsPost, ExternalSubscriber
from .forms import CategoryForm, DynamicCategoryPostForm, WidgetForm, DynamicWidgetPostForm, AdminUserCreationForm, SiteSettingsKeyForm, RoleForm, BroadcastForm, Subcribers, CSVUploadForm
from .tasks import send_broadcast_task 
utc = datetime.UTC
from zoneinfo import ZoneInfo


def get_client_ip(request):
    """Utility to extract IP address from request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def is_super_admin(user):
    return user.is_authenticated and user.is_superuser

class IndexView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        return render(request, "home.html")


# =========================================================
#             1. CATEGORY & CATEGORY POST VIEWS
# =========================================================

class CategoryListView(LoginRequiredMixin, ListView):
    model = Category
    template_name = 'categories/category_list.html'
    context_object_name = 'categories'

    def get_queryset(self):
        return Category.objects.annotate(post_count=Count('posts')).order_by('title')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Convert the tuple of tuples into a dictionary so get_item can work
        context['POST_FIELD_CHOICES'] = dict(POST_FIELD_CHOICES)
        return context


class CategoryCreateView(LoginRequiredMixin, CreateView):
    model = Category
    form_class = CategoryForm
    template_name = 'categories/category_form.html'
    success_url = reverse_lazy('category_list')

class CategoryEditView(LoginRequiredMixin, UpdateView):
    model = Category
    form_class = CategoryForm
    template_name = 'categories/category_form.html'
    slug_url_kwarg = 'slug'
    success_url = reverse_lazy('category_list')

class CategoryDeleteView(LoginRequiredMixin, DeleteView):
    model = Category
    slug_url_kwarg = 'slug'
    success_url = reverse_lazy('category_list') 

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.delete()
        messages.success(request, "Category and posts deleted.")
        return redirect(self.success_url)


# --- Category Posts ---

class PostListByCategoryView(LoginRequiredMixin, ListView):
    model = CategoryPost
    template_name = 'categories/post_list.html'
    context_object_name = 'posts'

    def get_queryset(self):
        self.category = get_object_or_404(Category, slug=self.kwargs['category_slug'])
        return CategoryPost.objects.filter(category=self.category).order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.category
        return context

class PostCreateView(LoginRequiredMixin, CreateView):
    model = CategoryPost
    form_class = DynamicCategoryPostForm
    template_name = 'categories/post_create.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Fetch and store category once
        self.category = get_object_or_404(Category, slug=self.kwargs['category_slug'])
        kwargs['category_id'] = self.category.id
        return kwargs
        
    def form_valid(self, form):
        # 1. Save the main Post instance first
        form.instance.author = self.request.user
        # If CreateView, ensure category is set (as we did before)
        if not hasattr(form.instance, 'category'):
            form.instance.category = get_object_or_404(Category, slug=self.kwargs['category_slug'])
        
        response = super().form_valid(form)
        
        # 2. Handle Multiple Image Uploads
        images = self.request.FILES.getlist('gallery_images')
        for f in images:
            # Assuming your gallery model is 'PostImage' and has a foreign key 'post'
            Category.image.objects.create(post=self.object, image=f)
            
        return response
    
    def form_valid(self, form):
        # Attach the stored category and author
        form.instance.category = self.category
        form.instance.author = self.request.user
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.category # Use the cached version
        return context
    
    def get_success_url(self):
        return reverse('post_list_by_category', kwargs={'category_slug': self.kwargs['category_slug']})
     

class PostEditView(LoginRequiredMixin, UpdateView):
    model = CategoryPost
    form_class = DynamicCategoryPostForm
    template_name = 'categories/post_edit.html'
    slug_url_kwarg = 'post_slug'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['category_instance'] = self.get_object().category.id
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.object.category
        context['category_slug'] = self.object.category.slug 
        return context
    
    def get_success_url(self):
        return reverse('post_list_by_category', kwargs={'category_slug': self.kwargs['category_slug']})


class PostDetailView(LoginRequiredMixin, DetailView):
    model = CategoryPost
    template_name = 'categories/post_detail.html'
    slug_url_kwarg = 'post_slug'
    context_object_name = 'post'

class PostDeleteView(LoginRequiredMixin, DeleteView):
    model = CategoryPost
    slug_url_kwarg = 'post_slug'
    success_url = reverse_lazy('post_list_by_category')

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        slug = self.kwargs['category_slug']
        self.object.delete()
        return redirect(reverse('post_list_by_category', kwargs={'category_slug': slug}))
    
    def get_success_url(self):
        return reverse('post_list_by_category', kwargs={'category_slug': self.kwargs['category_slug']})
    

# =========================================================
#             2. WIDGET & WIDGET POST VIEWS
# =========================================================

class WidgetListView(LoginRequiredMixin, ListView):
    model = Widget
    template_name = 'widgets/widget_list.html'
    context_object_name = 'widgets'

    def get_queryset(self):
        return Widget.objects.annotate(post_count=Count('widget_posts')).order_by('title')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['POST_FIELD_CHOICES'] = dict(POST_FIELD_CHOICES)
        return super().get_context_data(**kwargs)

class WidgetCreateView(LoginRequiredMixin, CreateView):
    model = Widget
    form_class = WidgetForm
    template_name = 'widgets/widget_form.html'
    success_url = reverse_lazy('widget_list')

class WidgetEditView(LoginRequiredMixin, UpdateView):
    model = Widget
    form_class = WidgetForm
    template_name = 'widgets/widget_form.html'
    slug_url_kwarg = 'slug'
    success_url = reverse_lazy('widget_list')

class WidgetDeleteView(LoginRequiredMixin, DeleteView):
    model = Widget
    slug_url_kwarg = 'slug'
    success_url = reverse_lazy('widget_list')

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.delete()
        return redirect(self.success_url)

class PostListByWidgetView(LoginRequiredMixin, ListView):
    model = WidgetPost
    template_name = 'widgets/wid_post_list.html'
    context_object_name = 'posts'

    def get_queryset(self):
        self.widget = get_object_or_404(Widget, slug=self.kwargs['widget_slug'])
        return WidgetPost.objects.filter(widget=self.widget).order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['widget'] = self.widget
        return context

class WidgetPostCreateView(LoginRequiredMixin, CreateView):
    model = WidgetPost
    form_class = DynamicWidgetPostForm
    template_name = 'widgets/wid_postcreate.html'

    def get_widget(self):
        return get_object_or_404(Widget, slug=self.kwargs['widget_slug'])

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['widget_id'] = self.get_widget().id
        return kwargs
    
    def form_valid(self, form):
        form.instance.widget = self.get_widget()
        form.instance.author = self.request.user
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Pass the actual widget object so {{ widget.slug }} works in templates
        context['widget'] = self.get_widget()
        return context

    def get_success_url(self):
        return reverse('post_list_by_widget', kwargs={'widget_slug': self.kwargs['widget_slug']})


class WidgetPostEditView(LoginRequiredMixin, UpdateView):
    model = WidgetPost
    form_class = DynamicWidgetPostForm
    template_name = 'widgets/wid_post_edit.html'
    slug_url_kwarg = 'post_slug'

    def get_object(self, queryset=None):
        """
        Ensures the post exists AND belongs to the widget in the URL.
        This prevents 404s when the slugs don't match exactly.
        """
        return get_object_or_404(
            WidgetPost, 
            slug=self.kwargs.get('post_slug'),
            widget__slug=self.kwargs.get('widget_slug')
        )

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Fetch the object once to avoid multiple DB hits
        obj = self.get_object()
        kwargs['widget_id'] = obj.widget.id
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Pass the widget to the template for the breadcrumbs/header
        context['widget'] = self.get_object().widget
        return context
    
    def get_success_url(self):
        # Redirect back to the slide list for this specific widget
        return reverse('post_list_by_widget', kwargs={'widget_slug': self.object.widget.slug})


class WidgetPostDeleteView(LoginRequiredMixin, DeleteView):
    model = WidgetPost
    slug_url_kwarg = 'post_slug'

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        widget_slug = self.object.widget.slug
        self.object.delete()
        return redirect('post_list_by_widget', widget_slug=widget_slug)

# =========================================================
#             3. USER & ROLE MANAGEMENT VIEWS
# =========================================================

    
class ManageUsersListView(UserPassesTestMixin, ListView):
    model = CustomUser
    template_name = 'users/manage_users.html'
    context_object_name = 'users'
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role is not None
    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return CustomUser.objects.all().exclude(pk=user.pk).select_related('role', 'assigned_to')
        return CustomUser.objects.filter(assigned_to=user).select_related('role', 'assigned_to')


class AdminRegisterUserView(RolePermissionRequiredMixin, CreateView):
    required_permission = 'can_create_user' 
    model = CustomUser
    form_class = AdminUserCreationForm
    template_name = 'users/register_user_form.html'
    success_url = reverse_lazy('users:manage_users')


class EditSubordinateView(RolePermissionRequiredMixin, UpdateView):
    model = CustomUser
    form_class = AdminUserCreationForm
    template_name = 'users/edit_user_form.html'
    required_permission = 'can_assign_staff' 
    success_url = reverse_lazy('users:manage_users')


class UserDetailView(UserPassesTestMixin, DetailView):
    model = CustomUser
    template_name = 'users/user_detail.html'
    context_object_name = 'target_user'

    def test_func(self):
        return self.request.user.is_superuser or self.get_object() == self.request.user

# class ManageUsersListView(UserPassesTestMixin, ListView):
#     model = CustomUser
#     template_name = 'users/manage_users.html'
#     context_object_name = 'users'
#     def test_func(self):
#         return self.request.user.is_authenticated and self.request.user.role is not None
#     def get_queryset(self):
#         user = self.request.user
#         if user.is_superuser:
#             return CustomUser.objects.all().exclude(pk=user.pk).select_related('role', 'assigned_to')
#         return CustomUser.objects.filter(assigned_to=user).select_related('role', 'assigned_to')

# class AdminRegisterUserView(RolePermissionRequiredMixin, CreateView):
#     required_permission = 'can_create_user' 
#     model = CustomUser
#     form_class = AdminUserCreationForm
#     template_name = 'users/register_user_form.html'
#     success_url = reverse_lazy('manage_users')

# class EditSubordinateView(RolePermissionRequiredMixin, UpdateView):
#     model = CustomUser
#     form_class = AdminUserCreationForm
#     template_name = 'users/edit_user_form.html'
#     required_permission = 'can_assign_staff' 
#     success_url = reverse_lazy('manage_users')

# class UserDetailView(UserPassesTestMixin, DetailView):
#     model = CustomUser
#     template_name = 'users/user_detail.html'
#     context_object_name = 'target_user'
#     def test_func(self):
#         return self.request.user.is_superuser or self.get_object() == self.request.user

class StaffAssignmentView(RolePermissionRequiredMixin, ListView):
    required_permission = 'can_assign_staff' 
    model = CustomUser
    template_name = 'dashboard/staff_assignment.html'
    def get_queryset(self):
        return CustomUser.objects.filter(assigned_to=self.request.user)

class ManageRolesView(UserPassesTestMixin, ListView):
    model = Role
    template_name = 'roles/manage_roles.html'
    context_object_name = 'roles'
    def test_func(self): return self.request.user.is_superuser
    def get_queryset(self): return Role.objects.annotate(user_count=Count('users'))

class RoleCreateView(UserPassesTestMixin, CreateView):
    model = Role
    form_class = RoleForm
    template_name = 'roles/add_role.html'
    success_url = reverse_lazy('manage_roles')
    def test_func(self): return self.request.user.is_superuser

class RoleUpdateView(UserPassesTestMixin, UpdateView):
    model = Role
    form_class = RoleForm
    template_name = 'roles/edit_role.html'
    success_url = reverse_lazy('manage_roles')
    def test_func(self): return self.request.user.is_superuser

class RoleDeleteView(UserPassesTestMixin, DeleteView):
    model = Role
    success_url = reverse_lazy('manage_roles')
    def test_func(self): return self.request.user.is_superuser
    def get(self, request, *args, **kwargs):
        role = self.get_object()
        if not role.users.exists():
            role.delete()
            messages.success(request, "Role deleted.")
        else:
            messages.error(request, "Cannot delete role with assigned users.")
        return redirect(self.success_url)

# =========================================================
#             4. SETTINGS & AUTH VIEWS
# =========================================================

class SiteSettingsUpdateView(UserPassesTestMixin, FormView):
    form_class = SiteSettingsKeyForm
    template_name = 'settings/site_settings.html' 
    success_url = reverse_lazy('site_settings') 
    def test_func(self): return self.request.user.is_superuser
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        combined = []
        for setting in context['form'].settings:
            combined.append({
                'value_field': context['form'][setting.var_name],
                'description_field': context['form'][f'desc_{setting.var_name}'],
                'var_name': setting.var_name,
                'label': context['form'][setting.var_name].label
            })
        context['combined_settings_list'] = combined
        return context
    def form_valid(self, form):
        form.save()
        messages.success(self.request, "Settings updated.")
        return super().form_valid(form)

class CustomPasswordChangeView(LoginRequiredMixin, FormView):
    template_name = 'registration/password_change_form.html'
    success_url = reverse_lazy('login')
    def get_form_class(self):
        from django.contrib.auth.forms import PasswordChangeForm
        return PasswordChangeForm
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    def form_valid(self, form):
        user = form.save()
        update_session_auth_hash(self.request, user)
        messages.success(self.request, "Password updated.")
        return super().form_valid(form)





class SubcribersHubView(LoginRequiredMixin, FormView):
    """Handles manual addition, bulk CSV upload, and listing of subscribers."""
    template_name = 'subscribers_list.html'
    form_class = Subcribers
    success_url = reverse_lazy('subscriber_list')

    def get_success_url(self):
        next_url = self.request.POST.get('next') or self.request.META.get('HTTP_REFERER')
        
        if next_url:
            return next_url
        return reverse_lazy('subscriber_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['subscribers'] = ExternalSubscriber.objects.all().order_by('-id')
        if 'bulk_form' not in context:
            context['bulk_form'] = CSVUploadForm()
        return context

    def post(self, request, *args, **kwargs):
        # Determine if this is a bulk upload or manual addition
        if 'csv_file' in request.FILES:
            return self.handle_bulk_upload(request)
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        subscriber = form.save(commit=False)
        subscriber.ip_address = get_client_ip(self.request)
        subscriber.save() # Triggers Celery IP lookup in signals/models
        messages.success(self.request, "Subscriber added successfully!")
        return HttpResponseRedirect(self.get_success_url())

    def handle_bulk_upload(self, request):
        bulk_form = CSVUploadForm(request.POST, request.FILES)
        if bulk_form.is_valid():
            csv_file = request.FILES['csv_file']
            if not csv_file.name.endswith('.csv'):
                messages.error(request, 'Please upload a valid CSV file.')
                return redirect(self.success_url)

            try:
                data_set = csv_file.read().decode('UTF-8')
                io_string = io.StringIO(data_set)
                reader = csv.reader(io_string, delimiter=',', quotechar="|")
                next(reader) # Skip header

                created_count = 0
                client_ip = get_client_ip(request)
                for row in reader:
                    if not row: continue
                    email = row[0].strip()
                    if email and not ExternalSubscriber.objects.filter(email=email).exists():
                        ExternalSubscriber.objects.create(email=email, ip_address=client_ip)
                        created_count += 1
                
                messages.success(request, f"Successfully imported {created_count} new subscribers.")
            except Exception as e:
                messages.error(request, f"Error processing file: {e}")
        else:
            messages.error(request, "Bulk upload failed. Check the file format.")
        
        return redirect(self.success_url)


class SubscriberDeleteView(LoginRequiredMixin, DeleteView):
    model = ExternalSubscriber
    success_url = reverse_lazy('subscriber_list')
    
    def get(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        messages.warning(request, "Subscriber removed.")
        return super().delete(request, *args, **kwargs)


class DownloadCSVTemplateView(LoginRequiredMixin, View):
    """Exports all current subscribers to a CSV file."""
    def get(self, request):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="all_subscribers.csv"'
        writer = csv.writer(response)
        
        writer.writerow(['Email', 'Date Subscribed', 'IP Address', 'Region'])
        subscribers = ExternalSubscriber.objects.all().values_list(
            'email', 'date_subscribed', 'ip_address', 'region'
        )
        
        for sub in subscribers:
            writer.writerow(sub)

        return response


class BroadcastCreateView(LoginRequiredMixin, CreateView):
    model = NewsPost
    form_class = BroadcastForm
    template_name = 'send_email.html'
    success_url = reverse_lazy('broadcast_dashboard')

    def get(self, request, *args, **kwargs):
        """Handle AJAX requests for audience emails."""
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            audience = request.GET.get('audience')
            emails = set()

            if audience == 'is_manager':
                emails.update(CustomUser.objects.filter(is_manager=True, is_active=True).values_list('email', flat=True))
            elif audience == 'super_admin':
                emails.update(CustomUser.objects.filter(is_superuser=True, is_active=True).values_list('email', flat=True))
            elif audience == 'administrator':
                emails.update(CustomUser.objects.filter(is_staff=True, is_active=True).values_list('email', flat=True))
            elif audience == 'clients':
                emails.update(CustomUser.objects.filter(role__name__iexact='Clients', is_active=True).values_list('email', flat=True))
            elif audience == 'staff_only':
                emails.update(CustomUser.objects.filter(role__name__iexact='Staff', is_active=True).values_list('email', flat=True))
            elif audience == 'external_only':
                emails.update(ExternalSubscriber.objects.values_list('email', flat=True))
            elif audience == 'all':
                u_emails = CustomUser.objects.filter(is_active=True).values_list('email', flat=True)
                e_emails = ExternalSubscriber.objects.values_list('email', flat=True)
                emails.update(u_emails)
                emails.update(e_emails)

            return JsonResponse({'emails': sorted(list(emails))})

        return super().get(request, *args, **kwargs)

    def get_initial(self):
        """Prefill form if reusing a post."""
        initial = super().get_initial()
        reuse_id = self.request.GET.get('reuse')
        if reuse_id:
            post = get_object_or_404(NewsPost, id=reuse_id)
            initial.update({
                'title': post.title,
                'subject': post.subject,
                'content': post.content,
                'sender_email': post.sender_email,
                'target_audience': post.target_audience,
                'scheduled_time': post.scheduled_time
            })
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['recent_posts'] = NewsPost.objects.all().order_by('-created_at')[:10]
        return context

    # def form_valid(self, form):
    #     post = form.save(commit=False)

    #     if not post.sender_email:
    #         post.sender_email = settings.DEFAULT_FROM_EMAIL

    #     post.save()

    #     # Detect browser timezone
    #     user_tz_str = self.request.POST.get("user_timezone", "UTC")
    #     user_tz = ZoneInfo(user_tz_str)

    #     scheduled_time = post.scheduled_time
    #     now_utc = timezone.now()

    #     if scheduled_time:
    #         if is_naive(scheduled_time):
    #             scheduled_time = make_aware(scheduled_time, user_tz)

    #         scheduled_time_utc = scheduled_time.astimezone(ZoneInfo("UTC"))

    #         if scheduled_time_utc <= now_utc:
    #             # SEND NOW
    #             send_broadcast_task.delay(post.id)
    #             post.status = "sending"
    #         else:
    #             # SCHEDULE
    #             send_broadcast_task.apply_async(
    #                 args=[post.id],
    #                 eta=scheduled_time_utc
    #             )
    #             post.status = "scheduled"
    #     else:
    #         # No time → send now
    #         send_broadcast_task.delay(post.id)
    #         post.status = "sending"

    #     post.save(update_fields=["status"])
    #     return redirect(self.success_url)




    def form_valid(self, form):
        self.object = form.save()

        # Gather recipients
        recipient_list = self.request.POST.getlist('final_recipients')
        if not recipient_list:
            recipient_list = self.object.gather_emails()

        if not recipient_list:
            messages.error(self.request, "No recipients found.")
            return redirect(self.success_url)

        # Get scheduled time from form
        scheduled_time = self.object.scheduled_time

        # Detect user timezone from hidden input
        user_tz_str = self.request.POST.get('user_timezone', 'UTC')
        try:
            user_tz = ZoneInfo(user_tz_str)
        except Exception:
            user_tz = ZoneInfo('UTC')

        # Make aware datetime in user's timezone
        if scheduled_time:
            if is_naive(scheduled_time):
                scheduled_time = make_aware(scheduled_time, user_tz)
            scheduled_time_utc = scheduled_time.astimezone(ZoneInfo('UTC'))
        else:
            scheduled_time_utc = None

        current_time_utc = timezone_now()

        # Decide whether to send immediately or schedule
        if scheduled_time_utc and scheduled_time_utc > current_time_utc:
            # Schedule for future
            send_broadcast_task.apply_async(
                kwargs={
                    'post_id': self.object.id,
                    'recipient_list': recipient_list,
                    'from_email': self.object.sender_email
                },
                eta=scheduled_time_utc
            )
            self.object.status = 'scheduled'
            messages.success(
                self.request,
                f"📅 Broadcast scheduled for {scheduled_time.strftime('%Y-%m-%d %H:%M:%S')} ({user_tz_str})"
            )
        else:
            # Send immediately
            send_broadcast_task.delay(
                post_id=self.object.id,
                recipient_list=recipient_list,
                from_email=self.object.sender_email
            )
            self.object.status = 'sending'
            messages.success(self.request, "🚀 Broadcast is being sent immediately.")

        self.object.save(update_fields=['status'])
        return redirect(self.success_url)



class BroadcastDeleteView(LoginRequiredMixin, DeleteView):
    model = NewsPost
    success_url = reverse_lazy('broadcast_dashboard')

    def get(self, request, *args, **kwargs):
        """Allows deletion via a simple link (GET request)."""
        return self.post(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Broadcast history removed.")
        return super().delete(request, *args, **kwargs)


@role_permission_required('can_create_user')
def create_new_student_record(request):
    return render(request, 'dashboard/create_student.html', {})
