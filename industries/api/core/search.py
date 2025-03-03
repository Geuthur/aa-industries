from typing import Any

from ninja import NinjaAPI

from django.shortcuts import render, resolve_url
from django.utils.translation import gettext as _
from eveuniverse.models import EveIndustryActivityMaterial, EveType, EveTypeMaterial

from industries.api.helpers import generate_button
from industries.constants import (
    AA_INDUSTRIES_CONSTRUCTION_CHAIN,
    AA_INDUSTRIES_PRODUCTION_CHAIN,
)
from industries.helpers import lazy
from industries.hooks import get_extension_logger

logger = get_extension_logger(__name__)

CACHE_TIME = 60 * 60 * 24


def get_reaction_blueprint(reaction: EveType):
    """Get the blueprint for a reaction"""
    reaction_formula_name = reaction.name + " Reaction Formula"
    reaction_formula = EveType.objects.filter(name=reaction_formula_name).first()
    if not reaction_formula:
        return None
    return reaction_formula


def get_materials(material: EveIndustryActivityMaterial):
    """Recursively get all materials for a given material"""
    material_dict = {
        "portrait": lazy.get_type_icon_url(
            type_id=material.material_eve_type.id,
            size=32,
            type_name=material.material_eve_type.name,
            as_html=True,
        ),
        "material_eve_type__name": material.material_eve_type.name,
        "material_eve_type_id": material.material_eve_type.id,
        "material_eve_type__group__id": material.material_eve_type.eve_group.id,
        "quantity": material.quantity,
        "materials": [],
    }
    reaction_blueprint = None

    # Check if the material is a reaction
    if material.material_eve_type.eve_group.id in AA_INDUSTRIES_PRODUCTION_CHAIN:
        reaction_blueprint = get_reaction_blueprint(material.material_eve_type)

    if reaction_blueprint is not None:
        if not EveIndustryActivityMaterial.objects.filter(
            eve_type=reaction_blueprint
        ).exists():
            EveIndustryActivityMaterial.objects.update_or_create_api(
                eve_type=reaction_blueprint
            )
        submaterials = EveIndustryActivityMaterial.objects.filter(
            eve_type=reaction_blueprint
        )
    else:
        if (
            not EveTypeMaterial.objects.filter(
                eve_type=material.material_eve_type
            ).exists()
            and material.material_eve_type.eve_group.id
            in AA_INDUSTRIES_CONSTRUCTION_CHAIN
        ):
            EveTypeMaterial.objects.update_or_create_api(
                eve_type=material.material_eve_type
            )
        submaterials = EveTypeMaterial.objects.filter(
            eve_type=material.material_eve_type
        )

    for submaterial in submaterials:
        submaterial_dict = get_materials(submaterial)
        material_dict["materials"].append(submaterial_dict)

    return material_dict


def get_details(request, material: EveIndustryActivityMaterial):
    """Get details for a material"""
    if (
        material.material_eve_type.eve_group.eve_category.id == 9
        or material.material_eve_type.eve_group.id
        in (AA_INDUSTRIES_CONSTRUCTION_CHAIN + AA_INDUSTRIES_PRODUCTION_CHAIN)
    ):
        template = "industries/partials/form/button.html"
        settings = {
            "title": _("Materials"),
            "icon": "fas fa-info",
            "color": "primary",
            "text": _("View Submaterials"),
            "modal": "modalViewDetailsContainer",
            "action": resolve_url(
                "industries:api:get_test", eve_id=material.material_eve_type.id
            ),
            "ajax": "ajax_details",
        }

        details_html = generate_button(
            corporation_id=0,
            template=template,
            queryset=material,
            settings=settings,
            request=request,
        )
        return details_html
    return ""


class SearchApiEndpoints:

    tags = ["Search"]

    # pylint: disable=too-many-statements
    def __init__(self, api: NinjaAPI):
        @api.get(
            "/blueprint/{blueprint_id}/view/industry/",
            response={200: Any, 403: str, 404: str},
            tags=["Search"],
        )
        # @decorate_view(cache_page(CACHE_TIME))
        def get_blueprint_industry(request, blueprint_id: int):
            if not request.user.has_perm("industries.basic_access"):
                return 403, _("Permission Denied")

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

            materials = EveIndustryActivityMaterial.objects.filter(
                eve_type=blueprint
            ).prefetch_related("material_eve_type")
            materials_data = []

            for material in materials:
                materials_data.append(
                    {
                        "portrait": lazy.get_type_icon_url(
                            type_id=material.material_eve_type.id,
                            size=32,
                            type_name=material.material_eve_type.name,
                            as_html=True,
                        ),
                        "material_eve_type__name": material.material_eve_type.name,
                        "material_eve_type_id": material.material_eve_type.id,
                        "material_eve_type__group__id": material.material_eve_type.eve_group.id,
                        "quantity": material.quantity,
                        "details": get_details(request=request, material=material),
                    }
                )

            industry_data = {"blueprint": blueprint.name, "materials": materials_data}

            return industry_data

        @api.get(
            "evetype/{eve_id}/view/submaterial/", response={200: Any}, tags=["Search"]
        )
        def get_material(request, eve_id: str):
            if not request.user.has_perm("industries.basic_access"):
                return 403, _("Permission Denied")

            reaction_blueprint = None
            evetype = EveType.objects.get(id=eve_id)
            EveTypeMaterial.objects.update_or_create_api(eve_type=evetype)

            if evetype.eve_group.id in AA_INDUSTRIES_PRODUCTION_CHAIN:
                reaction_blueprint = get_reaction_blueprint(evetype)

            if reaction_blueprint is not None:
                materials = EveIndustryActivityMaterial.objects.filter(
                    eve_type=reaction_blueprint
                )
            else:
                materials = EveTypeMaterial.objects.filter(eve_type=evetype)

            materials_data = []

            for material in materials:
                material_dict = get_materials(material)
                materials_data.append(material_dict)

            industry_data = {
                "eve_type": evetype.name,
                "materials": materials_data,
            }

            return industry_data

        @api.get(
            "blueprint/{blueprint_id}/view/industryactivitymaterial/",
            response={200: Any},
            tags=["Search"],
        )
        def get_industryactivity(request, blueprint_id: str):
            if not request.user.has_perm("industries.basic_access"):
                return 403, _("Permission Denied")

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
            "evetype/{eve_id}/view/typematerial/", response={200: Any}, tags=["Search"]
        )
        def get_typematerial(request, eve_id: str):
            if not request.user.has_perm("industries.basic_access"):
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

        @api.get("evetype/{eve_id}/view/details/", response={200: Any}, tags=["Search"])
        def get_test(request, eve_id: str):
            if not request.user.has_perm("industries.basic_access"):
                return 403, _("Permission Denied")

            reaction_blueprint = None
            evetype = EveType.objects.get(id=eve_id)
            EveTypeMaterial.objects.update_or_create_api(eve_type=evetype)

            if evetype.eve_group.id in AA_INDUSTRIES_PRODUCTION_CHAIN:
                reaction_blueprint = get_reaction_blueprint(evetype)

            if reaction_blueprint is not None:
                materials = EveIndustryActivityMaterial.objects.filter(
                    eve_type=reaction_blueprint
                )
            else:
                materials = EveTypeMaterial.objects.filter(eve_type=evetype)

            materials_data = []

            for material in materials:
                material_dict = get_materials(material)
                materials_data.append(material_dict)

            context = {
                "name": evetype.name,
                "eve_id": evetype.id,
                "materials": materials_data,
            }

            return render(
                request,
                "industries/modals/view_details_materials.html",
                context,
            )
