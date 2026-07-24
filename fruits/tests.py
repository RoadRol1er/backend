from datetime import datetime, timezone as datetime_timezone
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase

from .models import Fruit, Notification, StockType, UserFruitWatch
from .services import ParsedStock, current_stock_cycle_key, parse_stock, update_stock_from_parsed


class StockServiceTests(TestCase):
    def test_parse_stock_reads_fruityblox_sections(self):
        html = """
        <section>
            <h2>Normal Stock</h2>
            <a href="/fruit/dragon"><h3>Dragon</h3></a>
            <a href="/fruit/light"><h3>Light</h3></a>
        </section>
        <section>
            <h2>Mirage Stock</h2>
            <a href="/fruit/kitsune"><h3>Kitsune</h3></a>
        </section>
        """

        parsed = parse_stock(html, "https://fruityblox.com/stock")

        self.assertEqual(parsed.normal, {"Dragon", "Light"})
        self.assertEqual(parsed.mirage, {"Kitsune"})

    def test_update_stock_creates_notifications_for_matching_watches(self):
        fruit = Fruit.objects.create(name="Dragon", rarity="Mythical", price=0)
        user = User.objects.create_user(username="player", password="password123")
        UserFruitWatch.objects.create(user=user, fruit=fruit, stock_type=StockType.ANY)

        snapshot = update_stock_from_parsed(
            ParsedStock(
                normal={"Dragon"},
                mirage=set(),
                raw_body="Normal stock: Dragon",
                source_url="https://example.com/stock",
            )
        )

        fruit.refresh_from_db()

        self.assertTrue(fruit.in_normal_stock)
        self.assertEqual(snapshot.entries.count(), 1)
        self.assertEqual(Notification.objects.filter(user=user, fruit=fruit).count(), 1)

    def test_update_stock_does_not_duplicate_notifications_in_same_cycle(self):
        fruit = Fruit.objects.create(name="Kitsune", rarity="Mythical", price=8000000)
        user = User.objects.create_user(username="watcher", password="password123")
        UserFruitWatch.objects.create(user=user, fruit=fruit, stock_type=StockType.ANY)
        checked_at = datetime(2026, 7, 24, 12, 15, tzinfo=datetime_timezone.utc)

        parsed = ParsedStock(
            normal={"Kitsune"},
            mirage=set(),
            raw_body="Normal stock: Kitsune",
            source_url="https://example.com/stock",
        )

        with patch("fruits.services.timezone.now", return_value=checked_at):
            update_stock_from_parsed(parsed)
            update_stock_from_parsed(parsed)

        notification = Notification.objects.get(user=user, fruit=fruit)
        self.assertEqual(Notification.objects.filter(user=user, fruit=fruit).count(), 1)
        self.assertEqual(notification.stock_cycle_key, "2026-07-24-12")

    def test_current_stock_cycle_key_uses_four_hour_windows(self):
        checked_at = datetime(2026, 7, 24, 15, 59, tzinfo=datetime_timezone.utc)

        self.assertEqual(current_stock_cycle_key(checked_at), "2026-07-24-12")

    def test_update_stock_creates_unknown_fruits_from_site(self):
        snapshot = update_stock_from_parsed(
            ParsedStock(
                normal={"Rocket"},
                mirage={"Smoke"},
                raw_body="Normal: Rocket Mirage: Smoke",
                source_url="https://fruityblox.com/stock",
            )
        )

        self.assertTrue(Fruit.objects.filter(name="Rocket", rarity="Unknown").exists())
        self.assertTrue(Fruit.objects.filter(name="Smoke", rarity="Unknown").exists())
        self.assertEqual(snapshot.entries.count(), 2)
