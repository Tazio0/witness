# Witness — Project Documentation
**Version:** 0.1.0 — Starter Code  
**Stack:** Python (FastAPI) + Flutter + SQLite + OpenStreetMap  
**Target:** Android (Samsung Note 9, API 21+)

---

## What Has Been Built

This is your starter code — the skeleton of the Witness app. It covers:

- A working **FastAPI backend** with user auth (register/login with JWT tokens), report submission, vote-based threshold system, and map data endpoint
- A working **Flutter mobile app** with a real OpenStreetMap view, incident markers, a report submission form, and a login/register screen
- A **SQLite database** with all the tables you need to start

You will build ~95% of the real app yourself on top of this foundation.

---

## Project Structure

```
witness/
├── backend/                     ← Python FastAPI server
│   ├── main.py                  ← App entry point, registers routes
│   ├── requirements.txt         ← Python dependencies
│   └── app/
│       ├── core/
│       │   └── database.py      ← SQLite setup, table creation, seeding
│       └── routers/
│           ├── auth.py          ← POST /auth/register, POST /auth/login
│           └── reports.py       ← POST /reports/, GET /reports/map, POST /reports/{id}/vote
│
└── flutter/                     ← Flutter mobile app
    ├── pubspec.yaml             ← Dependencies (flutter_map, http, geolocator, etc.)
    └── lib/
        ├── main.dart            ← App entry, auth gate (logged in? → map : login)
        ├── services/
        │   └── api_service.dart ← All HTTP calls to backend (single file, easy to edit)
        └── screens/
            ├── map_screen.dart  ← Main screen: OpenStreetMap + incident pins
            ├── report_screen.dart ← Form to submit an incident
            └── login_screen.dart  ← Login + register (toggle between them)
```

---

## How to Run the Backend

### 1. Set up Python environment
```bash
cd witness/backend
python3 -m venv venv
source venv/bin/activate        # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Start the server
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

`--reload` means the server auto-restarts when you save a file. Very useful during development.

### 3. Test it in your browser
Go to `http://localhost:8000/docs` — FastAPI gives you a free interactive API tester. You can register a user, submit a report, and check everything works without touching the Flutter app yet.

---

## How to Run the Flutter App

### Prerequisites
- Install Flutter: https://docs.flutter.dev/get-started/install/linux
- Install Android Studio (for the Android SDK and emulator)
- Connect your Samsung Note 9 via USB, enable Developer Options + USB Debugging

### 1. Install dependencies
```bash
cd witness/flutter
flutter pub get
```

### 2. Add location permission (Android)
Open `android/app/src/main/AndroidManifest.xml` and add inside `<manifest>`:
```xml
<uses-permission android:name="android.permission.ACCESS_FINE_LOCATION"/>
<uses-permission android:name="android.permission.ACCESS_COARSE_LOCATION"/>
<uses-permission android:name="android.permission.INTERNET"/>
```

### 3. Run on your phone
```bash
flutter run
```
Flutter will detect your connected phone and install the app on it.

### 4. Connecting phone to your local backend
When running on a real device, `localhost` on the phone is NOT the same as your PC.
Find your PC's local IP address:
```bash
ip addr show | grep "inet " | grep -v 127
```
Then update `api_service.dart`:
```dart
static const String baseUrl = 'http://YOUR_PC_IP:8000';
```
Both your phone and PC must be on the same WiFi network.

---

## How the Core Systems Work

