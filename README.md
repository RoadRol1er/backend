# Blox Stock Tracker Backend

Django REST backend for a Flutter Android app that tracks Roblox Blox Fruits stock, lets users watch desired fruits, and creates notifications when watched fruits appear.

## Features

- Fruit catalog with rarity, price, stock flags, and image URLs.
- FruityBlox stock parser.
- User registration and token auth.
- User watch list.
- Notification records with 4-hour stock-cycle duplicate protection.
- Optional Firebase Cloud Messaging push delivery.

## Local Setup

```powershell
cd D:\Python\BloxStockTracker
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_fruits
python manage.py scrape_stock
python manage.py runserver 127.0.0.1:8000
```

Open:

```text
http://127.0.0.1:8000/api/fruits/
http://127.0.0.1:8000/admin/
```

Create admin user if needed:

```powershell
python manage.py createsuperuser
```

## Environment Variables

Copy `.env.example` and set these values in your server environment.

```text
DJANGO_SECRET_KEY=change-me
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost
CORS_ALLOW_ALL_ORIGINS=True
CORS_ALLOWED_ORIGINS=
BLOX_FRUITS_STOCK_URL=https://fruityblox.com/stock
FIREBASE_CREDENTIALS_PATH=
```

The project does not auto-load `.env`; set variables in PowerShell, Linux shell, hosting panel, Docker, or process manager.

PowerShell example:

```powershell
$env:DJANGO_SECRET_KEY="local-dev-secret"
$env:DJANGO_DEBUG="True"
```

## API

Public:

- `POST /api/auth/register/`
- `POST /api/auth/token/`
- `GET /api/fruits/`
- `GET /api/fruits/?stock=normal`
- `GET /api/fruits/?stock=mirage`
- `GET /api/stock/current/`

Authenticated requests:

```text
Authorization: Token <token>
```

- `GET/POST /api/watches/`
- `GET/POST /api/devices/`
- `GET /api/notifications/`
- `POST /api/notifications/{id}/mark_sent/`

Admin:

- `POST /api/stock/scrape/`

## Stock Parser

Manual run:

```powershell
python manage.py scrape_stock
```

Recommended production schedule: run every 5 minutes.

Linux cron example:

```text
*/5 * * * * cd /path/to/BloxStockTracker && /path/to/venv/bin/python manage.py scrape_stock
```

The game stock changes every 4 hours, but the source site may update 10-20 minutes later. Frequent checks are safe because notifications are deduplicated by:

```text
user + fruit + stock_type + stock_cycle_key
```

## Firebase Push

Flutter uses `google-services.json`.

Django needs a private Firebase service account file. Do not commit it.

Download it from:

```text
Firebase Console -> Project settings -> Service accounts -> Generate new private key
```

Then set:

```powershell
$env:FIREBASE_CREDENTIALS_PATH="D:\Python\BloxStockTracker\firebase-service-account.json"
```

If `FIREBASE_CREDENTIALS_PATH` is empty, backend still creates `Notification` rows but skips real push sending.

## GitHub Safety

Do not commit:

- `db.sqlite3`
- `.env`
- Firebase service account JSON
- virtual environments
- logs

Images in `media/` can be committed for the учебный/demo project if you want the catalog to show fruit pictures immediately.
