"""App URLs"""

from django.urls import path, re_path

from industries import views
from industries.api import api

app_name: str = "industries"

urlpatterns = [
    path("", views.index, name="index"),
    path(
        "blueprint-autocomplete/",
        views.blueprint_autocomplete,
        name="blueprint_autocomplete",
    ),
    # -- API System
    re_path(r"^api/", api.urls),
]
