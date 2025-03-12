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
    get_industry_product_quantity,
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
                product = get_industry_product_quantity(material.material_eve_type)

                is_submaterial = False
                if product is not None:
                    is_submaterial = True

                portait = lazy.get_type_icon_url(
                    type_id=material.material_eve_type.id,
                    size=32,
                    type_name=material.material_eve_type.name,
                    as_html=True,
                )

                materials_data.append(
                    {
                        "material": f"{portait} {material.material_eve_type.name}",
                        "material_eve_type_id": material.material_eve_type.id,
                        "quantity": material.quantity,
                        "is_submaterial": is_submaterial,
                        "in_stock": 0,
                        "price": 0,
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

                blueprint = get_industry_product_quantity(material.material_eve_type)

                if blueprint is not None:

                    submaterials = EveIndustryActivityMaterial.objects.filter(
                        eve_type=blueprint.eve_type, activity_id__in=[1, 11]
                    )

                    for submaterial in submaterials:
                        product = get_industry_product_quantity(
                            submaterial.material_eve_type
                        )
                        if product:
                            # If the product quantity is less than the material quantity then we need 1 full product material
                            if material.quantity < product.quantity:
                                total_quantity = submaterial.quantity * 1
                            else:
                                total_quantity = (
                                    submaterial.quantity * quantity / product.quantity
                                )
                        else:
                            total_quantity = submaterial.quantity * quantity

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
        def get_industry_material2(
            request, material_id: int, quantity: int, category: str = "production"
        ):
            if not request.user.has_perm("industries.basic_access"):
                return 403, _("Permission Denied")

            unique_id = request.GET.get("unique_id", "No ID Found")

            material = EveType.objects.get(id=material_id)
            material_product = get_industry_product_quantity(material)

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

            if submaterials is not None:
                for submaterial in submaterials:
                    product = get_industry_product_quantity(
                        submaterial.material_eve_type
                    )
                    is_submaterial = False
                    if product:
                        # TODO - Better way to handle this? only checks if the ressource exist and create if not
                        # Check if there is a submaterials from product
                        materials = get_blueprint_materials(
                            blueprint=product.eve_type,
                            activity=activity,
                        )
                        if materials is not None:
                            is_submaterial = True

                        # If the product quantity is less than the material quantity then we need 1 full product material
                        if submaterial.quantity < product.quantity:
                            total_quantity = submaterial.quantity * 1
                        else:
                            total_quantity = (
                                submaterial.quantity * quantity / product.quantity
                            )
                    else:
                        total_quantity = submaterial.quantity * quantity

                    # Round up number
                    total_quantity = math.ceil(total_quantity)

                    submaterial_dict = {
                        "material_eve_type_name": submaterial.material_eve_type.name,
                        "material_eve_type_id": submaterial.material_eve_type.id,
                        "quantity": total_quantity,
                        "is_submaterial": is_submaterial,
                        "in_stock": 0,
                        "price": 0,
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
