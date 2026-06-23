"""Opening-stock import (BRD A5 / R-2 — the single biggest go-live gate).

Bulk-load the medicine master and opening batches from a CSV so the pharmacy
doesn't hand-key every SKU. Re-runnable: a medicine is matched by name, a
batch by (medicine, batch_number, expiry) — existing rows are updated, not
duplicated.

CSV columns (header row required; extras ignored):
    name, generic_name, manufacturer, hsn_code, gst_rate, schedule,
    pack_unit, rack_location, barcode, reorder_level, reorder_qty,
    batch_number, expiry_date, mfg_date, quantity, purchase_cost, mrp

- expiry_date / mfg_date: YYYY-MM-DD (or DD-MM-YYYY).
- A row with no batch_number just creates/updates the medicine master.

Usage:
    python manage.py import_stock opening_stock.csv
    python manage.py import_stock opening_stock.csv --dry-run
"""
import csv
from datetime import datetime
from decimal import Decimal, InvalidOperation

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.inventory.models import Batch, Medicine, StockMovement

SCHEDULES = {'OTC', 'H', 'H1', 'X'}


def _date(value):
    value = (value or '').strip()
    if not value:
        return None
    for fmt in ('%Y-%m-%d', '%d-%m-%Y', '%d/%m/%Y'):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    raise ValueError(f'Unrecognised date: "{value}"')


def _dec(value, default='0'):
    try:
        return Decimal(str(value).strip() or default)
    except (InvalidOperation, ValueError):
        return Decimal(default)


def _int(value, default=0):
    try:
        return int(float(str(value).strip()))
    except (ValueError, TypeError):
        return default


class Command(BaseCommand):
    help = 'Import the medicine master and opening stock from a CSV file.'

    def add_arguments(self, parser):
        parser.add_argument('csv_path')
        parser.add_argument('--dry-run', action='store_true',
                            help='Validate and report without writing.')

    def handle(self, *args, **options):
        path = options['csv_path']
        try:
            with open(path, newline='', encoding='utf-8-sig') as fh:
                rows = list(csv.DictReader(fh))
        except FileNotFoundError:
            raise CommandError(f'CSV not found: {path}')

        if not rows:
            raise CommandError('CSV has no data rows.')

        meds_seen, batches, errors = set(), 0, []

        try:
            with transaction.atomic():
                for i, row in enumerate(rows, start=2):  # row 1 is the header
                    name = (row.get('name') or '').strip()
                    if not name:
                        errors.append(f'Row {i}: missing name — skipped.')
                        continue

                    schedule = (row.get('schedule') or 'OTC').strip().upper() or 'OTC'
                    if schedule not in SCHEDULES:
                        schedule = 'OTC'

                    med, _ = Medicine.objects.update_or_create(
                        name=name,
                        defaults=dict(
                            generic_name=(row.get('generic_name') or '').strip(),
                            manufacturer=(row.get('manufacturer') or '').strip(),
                            hsn_code=(row.get('hsn_code') or '').strip(),
                            gst_rate=_dec(row.get('gst_rate'), '12'),
                            schedule=schedule,
                            pack_unit=(row.get('pack_unit') or '').strip(),
                            rack_location=(row.get('rack_location') or '').strip(),
                            barcode=(row.get('barcode') or '').strip(),
                            reorder_level=_int(row.get('reorder_level'), 10),
                            reorder_qty=_int(row.get('reorder_qty'), 50),
                        ),
                    )
                    meds_seen.add(med.id)

                    batch_no = (row.get('batch_number') or '').strip()
                    if not batch_no:
                        continue
                    try:
                        expiry = _date(row.get('expiry_date'))
                    except ValueError as exc:
                        errors.append(f'Row {i}: {exc} — batch skipped.')
                        continue
                    if not expiry:
                        errors.append(f'Row {i}: batch "{batch_no}" has no expiry — skipped.')
                        continue

                    qty = _int(row.get('quantity'), 0)
                    batch, created = Batch.objects.get_or_create(
                        medicine=med, batch_number=batch_no, expiry_date=expiry,
                        defaults=dict(
                            mfg_date=_date(row.get('mfg_date')),
                            purchase_cost=_dec(row.get('purchase_cost')),
                            mrp=_dec(row.get('mrp')),
                        ),
                    )
                    if created and qty:
                        StockMovement.objects.create(
                            batch=batch, reason=StockMovement.Reason.PURCHASE,
                            quantity=qty, note='Opening stock import',
                        )
                    batches += 1

                if options['dry_run']:
                    transaction.set_rollback(True)
        except Exception as exc:
            raise CommandError(f'Import failed, rolled back: {exc}')

        for err in errors:
            self.stdout.write(self.style.WARNING(err))
        verb = 'Would import' if options['dry_run'] else 'Imported'
        self.stdout.write(self.style.SUCCESS(
            f'{verb}: {len(meds_seen)} medicines, {batches} batches'
            + (f', {len(errors)} warning(s)' if errors else '') + '.'
        ))
