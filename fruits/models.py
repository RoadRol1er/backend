from django.conf import settings
from django.db import models


class StockType(models.TextChoices):
    NORMAL = "normal", "Normal"
    MIRAGE = "mirage", "Mirage"
    ANY = "any", "Any"


class NotificationStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    SENT = "sent", "Sent"
    FAILED = "failed", "Failed"


class Fruit(models.Model):
    name = models.CharField(
        max_length=50,
        unique=True
    )

    rarity = models.CharField(max_length=30)


    in_normal_stock = models.BooleanField(
        default=False
    )

    in_mirage_stock = models.BooleanField(
        default=False
    )

    price = models.PositiveIntegerField(
        default=0
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    @property
    def image_url(self):
        image_stems = {
            "Dragon East": "DragonEast",
            "Dragon West": "DragonWest",
            "Flame": "Fire",
            "Rumble": "Lighting",
            "T-Rex": "T-Rax",
            "Yeti": "Yetti",
        }
        stem = image_stems.get(self.name, self.name.replace(" ", ""))

        for extension in ("jpg", "jpeg", "png", "webp"):
            filename = f"{stem}.{extension}"
            if (settings.MEDIA_ROOT / filename).exists():
                return f"{settings.MEDIA_URL}{filename}"

        return ""

    def __str__(self):
        return self.name


class StockSnapshot(models.Model):
    source_url = models.URLField(blank=True)
    checked_at = models.DateTimeField(auto_now_add=True)
    raw_hash = models.CharField(max_length=64, blank=True)

    class Meta:
        ordering = ["-checked_at"]

    def __str__(self):
        return f"Stock snapshot {self.checked_at:%Y-%m-%d %H:%M:%S}"


class StockEntry(models.Model):
    snapshot = models.ForeignKey(
        StockSnapshot,
        related_name="entries",
        on_delete=models.CASCADE,
    )
    fruit = models.ForeignKey(
        Fruit,
        related_name="stock_entries",
        on_delete=models.CASCADE,
    )
    stock_type = models.CharField(
        max_length=10,
        choices=StockType.choices,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["snapshot", "fruit", "stock_type"],
                name="unique_stock_entry_per_snapshot",
            )
        ]
        ordering = ["stock_type", "fruit__name"]

    def __str__(self):
        return f"{self.fruit} in {self.stock_type} stock"


class UserFruitWatch(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="fruit_watches",
        on_delete=models.CASCADE,
    )
    fruit = models.ForeignKey(
        Fruit,
        related_name="watchers",
        on_delete=models.CASCADE,
    )
    stock_type = models.CharField(
        max_length=10,
        choices=StockType.choices,
        default=StockType.ANY,
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "fruit", "stock_type"],
                name="unique_user_fruit_watch",
            )
        ]
        ordering = ["fruit__name"]

    def __str__(self):
        return f"{self.user} watches {self.fruit} ({self.stock_type})"


class DeviceToken(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="device_tokens",
        on_delete=models.CASCADE,
    )
    token = models.CharField(max_length=255, unique=True)
    platform = models.CharField(max_length=20, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return f"{self.platform or 'device'} token for {self.user}"


class Notification(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="notifications",
        on_delete=models.CASCADE,
    )
    fruit = models.ForeignKey(
        Fruit,
        related_name="notifications",
        on_delete=models.CASCADE,
    )
    stock_type = models.CharField(max_length=10, choices=StockType.choices)
    title = models.CharField(max_length=120)
    body = models.TextField()
    stock_cycle_key = models.CharField(max_length=13, blank=True)
    status = models.CharField(
        max_length=10,
        choices=NotificationStatus.choices,
        default=NotificationStatus.PENDING,
    )
    payload = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "fruit", "stock_type", "stock_cycle_key"],
                name="unique_notification_per_stock_cycle",
            )
        ]

    def __str__(self):
        return f"{self.title} -> {self.user}"
