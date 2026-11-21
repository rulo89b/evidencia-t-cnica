
from django import forms
from django.contrib.auth import get_user_model

from .models import Template, TemplatePhoto, Job
from grupos.models import GroupMember

User = get_user_model()


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


class GroupJobForm(forms.ModelForm):

    class Meta:
        model = Job

        fields = [
            "template",
            "assigned_to",
            "site_name",
            "notes",
            "due_date",
        ]

        labels = {
            "template": "Plantilla",
            "assigned_to": "Técnico responsable",
            "site_name": "Nombre del sitio",
            "notes": "Notas",
            "due_date": "Fecha límite",
        }

        widgets = {
            "notes": forms.Textarea(
                attrs={"rows": 4}
            ),
            "due_date": forms.DateInput(
                attrs={"type": "date"}
            ),
        }

    def __init__(self, *args, user, group, **kwargs):
        super().__init__(*args, **kwargs)

        # Solo plantillas personales del administrador.
        self.fields["template"].queryset = (
            Template.objects.filter(
                owner=user,
                deleted_at__isnull=True,
            ).order_by("name")
        )

        # Solo usuarios que pertenecen al grupo.
        member_ids = GroupMember.objects.filter(
            group=group,
        ).values_list("user_id", flat=True)

        self.fields["assigned_to"].queryset = (
            User.objects.filter(
                pk__in=member_ids
            ).order_by("username")
        )

        self.fields["template"].empty_label = (
            "Selecciona una plantilla"
        )

        self.fields["assigned_to"].empty_label = (
            "Selecciona un responsable"
        )


class GroupJobReassignForm(forms.Form):

    assigned_to = forms.ModelChoiceField(
        queryset=User.objects.none(),
        label="Nuevo responsable",
        empty_label="Selecciona un técnico",
    )

    def __init__(
        self,
        *args,
        group,
        current_assignee,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)

        member_ids = GroupMember.objects.filter(
            group=group,
        ).values_list("user_id", flat=True)

        self.fields["assigned_to"].queryset = (
            User.objects.filter(
                pk__in=member_ids
            )
            .exclude(pk=current_assignee.pk)
            .order_by("username")
        )
