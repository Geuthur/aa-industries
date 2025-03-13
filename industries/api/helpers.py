import math

from django.db.models import Q
from django.utils import timezone
from django.utils.translation import gettext as _
from eveuniverse.models import (
    EveIndustryActivityMaterial,
    EveIndustryActivityProduct,
    EveMarketPrice,
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
    q_filter = q_filter & Q(name=f"{eve_type.name} Blueprint")

    blueprint = EveType.objects.filter(q_filter, published=True).first()

    if blueprint is None:
        return None
    return blueprint


def get_or_create_product_or_none(
    material: EveType,
) -> tuple[EveIndustryActivityMaterial | None, bool]:
    """Get or create a EveIndustryActivityProduct Product from Blueprint or return None if not exist"""
    try:
        product = EveIndustryActivityProduct.objects.get(
            product_eve_type=material, eve_type__published=True
        )
        return product, False
    except EveIndustryActivityProduct.DoesNotExist:
        blueprint = get_blueprint_from_eve_type(material)

        if blueprint is None:
            return None, False

        logger.debug(
            "Product not found try to create for: %s, Blueprint %s",
            material,
            blueprint,
        )
        EveIndustryActivityProduct.objects.update_or_create_api(eve_type=blueprint)
        try:
            product = EveIndustryActivityProduct.objects.get(
                product_eve_type=material, eve_type__published=True
            )
        except EveIndustryActivityProduct.DoesNotExist:
            return None, False
    return product, True


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


def get_or_create_market_price(
    eve_type: EveType,
) -> float:
    """Get or Create a Market Price for a Eve Type"""
    try:
        marketprice = EveMarketPrice.objects.get(eve_type=eve_type)
        price = marketprice.average_price
        if price is None:
            price = 0

    except EveMarketPrice.DoesNotExist:
        EveMarketPrice.objects.create(
            eve_type=eve_type,
            average_price=0,
            adjusted_price=0,
            updated_at=timezone.now() - timezone.timedelta(days=1),
        )
        price = 0
        return price, True

    price = math.ceil(price)
    return price, False
