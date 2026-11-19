
from django import forms

from .models import Template, TemplatePhoto, Job


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


class JobForm(forms.ModelForm):

    class Meta:
        model = Job

        fields = [
            "template",
            "site_name",
            "notes",
            "due_date",
        ]

        labels = {
            "template": "Plantilla",
            "site_name": "Nombre del sitio",
            "notes": "Notas",
            "due_date": "Fecha límite",
        }

        widgets = {
            "notes": forms.Textarea(attrs={"rows": 4}),
            "due_date": forms.DateInput(
                attrs={"type": "date"}
            ),
        }

    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["template"].queryset = (
            Template.objects.filter(
                owner=user,
                deleted_at__isnull=True,
            ).order_by("name")
        )


class JobPhotoForm(forms.Form):
    photo = forms.ImageField(
        label="Fotografía",
        widget=forms.ClearableFileInput(
            attrs={
                "accept": "image/jpeg,image/png,image/webp",
                "capture": "environment",
            }
        ),
    )

    def clean_photo(self):
        photo = self.cleaned_data["photo"]

        if photo.size > 10 * 1024 * 1024:
            raise forms.ValidationError(
                "La fotografía no puede superar 10 MB."
            )

        if photo.image.format not in ("JPEG", "PNG", "WEBP"):
            raise forms.ValidationError(
                "Solo se aceptan imágenes JPEG, PNG o WebP."
            )

        return photo
