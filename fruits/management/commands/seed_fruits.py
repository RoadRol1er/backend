from django.core.management.base import BaseCommand

from fruits.models import Fruit


FRUIT_CATALOG = {
    "Rocket": ("Common", 5_000),
    "Spin": ("Common", 7_500),
    "Blade": ("Common", 30_000),
    "Spring": ("Common", 60_000),
    "Bomb": ("Common", 80_000),
    "Smoke": ("Common", 100_000),
    "Spike": ("Common", 180_000),
    "Flame": ("Uncommon", 250_000),
    "Eagle": ("Uncommon", 300_000),
    "Ice": ("Uncommon", 350_000),
    "Sand": ("Uncommon", 420_000),
    "Dark": ("Uncommon", 500_000),
    "Diamond": ("Uncommon", 600_000),
    "Light": ("Rare", 650_000),
    "Rubber": ("Rare", 750_000),
    "Ghost": ("Rare", 940_000),
    "Magma": ("Rare", 960_000),
    "Quake": ("Legendary", 1_000_000),
    "Buddha": ("Legendary", 1_200_000),
    "Love": ("Legendary", 1_300_000),
    "Creation": ("Legendary", 1_400_000),
    "Spider": ("Legendary", 1_500_000),
    "Sound": ("Legendary", 1_700_000),
    "Phoenix": ("Legendary", 1_800_000),
    "Portal": ("Legendary", 1_900_000),
    "Rumble": ("Legendary", 2_100_000),
    "Pain": ("Legendary", 2_300_000),
    "Blizzard": ("Legendary", 2_400_000),
    "Gravity": ("Mythical", 2_500_000),
    "Mammoth": ("Mythical", 2_700_000),
    "T-Rex": ("Mythical", 2_700_000),
    "Dough": ("Mythical", 2_800_000),
    "Shadow": ("Mythical", 2_900_000),
    "Venom": ("Mythical", 3_000_000),
    "Control": ("Mythical", 3_200_000),
    "Gas": ("Mythical", 3_200_000),
    "Spirit": ("Mythical", 3_400_000),
    "Tiger": ("Mythical", 5_000_000),
    "Yeti": ("Mythical", 5_000_000),
    "Kitsune": ("Mythical", 8_000_000),
    "Dragon West": ("Mythical", 15_000_000),
    "Dragon East": ("Mythical", 15_000_000),
}


class Command(BaseCommand):
    help = "Seed the fruit catalog so users can watch fruits that are not in stock."

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Overwrite existing rarity and price values.",
        )

    def handle(self, *args, **options):
        created_count = 0
        updated_count = 0
        force = options["force"]

        for fruit_name, (rarity, price) in FRUIT_CATALOG.items():
            fruit, created = Fruit.objects.get_or_create(
                name=fruit_name,
                defaults={"rarity": rarity, "price": price},
            )

            should_update = force or fruit.rarity == "Unknown" or fruit.price == 0
            if not created and should_update:
                fruit.rarity = rarity
                fruit.price = price
                fruit.save(update_fields=["rarity", "price"])
                updated_count += 1

            if created:
                created_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                "Fruit catalog ready: "
                f"{created_count} created, {updated_count} updated, "
                f"{len(FRUIT_CATALOG)} total names."
            )
        )
