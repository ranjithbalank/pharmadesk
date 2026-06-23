# Business Requirements Document (BRD)
## Pharmacy Inventory, Billing & Supply-Chain Management System

| | |
|---|---|
| **Document version** | 0.5 (Draft) |
| **Date** | 21 June 2026 |
| **Prepared by** | Product Director (functional) & Security Lead (security/compliance) |
| **Client** | Single-location retail pharmacy, Perundurai, Erode District, Tamil Nadu |
| **Status** | For client review — open questions in Section 13 must be closed before build |

---

## 1. Executive Summary

This document defines the business requirements for a software system that manages a small retail pharmacy's stock, purchasing, suppliers, billing and customer/prescription records. The system is **offline-first**: it must work fully without internet at the counter and synchronise to the cloud when a connection is available — a deliberate choice given intermittent connectivity in the operating area.

The scope confirmed with the client covers four pillars: (1) inventory with batch and expiry control, (2) purchase orders and supplier management, (3) GST-compliant billing with customer and prescription records, and (4) reporting and in-app alerting. Because the system stores prescriptions and customer data, it carries health-data privacy obligations under India's DPDP Act and drug record-keeping duties under the Drugs & Cosmetics Rules. Security and compliance are therefore treated as first-class requirements, not add-ons.

---

## 2. Business Context & Objectives

The pharmacy currently faces the problems a manual or partly-manual operation typically has: stock-outs of fast-moving medicines, money locked in slow or expiring stock, no early warning before items run out, and reordering driven by memory rather than data. The system exists to fix these.

**Primary business objectives**

1. Never lose a sale to an avoidable stock-out, and never sell or hold expired stock.
2. Reduce capital tied up in dead/near-expiry inventory through expiry-aware reporting.
3. Make purchasing decisions data-driven (reorder points, supplier lead times).
4. Produce GST-correct bills quickly at the counter.
5. Keep statutory records (Schedule H1 register, expiry/batch trace) without extra manual books.
6. Give the owner clear visibility through reports exportable to Excel and PDF.

**Success metrics (to baseline and review at 3 months post go-live)**

- Reduction in stock-out incidents on the top-50 fast-moving items.
- Reduction in value of stock written off to expiry.
- Average billing time per customer at the counter.
- % of purchase orders generated from system reorder suggestions vs. manual.

---

## 3. Scope

### 3.1 In scope
- Inventory / stock management with batch number, expiry date, and FEFO (first-expiry-first-out) handling.
- Purchase order creation, supplier (distributor) management, goods-receipt against POs.
- GST-compliant sales billing / invoicing.
- Customer records and prescription (Rx) capture, including the Schedule H1 register.
- In-app notifications: low stock, reorder-point reached, out-of-stock, and near-expiry.
- Reports with export to **Excel (.xlsx)** and **PDF**.
- Multi-user access on a shared counter device with individual accountability (see Section 7).
- Offline-first operation with cloud sync and automatic local + cloud backup.

### 3.2 Out of scope (this phase — candidates for later)
- Direct electronic ordering / EDI integration with distributors' systems.
- Accounting/ledger system, GST return filing (GSTR-1/3B) automation, e-invoice IRN generation (not mandatory at this turnover; can be added later if turnover grows past ₹5 crore).
- Online/e-commerce storefront or home-delivery module.
- Insurance / third-party-payer claim processing.
- Multi-branch / franchise consolidation (architecture will not block this, but it is not built now).
- Biometric hardware integration.

---

## 4. Stakeholders & Users

| Role | Who | What they do in the system |
|---|---|---|
| Owner / Pharmacist-in-charge | Business owner | Full access: reports, pricing, purchasing, user management, settings |
| Counter staff | 2–3 staff total | Billing, stock lookup, goods receipt, raising indents |
| (External) Drug Inspector / Auditor | Occasional | No login; staff produce statutory reports on request |
| Distributors / Suppliers | External | No login; represented as data records (supplier master) |

> **Login model (confirmed):** the client has chosen a **single shared login** — the system is run as one responsibility on one counter PC. Per-user logins and audit trails are noted as an optional later add-on if staff or branches grow.

---

## 5. Functional Requirements

Requirements are grouped by module and tagged (FR-x). Priority: **M** = Must-have (MVP), **S** = Should-have, **C** = Could-have (later).

### 5.1 Inventory & Stock Management

