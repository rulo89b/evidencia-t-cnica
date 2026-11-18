
from django import forms

from .models import Template


class TemplateForm(forms.ModelForm):

    class Meta:
        model = Template
        fields = ["name", "description"]

        labels = {
            "name": "Nombre",
            "description": "Descripción",
        }

        widgets = {
            "description": forms.Textarea(
                attrs={"rows": 4}
            ),
        }
