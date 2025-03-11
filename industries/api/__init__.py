from ninja import NinjaAPI
from ninja.security import django_auth

from django.conf import settings

from industries.api import core, industry
from industries.hooks import get_extension_logger

logger = get_extension_logger(__name__)

api = NinjaAPI(
    title="Geuthur API",
    version="0.1.0",
    urls_namespace="industries:api",
    auth=django_auth,
    csrf=True,
    openapi_url=settings.DEBUG and "/openapi.json" or "",
)

# Add the character endpoints
core.setup(api)

# Add the industry endpoints
industry.setup(api)
