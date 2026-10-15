# Fob Tracker

A small time-tracking app for USB RFID/NFC fob readers. Staff tap a fob on
the reader, the kiosk screen shows a big "Clocked IN/OUT" message, and the
manager gets a live dashboard, a monthly Excel export, and a REST API.

## Features

- **Kiosk scan page** — auto-focused input catches whatever a USB
  HID-style RFID/NFC reader types; direction (IN/OUT) toggles automatically
  from the user's previous scan that day.
- **Manager dashboard** — live tiles for who's currently clocked in,
  today's activity, this week's hours, and the last 20 scans.
- **Users & fobs** — add users, assign fobs to users on a dedicated
  enrollment page (scan the fob, pick the user, done).
- **Manual scans** — admin can retro-enter a clock-in/out with a reason
  note; manual entries are flagged in the dashboard and in the Excel export.
- **Monthly Excel** — Summary (per-user totals) + Daily (clock-in/out pairs
  with session hours).
- **REST API** — read-only JSON endpoints behind an `X-API-Key` header,
  for your own dashboard to pull from.

## Quick start

```bash
cd fob-tracker/
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                                   # then edit secrets
python run.py
```

Then on the kiosk PC open <http://localhost:5000/> and tap a fob.
Admin login is at <http://localhost:5000/admin/login>.

## How the reader is wired in

Most cheap USB RFID/NFC readers act as a **HID keyboard**: when a fob is
tapped, they type its UID and press Enter. The kiosk page (`/`) keeps a
hidden `<input>` focused and submits whatever text was typed to the backend
on Enter. No drivers, no SDK — if you can type into a text box, the reader
works.

If your reader adds a prefix/suffix (e.g. leading zeros, carriage return),
tweak the `strip` logic at the top of `app/static/scan.js` once, and move on.

## Tests

```bash
pytest -q
```

## Known limitations (v1)

- Shifts crossing midnight are split at midnight. Hours after midnight count
  on the following day. Add a shift-aware mode later if you have night staff.
- Single admin login (from `.env`); no per-manager accounts.
- No HTTPS by itself — run behind a reverse proxy or on a trusted LAN.
- No rate-limiting on the API — fine for a LAN deployment.
