from django import forms
from .models import Contact
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Field, Div, HTML, Fieldset
import logging

logger = logging.getLogger(__name__)

class ContactForm(forms.ModelForm):
    """
    Form for creating and editing contacts with comprehensive information.
    """
    
    class Meta:
        model = Contact
        fields = [
            'first_name', 'last_name', 'alias',
            'email', 'private_email', 'professional_email',
            'phone', 'private_phone', 'professional_phone',
            'address', 'notes', 'category'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'placeholder': 'First Name'}),
            'last_name': forms.TextInput(attrs={'placeholder': 'Last Name'}),
            'alias': forms.TextInput(attrs={'placeholder': 'Nickname or Alias (optional)'}),
            'email': forms.EmailInput(attrs={'placeholder': 'Main Email Address'}),
            'private_email': forms.EmailInput(attrs={'placeholder': 'Private Email Address'}),
            'professional_email': forms.EmailInput(attrs={'placeholder': 'Work Email Address'}),
            'phone': forms.TextInput(attrs={'placeholder': 'Main Phone Number'}),
            'private_phone': forms.TextInput(attrs={'placeholder': 'Private/Mobile Phone'}),
            'professional_phone': forms.TextInput(attrs={'placeholder': 'Work Phone Number'}),
            'address': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Physical Address'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Additional Notes'}),
            'category': forms.TextInput(attrs={'placeholder': 'Category (optional)'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_class = 'form-horizontal'
        
        # Only first_name is required
        self.fields['first_name'].required = True
        for field_name in self.fields:
            if field_name != 'first_name':
                self.fields[field_name].required = False
        
        self.helper.layout = Layout(
            Fieldset(
                'Basic Information',
                Div(
                    Div(Field('first_name'), css_class='col-md-6'),
                    Div(Field('last_name'), css_class='col-md-6'),
                    css_class='row'
                ),
                Field('alias'),
                Field('category'),
            ),
            Fieldset(
                'Contact Information',
                Div(
                    Div(Field('email'), css_class='col-md-6'),
                    Div(Field('phone'), css_class='col-md-6'),
                    css_class='row'
                ),
                Div(
                    Div(Field('private_email'), css_class='col-md-6'),
                    Div(Field('private_phone'), css_class='col-md-6'),
                    css_class='row'
                ),
                Div(
                    Div(Field('professional_email'), css_class='col-md-6'),
                    Div(Field('professional_phone'), css_class='col-md-6'),
                    css_class='row'
                ),
            ),
            Fieldset(
                'Additional Details',
                Field('address'),
                Field('notes'),
            ),
            Div(
                Submit('submit', 'Save Contact', css_class='btn btn-primary mt-3'),
                HTML('<a href="{% url \'contacts:list\' %}" class="btn btn-secondary mt-3 ms-2">Cancel</a>'),
                css_class='text-center'
            )
        )
    
    def clean_phone(self):
        return self._validate_phone_field('phone')
        
    def clean_private_phone(self):
        return self._validate_phone_field('private_phone')
        
    def clean_professional_phone(self):
        return self._validate_phone_field('professional_phone')
        
    def _validate_phone_field(self, field_name):
        phone = self.cleaned_data.get(field_name)
        # Basic phone validation - allow only digits, spaces, parentheses, dashes, and plus sign
        if phone and not all(char in "0123456789 ()-+." for char in phone):
            logger.debug(f"{field_name} validation failed: invalid characters in {phone}")
            raise forms.ValidationError("Phone number can only contain digits, spaces, parentheses, dashes, plus sign, and periods.")
        return phone 