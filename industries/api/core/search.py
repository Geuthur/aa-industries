from typing import Any

from ninja import NinjaAPI

from django.utils.translation import gettext as _
from eveuniverse.models import (
    EveIndustryActivityMaterial,
    EveIndustryActivityProduct,
    EveType,
    EveTypeMaterial,
)

from industries.hooks import get_extension_logger

logger = get_extension_logger(__name__)

CACHE_TIME = 60 * 60 * 24


class SearchApiEndpoints:
    tags = ["Search"]

    # pylint: disable=too-many-statements
    def __init__(self, api: NinjaAPI):
        @api.get(
            "blueprint/{blueprint_id}/view/industryactivitymaterial/",
            response={200: Any},
            tags=["Search"],
            description=_("Get the materials required to build a blueprint product."),
        )
        def eveindustryactivitymaterial(request, blueprint_id: str):
            if not request.user.has_perm("industries.admin_access"):
                return 403, _("Permission Denied")

            # pylint: disable=duplicate-code
            try:
                blueprint = EveType.objects.get(id=blueprint_id)
            except EveType.DoesNotExist:
                return 404, _("Blueprint not found")

            if not EveIndustryActivityMaterial.objects.filter(
                eve_type=blueprint
            ).exists():
                EveIndustryActivityMaterial.objects.update_or_create_api(
                    eve_type=blueprint
                )

            material_data = []

            materials = EveIndustryActivityMaterial.objects.filter(eve_type=blueprint)

            for material in materials:
                material_data.append(
                    {
                        "material_eve_type__name": material.material_eve_type.name,
                        "material_eve_type_id": material.material_eve_type.id,
                        "quantity": material.quantity,
                    }
                )

            industry_data = {
                "blueprint": blueprint.name,
                "materials": material_data,
            }

            return industry_data

        @api.get(
            "evetype/{eve_id}/view/typematerial/",
            response={200: Any},
            tags=["Search"],
            description="Get the materials from a eve type.",
        )
        def evetypematerial(request, eve_id: str):
            if not request.user.has_perm("industries.admin_access"):
                return 403, _("Permission Denied")

            evetype = EveType.objects.get(id=eve_id)
            if not EveTypeMaterial.objects.filter(eve_type=evetype).exists():
                EveTypeMaterial.objects.update_or_create_api(eve_type=evetype)

            material_data = []

            materials = EveTypeMaterial.objects.filter(eve_type=evetype)

            for material in materials:
                material_data.append(
                    {
                        "material_eve_type__name": material.material_eve_type.name,
                        "material_eve_type_id": material.material_eve_type.id,
                        "quantity": material.quantity,
                    }
                )

            industry_data = {
                "eve_type": evetype.name,
                "materials": material_data,
            }

            return industry_data

        @api.get(
            "evetype/{eve_id}/view/industryactivityproduct/",
            response={200: Any},
            tags=["Search"],
            description=_("Get Quantities of products for blueprints."),
        )
        def eveindustryactivityproduct(request, eve_id: str):
            if not request.user.has_perm("industries.admin_access"):
                return 403, _("Permission Denied")

            evetype = EveType.objects.get(id=eve_id)
            if not EveIndustryActivityProduct.objects.filter(eve_type=evetype).exists():
                logger.debug("Product not found: %s", evetype)
                EveIndustryActivityProduct.objects.update_or_create_api(
                    eve_type=evetype
                )

            material_data = []

            materials = EveIndustryActivityProduct.objects.filter(eve_type=evetype)

            for material in materials:
                material_data.append(
                    {
                        "material_eve_type__name": material.eve_type.name,
                        "material_eve_type_id": material.eve_type.id,
                        "product_eve_type__name": material.product_eve_type.name,
                        "product_eve_type_id": material.product_eve_type.id,
                        "quantity": material.quantity,
                    }
                )

            industry_data = {
                "eve_type": evetype.name,
                "materials": material_data,
            }

            return industry_data
