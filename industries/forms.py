"""Forms for the taxsystem app."""

from django import forms
from django.utils.translation import gettext_lazy as _


class BlueprintForm(forms.Form):
    blueprint = forms.CharField(
        label="Blueprint",
        help_text="Select your Blueprint. Start typing to see suggestions.",
        required=True,
    )

    blueprint_id = forms.IntegerField(
        label="Blueprint ID",
        initial=0,
        required=False,
        widget=forms.HiddenInput(),
    )
