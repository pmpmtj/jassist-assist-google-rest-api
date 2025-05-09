from django import forms
from .models import ManualEntry
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Field, Div
import logging

logger = logging.getLogger(__name__)

class ManualEntryForm(forms.ModelForm):
    """
    Form for creating and editing manual entries.
    Includes validation to ensure content is at least 15 characters.
    """
    
    class Meta:
        model = ManualEntry
        fields = ['content', 'classification']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 5, 'placeholder': 'Enter your text here (minimum 15 characters)'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-md-3'
        self.helper.field_class = 'col-md-9'
        self.helper.layout = Layout(
            Field('classification'),
            Field('content', css_class='form-control'),
            Div(
                Submit('submit', 'Save Entry', css_class='btn btn-primary mt-3'),
                css_class='text-center'
            )
        )
    
    def clean_content(self):
        content = self.cleaned_data.get('content')
        if content and len(content) < 15:
            logger.debug(f"Content validation failed: too short ({len(content)} chars)")
            raise forms.ValidationError("Content must be at least 15 characters long.")
        return content 