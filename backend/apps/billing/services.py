"""Billing domain logic: FEFO batch allocation, stock posting, numbering.

Kept out of the serializer so the same rules can be reused by reports,
returns, and any future cloud sync without dragging in DRF.
"""
from decimal import Decimal

from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from apps.inventory.models import Batch, StockMovement

from .models import Invoice, InvoiceLine


def next_invoice_number():
    """Sequential, human-readable invoice number: <PREFIX>-YYYYMMDD-NNNN.
    The prefix is configurable in Shop settings (default 'INV')."""
    from apps.core.models import ShopSetting
    today = timezone.localdate()
    prefix = f'{ShopSetting.load().invoice_prefix}-{today:%Y%m%d}-'
    last = (
        Invoice.objects.filter(number__startswith=prefix)
        .order_by('-number')
        .values_list('number', flat=True)
        .first()
    )
    seq = int(last.split('-')[-1]) + 1 if last else 1
    return f'{prefix}{seq:04d}'


def allocate_fefo(medicine, quantity):
    """Return a list of (batch, qty) issuing earliest-expiring stock first
    (FR-3). Skips expired batches entirely (FR-4). Raises if short.
    """
    remaining = quantity
    allocations = []
    batches = (
        Batch.objects.filter(
            medicine=medicine,
            quantity__gt=0,
            expiry_date__gte=timezone.localdate(),
        )
        .order_by('expiry_date', 'received_at')
    )
    for batch in batches:
        if remaining <= 0:
            break
        take = min(batch.quantity, remaining)
        allocations.append((batch, take))
        remaining -= take

    if remaining > 0:
        available = quantity - remaining
        raise serializers.ValidationError(
            f'Insufficient non-expired stock for "{medicine.name}": '
            f'requested {quantity}, available {available}.'
        )
    return allocations


def allocate_fefo_units(medicine, units):
    """FEFO allocation for loose-unit sales (e.g. 3 tablets). Returns a list of
    (batch, units) using each batch's loose-equivalent availability."""
    remaining = units
    allocations = []
    batches = (
        Batch.objects.filter(medicine=medicine, expiry_date__gte=timezone.localdate())
        .order_by('expiry_date', 'received_at')
    )
    for batch in batches:
        if remaining <= 0:
            break
        avail = batch.available_units
        if avail <= 0:
            continue
        take = min(avail, remaining)
        allocations.append((batch, take))
        remaining -= take

    if remaining > 0:
        raise serializers.ValidationError(
            f'Insufficient stock for "{medicine.name}": requested {units} unit(s), '
            f'available {units - remaining}.'
        )
    return allocations


def _dispense_loose(batch, units):
    """Remove `units` loose units from a batch, opening whole packs as needed.
    Packs opened are posted to the ledger; the opened-pack remainder is tracked
    in batch.loose_units (a counter, not a ledger quantity)."""
    import math
    upp = batch.medicine.units_per_pack or 1
    from_loose = min(batch.loose_units, units)
    new_loose = batch.loose_units - from_loose
    remaining = units - from_loose
    packs_to_open = math.ceil(remaining / upp) if remaining > 0 else 0
    new_loose += packs_to_open * upp - remaining
    if packs_to_open:
        StockMovement.objects.create(
            batch=batch, reason=StockMovement.Reason.SALE, quantity=-packs_to_open,
            note=f'opened {packs_to_open} pack(s) for {units} loose unit(s)',
        )
    Batch.objects.filter(pk=batch.pk).update(loose_units=new_loose)


@transaction.atomic
def create_invoice(*, customer, payment_mode, bill_discount, items, note='',
                   actor='counter', prescriptions=None):
    """Create an invoice from a list of {medicine, quantity, discount} items.

    Each item is split across batches via FEFO; one InvoiceLine per batch.
    Stock is decremented through StockMovement so the ledger stays correct.

    ``prescriptions`` is an optional list of Rx dicts (FR-23). Any scheduled
    drug (H/H1/X) in the cart must be covered by one, so the Schedule H1
    register (FR-24) has a record for every scheduled-drug sale.
    """
    prescriptions = prescriptions or []
    _require_prescriptions(items, prescriptions)
    invoice = Invoice.objects.create(
        number=next_invoice_number(),
        customer=customer,
        payment_mode=payment_mode,
        discount=bill_discount or Decimal('0'),
        status=Invoice.Status.CREDIT if payment_mode == Invoice.PaymentMode.CREDIT
        else Invoice.Status.PAID,
        note=note,
        actor=actor,
    )

    for item in items:
        medicine = item['medicine']
        qty = item['quantity']
        line_discount = item.get('discount') or Decimal('0')
        loose = item.get('unit_mode') == 'loose' and medicine.units_per_pack > 1
        upp = medicine.units_per_pack or 1

        allocations = (allocate_fefo_units(medicine, qty) if loose
                       else allocate_fefo(medicine, qty))

        for batch, take in allocations:
            # Spread the line discount proportionally across split batches.
            share = (Decimal(take) / Decimal(qty)) * line_discount
            # Loose lines price per unit (pack MRP / units per pack); pack lines
            # price per pack at MRP.
            rate = (batch.mrp / upp) if loose else batch.mrp
            line = InvoiceLine.objects.create(
                invoice=invoice,
                batch=batch,
                medicine_name=medicine.name,
                hsn_code=medicine.hsn_code,
                batch_number=batch.batch_number,
                expiry_date=batch.expiry_date,
                unit_mode='loose' if loose else 'pack',
                quantity=take,
                mrp=batch.mrp,
                rate=rate,
                discount=share,
                gst_rate=medicine.gst_rate,
            )
            if loose:
                _dispense_loose(batch, take)
            else:
                StockMovement.objects.create(
                    batch=batch,
                    reason=StockMovement.Reason.SALE,
                    quantity=-take,
                    note=f'{invoice.number} line {line.id}',
                    actor=actor,
                )

    invoice.recalculate()
    invoice.save()

    # FR-23/24: persist captured prescriptions against this invoice.
    from apps.customers.models import Prescription
    for rx in prescriptions:
        Prescription.objects.create(
            customer=customer,
            invoice=invoice,
            patient_name=rx.get('patient_name', ''),
            prescriber_name=rx.get('prescriber_name', ''),
            prescriber_reg_no=rx.get('prescriber_reg_no', ''),
            medicine=rx['medicine'],
            quantity=rx.get('quantity', 1),
            rx_date=rx.get('rx_date') or timezone.localdate(),
        )

    # FR-22c: a credit sale increases the customer's outstanding balance.
    if customer and payment_mode == Invoice.PaymentMode.CREDIT:
        customer.credit_balance = (customer.credit_balance or Decimal('0')) + invoice.total
        customer.save(update_fields=['credit_balance'])

    return invoice


def _require_prescriptions(items, prescriptions):
    """Block billing a scheduled drug unless an Rx for it is supplied."""
    covered = {rx['medicine'].id for rx in prescriptions if rx.get('medicine')}
    missing = [
        item['medicine'].name
        for item in items
        if item['medicine'].is_scheduled and item['medicine'].id not in covered
    ]
    if missing:
        raise serializers.ValidationError(
            'Prescription details are required for scheduled drug(s): '
            + ', '.join(missing) + '.'
        )
