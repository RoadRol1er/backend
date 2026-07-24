from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from rest_framework import serializers

from .models import (
    DeviceToken,
    Fruit,
    Notification,
    StockEntry,
    StockSnapshot,
    StockType,
    UserFruitWatch,
)


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    token = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "username", "email", "password", "token"]

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)

    def get_token(self, obj):
        token, _ = Token.objects.get_or_create(user=obj)
        return token.key


class FruitSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Fruit
        fields = [
            "id",
            "name",
            "rarity",
            "price",
            "in_normal_stock",
            "in_mirage_stock",
            "image_url",
            "updated_at",
        ]

    def get_image_url(self, obj):
        request = self.context.get("request")
        url = obj.image_url
        return request.build_absolute_uri(url) if request else url


class StockEntrySerializer(serializers.ModelSerializer):
    fruit = FruitSerializer(read_only=True)

    class Meta:
        model = StockEntry
        fields = ["id", "fruit", "stock_type"]


class StockSnapshotSerializer(serializers.ModelSerializer):
    entries = StockEntrySerializer(many=True, read_only=True)

    class Meta:
        model = StockSnapshot
        fields = ["id", "source_url", "checked_at", "entries"]


class UserFruitWatchSerializer(serializers.ModelSerializer):
    fruit_detail = FruitSerializer(source="fruit", read_only=True)

    class Meta:
        model = UserFruitWatch
        fields = [
            "id",
            "fruit",
            "fruit_detail",
            "stock_type",
            "is_active",
            "created_at",
        ]
        read_only_fields = ["created_at"]

    def validate_stock_type(self, value):
        if value not in StockType.values:
            raise serializers.ValidationError("Unknown stock type.")
        return value

    def create(self, validated_data):
        user = self.context["request"].user
        watch, _ = UserFruitWatch.objects.update_or_create(
            user=user,
            fruit=validated_data["fruit"],
            stock_type=validated_data.get("stock_type", StockType.ANY),
            defaults={"is_active": validated_data.get("is_active", True)},
        )
        return watch


class DeviceTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeviceToken
        fields = ["id", "token", "platform", "is_active", "created_at", "updated_at"]
        read_only_fields = ["created_at", "updated_at"]

    def create(self, validated_data):
        user = self.context["request"].user
        token, _ = DeviceToken.objects.update_or_create(
            token=validated_data["token"],
            defaults={
                "user": user,
                "platform": validated_data.get("platform", ""),
                "is_active": validated_data.get("is_active", True),
            },
        )
        return token


class NotificationSerializer(serializers.ModelSerializer):
    fruit = FruitSerializer(read_only=True)

    class Meta:
        model = Notification
        fields = [
            "id",
            "fruit",
            "stock_type",
            "title",
            "body",
            "stock_cycle_key",
            "status",
            "payload",
            "created_at",
            "sent_at",
        ]
