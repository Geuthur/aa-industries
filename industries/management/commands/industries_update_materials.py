from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Update all existing Industry Materials and Products"

    # pylint: disable=unused-argument
    def handle(self, *args, **options):
        self.stdout.write("Update existing Materials and Products from Eveuniverse")
