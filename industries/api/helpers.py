from django.db.models import Q
from django.utils.translation import gettext as _
from eveuniverse.models import (
    EveIndustryActivityMaterial,
    EveIndustryActivityProduct,
    EveType,
)

from industries.constants import (
    AA_INDUSTRIES_REACTION,
)
from industries.hooks import get_extension_logger

logger = get_extension_logger(__name__)


# TODO - Better way to handle this?
def fix_fullerides(material: EveType) -> EveType:
    """Fix Fullerides"""
    if material.name == "Fullerides":
        material.name = "Fulleride"
    return material


# TODO - Better way to handle this?
def get_blueprint_from_eve_type(eve_type: EveType) -> EveType:
    """Get the blueprint from a eve type"""
    q_filter = Q(eve_group__eve_category__id=9)

    # TODO - Find a way without bad hardcoded values
    if eve_type.eve_group.id in AA_INDUSTRIES_REACTION:
        q_filter = q_filter & Q(name__contains="Formula")
        if eve_type.name == "Fullerides":
            eve_type = fix_fullerides(eve_type)

    # TODO - Find a way without bad hardcoded values
    if eve_type.eve_group.eve_category.id == 7:  # Module Category
        q_filter = q_filter & Q(name=f"{eve_type.name} Blueprint")

    q_filter = q_filter & Q(name__contains=eve_type.name)

    blueprint = EveType.objects.filter(q_filter).first()

    if blueprint is None:
        return None
    return blueprint


def get_industry_product_quantity(material: EveType) -> EveIndustryActivityProduct:
    """Get the quantity of a Material Blueprint or create if not exists"""
    # Skip some groups
    if (
        material.eve_group.id in [18, 1136, 427]
        or material.eve_group.eve_category.id == 43
    ):
        return None

    try:
        product = EveIndustryActivityProduct.objects.get(
            product_eve_type=material, eve_type__published=True
        )
    except EveIndustryActivityProduct.DoesNotExist as exc:
        logger.debug(
            "Product not found try to create for: %s",
            material,
        )
        blueprint = get_blueprint_from_eve_type(material)

        EveIndustryActivityProduct.objects.update_or_create_api(eve_type=blueprint)
        try:
            product = EveIndustryActivityProduct.objects.get(
                product_eve_type=material, eve_type__published=True
            )
        except EveIndustryActivityProduct.DoesNotExist:
            raise ValueError(_("Product not found")) from exc
    except EveIndustryActivityProduct.MultipleObjectsReturned:
        logger.debug(
            "Multiple products found for: %s",
            material,
        )
        product = None
    return product


def get_blueprint_materials(
    blueprint: EveType, activity: list
) -> EveIndustryActivityMaterial:
    """Get the materials from a Blueprint or create if not exists"""
    if blueprint.eve_group.eve_category.id != 9:
        raise ValueError(_("Please use a Blueprint"))

    try:
        materials = EveIndustryActivityMaterial.objects.filter(
            eve_type=blueprint, activity_id__in=activity
        )
        if not materials.exists():
            raise EveIndustryActivityMaterial.DoesNotExist
    except EveIndustryActivityMaterial.DoesNotExist:
        logger.debug(
            "Materials not found try to create for: %s",
            blueprint,
        )
        EveIndustryActivityMaterial.objects.update_or_create_api(eve_type=blueprint)

        materials = EveIndustryActivityMaterial.objects.filter(
            eve_type=blueprint, activity_id__in=activity
        )
        if not materials.exists():
            return None
    return materials
