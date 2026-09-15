from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

# extends djangos signup form to require and validate the email address
class CreateAccountForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email')

    # blocks signup if the email is already registered to another account
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email=email).exists():
            raise forms.ValidationError('An account with this email already exists.')
        return email