| ID | Requirement | Priority |
|---|---|---|
| FR-1 | Maintain a medicine master: name, generic/composition, manufacturer, HSN code, GST rate, schedule (H/H1/X/OTC), pack/unit, rack location. | M |
| FR-2 | Track stock at **batch level** with batch number, manufacturing date, expiry date, purchase cost, and MRP. | M |
| FR-3 | Apply **FEFO** — when billing, the system defaults to issuing the earliest-expiring batch first. | M |
| FR-4 | Block billing of an expired batch; warn on near-expiry (configurable window, e.g. 90 days). | M |
| FR-5 | Per-item reorder configuration: reorder level, reorder quantity, and (optionally) min/max stock. | M |
| FR-6 | Stock adjustments (damage, expiry write-off, count correction) with reason and user stamp. | M |
| FR-7 | Stock-take / physical-count mode that reconciles counted vs. system quantity. | S |
| FR-8 | Barcode scan support for fast lookup at billing and goods-receipt (USB/standard scanner). | S |

### 5.2 Purchase Orders & Supply Chain

| ID | Requirement | Priority |
|---|---|---|
| FR-9 | Supplier (distributor) master: name, GSTIN, contact, payment terms, lead time. | M |
| FR-10 | Auto-generate a suggested purchase order / indent from items at or below reorder level, grouped by preferred supplier. | M |
| FR-11 | Create, edit, and finalise a Purchase Order; export PO to PDF for sending to the distributor. | M |
| FR-12 | Goods receipt against a PO: record received batches, expiry, cost, free quantity/scheme; update stock automatically. | M |
| FR-13 | Handle partial receipts and short supply against an open PO. | S |
| FR-14 | Record purchase returns to supplier (e.g. near-expiry returns). | S |
| FR-15 | Supplier performance view: lead-time adherence, short-supply history. | C |

### 5.3 Billing / Invoicing (GST)

| ID | Requirement | Priority |
|---|---|---|
| FR-16 | Generate a GST-compliant tax invoice: seller GSTIN & drug-licence no., item lines with HSN, batch, expiry, quantity, rate, CGST/SGST split, total. | M |
| FR-17 | Support cash and credit sales; print or share invoice as PDF; thermal/A5 print layout. | M |
| FR-18 | Sales return / refund against an existing invoice, restoring stock to the correct batch. | M |
| FR-19 | Discounts (line and bill level) within owner-set limits. | S |
| FR-20 | Daily sales summary / cash reconciliation at end of day. | M |
| FR-21 | Design billing data model so e-invoice (IRN/QR) can be added later without rework, in case turnover crosses ₹5 crore. | S |

### 5.4 Customer & Prescription (Rx) Records

| ID | Requirement | Priority |
|---|---|---|
| FR-22 | Customer master: name, phone, optional address; link sales history to a customer. | M |
| FR-22a | **Regular customer:** flag a customer as a regular; one-tap view of their purchase history and usual medicines. | M |
| FR-22b | **Quick re-bill:** for a regular, pull their previous/usual items into a new bill to speed up repeat purchases. | S |
| FR-22c | **Credit / khata (optional):** record credit sales and payments for trusted regulars and show outstanding balance. | S |
| FR-23 | Capture prescription details for scheduled drugs: prescriber name & registration, patient name, drug, quantity, date. | M |
| FR-24 | Maintain the **Schedule H1 register** as a system-generated, exportable record retained for the statutory period (3 years). | M |
| FR-25 | Optional attachment of a scanned/photographed prescription image to a sale. | C |
| FR-26 | Consent capture/notice for storing customer personal data (DPDP). | M |

### 5.5 Notifications / Alerts (in-app)

| ID | Requirement | Priority |
|---|---|---|
| FR-27 | **Low-stock** alert when quantity falls to/below reorder level. | M |
| FR-28 | **Reorder** prompt that lets the user push flagged items straight into a draft PO. | M |
| FR-29 | **Out-of-stock** alert for zero-quantity items that are normally stocked. | M |
| FR-30 | **Near-expiry** alert for batches inside the configured expiry window. | M |
| FR-31 | A single in-app notification centre / dashboard badge; alerts persist until actioned or dismissed. | M |
| FR-32 | Optional daily digest (e.g. a morning summary of items needing attention). | S |

> Notifications are **in-app** and work fully offline — no internet or external messaging service required.

### 5.6 Reporting & Export

