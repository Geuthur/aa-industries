import math

from django.db.models import Q
from django.shortcuts import resolve_url
from django.template.loader import render_to_string
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import gettext as _
from eveuniverse.models import (
    EveIndustryActivityMaterial,
    EveIndustryActivityProduct,
    EveType,
    EveTypeMaterial,
)

from industries.constants import (
    AA_INDUSTRIES_CONSTRUCTION_CHAIN,
    AA_INDUSTRIES_REACTION,
)
from industries.helpers import lazy
from industries.hooks import get_extension_logger

logger = get_extension_logger(__name__)


def generate_button(
    corporation_id: int, template, queryset, settings, request
) -> mark_safe:
    """Generate a html button for the tax system"""
    return format_html(
        render_to_string(
            template,
            {
                "corporation_id": corporation_id,
                "queryset": queryset,
                "settings": settings,
            },
            request=request,
        )
    )


def fix_fullerides(material: EveType) -> EveType:
    """Fix Fullerides"""
    if material.name == "Fullerides":
        material.name = "Fulleride"
    return material


# TODO Refactor this and make it more efficient
def get_blueprint_product(material: EveType) -> EveIndustryActivityProduct:
    """Get the endproduct from a blueprint"""

    q_filter = Q(eve_group__eve_category__id=9)

    if material.eve_group.id in AA_INDUSTRIES_REACTION:
        q_filter = q_filter & Q(name__contains="Formula")
        if material.name == "Fullerides":
            material = fix_fullerides(material)

    q_filter = q_filter & Q(name__contains=material.name)

    eve_type = EveType.objects.filter(q_filter).first()
    if not eve_type:
        logger.debug("Material is not a blueprint: %s", material)
        raise ValueError(f"{material} is not a blueprint")

    try:
        product = EveIndustryActivityProduct.objects.get(eve_type=eve_type)
    except EveIndustryActivityProduct.DoesNotExist:
        logger.debug("Product not found: %s", material)
        EveIndustryActivityProduct.objects.update_or_create_api(eve_type=eve_type)
        product = EveIndustryActivityProduct.objects.get(eve_type=eve_type)

    return product


def get_material_components(material: EveType) -> EveTypeMaterial:
    """Get the components from a material"""
    if EveTypeMaterial.objects.filter(eve_type=material).exists():
        components = EveTypeMaterial.objects.filter(eve_type=material).prefetch_related(
            "eve_type"
        )
    else:
        EveTypeMaterial.objects.update_or_create_api(eve_type=material)
        components = EveTypeMaterial.objects.filter(eve_type=material).prefetch_related(
            "eve_type"
        )
    return components


def get_submaterials(material: EveTypeMaterial) -> EveIndustryActivityMaterial:
    """Get Submaterials Queryset from EveIndustryActivityMaterial"""
    product = get_blueprint_product(material.material_eve_type)

    if not EveIndustryActivityMaterial.objects.filter(
        eve_type=product.eve_type, activity_id__in=[1, 11]
    ).exists():
        logger.debug("Submaterials not found: %s", product.eve_type)
        EveIndustryActivityMaterial.objects.update_or_create_api(
            eve_type=product.eve_type
        )

    submaterials = EveIndustryActivityMaterial.objects.filter(
        eve_type=product.eve_type, activity_id__in=[1, 11]
    )
    return submaterials


def get_materials(material: EveTypeMaterial, quantity=1):
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
        "quantity": material.quantity * quantity,
        "materials": [],
    }

    submaterials = get_submaterials(material=material)

    if not submaterials:
        return material_dict

    for submaterial in submaterials:
        # Get the End Product from the Blueprint
        try:
            product = EveIndustryActivityProduct.objects.get(
                eve_type=submaterial.eve_type
            )
        except EveIndustryActivityProduct.DoesNotExist:
            logger.debug("Product not found: %s", submaterial.eve_type)
            EveIndustryActivityProduct.objects.update_or_create_api(
                eve_type=submaterial.eve_type
            )
            product = EveIndustryActivityProduct.objects.get(
                eve_type=submaterial.eve_type
            )
            logger.debug("Product created: %s", product.eve_type)

        try:
            a_material = EveIndustryActivityMaterial.objects.get(
                material_eve_type=submaterial.material_eve_type,
                eve_type=submaterial.eve_type,
            )
        except EveIndustryActivityMaterial.DoesNotExist:
            logger.debug("Material not found: %s", submaterial.material_eve_type)
            EveIndustryActivityMaterial.objects.update_or_create_api(
                eve_type=submaterial.eve_type
            )
            a_material = EveIndustryActivityMaterial.objects.get(
                material_eve_type=submaterial.material_eve_type,
                eve_type=submaterial.eve_type,
            )
            logger.debug("Material created: %s", a_material.material_eve_type)

        # Calculate the quantity of the material
        product_quantity = (material.quantity * quantity) / product.quantity
        industry_quantity = a_material.quantity * product_quantity

        # Round the quantity up
        industry_quantity = math.ceil(industry_quantity)

        submaterial_dict = {
            "portrait": lazy.get_type_icon_url(
                type_id=submaterial.material_eve_type.id,
                size=32,
                type_name=submaterial.material_eve_type.name,
                as_html=True,
            ),
            "material_eve_type__name": submaterial.material_eve_type.name,
            "material_eve_type_id": submaterial.material_eve_type.id,
            "material_eve_type__group__id": submaterial.material_eve_type.eve_group.id,
            "quantity": industry_quantity,
        }

        material_dict["materials"].append(submaterial_dict)

    return material_dict


def get_details(request, material: EveIndustryActivityMaterial):
    """Get details for a material"""
    if (
        material.material_eve_type.eve_group.eve_category.id == 9
        or material.material_eve_type.eve_group.id
        in (AA_INDUSTRIES_CONSTRUCTION_CHAIN + AA_INDUSTRIES_REACTION)
    ):
        template = "industries/partials/form/button.html"
        settings = {
            "title": _("Materials"),
            "icon": "fas fa-info",
            "color": "primary",
            "text": _("View Submaterials"),
            "modal": "modalViewDetailsContainer",
            "action": resolve_url(
                "industries:api:get_material_industry",
                eve_id=material.material_eve_type.id,
                quantity=material.quantity,
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
