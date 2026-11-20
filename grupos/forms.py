
from django import forms

from .models import Group


class GroupForm(forms.ModelForm):
    class Meta:
        model = Group

        fields = ["name", "description"]

        labels = {
            "name": "Nombre del grupo",
            "description": "Descripción",
        }

        widgets = {
            "description": forms.Textarea(
                attrs={"rows": 3}
            ),
        }
