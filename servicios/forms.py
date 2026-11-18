
from django import forms

from .models import Template, TemplatePhoto


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


class TemplatePhotoForm(forms.ModelForm):

    class Meta:
        model = TemplatePhoto

        fields = [
            "title",
            "instructions",
            "stage",
            "is_required",
        ]

        labels = {
            "title": "Título",
            "instructions": "Instrucciones",
            "stage": "Etapa",
            "is_required": "Fotografía obligatoria",
        }

        widgets = {
            "instructions": forms.Textarea(
                attrs={"rows": 4}
            ),
        }
