from django import forms
from .models import Contact
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Field, Div, HTML
import logging

logger = logging.getLogger(__name__)

class ContactForm(forms.ModelForm):
    """
    Form for creating and editing contacts.
    """
    
    class Meta:
        model = Contact
        fields = ['name', 'email', 'phone', 'address', 'notes', 'category']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Full Name'}),
            'email': forms.EmailInput(attrs={'placeholder': 'Email Address'}),
            'phone': forms.TextInput(attrs={'placeholder': 'Phone Number'}),
            'address': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Physical Address'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Additional Notes'}),
            'category': forms.TextInput(attrs={'placeholder': 'Category (optional)'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-md-3'
        self.helper.field_class = 'col-md-9'
        
        # Only name is required
        self.fields['name'].required = True
        for field_name in ['email', 'phone', 'address', 'notes', 'category']:
            self.fields[field_name].required = False
        
        self.helper.layout = Layout(
            Field('name', css_class='form-control'),
            Field('email', css_class='form-control'),
            Field('phone', css_class='form-control'),
            Field('category', css_class='form-control'),
            Field('address', css_class='form-control'),
            Field('notes', css_class='form-control'),
            Div(
                Submit('submit', 'Save Contact', css_class='btn btn-primary mt-3'),
                HTML('<a href="{% url \'contacts:list\' %}" class="btn btn-secondary mt-3 ms-2">Cancel</a>'),
                css_class='text-center'
            )
        )
    
    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        # Basic phone validation - allow only digits, spaces, parentheses, dashes, and plus sign
        if phone and not all(char in "0123456789 ()-+." for char in phone):
            logger.debug(f"Phone validation failed: invalid characters in {phone}")
            raise forms.ValidationError("Phone number can only contain digits, spaces, parentheses, dashes, plus sign, and periods.")
        return phone 