from django import forms
from django.contrib.auth.forms import AuthenticationForm
import datetime


class RegisterForm(forms.Form):
    name     = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'placeholder': 'Full Name'}))
    email    = forms.EmailField(widget=forms.EmailInput(attrs={'placeholder': 'Email'}))
    password = forms.CharField(min_length=6, widget=forms.PasswordInput(attrs={'placeholder': 'Password'}))
    confirm  = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Confirm Password'}))

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('password') != cleaned.get('confirm'):
            raise forms.ValidationError("Passwords do not match.")
        return cleaned


class LoginForm(forms.Form):
    email    = forms.EmailField(widget=forms.EmailInput(attrs={'placeholder': 'Email'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Password'}))


class TransactionForm(forms.Form):
    from .models import Category
    amount      = forms.DecimalField(min_value=0.01, decimal_places=2)
    category    = forms.ModelChoiceField(queryset=None)
    description = forms.CharField(max_length=255, required=False)
    date        = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}),
                                  initial=datetime.date.today)

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        from .models import Category
        if user:
            self.fields['category'].queryset = Category.objects.filter(
                models.Q(source='system') | models.Q(owner=user)
            )
        else:
            self.fields['category'].queryset = Category.objects.filter(source='system')

    # fix import inside __init__
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        from .models import Category
        from django.db.models import Q
        if user:
            self.fields['category'].queryset = Category.objects.filter(
                Q(source='system') | Q(owner=user)
            )
        else:
            self.fields['category'].queryset = Category.objects.filter(source='system')


class BudgetForm(forms.Form):
    category   = forms.ModelChoiceField(queryset=None)
    amount     = forms.DecimalField(min_value=0.01, decimal_places=2, label='Limit Amount')
    start_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    end_date   = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        from .models import Category
        from django.db.models import Q
        if user:
            self.fields['category'].queryset = Category.objects.filter(
                Q(source='system') | Q(owner=user)
            )
        else:
            self.fields['category'].queryset = Category.objects.filter(source='system')

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('start_date') and cleaned.get('end_date'):
            if cleaned['end_date'] <= cleaned['start_date']:
                raise forms.ValidationError("End date must be after start date.")
        return cleaned
