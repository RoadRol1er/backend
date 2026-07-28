import json

from django.conf import settings

from .models import DeviceToken, Notification

try:
    import firebase_admin
    from firebase_admin import credentials, messaging
except ImportError:  # pragma: no cover - optional production dependency
    firebase_admin = None
    credentials = None
    messaging = None


def send_push_notification(notification: Notification) -> int:
    if not _firebase_is_ready():
        return 0

    sent_count = 0
    device_tokens = DeviceToken.objects.filter(
        user=notification.user,
        is_active=True,
    )

    for device in device_tokens:
        message = messaging.Message(
            token=device.token,
            notification=messaging.Notification(
                title=notification.title,
                body=notification.body,
            ),
            data={
                "notification_id": str(notification.id),
                "fruit_id": str(notification.fruit_id),
                "stock_type": notification.stock_type,
                "stock_cycle_key": notification.stock_cycle_key,
            },
        )

        try:
            messaging.send(message)
            sent_count += 1
        except Exception:
            device.is_active = False
            device.save(update_fields=["is_active"])

    return sent_count


def _firebase_is_ready() -> bool:
    if firebase_admin is None or credentials is None:
        return False

    if firebase_admin._apps:
        return True

    credentials_json = settings.FIREBASE_CREDENTIALS_JSON
    if credentials_json:
        firebase_admin.initialize_app(credentials.Certificate(json.loads(credentials_json)))
        return True

    credentials_path = settings.FIREBASE_CREDENTIALS_PATH
    if not credentials_path:
        return False

    firebase_admin.initialize_app(credentials.Certificate(credentials_path))
    return True
