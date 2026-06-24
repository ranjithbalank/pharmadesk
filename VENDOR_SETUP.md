# PharmaDesk — Counter PC Setup & Go-Live Guide

A step-by-step guide to install PharmaDesk on the pharmacy's counter PC and
hand it over ready for billing. Written for the person doing the install.

> Treat the first 1–2 weeks as a **pilot run alongside the paper register**
> until you trust it (BRD R-1). Do the opening-stock entry early — it is the
> single biggest task before go-live (BRD A5).

---

## 0. What you need

- A Windows 10/11 PC (the counter machine).
- **Python 3.13+** and **Node.js 20+** installed (one-time).
- The PharmaDesk project folder copied to the PC, e.g. `D:\pharma desk`.
- The shop's **GSTIN**, **drug-licence number**, and GST rates/HSN for its range.
- A receipt/A5 printer (optional for pilot; PDF works without one).

---

## 1. One-time install

Open a terminal in the project folder and set up the backend:

```bat
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
```

Then build the user interface into the app:

```bat
cd ..
build-desktop.bat
```

This compiles the React UI and bundles it into the local server. Re-run
`build-desktop.bat` only when the code changes.

---

## 2. Make it the shop's own (clean go-live data)

The project ships with demo data for trying it out. Before real billing, wipe
it and set the shop's identity:

```bat
cd backend
venv\Scripts\activate
python manage.py prepare_golive --yes ^
  --shop "Sri Sakthi Medicals" ^
  --gstin 33ABCFS1234K1Z9 ^
  --licence TN/ERD/20B/2021/0456 ^
  --address "Perundurai, Erode District, Tamil Nadu" ^
  --phone "04294 222333"
```

(You can also change these any time later in the app under **Settings**.)

---

## 3. Enter the opening stock

This is the big one. Two ways:

**A. Bulk import (recommended for many items)** — fill in a spreadsheet using
`opening_stock_template.csv` as the format, save as CSV, then:

```bat
python manage.py import_stock "C:\path\to\opening_stock.csv" --dry-run   :: check first
python manage.py import_stock "C:\path\to\opening_stock.csv"             :: real import
```

Re-running is safe — it updates rather than duplicating. Tip: enter the
fast-moving items first so you can start billing while the long tail is keyed in.

**B. By hand** — open the app (next step) and add medicines and batches on the
**Inventory** screen.

---

## 4. Launch the app

```bat
start-desktop.bat
```

A PharmaDesk window opens. Everything runs locally on this PC — no internet
needed. (If the window doesn't open on this machine, use
`start-desktop.bat --browser` to open it in the default browser instead.)

### Sign in (single shared login)

Default credentials on first launch:

- **Username:** `admin`
- **Password:** `pharmadesk`

**Change the password** right after go-live: **Settings → Login password**.
(You can also set custom defaults before first run with the `PHARMADESK_USER`
and `PHARMADESK_PASSWORD` environment variables.)

### Make it start automatically + back up daily

```powershell
powershell -ExecutionPolicy Bypass -File install-autostart.ps1
```

This registers PharmaDesk to launch at logon and back up the database every
night at 9 pm.

---

## 5. Protect the data (do not skip)

A PC failure or theft must not lose the shop's data (BRD R-3 / SEC-3). Point
backups at an off-machine location — an external drive or a cloud-synced folder:

```bat
setx PHARMADESK_BACKUP_DIR "E:\Backups\PharmaDesk"
```

Backups are written to `backend\backups\` and copied to that folder. To restore
after a problem (stop the app first):

```bat
python manage.py restore_db          :: shows what the latest backup would restore
python manage.py restore_db --yes    :: restore it (your current DB is parked first)
```

---

## 6. First-day checklist

- [ ] Shop name, GSTIN, licence show correctly on a test invoice (Billing → Save → Print/PDF).
- [ ] A known medicine searches and bills; stock goes down after the sale.
- [ ] A Schedule H1 medicine asks for prescription details before it will bill.
- [ ] Low-stock / near-expiry alerts appear on the Dashboard.
- [ ] Reports open and export to Excel and PDF.
- [ ] `start-desktop.bat` launches the app; a backup file appears in `backend\backups\`.
- [ ] Off-machine backup folder is set and a copy lands there.

When all boxes are ticked, run it beside the paper register for a week, then go live.

---

## Daily use, in one line

Double-click the PharmaDesk icon (or just log in if auto-start is set) → bill on
the **Billing** screen → check the **Dashboard** for alerts → **Day close** at
night to reconcile cash. Backups run themselves.

For troubleshooting and developer details, see `README.md`.
