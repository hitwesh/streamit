# StreamIt — Manual End-to-End Testing (Gold Reference)

This document defines the **only testing flow required (for now)**.

Constraints:
- Test **end-to-end**, exactly like a real client.
- Use **PowerShell / curl** for HTTP APIs.
- Use **Browser DevTools / wscat** for WebSockets.
- Commands and expected outputs below are the reference contract.

> Notes
> - Start Redis (required for Channels fan-out) and start the backend server before running steps.
> - WebSocket message ordering may vary in places where noted.

---

## 0️⃣ Prerequisites (once)

### 0.0 Initialize the database (FIRST RUN)

These commands must be run in this exact order when setting up the backend.

📍 Run from `backend/`:

```bash
python manage.py makemigrations
python manage.py migrate
```

What each does:
- `makemigrations` → generates migration files (schema intent)
- `migrate` → applies schema to the database

⚠️ You already have migrations in this repo, so on fresh setup:

```bash
python manage.py migrate
```

is usually enough.

### 0.1 Create a superuser (recommended)

Most manual testing assumes you have at least one registered user to log in as the **host**.

Run:

```bash
python backend/manage.py createsuperuser
```

This will prompt for email and password.

Expected behavior in this project:
- The superuser’s `display_name` defaults to `Admin`.
- You can use this account as the room host in the flows below.

### 0.2 Install wscat (WebSocket CLI)

```bash
npm install -g wscat
```

### 0.3 Verify

```bash
wscat --help
```

---

## 1️⃣ AUTH TESTING (HTTP)

### 1.1 Login (registered user)

```powershell
$session = New-Object Microsoft.PowerShell.Commands.WebRequestSession

$resp = Invoke-RestMethod http://127.0.0.1:8000/api/auth/login/ `
  -Method POST `
  -ContentType "application/json" `
  -Body '{"email":"hiteshroy0001@gmail.com","password":"Notimetodie007"}' `
  -WebSession $session
```

EXPECTED

```json
{
  "id": "...",
  "display_name": "Admin",
  "access_token": "eyJhbGciOi..."
}
```

Extract token:

```powershell
$token = $resp.access_token
```

✅ PASS CONDITION
- HTTP 200
- `access_token` present

---

### 1.2 Guest login

```powershell
$guest = Invoke-RestMethod http://127.0.0.1:8000/api/auth/guest/ `
  -Method POST `
  -ContentType "application/json" `
  -Body '{"display_name":"UserB"}'

$guestToken = $guest.access_token
```

✅ PASS
- Guest user created
- `access_token` returned

---

## 2️⃣ ROOM LIFECYCLE (HTTP)

### 2.1 Create room (HOST)

```powershell
$room = Invoke-RestMethod http://127.0.0.1:8000/api/rooms/create/ `
  -Method POST `
  -ContentType "application/json" `
  -Body '{"is_private": false}' `
  -WebSession $session

$code = $room.code
```

EXPECTED

```json
{
  "room_id": "...",
  "code": "ABCDE",
  "is_private": false
}
```

✅ PASS
- Room code returned
- Host auto-approved

---

### 2.2 Join room (guest)

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/rooms/join/ `
  -Method POST `
  -ContentType "application/json" `
  -Body "{\"code\":\"$code\"}"
```

EXPECTED

```json
{
  "status": "APPROVED",
  "is_host": false
}
```

---

## 3️⃣ WEBSOCKET TESTING (REAL TIME)

Open **TWO terminals** (or browser consoles).

### 3.1 Host WebSocket connection

```bash
wscat -c "ws://127.0.0.1:8000/ws/room/$code/?token=$token"
```

EXPECTED (order may vary)

```json
{"type":"CHAT_HISTORY","messages":[]}
{"type":"PLAYBACK_STATE","is_playing":false,"time":0}
{"type":"ROOM_PARTICIPANTS","participants":["Admin"],"host":"Admin"}
{"type":"USER_JOINED","user":"Admin"}
```

✅ PASS
- No disconnect
- No `1011` / `1006`
- Playback state always sent

---

### 3.2 Guest WebSocket connection

```bash
wscat -c "ws://127.0.0.1:8000/ws/room/$code/?token=$guestToken"
```

EXPECTED (on guest side)

```json
{"type":"CHAT_HISTORY","messages":[]}
{"type":"PLAYBACK_STATE","is_playing":false,"time":0}
{"type":"ROOM_PARTICIPANTS","participants":["Admin","UserB"],"host":"Admin"}
{"type":"USER_JOINED","user":"UserB"}
```

EXPECTED (on host side)

```json
{"type":"USER_JOINED","user":"UserB"}
```

---

## 4️⃣ CHAT TESTING

### 4.1 Chat from host

In host wscat:

```json
{"type":"CHAT_MESSAGE","message":"hello from host"}
```

EXPECTED (both sides)

```json
{"type":"CHAT_MESSAGE","user":"Admin","message":"hello from host"}
```

---

### 4.2 Disable chat (admin action)

(If you have an endpoint or admin toggle)

Then send again:

```json
{"type":"CHAT_MESSAGE","message":"should fail"}
```

EXPECTED

```json
{"type":"ERROR","message":"Chat is disabled in this room"}
```

✅ PASS
- No disconnect
- Error returned only to sender

---

## 5️⃣ PLAYBACK SYNC TESTING (CRITICAL)

### 5.1 Host plays

```json
{"type":"PLAY","time":50}
```

EXPECTED (both)

```json
{"type":"PLAY","time":50}
```

---

### 5.2 Guest tries to control playback

```json
{"type":"PAUSE"}
```

EXPECTED
- ❌ NO MESSAGE
- ❌ NO DISCONNECT

Silently ignored.

---

## 6️⃣ DISCONNECT TEST

Close guest connection (`CTRL+C`).

EXPECTED (host)

```json
{"type":"USER_LEFT","user":"UserB"}
```

---

## 7️⃣ FAILURE TESTS (YOU MUST RUN THESE)

### 7.1 Invalid token

```bash
wscat -c "ws://127.0.0.1:8000/ws/room/$code/?token=INVALID"
```

Expected:
- Immediate disconnect
- Server logs auth failure

---

### 7.2 Non-participant

Login as another user.

Connect WS without joining room.

Expected:
- WS close with code `4003`

---

## 8️⃣ Where this lives

This file is the gold reference:
- `docs/manual-testing.md`
