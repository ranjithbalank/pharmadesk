# PharmaDesk — Operating Manual

**For:** Counter staff and the pharmacy owner
**System:** PharmaDesk — Pharmacy Inventory, Billing & Supply-Chain Software
**Runs:** On your counter PC. No internet needed.

---

## Contents

1. [Getting started — opening the app & signing in](#1-getting-started)
2. [The screen layout](#2-the-screen-layout)
3. [Billing — making a sale](#3-billing--making-a-sale)
4. [Selling loose tablets](#4-selling-loose-tablets)
5. [Scheduled drugs & prescriptions](#5-scheduled-drugs--prescriptions)
6. [Customers](#6-customers)
7. [End of day — cash reconciliation](#7-end-of-day--cash-reconciliation)
8. [Inventory — medicines, batches & prices](#8-inventory)
9. [Stock adjustments](#9-stock-adjustments)
10. [Suppliers](#10-suppliers)
11. [Purchase orders & receiving stock](#11-purchase-orders--receiving-stock)
12. [Alerts & notifications](#12-alerts--notifications)
13. [Reports & downloads](#13-reports--downloads)
14. [Settings](#14-settings)
15. [Backups & safety](#15-backups--safety)
16. [Keyboard shortcuts](#16-keyboard-shortcuts)
17. [Common questions](#17-common-questions)

---

## 1. Getting started

1. **Switch on the counter PC.** PharmaDesk opens by itself (a desktop window). If it doesn't, double-click the **PharmaDesk** icon.
2. **Sign in.** Type the username and password and click **Sign in**.
   - First-time login: **Username** `admin`, **Password** `pharmadesk`.
   - **Change this password** after the first day (see [Settings](#14-settings)).
3. You'll land on the **Dashboard**.

> Everything runs on this one computer. You do **not** need internet to bill, look up stock, or print.

---

## 2. The screen layout

- **Left sidebar** — the main menu: Dashboard, Billing, Inventory, Purchase Orders, Suppliers, Customers, Reports, Settings.
- **Top bar** —
  - 🔔 **Bell** (right side): your alerts (low stock, near expiry). A red number means items need attention.
  - 👤 **Round icon** (far right): your shop details and the **Sign out** button.
- **Main area** — whatever screen you've opened.

---

## 3. Billing — making a sale

Open **Billing** (or press **F2** from anywhere).

1. **Find the medicine.** Click the search box (or press **F3**) and type the medicine name, composition, or scan the barcode.
2. **Add it.** Click the medicine in the list — it drops into the bill.
3. **Set the quantity** in the **Qty** box. Add more medicines the same way.
4. **(Optional) Discount.** Type a per-item discount in the **Disc** box, or a whole-bill discount on the right.
5. **(Optional) Choose the customer** — see [Customers](#6-customers).
6. **Pick payment mode** — Cash, UPI, Card, or Credit (khata).
7. Check the **Total** on the right, then click **Save & bill**.
8. On the confirmation screen, click **Print / PDF** to print the receipt.
9. Click **New bill** to start the next customer.

> Which batch is sold? The system **automatically picks the earliest-expiring batch** (so older stock goes out first). You don't choose batches manually.

---

## 4. Selling loose tablets

If a medicine is sold in strips (e.g. a strip of 10) and a customer wants just a
few tablets:

1. Add the medicine to the bill as usual.
2. Under the medicine name you'll see a small **Pack | Loose** switch — click **Loose**.
3. Now type the **number of tablets** in the Qty box (e.g. `3`).
4. The price changes to **per-tablet** automatically (strip price ÷ tablets per strip).

The system opens one strip, sells the loose tablets, and **keeps the rest of that
strip** in stock for the next customer.

> Loose selling only appears for items set up with "units per pack" greater than 1 (tablets/capsules). Syrups and bottles are always sold whole.

---

## 5. Scheduled drugs & prescriptions

When you add a **Schedule H, H1, or X** medicine to a bill, a yellow
**"Prescription required"** box appears. You must fill in:

- **Patient name**
- **Prescriber (doctor) name**
- **Registration no.** (optional)

The bill won't save until these are filled. This automatically builds your
**Schedule H1 register** (available under Reports), so you have the legal record.

---

## 6. Customers

You can bill a walk-in customer (the default) or link the sale to a saved customer.

**To attach a customer to a bill:**
- Pick them from the **Customer** dropdown, **or**
- Type their **phone number or customer ID** in the "Fetch by…" box and click **Fetch**.

**To add a new customer** — open **Customers → Add customer**:
- Name, Phone (numbers only).
- Tick **Regular customer** for repeat buyers.
- Tick **Allow credit / khata** to let them buy on credit; their outstanding
  balance then shows on the Customers list and on the Dashboard.
- Tick **Consent given** (for storing their details).
- Tick **Holds a medical supply licence** for clinics/institutions, and enter the licence number.

Credit (khata) sales: choose **Credit** as the payment mode at billing. Their
balance goes up. (Recording repayments is done by your owner/advisor's process.)

---

## 7. End of day — cash reconciliation

At closing time, open **Billing → "Day close · cash recon"**.

You'll see today's totals:
- Number of bills and gross sales.
- **Cash in drawer** — match this against the physical cash.
- Sales split by Cash / UPI / Card / Credit.
- GST collected, and any returned bills.

Use this to count and reconcile the cash drawer.

---

## 8. Inventory

Open **Inventory**. You'll see every medicine with its stock and status
(In stock / Low stock / Out of stock).

### Add a medicine
**Add medicine** → fill in:
- **Name**, generic/composition, manufacturer.
- **Type** (Tablet, Syrup, Injection, etc.).
- **GST rate** and **HSN code**.
- **Schedule** (OTC / H / H1 / X) — click **Schedule guide** if unsure what these mean.
- **Pack / unit** (e.g. "Strip of 10") and **Units per pack** (e.g. `10` to allow loose tablet sales; `1` for syrups).
- **Reorder level** and **reorder qty** (when stock drops to the reorder level you get a low-stock alert).
- **Rack location**, barcode, preferred supplier (optional).

### Edit a medicine
Click **Edit** on its row, change anything, **Save changes**.

### Add stock (batches) and set prices
Click **Batches** on a medicine:
- The list shows each batch with its **Cost** and **MRP/price** — edit these boxes and click the green ✓ to update a price.
- To add new stock use **Add / receive batch**: enter **Batch number, Expiry date, Mfg date, Quantity, Purchase cost, MRP**.
- You **cannot** add stock with an expiry date in the past — the system blocks it.

> **Where do prices come from?** Each batch carries its own **MRP** (because different lots can have different printed MRPs). Billing always uses the price of the batch being sold.

### Retiring a medicine
Open **Edit** → bottom section:
- **Discontinue** — hides the medicine from billing but keeps all its history. Use this for products you've stopped stocking. You can **Reactivate** later.
- **Delete permanently** — only works for an item that has **never** been sold/ordered (e.g. added by mistake). If it has history, the system stops you and asks you to discontinue instead.

---

## 9. Stock adjustments

To record damage, expiry write-off, or a stock count correction:

1. **Inventory → Batches** on the medicine → **Adjust stock** tab.
2. Pick the batch, choose a reason (Damage / Expiry / Count correction), enter the
   quantity (use a minus sign to reduce, e.g. `-5`), add a note, **Post**.
3. Recent adjustments are listed below with a **Reverse** button if you made a mistake.

---

## 10. Suppliers

Open **Suppliers → Add supplier** (or **Edit**):
- Supplier **code**, name, GSTIN, contact, phone, email, address.
- **Payment term** and **Lead time** — chosen from lists you manage in Settings.
- Tick **Holds a medical supply licence** and enter the licence number.

---

## 11. Purchase orders & receiving stock

Open **Purchase Orders**.

### Create an order
1. Click **Suggest reorder** — the system lists items at or below their reorder level, grouped by supplier.
2. **Adjust the strip/pack quantity and unit cost** for each item as needed.
3. Click **Create draft PO**.

### Send it to the agency
- Open the PO. You can still **edit quantities** while it's a draft.
- Click **PDF** to get a printable purchase order (with your logo, GST, and HSN) to send to the distributor.
- Click **Place order** to mark it as sent.

### Receive the goods
When stock arrives, open the PO → **Receive goods**, and for each item enter:
- **Batch no**, **Mfg date**, **Expiry date** (required), **Qty**, **Cost/unit**, **MRP**.
- Click **Confirm receipt** — stock is added automatically and the PO is marked received (or partially received).

---

## 12. Alerts & notifications

Click the 🔔 **bell** (top right) anytime. It refreshes by itself and shows:
- **Low stock** — at or below the reorder level.
- **Out of stock** — a normally-stocked item at zero.
- **Near expiry** — batches expiring within your warning window (default 90 days).

Click an alert to jump to Inventory, or **×** to dismiss it. The Dashboard shows
the same alerts in its "Alerts & reorder" panel.

---

## 13. Reports & downloads

Open **Reports**. Available reports:
- **Stock & Valuation** — what you hold and its value.
- **Low / Out-of-Stock**.
- **Near-Expiry**.
- **Sales** (by date range).
- **Bills (detailed)** — every bill with its items.
- **GST Summary** (by date range).
- **Schedule H1 Register** — the legal record of scheduled-drug sales.

Each report can be **exported to Excel or PDF** (buttons top-right). Reports with
dates have **From / To** pickers.

**Quick bills download:** on the **Billing** screen, click **Download bills** →
pick *Today* or *This month* → **Download Excel**. You get a two-sheet workbook:
a per-bill summary and the full line-item detail.

---

## 14. Settings

Open **Settings** (bottom of the sidebar). Owner tasks:

- **Shop & licence** — shop name, GSTIN, drug licence number, address, phone, and **logo** (shown on the purchase order). Tick whether the shop holds a drug licence.
- **Document numbering** — invoice prefix, PO prefix, and the next PO number.
- **Operational defaults** — near-expiry warning window (days), default reorder level/qty.
- **Masters** — manage the **Payment terms** and **Lead times** lists used for suppliers.
- **Login password** — change the sign-in password. **Do this after go-live.**

Click **Save settings** after editing the shop details.

---

## 15. Backups & safety

- The system makes a **backup of all your data every day** automatically, and one
  each time the app starts.
- Backups are kept on the PC, and (if set up) copied to an external drive or
  cloud folder for safety.
- **Don't switch off the PC at the wall during a sale.** Close the window normally.
- If anything ever goes wrong with the data, your installer can **restore** the
  most recent backup — at most one day's data is ever at risk.

> Ask your installer to confirm an **off-machine backup folder** is set, so a PC
> failure or theft can never lose your records.

---

## 16. Keyboard shortcuts

| Key | Does |
|-----|------|
| **F2** | Jump to **Billing** from anywhere |
| **F3** | Put the cursor in the **medicine search** box (on Billing) |
| **Enter** | (in the customer fetch box) look up the customer |

---

## 17. Common questions

**Do I need internet?**
No. Everything works offline on the counter PC.

**Which batch gets sold?**
Always the earliest-expiring one in stock (first-expiry-first-out). Automatic.

**A customer wants 3 tablets, not a full strip.**
Add the medicine, switch the line to **Loose**, type `3`. See [Section 4](#4-selling-loose-tablets).

**The system won't let me bill a medicine.**
Either it's out of (non-expired) stock, or it's a scheduled drug needing
prescription details. Read the message on screen.

**I can't delete a medicine.**
If it has sales/order history, the law needs those records kept — **Discontinue**
it instead (it disappears from billing but the history stays).

**I entered a wrong stock adjustment.**
Inventory → Batches → Adjust stock tab → **Reverse** the entry.

**How do I see today's sales?**
Dashboard ("Today's sales" card) or Billing → **Day close**.

**How do I give the accountant the bills?**
Billing → **Download bills** → This month → **Download Excel**. Or Reports →
**Bills (detailed)** / **GST Summary**.

---

*PharmaDesk — built for fast, reliable counter work. Keep this manual at the counter.*