### Authentication (JWT)
1. User registers → backend hashes their password with bcrypt → stores in `users` table → returns a JWT token
2. Flutter stores that token in `SharedPreferences` (phone's local storage)
3. Every request that needs auth sends the token as: `Authorization: Bearer <token>`
4. Backend decodes the token to identify who the user is — no session, no cookies

### Threshold System (anti-fake-reports)
This is the core feature that makes Witness trustworthy. The logic lives in `reports.py`:

1. User submits a report → saved in DB with `visible = 0`, `vote_count = 1`
2. Other users see the report in a "confirm" state (not on the map yet)
3. Each user who taps "I can confirm this" adds a vote via `POST /reports/{id}/vote`
4. The `votes` table has a `UNIQUE(user_id, report_id)` constraint — one person can only vote once
5. When `vote_count >= 5` → backend sets `visible = 1` → report appears on the map
6. **Users never see the threshold number.** They just tap "confirm." This prevents gaming.

To change the threshold (make it stricter or looser), edit this line in `reports.py`:
```python
VISIBILITY_THRESHOLD = 5
```

### Map (OpenStreetMap via flutter_map)
- The `FlutterMap` widget in `map_screen.dart` loads tiles from `tile.openstreetmap.org`
- This is 100% free — no API key, no credit card, no usage limits for a small app
- Incident markers are positioned using `latitude` and `longitude` from the database
- Marker colour = severity (yellow = minor, orange = serious, red = dangerous)
- Tap a marker → bottom sheet shows details + "Confirm" button

### Report Expiry
Reports automatically expire after 24 hours. The backend filters them out in the map query:
```sql
AND (r.expires_at IS NULL OR r.expires_at > CURRENT_TIMESTAMP)
```
This keeps the map clean. An accident from yesterday is no longer relevant.

---

## Database Schema

### users
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | Auto-increment |
| email | TEXT UNIQUE | Login identifier |
| username | TEXT | Display name |
| password_hash | TEXT | bcrypt hash, never plain text |
| created_at | TIMESTAMP | Auto |

### categories
Pre-seeded with: Crime, Accident, Fire, Hazard, Protest, Flooding, Load Shedding

### reports
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| user_id | INTEGER FK | Who submitted it |
| category_id | INTEGER FK | Type of incident |
| latitude / longitude | REAL | Location |
| vote_count | INTEGER | Starts at 1 |
| visible | INTEGER | 0 = hidden, 1 = on map |
| severity | TEXT | low / medium / high |
| expires_at | TIMESTAMP | 24 hours from submission |

### votes
One row per user per report. The `UNIQUE(user_id, report_id)` constraint is your anti-spam lock.

---

## API Reference

| Method | Endpoint | Auth required | What it does |
|---|---|---|---|
| POST | /auth/register | No | Create new account |
| POST | /auth/login | No | Get JWT token |
| POST | /reports/ | Yes | Submit new report |
| GET | /reports/map?lat=&lng= | No | Get visible reports near location |
| POST | /reports/{id}/vote | Yes | Confirm a report |
| GET | /reports/categories | No | Get all incident types |

Interactive docs: `http://localhost:8000/docs` (auto-generated by FastAPI)

---

## Deployment (When You're Ready)

### Backend → Railway.app
1. Create a free account at railway.app
2. Connect your GitHub repo
3. Railway auto-detects FastAPI and deploys it
4. Add environment variables in Railway dashboard:
   - `SECRET_KEY` = a long random string
5. Update `baseUrl` in `api_service.dart` to your Railway URL

### App → Google Play Store
**Cost:** $25 once, forever

**When is it ready for the Play Store?**
Your app is ready when:
- All Phase 1–4 items on the roadmap are done
- You've tested on at least 3 real Android devices
- The app doesn't crash
- You have a privacy policy (required by Google — you can generate one free at privacypolicygenerator.info)
- You have screenshots and a description ready

**How to build the APK:**
```bash
flutter build apk --release
```
The file will be at `build/app/outputs/flutter-apk/app-release.apk`

---

## Monetisation Options (Phase 5)

These are ideas for later — do not think about these until the app is live and has users.

1. **Freemium** — Basic app is free. Premium tier ($1-2/month) gives: alerts for your saved routes, 7-day history instead of 24h, custom notification zones
2. **B2B / Government** — Sell a dashboard to municipalities or security companies. They see aggregated data, trends, heat maps. This is where real money is.
3. **Ads** — Last resort. Use Google AdMob. Only do this if the other two don't work — ads damage user trust on a safety app.

**Recommended path:** Launch free → grow users → approach City of Cape Town / SAPS / private security firms → pitch the dashboard.

---

## What You Build Next (Phase 1 Tasks)

1. **Run the backend** — follow the steps above, open `/docs`, register a user
2. **Set up Flutter** — install Flutter + Android Studio, run `flutter pub get`, run on your phone
3. **Connect them** — update the IP in `api_service.dart`, test login from your phone
4. **Add your first feature** — suggestion: add an "incident age" label on the map marker bottom sheet ("reported 2 hours ago")

When you're done with that, come back and we'll start Phase 2.

---

## Learning Resources

### Flutter (Dart)
- Official docs: https://docs.flutter.dev
- Best free course: "Flutter & Dart - The Complete Guide" on YouTube (Academind)
- Dart language tour: https://dart.dev/language

### FastAPI (Python)
- Official tutorial: https://fastapi.tiangolo.com/tutorial/ — genuinely the best backend tutorial online
- You already know Python, so FastAPI will feel very natural

### Android Development
- You don't need to learn native Android (Kotlin/Java) — Flutter handles it for you
- If you're curious: https://developer.android.com/courses

---

*Built with Claude — Anthropic. Keep pushing, Tazio. Witness could be something real.*
