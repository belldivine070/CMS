from .models import AppVariable, Category


def app_settings_processor(request):
    settings_dict = {}
    try:
        # Fetch only the var_name and var_value columns
        variables = AppVariable.objects.all().values('var_name', 'var_value')
        
        for var in variables:
            # Add the setting directly to the dictionary
            settings_dict[var['var_name']] = var['var_value']
            
        # Optional print statements for debugging (remove in production)
        # print("\n--- APP VARIABLE KEYS LOADED ---")
        # print(settings_dict.keys())
        # print("--------------------------------\n")
            
    except Exception as e:
        print(f"Error loading AppVariables: {e}")
        # Return an empty dictionary if loading fails
        settings_dict = {}

    # CRITICAL FIX: Return the dictionary directly, not nested
    return settings_dict