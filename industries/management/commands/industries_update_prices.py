from django.core.management.base import BaseCommand

from industries.tasks import update_market_prices


class Command(BaseCommand):
    help = "Update or Populate EVE Item prices"

    # pylint: disable=unused-argument
    def handle(self, *args, **options):
        self.stdout.write("Update existing Prices from Eveuniverse")
        return update_market_prices()
