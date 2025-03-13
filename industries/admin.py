from django.contrib import admin
from django.utils.html import format_html

from allianceauth.eveonline.evelinks import eveimageserver

from industries.models.industries import CharacterAudit


# TODO make a ETAG Cache clear option?
@admin.register(CharacterAudit)
class CharacterAuditAdmin(admin.ModelAdmin):
    """Admin Interface for Characters"""

    model = CharacterAudit
    model._meta.verbose_name = "Character"
    model._meta.verbose_name_plural = "Characters"

    list_display = (
        "_entity_pic",
        "_character__character_id",
        "_character__character_name",
        "_last_update_industry",
    )

    list_display_links = (
        "_entity_pic",
        "_character__character_id",
        "_character__character_name",
    )

    list_select_related = ("character",)

    ordering = ["character__character_name"]

    search_fields = ["character__character_name", "character__character_id"]

    actions = [
        "delete_objects",
    ]

    @admin.display(description="")
    def _entity_pic(self, obj: CharacterAudit):
        eve_id = obj.character.character_id
        return format_html(
            '<img src="{}" class="img-circle">',
            eveimageserver._eve_entity_image_url("character", eve_id, 32),
        )

    @admin.display(description="Character ID", ordering="character__character_id")
    def _character__character_id(self, obj: CharacterAudit):
        return obj.character.character_id

    @admin.display(description="Character Name", ordering="character__character_name")
    def _character__character_name(self, obj: CharacterAudit):
        return obj.character.character_name

    @admin.display(description="Last Update Industry", ordering="last_update_industry")
    def _last_update_industry(self, obj: CharacterAudit):
        return obj.last_update_industry

    # pylint: disable=unused-argument
    def has_add_permission(self, request):
        return False

    # pylint: disable=unused-argument
    def has_change_permission(self, request, obj=None):
        return False
