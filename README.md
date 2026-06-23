# PharmaDesk — Pharmacy Inventory, Billing & Supply-Chain System

Offline-first management system for a single-location retail pharmacy
(*Sri Sakthi Medicals*, Perundurai, Erode). Built to the BRD v0.5 confirmed
stack: **Django + DRF + SQLite** backend, **React + TypeScript + Tailwind**
frontend. Everything runs locally on one counter PC — no internet required.

## What's implemented (core pilot)

| BRD area | Status |
|---|---|
| Medicine master + batch/expiry stock, FEFO, reorder config | ✅ |
| GST billing with CGST/SGST split, invoice PDF (A5) | ✅ |
| Sales return / refund (restores stock to batch) | ✅ |
| Customers + regular flag + credit / khata | ✅ |
| Prescription capture + Schedule H1 register | ✅ (model + report) |
| Suppliers + purchase orders + auto-suggest reorder + goods receipt | ✅ |
| In-app alerts: low / out-of-stock / near-expiry (offline) | ✅ |
| Reports (stock, sales, GST, near-expiry, H1) → Excel & PDF | ✅ |
| Shop / GST / operational settings | ✅ |

## Project layout

```
backend/    Django + DRF API (apps: core, inventory, customers, billing, purchasing, reports)
frontend/   Vite + React + TS + Tailwind SPA
```

## Running it (development)

Two terminals. **Backend** (port 8000):

```bash
cd backend
venv/Scripts/python manage.py migrate        # first run only
venv/Scripts/python manage.py seed_demo      # optional: demo data
venv/Scripts/python manage.py runserver
```

**Frontend** (port 5173, proxies /api to :8000):

```bash
cd frontend
npm install                                  # first run only
npm run dev
```

Open the printed `http://localhost:5173/` URL.

## Running it as the counter app (packaged, single PC)

This is how the pharmacy actually runs it — one local server, one window, no
internet. Django serves the built React UI; Waitress runs it; pywebview gives
the desktop window (BRD §9.4).

```bat
build-desktop.bat      :: builds the UI + collects static + migrates (run after code changes)
start-desktop.bat      :: launches the desktop app (Waitress + window)
start-desktop.bat --browser   :: serve only; open in the default browser instead
```

`desktop.py` migrates the DB, collects static, takes a startup backup, serves
on `127.0.0.1:8000`, and opens the window. Everything is localhost.

### Auto-start at logon + daily backup

```powershell
powershell -ExecutionPolicy Bypass -File install-autostart.ps1
```

Registers two Scheduled Tasks: launch at logon, and a daily 21:00 DB backup.

## Backup & restore (SEC-3 — the one security item kept firmly in MVP)

```bash
python manage.py backup_db        # timestamped copy in backend/backups/ (+ off-machine if set)
python manage.py restore_db       # show what the latest backup would restore
python manage.py restore_db --yes # restore latest (parks current DB first, so it's reversible)
python manage.py restore_db path/to/file.sqlite3 --yes
```

Set an **off-machine** copy (external drive / cloud-synced folder) so a PC
failure can't lose data (BRD R-3):

```bat
setx PHARMADESK_BACKUP_DIR "D:\Backups\PharmaDesk"
```

## Key API endpoints

- `GET /api/dashboard/` — counters for the dashboard cards
- `GET /api/medicines/?search=` — medicine master / lookup
- `POST /api/invoices/` — create a bill (FEFO allocation handled server-side)
- `GET /api/invoices/{id}/pdf/` — invoice PDF
- `POST /api/notifications/refresh/` — recompute alerts
- `GET /api/reports/{key}/?export=xlsx|pdf` — reports + export
  (keys: `stock_valuation`, `low_stock`, `near_expiry`, `sales`, `gst_summary`, `schedule_h1`)

## Notes

- `format` is reserved by DRF, so report export uses `?export=xlsx|pdf`.
- Single shared login per BRD §7 (auth left light for v1).
- Cloud sync is deferred (BRD §12.3) — the same Django backend redeploys to
  PostgreSQL later with config-only changes.
- **WhiteNoise** (MIT, permissive) was added beyond the BRD §15 SBOM to serve
  the React build from the local Django server. Regenerate the SBOM on release
  per BRD §15.5; the licence stance (closed-source, commercial) is unchanged.
