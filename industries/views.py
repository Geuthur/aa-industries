"""PvE Views"""

# Django
from django.contrib.auth.decorators import login_required, permission_required
from django.db.models import F
from django.http import JsonResponse
from django.shortcuts import render
from django.utils.translation import gettext as _
from eveuniverse.models import EveType

from industries import forms

from .hooks import get_extension_logger

logger = get_extension_logger(__name__)


@login_required
@permission_required("industries.basic_access")
def index(request):
    blueprint_id = request.GET.get("blueprint_id", 0)
    form = forms.BlueprintForm(request.POST or None)

    if request.method == "POST":
        if form.is_valid():
            blueprint_id = request.POST.get("blueprint_id", 0)

    context = {
        "form": form,
        "blueprint_id": blueprint_id,
    }
    return render(request, "industries/index.html", context=context)


@login_required
@permission_required("industries.basic_access")
def blueprint_autocomplete(request):
    search_query = None
    if request.headers.get("x-requested-with") == "XMLHttpRequest":  # is_ajax
        search_query = request.GET.get("term")

    if not search_query:
        return JsonResponse({"error": _("No search query")}, status=400)

    items = EveType.objects.filter(
        published=True, eve_group__eve_category__id=9, name__icontains=search_query
    )

    items = items.annotate(
        value=F("id"),
        label=F("name"),
    ).values("value", "label")

    return JsonResponse(list(items), safe=False)
