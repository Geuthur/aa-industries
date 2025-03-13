"""App Tasks"""

from celery import shared_task

from eveuniverse.models import EveMarketPrice

from industries.hooks import get_extension_logger

logger = get_extension_logger(__name__)


@shared_task
def update_all_industries():
    """Update all industries."""
    # pylint: disable=unnecessary-pass
    pass


@shared_task
def update_market_prices():
    """Update all existing Market Prices."""
    count = EveMarketPrice.objects.update_from_esi()
    logger.info("Updated %s Market Prices", count)
    return count
