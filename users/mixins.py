from django.contrib.auth.mixins import AccessMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from functools import wraps

# --- Class-Based View Mixin ---

# Helper function to check for Super Admin status
def is_super_admin(user):
    """Checks if the user is authenticated and has superuser status."""
    return user.is_authenticated and user.is_superuser


class RolePermissionRequiredMixin(AccessMixin):
    """
    Mixin to check if the current user's role has a specific boolean permission field set to True.
    """
    required_permission = None  # Example: 'can_create_user'

    def dispatch(self, request, *args, **kwargs):
        # 1. Check if the user is authenticated
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        user_role = request.user.role

        # 2. Check if the user has a role and if the required_permission is set
        if user_role and hasattr(user_role, self.required_permission):
            # Use getattr to dynamically fetch the permission field value (True/False)
            if getattr(user_role, self.required_permission):
                return super().dispatch(request, *args, **kwargs)

        # 3. If permission check fails
        return self.handle_no_permission()

# --- Function-Based View Decorator ---

def role_permission_required(permission_name):
    """
    Decorator for Function-Based Views (FBVs) to check role permissions.
    Usage: @role_permission_required('can_assign_staff')
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                # Redirect unauthenticated users to the login page (or handle_no_permission)
                return redirect('login') 

            user_role = request.user.role

            if user_role and hasattr(user_role, permission_name):
                if getattr(user_role, permission_name):
                    return view_func(request, *args, **kwargs)

            # If permission check fails, raise 403 Forbidden
            raise PermissionDenied
        return wrapper
    return decorator