from django.core.management.base import BaseCommand

from fruits.services import scrape_and_update_stock


class Command(BaseCommand):
    help = "Scrape Blox Fruits stock and create pending notifications for matching watches."

    def add_arguments(self, parser):
        parser.add_argument(
            "--url",
            default=None,
            help="Override BLOX_FRUITS_STOCK_URL for this run.",
        )

    def handle(self, *args, **options):
        snapshot = scrape_and_update_stock(options["url"])
        self.stdout.write(
            self.style.SUCCESS(
                f"Created stock snapshot {snapshot.id} with {snapshot.entries.count()} entries."
            )
        )
