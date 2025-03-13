import math
from collections import defaultdict
from typing import Any

from ninja import NinjaAPI

from django.shortcuts import render
from django.utils.translation import gettext as _
from eveuniverse.models import (
    EveIndustryActivityMaterial,
    EveType,
)

from industries.api.helpers import (
    get_blueprint_materials,
    get_or_create_market_price,
    get_or_create_product_or_none,
)
from industries.helpers import lazy
from industries.hooks import get_extension_logger

logger = get_extension_logger(__name__)


class IndustryApiEndpoints:
    tags = ["Industry"]

    # pylint: disable=too-many-statements
    def __init__(self, api: NinjaAPI):
        @api.get(
            "/blueprint/{blueprint_id}/category/{category}/view/industry/",
            response={200: Any, 403: str, 404: str},
            tags=["Industry"],
        )
        def get_blueprint_industry(request, blueprint_id: int, category):
            if not request.user.has_perm("industries.basic_access"):
                return 403, _("Permission Denied")

            try:
                blueprint = EveType.objects.get(
                    id=blueprint_id, published=True, eve_group__eve_category_id=9
                )
            except EveType.DoesNotExist:
                return 404, _("Blueprint not found")

            materials_data = []

            # TODO: IMPLEMENT THIS
            # Get the activity
            if category == "production":
                activity = [1, 11]
            elif category == "copy":
                activity = [5]
            else:
                return 404, _("Category not found")

            materials = get_blueprint_materials(blueprint=blueprint, activity=activity)

            if materials is None:
                logger.debug("Materials not found for: %s", blueprint)
                return 404, _("Materials not found")

            for material in materials:
                is_submaterial = True
                product, __ = get_or_create_product_or_none(material.material_eve_type)
                if product is None:
                    is_submaterial = False

                portait = lazy.get_type_icon_url(
                    type_id=material.material_eve_type.id,
                    size=32,
                    type_name=material.material_eve_type.name,
                    as_html=True,
                )

                price, __ = get_or_create_market_price(
                    eve_type=material.material_eve_type,
                )
                logger.debug(
                    "Price for %s Q:%s: %s",
                    material.material_eve_type,
                    material.quantity,
                    price,
                )

                # Get Total Price
                total_price = price * material.quantity

                materials_data.append(
                    {
                        "material": f"{portait} {material.material_eve_type.name}",
                        "material_eve_type_id": material.material_eve_type.id,
                        "quantity": material.quantity,
                        "is_submaterial": is_submaterial,
                        "in_stock": 0,
                        "single_price": price,
                        "price": total_price,
                    }
                )

            industry_data = {
                "blueprint": blueprint.name,
                "blueprint_id": blueprint_id,
                "materials": materials_data,
            }

            return industry_data

        @api.get(
            "blueprint/{blueprint_id}/view/industry/summary/",
            response={200: Any},
            tags=["Industry"],
        )
        def get_blueprint_industry_summary(request, blueprint_id: int):
            if not request.user.has_perm("industries.basic_access"):
                return 403, _("Permission Denied")

            try:
                blueprint = EveType.objects.get(id=blueprint_id)
            except EveType.DoesNotExist:
                return 404, _("Blueprint not found")

            materials_data = defaultdict(
                lambda: {"portrait": "", "id": "", "name": "", "quantity": 0}
            )
            materials = EveIndustryActivityMaterial.objects.filter(
                eve_type=blueprint, activity_id__in=[1, 11]
            )

            for material in materials:
                quantity = material.quantity
                material_name = material.material_eve_type.name

                product, __ = get_or_create_product_or_none(material.material_eve_type)

                material_quantity = quantity / product.quantity
                # Round up number
                material_quantity = math.ceil(material_quantity)

                if product is not None:
                    submaterials = EveIndustryActivityMaterial.objects.filter(
                        eve_type=product.eve_type, activity_id__in=[1, 11]
                    )

                    for submaterial in submaterials:
                        get_or_create_product_or_none(submaterial.material_eve_type)

                        total_quantity = submaterial.quantity * material_quantity

                        material_id = submaterial.material_eve_type.id
                        material_name = submaterial.material_eve_type.name
                        materials_data[material_id]["portrait"] = (
                            lazy.get_type_icon_url(
                                type_id=submaterial.material_eve_type.id,
                                size=32,
                                type_name=submaterial.material_eve_type.name,
                                as_html=True,
                            )
                        )
                        materials_data[material_id]["id"] = material_id
                        materials_data[material_id]["name"] = material_name
                        materials_data[material_id]["quantity"] += total_quantity

            return dict(materials_data)

        @api.get(
            "industry/{material_id}/quantity/{quantity}/view/industry/material/",
            response={200: Any, 404: str},
            tags=["Industry"],
        )
        # pylint: disable=too-many-locals
        def get_industry_material(
            request, material_id: int, quantity: int, category: str = "production"
        ):
            if not request.user.has_perm("industries.basic_access"):
                return 403, _("Permission Denied")

            unique_id = request.GET.get("unique_id", "No ID Found")

            material = EveType.objects.get(id=material_id)
            material_product, __ = get_or_create_product_or_none(material)

            if material_product is None:
                return 404, _("Material not found")

            submaterial_data = []

            # TODO: IMPLEMENT THIS
            # Get the activity
            if category == "production":
                activity = [1, 11]
            elif category == "copy":
                activity = [5]
            else:
                return 404, _("Category not found")

            submaterials = get_blueprint_materials(
                blueprint=material_product.eve_type, activity=activity
            )

            material_quantity = quantity / material_product.quantity
            # Round up number
            material_quantity = math.ceil(material_quantity)

            if submaterials is not None:
                for submaterial in submaterials:
                    is_submaterial = True
                    product, __ = get_or_create_product_or_none(
                        submaterial.material_eve_type
                    )
                    if product is None:
                        is_submaterial = False

                    total_quantity = submaterial.quantity * material_quantity

                    price, __ = get_or_create_market_price(
                        eve_type=submaterial.material_eve_type,
                    )

                    total_price = price * total_quantity

                    submaterial_dict = {
                        "material_eve_type_name": submaterial.material_eve_type.name,
                        "material_eve_type_id": submaterial.material_eve_type.id,
                        "quantity": total_quantity,
                        "is_submaterial": is_submaterial,
                        "in_stock": 0,
                        "single_price": price,
                        "price": total_price,
                    }
                    submaterial_data.append(submaterial_dict)

            context = {
                "unique_id": unique_id,
                "material_eve_type__name": material.name,
                "material_eve_type_id": material_id,
                "quantity": quantity,
                "submaterials": submaterial_data,
            }
            return render(
                request=request,
                template_name="industries/partials/table/submaterials.html",
                context=context,
            )
