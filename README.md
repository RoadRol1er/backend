# Blox Stock Tracker Backend

Django REST backend for the Blox Stock Mobile Android app.

The backend parses Blox Fruits stock, stores a full fruit catalog, tracks user watch lists, creates notifications, and can send Firebase Cloud Messaging push notifications.

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

Check:

```text
http://127.0.0.1:8000/api/fruits/
http://127.0.0.1:8000/admin/
```

## Environment Variables

Use `.env.example` as a checklist. The project does not auto-load `.env`; set variables in the hosting dashboard, shell, process manager, or Docker environment.

Important variables:

```text
DJANGO_SECRET_KEY=change-me
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=your-host.koyeb.app
CORS_ALLOW_ALL_ORIGINS=False
CORS_ALLOWED_ORIGINS=https://your-frontend-origin.com
DATABASE_URL=postgresql://...
DATABASE_SSL_REQUIRE=True
BLOX_FRUITS_STOCK_URL=https://fruityblox.com/stock
FIREBASE_CREDENTIALS_PATH=
FIREBASE_CREDENTIALS_JSON=
SCRAPE_SECRET_KEY=long-random-secret
SERVE_MEDIA_FILES=True
```

For local development you can keep:

```text
DJANGO_DEBUG=True
CORS_ALLOW_ALL_ORIGINS=True
```

## Free Hosting MVP

Recommended free-ish MVP stack:

- Koyeb Free Web Service for Django.
- Neon Free Postgres for database.
- External free scheduler/monitor to call the protected scrape endpoint every 5 minutes.

Why not only local SQLite: free web hosts usually have ephemeral filesystems, so SQLite data can disappear after restart/redeploy.

## Deploy On Koyeb

Push this backend repo to GitHub first.

Create Neon Postgres and copy the pooled connection string.

In Koyeb:

```text
Create Web Service -> GitHub repo -> Buildpack
```

Build command:

```bash
bash build.sh
```

Run command:

```bash
gunicorn BloxStockTracker.wsgi:application --bind 0.0.0.0:$PORT
```

Environment variables:

```text
DJANGO_SECRET_KEY=<generate long random string>
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=<your-koyeb-domain>
DATABASE_URL=<neon-postgres-url>
DATABASE_SSL_REQUIRE=True
CORS_ALLOW_ALL_ORIGINS=True
SCRAPE_SECRET_KEY=<generate long random string>
SERVE_MEDIA_FILES=True
```

After deploy, check:

```text
https://your-koyeb-domain/api/fruits/
```

## Regular Stock Checks

Manual local run:

```powershell
python manage.py scrape_stock
```

For free hosting, use the protected HTTP endpoint:

```text
POST https://your-koyeb-domain/api/stock/scheduled-scrape/?key=SCRAPE_SECRET_KEY
```

Call it every 5 minutes from an external scheduler/monitor.

The game stock changes every 4 hours, but FruityBlox can update 10-20 minutes later. Frequent checks are safe because notifications are deduplicated by:

```text
user + fruit + stock_type + stock_cycle_key
```

So one user gets only one notification for the same fruit in the same 4-hour stock period.

## Firebase Push

Flutter Android uses:

```text
android/app/google-services.json
```

Django needs a private Firebase service account file. Never commit it.

Download:

```text
Firebase Console -> Project settings -> Service accounts -> Generate new private key
```

On hosting, the easiest option is to store the whole service account JSON as a secret env variable:

```text
FIREBASE_CREDENTIALS_JSON={...full firebase service account json...}
```

Alternative file-based option:

```text
FIREBASE_CREDENTIALS_PATH=/path/to/firebase-service-account.json
```

If both are empty, Django still creates `Notification` rows but skips real push sending.

## API

Public:

- `POST /api/auth/register/`
- `POST /api/auth/token/`
- `GET /api/fruits/`
- `GET /api/fruits/?stock=normal`
- `GET /api/fruits/?stock=mirage`
- `GET /api/stock/current/`

Authenticated:

```text
Authorization: Token <token>
```

- `GET/POST /api/watches/`
- `GET/POST /api/devices/`
- `GET /api/notifications/`
- `POST /api/notifications/{id}/mark_sent/`

Admin:

- `POST /api/stock/scrape/`

Scheduler:

- `POST /api/stock/scheduled-scrape/?key=<SCRAPE_SECRET_KEY>`

## Do Not Commit

- `db.sqlite3`
- `.env`
- Firebase service account JSON
- `.venv/`
- logs

Fruit images in `media/` may be committed for the demo project so the mobile catalog has pictures immediately.
