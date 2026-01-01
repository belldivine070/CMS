from django.db import migrations, models

def create_initial_roles(apps, schema_editor):
    Role = apps.get_model('users', 'Role')
    
    # 1. SUPER ADMIN ROLE (Mandatory for createsuperuser)
    # Note: We don't set is_superuser here, the user model handles that.
    Role.objects.get_or_create(
        name='Super Administrator', 
        slug='super_admin',
        defaults={
            'can_create_user': True,
            'can_assign_staff': True,
        }
    )
    
    # 2. GENERAL MANAGER ROLE (Example for high-level staff)
    Role.objects.get_or_create(
        name='General Manager', 
        slug='manager',
        defaults={
            'can_create_user': True,
            'can_assign_staff': True,
        }
    )

def reverse_initial_roles(apps, schema_editor):
    Role = apps.get_model('users', 'Role')
    Role.objects.filter(slug__in=['super_admin', 'manager']).delete()

class Migration(migrations.Migration):

    dependencies = [
        # Ensure the dependency points to your last migration file (e.g., 0003)
        ('users', '0003_appvariable'), 
    ]

    operations = [
        migrations.RunPython(create_initial_roles, reverse_initial_roles),
    ]

   