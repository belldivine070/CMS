from django.urls import path
from . import views
from django.contrib.auth.views import LoginView, LogoutView
from .forms import EmailAuthenticationForm 

app_name = 'users' 

urlpatterns = [
    # =========================================================
    # 0. AUTH / INDEX / SYSTEM SETTINGS
    # =========================================================
    path("", views.IndexView.as_view(), name="index"),
    path('site/settings/', views.SiteSettingsUpdateView.as_view(), name='site_settings'),
    
    path('login/', LoginView.as_view(
        template_name='registration/login.html', 
        authentication_form=EmailAuthenticationForm,
        next_page='index' 
    ), name='login'), 
    path('logout/', LogoutView.as_view(next_page='users:login'), name='logout'),
    path('password/change/', views.CustomPasswordChangeView.as_view(), name='password_change'),
    
    # =========================================================
    # 1. CATEGORY & WIDGET DEFINITIONS (CRUD)
    # =========================================================
    
    # --- Categories ---
    path('category/lists/', views.CategoryListView.as_view(), name='category_list'),
    path('category/create/', views.CategoryCreateView.as_view(), name='category_create'),
    path('category/update/<slug:slug>/', views.CategoryEditView.as_view(), name='category_update'),
    path('category/delete/<slug:slug>/', views.CategoryDeleteView.as_view(), name='category_delete'),

    # --- Widgets ---
    path('widget/lists/', views.WidgetListView.as_view(), name='widget_list'),
    path('widget/create/', views.WidgetCreateView.as_view(), name='widget_create'),
    path('widget/update/<slug:slug>/', views.WidgetEditView.as_view(), name='widget_update'),
    path('widget/delete/<slug:slug>/', views.WidgetDeleteView.as_view(), name='widget_delete'),

    # =========================================================
    # 2. USER / ROLE MANAGEMENT
    # =========================================================
    path('users/', views.ManageUsersListView.as_view(), name='manage_users'),
    path('users/register/', views.AdminRegisterUserView.as_view(), name='register_user'),
    path('users/edit/<uuid:pk>/', views.EditSubordinateView.as_view(), name='edit_user'),
    path('users/details/<uuid:pk>/', views.UserDetailView.as_view(), name='user_detail'),
    path('roles/add/', views.RoleCreateView.as_view(), name='add_role'),
    path('roles/manage/', views.ManageRolesView.as_view(), name='manage_roles'),
    path('roles/edit/<int:pk>/', views.RoleUpdateView.as_view(), name='edit_role'),
    path('roles/delete/<int:pk>/', views.RoleDeleteView.as_view(), name='delete_role'),

    # =========================================================
    # 3. CHILD POSTS (CATEGORY POSTS & WIDGET POSTS)
    # =========================================================

    # --- Category Post CRUD ---
    path('category/<slug:category_slug>/posts/', views.PostListByCategoryView.as_view(), name='post_list_by_category'), 
    path('category/<slug:category_slug>/create/', views.PostCreateView.as_view(), name='post_create'),
    path('category/<slug:category_slug>/edit/<slug:post_slug>/', views.PostEditView.as_view(), name='post_edit'),
    path('category/<slug:category_slug>/delete/<slug:post_slug>/', views.PostDeleteView.as_view(), name='category_post_delete'), 

    # --- Widget Post CRUD ---
    path('widget/<slug:widget_slug>/posts/', views.PostListByWidgetView.as_view(), name='post_list_by_widget'), 
    path('widget/<slug:widget_slug>/create/', views.WidgetPostCreateView.as_view(), name='widget_post_create'),
    path('widget/<slug:widget_slug>/edit/<slug:post_slug>/', views.WidgetPostEditView.as_view(), name='widget_post_edit'),
    path('widget/<slug:widget_slug>/delete/<slug:post_slug>/', views.WidgetPostDeleteView.as_view(), name='widget_post_delete'),


    # ==========================================    
    # Send Emails
    # ==========================================
    
    # --- Subscriber Management ---
    path('subscribers/', views.SubcribersHubView.as_view(), name='subscriber_list'),
    path('subscriber/delete/<int:pk>/', views.SubscriberDeleteView.as_view(), name='delete_subscriber'),
    path('subscribers/download-csv/', views.DownloadCSVTemplateView.as_view(), name='download_subscribers_csv'),

    # --- Broadcast System ---
    path('broadcast/', views.BroadcastCreateView.as_view(), name='broadcast_dashboard'),
    path('broadcast/delete/<int:pk>/', views.BroadcastDeleteView.as_view(), name='delete_broadcast'),

]
