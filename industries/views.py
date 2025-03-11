"""PvE Views"""

# Django
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.db.models import F
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils.translation import gettext as _
from eveuniverse.models import EveType

from industries import forms
from industries.app_settings import INDUSTRIES_APP_NAME

from .hooks import get_extension_logger

logger = get_extension_logger(__name__)


@login_required
@permission_required("industries.basic_access")
def index(request):
    return redirect(
        "industries:industry_character",
        request.user.profile.main_character.corporation_id,
    )


@login_required
@permission_required("industries.basic_access")
def industry_character(request, character_id):
    """Payments View"""
    if character_id is None:
        character_id = request.user.profile.main_character.corporation_id

    perms = True

    if perms is None:
        messages.error(request, _("No corporation found."))
        return redirect("industries:index")

    context = {
        "character_id": character_id,
        "title": _("Index") + f" ⋗ {INDUSTRIES_APP_NAME}",
    }
    # context = add_info_to_context(request, context)

    return render(request, "industries/index.html", context=context)


@login_required
@permission_required("industries.basic_access")
def blueprint(request):
    blueprint_id = request.GET.get("blueprint_id", 0)
    form = forms.BlueprintForm(request.POST or None)

    if request.method == "POST":
        if form.is_valid():
            blueprint_id = request.POST.get("blueprint_id", 0)

    context = {
        "title": _("Blueprint Calculator") + f" ⋗ {INDUSTRIES_APP_NAME}",
        "form": form,
        "blueprint_id": blueprint_id,
    }
    return render(request, "industries/blueprint.html", context=context)


@login_required
@permission_required("industries.basic_access")
def blueprint_autocomplete(request, search_query=None):
    if request.headers.get("x-requested-with") == "XMLHttpRequest":  # is_ajax
        search_query = request.GET.get("term")

    if not search_query:
        return JsonResponse([], safe=False)

    items = EveType.objects.filter(
        published=True, eve_group__eve_category__id=9, name__icontains=search_query
    )

    items = items.annotate(
        value=F("id"),
        label=F("name"),
    ).values("value", "label")

    return JsonResponse(list(items), safe=False)