| ID | Requirement | Priority |
|---|---|---|
| FR-33 | Standard reports: current stock & valuation, low/out-of-stock, near-expiry/expired, sales (by day/item/category), purchases, supplier-wise purchase, GST summary, Schedule H1 register. | M |
| FR-34 | Every report exportable to **Excel (.xlsx)** and **PDF**. | M |
| FR-35 | Date-range and category filters on reports. | M |
| FR-36 | Reports run against local data so they work offline. | M |

### 5.7 User & System Administration

| ID | Requirement | Priority |
|---|---|---|
| FR-37 | Owner can create staff users, assign roles, and deactivate users. | M |
| FR-38 | Role-based permissions (e.g. counter staff cannot change pricing or view profit margins). | M |
| FR-39 | Audit log of sensitive actions (price change, stock write-off, refund, user changes), attributable to a user. | M |
| FR-40 | Configurable settings: GST rates, reorder defaults, expiry-alert window, shop/licence details. | M |
| FR-41 | Manual + automatic backup and a tested restore procedure. | M |

---

## 6. Non-Functional Requirements

| ID | Area | Requirement |
|---|---|---|
| NFR-1 | **Offline-first** | All counter operations (billing, lookup, stock, goods receipt) must work with zero internet. The app holds a complete local copy of the working data. |
| NFR-2 | **Sync** | When online, data syncs automatically to the cloud. Sync must be resilient to dropped connections and must define conflict-resolution rules (see risk R-2). For a single-device shop, conflicts are rare; the system must still handle them deterministically. |
| NFR-3 | **Performance** | Billing a typical basket and item lookup should feel instant (sub-second) on modest hardware, since these run locally. |
| NFR-4 | **Reliability / Backup** | Local automatic backup daily; cloud backup on sync. Documented, tested restore. Loss tolerance: at most one day of data. |
| NFR-5 | **Usability** | Optimised for fast counter use, keyboard- and barcode-driven, minimal clicks per bill. Language: English UI for v1; Tamil labels a later option (C). |
| NFR-6 | **Hardware footprint** | Runs on a standard low-to-mid spec Windows counter PC; supports a standard receipt/thermal printer and USB barcode scanner. |
| NFR-7 | **Maintainability** | Built on a mainstream, well-supported stack so future developers can maintain it; configuration not hard-coded. |
| NFR-8 | **Data retention** | Statutory records retained per law (e.g. Schedule H1 for 3 years); personal data retained no longer than needed (DPDP principle). |

---

## 7. Security & Data Safety (kept light per client direction)

Per the client's decision, this is operated as a **single system on one counter PC under one responsibility**, so heavyweight access control (per-user logins, full audit trails, encryption-at-rest) is **not** built into v1. What remains is the minimum that protects the business from data loss and casual misuse:

