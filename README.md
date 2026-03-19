# Witness 👁️
> Community safety reporting for South Africa

Witness is a mobile app that lets South Africans report crimes, accidents, fires and hazards in real time. Incidents are pinned on a live map so people can see what's happening around them and stay safe on their daily commute.

---

## The problem
South Africans have no accessible, real-time tool to warn each other about dangers in their area. WhatsApp groups exist but they're scattered, unverified and hard to act on quickly.

## The solution
A map-based reporting app where the community is the sensor network. Reports are verified by crowd consensus before they appear — keeping the map trustworthy.

---

## Features
- 📍 Live incident map powered by OpenStreetMap
- 🚨 Report crimes, accidents, fires, hazards and more
- ✅ Crowd verification system — incidents need multiple confirmations before going live
- ⏱️ Reports expire automatically after 24 hours
- 🔒 Secure auth with JWT tokens
- 📱 Android-first (Play Store)

---

## Tech stack
| Layer | Technology |
|-------|-----------|
| Mobile | Flutter (Dart) |
| Backend | Python + FastAPI |
| Database | SQLite → PostgreSQL |
| Maps | OpenStreetMap (flutter_map) |
| Auth | JWT + bcrypt |
| Hosting | Railway.app |

---

## Getting started

### Backend
```bash
cd backend
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```
API docs available at `http://localhost:8000/docs`

### Flutter
```bash
cd flutter
flutter pub get
flutter run
```

---

## API endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /auth/register | Create account |
| POST | /auth/login | Login, returns JWT |
| POST | /reports/ | Submit incident |
| GET | /reports/map | Fetch verified incidents near location |
| POST | /reports/{id}/vote | Confirm an incident |
| GET | /reports/categories | List incident types |

---

## Roadmap
- [x] Backend API with auth and reporting
- [x] SQLite database with threshold verification
- [ ] Flutter map screen with live incident pins
- [ ] Android app on Play Store
- [ ] Push notifications
- [ ] Neighbourhood communities
- [ ] Authority alert system
- [ ] National expansion

---

## Licence
MIT © 2026 Tazio Petersen
