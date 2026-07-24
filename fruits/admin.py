from django.contrib import admin

from .models import (
    DeviceToken,
    Fruit,
    Notification,
    StockEntry,
    StockSnapshot,
    UserFruitWatch,
)


@admin.register(Fruit)
class FruitAdmin(admin.ModelAdmin):
    list_display = ("name", "rarity", "price", "in_normal_stock", "in_mirage_stock", "updated_at")
    list_filter = ("rarity", "in_normal_stock", "in_mirage_stock")
    search_fields = ("name",)


class StockEntryInline(admin.TabularInline):
    model = StockEntry
    extra = 0
    autocomplete_fields = ("fruit",)


@admin.register(StockSnapshot)
class StockSnapshotAdmin(admin.ModelAdmin):
    list_display = ("checked_at", "source_url", "raw_hash")
    readonly_fields = ("checked_at", "raw_hash")
    inlines = [StockEntryInline]


@admin.register(UserFruitWatch)
class UserFruitWatchAdmin(admin.ModelAdmin):
    list_display = ("user", "fruit", "stock_type", "is_active", "created_at")
    list_filter = ("stock_type", "is_active")
    autocomplete_fields = ("user", "fruit")


@admin.register(DeviceToken)
class DeviceTokenAdmin(admin.ModelAdmin):
    list_display = ("user", "platform", "is_active", "updated_at")
    list_filter = ("platform", "is_active")
    search_fields = ("user__username", "token")


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("user", "fruit", "stock_type", "status", "created_at", "sent_at")
    list_filter = ("stock_type", "status")
    autocomplete_fields = ("user", "fruit")