- SEC-1 (M): **Single shared login** for the system (client's confirmed choice).
- SEC-2 (M): A simple **admin password** to protect settings that shouldn't be changed casually (pricing, GST rates, shop/licence details).
- SEC-3 (M): **Automatic backup with a tested restore.** This is the one item we keep firmly in MVP — for a 7-day-built system holding your stock and sales, losing the data must not be possible. Daily local backup plus a copy off the machine (cloud or external drive).
- SEC-4 (note): Because prescriptions and customer phone numbers are personal data, keep ordinary care — don't expose the data, keep backups private. Formal DPDP tooling is intentionally out of scope at this scale.

Heavier controls (per-user PINs, full audit log, encryption-at-rest) are available as a later add-on if the pharmacy grows or adds staff.

---

## 8. Compliance (kept light — very small scale, per client direction)

Not built as a heavy module. Two points worth keeping in mind:

- **GST (confirmed in place):** Sales invoices are GST-compliant — GSTIN, HSN code, CGST/SGST split, totals. Government **e-invoicing (IRN/QR) does not apply** at this turnover.
- **Worth knowing (not heavily built):** selling Schedule H1 drugs still legally requires a register, and storing customer data carries baseline data-privacy duties. The system still captures prescription details against scheduled-drug sales (FR-23) so a record exists if ever asked for, but no dedicated compliance tooling is built in v1. Confirm specifics with your own advisor if needed.

---

## 9. Recommended Technical Architecture & Stack

### 9.1 Architecture shape (confirmed: Django + DRF + React, single PC)

In v1, everything runs on **one counter PC**. A local **Django + Django REST Framework (DRF)** API talks to a local database; the **React** UI runs in a desktop window (or browser) and calls that API over **localhost**. No internet is required — it's a local server, not a cloud dependency.

```
[ Counter PC ]
  React UI (desktop window / browser)
        |  HTTP over localhost
  Django + DRF API  ──  SQLite (local DB)
        |
  Receipt printer  (USB barcode scanner optional)

Later cloud version: the SAME Django + DRF backend deploys to a server
with PostgreSQL; the React app simply points at it (multi-store, remote reports).
```

The key payoff of this stack: the backend you build for one shop is the backend you'll redeploy to the cloud for the SaaS version — minimal rework.

### 9.2 Confirmed stack

| Layer | Choice | Why |
|---|---|---|
| Backend / API | **Python + Django + Django REST Framework** | Mature, batteries-included; clean REST API; great Claude-Code + Python-team fit |
| Database (v1) | **SQLite** (Django default) | Zero-config, perfect for a single PC, backed up as a single file |
| Database (cloud, later) | **PostgreSQL** | Same Django ORM — change config, not code |
| Frontend | **React + TypeScript + Tailwind CSS** | Fast, clean counter UI |
| Data fetching / live UI | **React Query (TanStack Query)** | Refetch-on-action gives the real-time feel against the local API |
| Local app server | **Waitress** (Windows-friendly WSGI) or Uvicorn/Gunicorn | Runs Django as a background service that auto-starts on the counter PC |
| Desktop packaging | **pywebview** wrapping the local server (optionally PyInstaller to bundle Python) | Gives a desktop-app feel; one icon to launch |
| Excel export | **openpyxl** (server-side, Python) | Generates `.xlsx` reports |
| PDF export & invoices | **WeasyPrint** or **ReportLab** (server-side) | Invoices and report PDFs, generated locally |
| Notifications | In-app, computed from stock thresholds | Fully offline |
| Auth | Django's built-in auth (single shared login) | Simple, sufficient for v1 |

### 9.3 Real-time + dynamic offline on this stack
- **"Real-time":** React Query refetches right after each action (save a bill → stock and alerts update immediately). Every call is localhost, so latency is tiny. True server-push (for multiple counters) can be added later with Django Channels / WebSockets.
- **"Dynamic offline":** Django, the database, all business logic, and PDF/Excel generation run on the counter PC, and the React app talks only to localhost — so the system is **100% functional with zero internet**.
- **Single counter in v1.** Live stock-sharing across two counters at once needs the cloud/server version.

### 9.4 The one thing to get right for v1: running the local server
Unlike an embedded-database desktop app, this stack has a **server process**, so make sure:
- The Django server **auto-starts** on PC boot (Windows service / Task Scheduler) and restarts if it crashes.
- One **desktop shortcut** launches the UI (a pywebview window, or the browser in app/kiosk mode pointed at `localhost`).
- Django **serves the built React app** (static files), so there's a single thing to run.
- **Daily local DB backup** + an off-machine copy (external drive) — unchanged from before.

This is slightly more setup than a single-`.exe` app, but it's the reason the same code base scales straight into your cloud SaaS later.

---

## 10. High-Level Data Entities

Medicine (item) · Batch (links to Medicine; carries expiry/cost/MRP) · Stock movement (purchase, sale, return, adjustment) · Supplier · Purchase Order · PO line · Goods Receipt · Invoice · Invoice line · Customer · Prescription record · Schedule H1 register entry · User · Role · Audit log · Notification · Settings.

These map directly to the functional requirements and are listed so the eventual developer can validate coverage.

---

## 11. Assumptions & Dependencies

- A1: Single physical location, one primary counter PC; 2–3 staff total.
- A2: A reliable enough power and occasional-internet environment for periodic sync.
- A3: A receipt/thermal printer and (optionally) a USB barcode scanner are available or will be purchased.
- A4: The pharmacy can supply its GSTIN, drug-licence number, and GST rates/HSN data for its product range.
- A5: **No existing digital data.** Records are currently kept on a physical register. The medicine master and opening stock must be **entered manually** at setup — this is a real, sizeable task (see timeline, Section 12) and the single biggest go-live dependency.
- A6: Compliance specifics (Schedule H1 format, retention) will be confirmed with the pharmacy's advisor before go-live.

---

## 12. Timeline & Delivery Estimate

**Team (confirmed):** two developers — one **senior**, one **junior** — plus **Claude Code** for AI-assisted scaffolding. v1 is **local-only, single PC (no cloud sync)**. Dropping sync removes the single hardest piece, and AI-assisted coding speeds the boilerplate, so the realistic full-v1 timeline is roughly **2.5–3 weeks** — not the 5–6 weeks a lone developer with sync would need. What still cannot be compressed: real-money/real-stock testing, and manual opening-stock data entry.

### 12.1 Honest read on the 28 June 2026 target
Today is 21 June 2026 → **7 calendar days (~5 working days)**. Even with two developers + Claude Code, building **all** of the BRD — inventory with batch/expiry, GST billing, purchase orders, customers/regulars, reports with Excel/PDF — and testing it enough to trust with real money in 5 working days is still too tight. The safe play is a **core pilot by 28 June**, run alongside the paper register, with the rest following over the next ~2 weeks.

### 12.2 What can realistically ship by 28 June (core pilot)
Single PC, local-only, single shared login:
- Medicine master + batch/expiry stock (real-time, fully offline)
- GST billing with print + PDF
- In-app low-stock / out-of-stock / near-expiry alerts
- Basic stock & sales reports with Excel/PDF export
- Customer + regular-customer basics

Treat this as a **pilot to test, not the final system** — keep the paper register running in parallel until it's proven.

### 12.3 Full v1 phased timeline (2 devs + Claude Code, local-only)

| Phase | Scope | Owner | Calendar |
|---|---|---|---|
| 0 | Django + DRF + React project setup, SQLite schema, local-server packaging (pywebview/auto-start) | Senior + Claude Code | Days 1–2 |
| 1 | Inventory: medicine master, batch/expiry, FEFO, reorder config | Senior | Days 1–4 |
| 2 | GST billing + invoice print/PDF | Senior | Days 3–7 → **core pilot ≈ 28 Jun** |
| 3 | Customers + regular customers + Rx capture | Junior | Days 4–7 |
| 4 | In-app notifications | Junior | Days 6–8 |
| 5 | Reports + Excel/PDF export | Junior | Days 7–10 |
| 6 | Purchase orders, goods receipt, supplier master | Senior | Days 8–12 |
| 7 | Opening-stock data entry, testing, deployment, training | Both | Days 11–15 → **full go-live ≈ wk 3** |
| — | Cloud sync + backup | **Deferred to later version** (client decision) | — |

> **Biggest schedule risk:** Phase 7 manual data entry. With no existing digital data, every medicine and its opening stock is keyed in by hand — the more SKUs, the longer, and it gates go-live regardless of build speed. Start it early; consider entering fast-movers first.

### 12.4 Notes on the team mix
- **Claude Code** is most valuable on scaffolding, repetitive CRUD screens, and report/export code — let it draft, senior reviews.
- **Stack note (Django + DRF + React):** versus an embedded-database desktop app, this adds a REST API tier (DRF serializers + viewsets per module) and the local-server packaging in Phase 0. The team's Python familiarity + Claude Code's strong Django/DRF support absorb most of it, but **local-server packaging and reliable auto-start are the new wildcard** for hitting the 28 June pilot — prove that on Day 1–2 before building features on top.
- **Split work to skill:** senior owns billing logic, GST correctness, and data integrity (where mistakes cost money); junior owns customer screens, notifications, and reports (lower-risk, good learning surface) with senior review.
- **Off-the-shelf check (worth 10 minutes):** ready-made Indian pharmacy software exists cheaply (see Section 13 / charging note). Confirm the client wants a tailored build before committing the two weeks — the case for custom here is the specific extras (regular-customer khata, full local control) and your own product ambitions, not cost.

---

## 13. Confirmed Decisions & Remaining Questions

**Confirmed by client**
- Login: **single shared login** (one system, one responsibility) — accepted.
- Security & compliance: **kept light** for this very small scale (see Sections 7–8).
- GST: **registered / in place**; GST-compliant invoices required.
- Existing data: **none digital** — currently a physical register; opening stock entered manually at setup.
- Added feature: **regular customers** (FR-22a/b/c).
- Target: **28 June 2026** — addressed in Section 12 (recommend a core pilot by that date, full system ~5–6 weeks).

**Still needed to finalise the build plan**
1. **Developer capacity:** one developer, two, or AI-assisted? (Directly sets the calendar in Section 12.)
2. **Number of SKUs** roughly stocked — drives the manual data-entry effort, the main go-live gate.
3. **Hardware:** receipt/thermal printer model, and will a barcode scanner be used?
4. **Cloud sync in v1 or later?** Dropping it (local-only + backup) is the single biggest way to hit the deadline (Section 12.4).
5. **Budget band** for build + (if kept) small recurring cloud cost.

---

## 14. Risks

| ID | Risk | Mitigation |
|---|---|---|
| R-1 | **Tight 28 June deadline** forces an untested system into real billing use | Ship a core pilot by 28 June, run alongside the paper register 1–2 weeks; full go-live ~wk 5–6 (Section 12) |
| R-2 | Manual opening-stock entry (no digital data) delays go-live | Start data entry early; size it against SKU count; consider phased entry (fast-movers first) |
| R-3 | Counter PC failure/theft loses all data | Automatic local backup + an off-machine copy (cloud or external drive), with tested restore (SEC-3) |
| R-4 | Sync complexity (if kept in v1) slows the build | Option to drop cloud sync from v1 and run local-only first (Section 12.4) |
| R-5 | Selling expired stock by mistake | Hard block on expired batches; FEFO; near-expiry alerts (FR-3/4/30) |
| R-6 | Scope creep into full accounting/e-commerce | Scope fixed in Section 3; extras deferred to later |

## 15. Software Bill of Materials (SBOM)

This is the indicative SBOM for the **local-only v1** (Django + DRF backend, React frontend, SQLite). Versions should be **pinned at build time** (`requirements.txt` / lockfile + `package-lock.json`); the authoritative, exact-version SBOM should be generated from those files (see 15.4). Anything online (e.g. future cloud sync) is an external service, listed separately.

### 15.1 Bundled components — Backend (Python)

| Component | Purpose | Typical licence |
|---|---|---|
| Python (runtime) | Language / interpreter | PSF (permissive) |
| Django | Web framework / ORM | BSD-3-Clause |
| Django REST Framework | REST API layer | BSD-3-Clause |
| Waitress (or Gunicorn / Uvicorn) | Local WSGI/ASGI server | ZPL-2.1 (Waitress) / MIT / BSD |
| SQLite (via Python `sqlite3` stdlib) | Local database engine | Public Domain |
| openpyxl | `.xlsx` report export | MIT |
| WeasyPrint *or* ReportLab | PDF / invoice generation | BSD-3-Clause |
| pywebview | Desktop window wrapper | BSD-3-Clause |
| PyInstaller *(optional, if bundling Python)* | Package app into an executable | **GPL-2.0 with bundling exception** — see 15.3 |

### 15.2 Bundled components — Frontend (JavaScript)

| Component | Purpose | Typical licence |
|---|---|---|
| React + React DOM | UI library | MIT |
| TypeScript | Typed language / compiler | Apache-2.0 |
| Vite | Build tool / bundler | MIT |
| Tailwind CSS | Styling | MIT |
| React Router | In-app navigation | MIT |
| TanStack Query (React Query) | Data fetching / live UI | MIT |
| lucide-react | Icons | ISC |
| day.js | Date handling | MIT |

### 15.3 External services (not bundled)

| Service | Purpose | Notes |
|---|---|---|
| PostgreSQL + driver (psycopg) | Cloud database | **Later version only.** psycopg is **LGPL-3.0** — see licence note below |

### 15.4 Licence summary
The **v1 stack is effectively all permissive** (BSD / MIT / Apache-2.0 / ISC / PSF / Public Domain / ZPL) — the product can be shipped **closed-source and sold commercially** with no source-disclosure obligation; you only retain the third-party licence notices (a bundled NOTICES file handles this). Two items to flag honestly rather than gloss over:
- **PyInstaller** (only if you bundle Python into an `.exe`) is GPL-2.0 **with an explicit exception** that permits packaging and distributing proprietary/closed-source applications — so it is fine commercially. (You can also avoid it entirely by installing Python on the counter PC and launching via a script.)
- **psycopg** (PostgreSQL driver, **cloud version only**) is **LGPL-3.0**. Used unmodified as a dependency, LGPL does not force you to open your own source, but it is not BSD/MIT — note it for the later cloud phase.

### 15.5 Keeping the SBOM real
There are now **two ecosystems**, so generate an SBOM for each (Claude Code can run these) and merge:

```
# Python backend
pip install cyclonedx-bom
cyclonedx-py requirements -o sbom-backend.json

# React frontend
npx @cyclonedx/cyclonedx-npm --output-file sbom-frontend.json
```

Regenerate on each release and scan for vulnerabilities (`pip-audit` for Python, `npm audit` / `osv-scanner` for JS). Keep the output with the build.

---

*End of BRD v0.5 — Draft for client review.*
