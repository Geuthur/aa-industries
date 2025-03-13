"""Models for Industries."""

# Django
from django.db import models
from django.utils.translation import gettext_lazy as _


class General(models.Model):
    """A model defining permissions for Industries."""

    class Meta:
        managed = False
        default_permissions = ()
        permissions = (
            ("basic_access", "Can access this app, Industries."),
            ("manage_access", "Can manage Industries."),
            ("corp_access", "Can access own Corporation."),
            ("corp_character_access", "Can access other Character's for own Corp."),
            ("ally_access", "Can access own Alliance."),
            ("ally_character_access", "Can access other Character's for own Alliance."),
            ("admin_access", "Can access all Alliance/Corporation/Character."),
        )
