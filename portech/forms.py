from django import forms
from users.models import ExternalSubscriber



class SubcribersForm(forms.ModelForm):
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
