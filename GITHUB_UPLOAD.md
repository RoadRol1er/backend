# GitHub Upload Guide

Current local layout:

```text
D:\Python\BloxStockTracker   # Django backend
D:\Python\bloxstockmobile    # Flutter mobile app
```

Do not upload the whole `D:\Python` folder. It contains many unrelated projects.

## Recommended Option: Two Repositories

Create two GitHub repositories:

```text
blox-stock-backend
blox-stock-mobile
```

Backend:

```powershell
cd D:\Python\BloxStockTracker
git init
git add .
git commit -m "Initial backend"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/blox-stock-backend.git
git push -u origin main
```

Mobile:

```powershell
cd D:\Python\bloxstockmobile
git init
git add .
git commit -m "Initial mobile app"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/blox-stock-mobile.git
git push -u origin main
```

## Do Not Commit

Backend:

```text
db.sqlite3
.env
firebase-service-account.json
.venv/
```

Mobile:

```text
build/
.dart_tool/
android/local.properties
key.properties
*.jks
```

## Firebase Files

`android/app/google-services.json` is used by the Android app. For a student/demo project it can be committed, or each student can create their own Firebase app and replace it.

Firebase service account JSON is a private server key. Never commit it.

## First Run After Clone

Backend:

```powershell
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_fruits
python manage.py scrape_stock
python manage.py runserver 127.0.0.1:8000
```

Mobile:

```powershell
flutter pub get
flutter run -d chrome --dart-define=API_BASE_URL=http://127.0.0.1:8000
```
