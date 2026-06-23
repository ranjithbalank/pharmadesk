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
