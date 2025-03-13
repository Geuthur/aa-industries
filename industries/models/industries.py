"""Models for Industries."""

# Django
from django.db import models
from django.utils.translation import gettext_lazy as _

from allianceauth.authentication.models import EveCharacter

from industries.managers import IndustriesManager


class CharacterAudit(models.Model):
    """Character model for Industries."""

    objects = IndustriesManager()

    name = models.CharField(
        max_length=255,
    )

    character = models.OneToOneField(
        EveCharacter,
        on_delete=models.CASCADE,
        related_name="+",
    )

    last_update_industry = models.DateTimeField(
        null=True,
        blank=True,
    )

    class Meta:
        abstract = True
        default_permissions = ()
        verbose_name = _("Industries Character Audit")
        verbose_name_plural = _("Industries Character Audits")
