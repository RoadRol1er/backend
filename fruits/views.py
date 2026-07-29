from django.conf import settings
from django.shortcuts import render
from rest_framework import mixins, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import DeviceToken, Fruit, Notification, StockSnapshot, UserFruitWatch
from .serializers import (
    DeviceTokenSerializer,
    FruitSerializer,
    NotificationSerializer,
    StockSnapshotSerializer,
    UserFruitWatchSerializer,
    UserSerializer,
)
from .services import scrape_and_update_stock


def index(request):
    return render(request, "index.html")


class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = UserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


class FruitViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Fruit.objects.all().order_by("name")
    serializer_class = FruitSerializer
    permission_classes = [permissions.AllowAny]
    search_fields = ["name", "rarity"]

    def get_queryset(self):
        queryset = super().get_queryset()
        stock = self.request.query_params.get("stock")

        if stock == "normal":
            return queryset.filter(in_normal_stock=True)
        if stock == "mirage":
            return queryset.filter(in_mirage_stock=True)
        if stock == "any":
            return queryset.filter(in_normal_stock=True) | queryset.filter(in_mirage_stock=True)

        return queryset


class CurrentStockView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        latest_snapshot = StockSnapshot.objects.prefetch_related("entries__fruit").first()
        if not latest_snapshot:
            return Response({"detail": "Stock has not been checked yet."}, status=status.HTTP_404_NOT_FOUND)

        serializer = StockSnapshotSerializer(latest_snapshot, context={"request": request})
        return Response(serializer.data)


class UserFruitWatchViewSet(viewsets.ModelViewSet):
    serializer_class = UserFruitWatchSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return UserFruitWatch.objects.filter(user=self.request.user).select_related("fruit")

    def perform_create(self, serializer):
        serializer.save()


class DeviceTokenViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = DeviceTokenSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return DeviceToken.objects.filter(user=self.request.user)


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user).select_related("fruit")

    @action(detail=True, methods=["post"])
    def mark_sent(self, request, pk=None):
        notification = self.get_object()
        notification.status = "sent"
        notification.save(update_fields=["status"])
        return Response(self.get_serializer(notification).data)


class ScrapeStockView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request):
        snapshot = scrape_and_update_stock()
        serializer = StockSnapshotSerializer(snapshot, context={"request": request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ScheduledScrapeStockView(APIView):
    permission_classes = [permissions.AllowAny]

    def _scrape(self, request):
        provided_key = request.headers.get("X-Scrape-Key") or request.query_params.get("key")
        if not settings.SCRAPE_SECRET_KEY or provided_key != settings.SCRAPE_SECRET_KEY:
            return Response({"detail": "Invalid scrape key."}, status=status.HTTP_403_FORBIDDEN)

        snapshot = scrape_and_update_stock()
        serializer = StockSnapshotSerializer(snapshot, context={"request": request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def get(self, request):
        return self._scrape(request)

    def post(self, request):
        return self._scrape(request)
