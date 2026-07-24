import hashlib
from dataclasses import dataclass
from typing import Iterable

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from .models import (
    Fruit,
    Notification,
    StockEntry,
    StockSnapshot,
    StockType,
    UserFruitWatch,
)
from .push import send_push_notification

try:
    import requests
except ImportError:  # pragma: no cover - dependency guard for deployment setup
    requests = None

try:
    from bs4 import BeautifulSoup
except ImportError:  # pragma: no cover - dependency guard for deployment setup
    BeautifulSoup = None


@dataclass(frozen=True)
class ParsedStock:
    normal: set[str]
    mirage: set[str]
    raw_body: str
    source_url: str


def fetch_stock_page(url: str | None = None) -> str:
    if requests is None:
        raise RuntimeError("Install requests to fetch stock pages.")

    response = requests.get(
        url or settings.BLOX_FRUITS_STOCK_URL,
        timeout=20,
        headers={"User-Agent": "BloxStockTracker/1.0"},
    )
    response.raise_for_status()
    return response.text


def parse_stock(raw_body: str, source_url: str | None = None) -> ParsedStock:
    stocks = parse_fruityblox_sections(raw_body)

    return ParsedStock(
        normal=_find_section(stocks, ["normal", "dealer"]),
        mirage=_find_section(stocks, ["mirage", "advanced"]),
        raw_body=raw_body,
        source_url=source_url or settings.BLOX_FRUITS_STOCK_URL,
    )


def scrape_and_update_stock(url: str | None = None) -> StockSnapshot:
    source_url = url or settings.BLOX_FRUITS_STOCK_URL
    parsed = parse_stock(fetch_stock_page(source_url), source_url)
    return update_stock_from_parsed(parsed)


def parse_fruityblox_sections(raw_body: str) -> dict[str, set[str]]:
    if BeautifulSoup is None:
        raise RuntimeError("Install beautifulsoup4 to parse FruityBlox stock pages.")

    soup = BeautifulSoup(raw_body, "html.parser")
    stocks = {}

    for section in soup.find_all("section"):
        heading = section.find("h2")
        if not heading:
            continue

        stock_name = heading.get_text(strip=True)
        fruits = set()

        for item in section.find_all("a", href=True):
            fruit_heading = item.find("h3")
            if fruit_heading:
                fruits.add(fruit_heading.get_text(strip=True))

        if fruits:
            stocks[stock_name] = fruits

    return stocks


@transaction.atomic
def update_stock_from_parsed(parsed: ParsedStock) -> StockSnapshot:
    raw_hash = hashlib.sha256(parsed.raw_body.encode("utf-8")).hexdigest()
    snapshot = StockSnapshot.objects.create(
        source_url=parsed.source_url,
        raw_hash=raw_hash,
    )

    normal_names = _normalize_names(parsed.normal)
    mirage_names = _normalize_names(parsed.mirage)

    Fruit.objects.update(in_normal_stock=False, in_mirage_stock=False)
    _set_stock(snapshot, normal_names, StockType.NORMAL)
    _set_stock(snapshot, mirage_names, StockType.MIRAGE)
    _create_notifications(normal_names, mirage_names)
    return snapshot


def _find_section(stocks: dict[str, set[str]], markers: list[str]) -> set[str]:
    for stock_name, fruit_names in stocks.items():
        lowered = stock_name.lower()
        if any(marker in lowered for marker in markers):
            return fruit_names
    return set()


def _set_stock(snapshot: StockSnapshot, fruit_names: set[str], stock_type: str) -> None:
    stock_field = "in_normal_stock" if stock_type == StockType.NORMAL else "in_mirage_stock"

    for fruit in Fruit.objects.filter(name__in=fruit_names):
        setattr(fruit, stock_field, True)
        fruit.updated_at = timezone.now()
        fruit.save(update_fields=[stock_field, "updated_at"])
        StockEntry.objects.create(
            snapshot=snapshot,
            fruit=fruit,
            stock_type=stock_type,
        )


def _create_notifications(normal_names: set[str], mirage_names: set[str]) -> None:
    active_watches = UserFruitWatch.objects.select_related("fruit", "user").filter(is_active=True)
    cycle_key = current_stock_cycle_key()

    for watch in active_watches:
        matched_stock_type = _matched_stock_type(watch, normal_names, mirage_names)
        if not matched_stock_type:
            continue

        notification, created = Notification.objects.get_or_create(
            user=watch.user,
            fruit=watch.fruit,
            stock_type=matched_stock_type,
            stock_cycle_key=cycle_key,
            defaults={
                "title": f"{watch.fruit.name} is in stock",
                "body": f"{watch.fruit.name} appeared in {matched_stock_type} stock.",
                "payload": {
                    "fruit_id": watch.fruit_id,
                    "stock_type": matched_stock_type,
                    "stock_cycle_key": cycle_key,
                },
            },
        )

        if created:
            send_push_notification(notification)


def current_stock_cycle_key(moment=None) -> str:
    moment = timezone.localtime(moment or timezone.now())
    cycle_hour = moment.hour - (moment.hour % 4)
    return f"{moment:%Y-%m-%d}-{cycle_hour:02d}"


def _matched_stock_type(
    watch: UserFruitWatch,
    normal_names: set[str],
    mirage_names: set[str],
) -> str | None:
    fruit_name = watch.fruit.name

    if watch.stock_type in (StockType.NORMAL, StockType.ANY) and fruit_name in normal_names:
        return StockType.NORMAL

    if watch.stock_type in (StockType.MIRAGE, StockType.ANY) and fruit_name in mirage_names:
        return StockType.MIRAGE

    return None


def _normalize_names(names: Iterable[str]) -> set[str]:
    normalized_names = set()

    for name in names:
        clean_name = name.strip()
        if not clean_name:
            continue

        fruit = Fruit.objects.filter(name__iexact=clean_name).first()
        if fruit is None:
            fruit = Fruit.objects.create(name=clean_name, rarity="Unknown", price=0)

        normalized_names.add(fruit.name)

    return normalized_names
