
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


class GroupInvitationForm(forms.Form):
    email = forms.EmailField(
        label="Correo del usuario",
        max_length=254,
        widget=forms.EmailInput(
            attrs={
                "placeholder": "usuario@ejemplo.com",
            }
        ),
    )

    def clean_email(self):
        return self.cleaned_data["email"].strip().lower()
