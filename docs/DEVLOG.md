# Witness — Dev Log
Personal notes, progress tracking and things I've learned. Not for public consumption.

---

## Progress log

### Day 1 — 19 March 2026
- Decided on the app idea (inspired by Citizen app)
- Named it **Witness**
- Chose the stack: Python backend, Flutter frontend, OpenStreetMap
- Generated starter code with Claude
- Created architecture diagram and wall roadmap
- Pushed first commit to GitHub: github.com/Tazio0/witness
- Registered on NYDA and submitted BMT training application
- Target laptop: Lenovo ThinkPad T14 Gen 2 (16GB RAM), R8,199 from Supercomm.co.za

### Day 2 — 20 March 2026
- Fixed Python version issue (system had 3.14, pydantic-core needs 3.12)
- Installed Python 3.12 via pyenv
- Fixed bcrypt compatibility issue — downgraded to bcrypt==4.0.1
- Got FastAPI backend running on localhost:8000
- Successfully registered first user via /docs
- Rewrote README to tell the real story of why Witness exists
- Added DEVLOG as separate personal file (README is now public facing only)
- Learned: POST vs GET, bcrypt hashing, JWT tokens, HTTP status codes, venv, pyenv
- Walked through main.py and database.py in detail (see concepts below)

---

## Concepts learned

### HTTP methods
- **POST** — send data, create something (register user, submit report)
- **GET** — fetch data (get map reports, get categories)
- **PUT** — update something that already exists
- **DELETE** — remove something

### Password hashing (bcrypt)
Passwords never get stored as plain text. bcrypt scrambles them into a long unreadable string. Even if someone stole the database they couldn't read the passwords. The scramble is one-way — you can't reverse it. What gets stored looks like: `$2b$12$xK9mN3Rq...`

### JWT tokens
When you log in, the server gives you a token — like a temporary ID card. You show this token on every future request instead of typing your password again. It expires after 7 days. On the Flutter side it gets stored using SharedPreferences (phone's local storage).

### HTTP status codes
- **200** — OK, here's what you asked for
- **201** — Created successfully
- **400** — Bad request (you sent something wrong)
- **401** — Unauthorised (need to log in)
- **404** — Not found
- **500** — Server crashed

### Virtual environments (venv)
An isolated Python installation for a project. Packages installed inside it don't affect other projects. Always activate before working: `source venv/bin/activate`. You'll see `(venv)` appear in your terminal prompt when it's active.

### pyenv
Lets you install and switch between multiple Python versions on the same machine. Needed because EndeavourOS ships Python 3.14 but some packages haven't caught up yet.

### SQLite
A database that lives in a single file (witness.db) on your machine. No separate server needed. Perfect for development. The file gets created automatically when the server first starts. We'll migrate to PostgreSQL for production.

### main.py — what it does
- Creates the FastAPI app (the web server)
- Adds CORS middleware so the Flutter app can talk to the backend from a different address
- Registers the auth and reports route groups
- Runs `init_db()` on startup to create tables
- Exposes a `/health` endpoint for Railway.app to check if the server is alive

### database.py — what it does
- `get_db()` opens a connection to witness.db — like opening a filing cabinet. Always closed after use.
- `init_db()` creates the four tables on startup using `CREATE TABLE IF NOT EXISTS` (won't crash if tables already exist)
- Seeds default categories on first run by checking if the table is empty first
- The `UNIQUE(user_id, report_id)` constraint on the votes table is the database-level anti-spam lock — even if someone bypasses the API, the database itself rejects duplicate votes

### The four tables and how they relate
- **users** — one row per person. Stores hashed password, never plain text
- **categories** — incident types, pre-seeded (Crime, Fire, Accident, Hazard, Protest, Flooding, Load Shedding)
- **reports** — every submitted incident. Starts with `visible = 0`. Flips to `visible = 1` after threshold is hit
- **votes** — who confirmed what. One row per user per report, enforced by database constraint

---

## Planned features (not yet built)

### Device fingerprinting — prevent multiple accounts per device
**Why:** Someone could create 5 accounts and confirm their own fake report 5 times, making it visible.

**How it'll work:**
- When registering, Flutter sends a unique device ID alongside email/password (using the `device_info_plus` package)
- Backend stores the device ID against the user account
- If someone tries to register a second account with the same device ID — blocked
- Phone transfers allowed, but only once every 90 days (store a `device_last_changed` timestamp)

**Why not built yet:** Requires Flutter to be working first. Device fingerprinting needs both sides to work together. Build in Phase 2.

**Limitation to keep in mind:** Device IDs can be spoofed by determined people. But combined with the 5-vote threshold, someone would need 5 different devices to get one fake report visible — a serious barrier for 99% of bad actors.

### Community groups (Phase 5)
Neighbourhood-based chat/communication. People in the same area can talk to each other, verify reports together, ask questions. Needs real-time messaging (WebSockets) which is expensive on free hosting — build only once there's an active user base. Consider using Stream Chat or Supabase for the messaging layer rather than building from scratch.

### Authority notifications (Phase 5)
High severity reports (or reports that hit a higher vote threshold) trigger an automatic alert to relevant authorities via email or SMS webhook. Twilio for SMS, simple SMTP for email.

### Push notifications (Phase 5)
Alert users when a new incident is reported near their saved locations or regular routes. Firebase Cloud Messaging (FCM) — free tier is generous.

---

## Known issues / fixes applied
- bcrypt 5.x incompatible with passlib on Python 3.12 — pinned to `bcrypt==4.0.1` in requirements.txt
- pyenv shim didn't activate properly — had to use full path to create venv: `~/.pyenv/versions/3.12.13/bin/python -m venv venv`
- System Python is 3.14, pydantic-core max supported is 3.12 — solved with pyenv

---

## How to run the backend
```bash
cd ~/Desktop/witness/backend
source venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```
Then open: http://localhost:8000/docs

---

## NYDA funding application
- Registered: 19 March 2026
- BMT application submitted: 19 March 2026
- Waiting for NYDA to call and schedule BMT session
- After BMT certificate → grant application unlocks → R8,199 for ThinkPad T14

---

## Roadmap
| Phase | What | Status |
|-------|------|--------|
| 1 | Backend running + DB working | ✅ Done |
| 2 | Auth + reports API fully tested | 🔄 In progress |
| 3 | Flutter setup + map on phone | ⏳ Next |
| 4 | Deploy to Railway.app | ⏳ Pending |
| 5 | Play Store ($25 one-time fee) | ⏳ Pending |
| 6 | Device fingerprinting | ⏳ Pending |
| 7 | Communities feature | 💡 Future |
| 8 | Authority notifications | 💡 Future |
| 9 | Push notifications | 💡 Future |
| 10 | Monetisation | 💡 Future |

---

## Resources
- FastAPI docs: https://fastapi.tiangolo.com/tutorial/
- Flutter docs: https://docs.flutter.dev
- device_info_plus package: https://pub.dev/packages/device_info_plus
- Railway hosting: https://railway.app
- NYDA portal: https://erp.nyda.gov.za
- Supercomm laptop: https://supercomm.co.za
