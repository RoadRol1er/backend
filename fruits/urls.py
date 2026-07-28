from django.urls import include, path
from rest_framework.authtoken.views import obtain_auth_token
from rest_framework.routers import DefaultRouter

from .views import (
    CurrentStockView,
    DeviceTokenViewSet,
    FruitViewSet,
    NotificationViewSet,
    RegisterView,
    ScrapeStockView,
    ScheduledScrapeStockView,
    UserFruitWatchViewSet,
    index,
)

router = DefaultRouter()
router.register("fruits", FruitViewSet, basename="fruit")
router.register("watches", UserFruitWatchViewSet, basename="watch")
router.register("devices", DeviceTokenViewSet, basename="device")
router.register("notifications", NotificationViewSet, basename="notification")

urlpatterns = [
    path("", index, name="index"),
    path("api/", include(router.urls)),
    path("api/auth/register/", RegisterView.as_view(), name="register"),
    path("api/auth/token/", obtain_auth_token, name="api-token-auth"),
    path("api/stock/current/", CurrentStockView.as_view(), name="current-stock"),
    path("api/stock/scrape/", ScrapeStockView.as_view(), name="scrape-stock"),
    path("api/stock/scheduled-scrape/", ScheduledScrapeStockView.as_view(), name="scheduled-scrape-stock"),
    path("api-auth/", include("rest_framework.urls")),
]
