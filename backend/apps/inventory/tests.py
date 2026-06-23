"""Tests for the inventory core: stock totals, expiry handling and FEFO.

These cover the rules where a mistake costs money or breaks the law
(selling expired stock, wrong batch issued), per BRD R-5.
"""
from datetime import timedelta

from django.test import TestCase
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.billing.services import allocate_fefo
from apps.inventory.models import Batch, Medicine, StockMovement


def make_medicine(**kwargs):
    defaults = dict(name='Paracetamol 500mg', gst_rate=12, schedule='OTC',
                    reorder_level=10, reorder_qty=50)
    defaults.update(kwargs)
    return Medicine.objects.create(**defaults)


def make_batch(med, qty, days_to_expiry=200, batch_number='B1', mrp=100):
    """Create a batch and book its opening stock through the ledger."""
    batch = Batch.objects.create(
        medicine=med, batch_number=batch_number,
        expiry_date=timezone.localdate() + timedelta(days=days_to_expiry), mrp=mrp,
    )
    StockMovement.objects.create(batch=batch, reason=StockMovement.Reason.PURCHASE, quantity=qty)
    batch.refresh_from_db()
    return batch


class StockTotalsTests(TestCase):
    def test_stock_movement_updates_batch_quantity(self):
        med = make_medicine()
        batch = make_batch(med, 40)
        self.assertEqual(batch.quantity, 40)
        StockMovement.objects.create(batch=batch, reason=StockMovement.Reason.SALE, quantity=-15)
        batch.refresh_from_db()
        self.assertEqual(batch.quantity, 25)

    def test_total_stock_excludes_expired(self):
        med = make_medicine()
        make_batch(med, 30, days_to_expiry=100, batch_number='GOOD')
        make_batch(med, 50, days_to_expiry=-5, batch_number='EXPIRED')
        self.assertEqual(med.total_stock, 30)

    def test_stock_status_thresholds(self):
        med = make_medicine(reorder_level=10)
        self.assertEqual(med.stock_status, 'out_of_stock')
        make_batch(med, 8)
        self.assertEqual(med.stock_status, 'low_stock')
        make_batch(med, 20, batch_number='B2')
        self.assertEqual(med.stock_status, 'in_stock')

    def test_sell_mrp_uses_fefo_batch(self):
        med = make_medicine()
        make_batch(med, 10, days_to_expiry=300, batch_number='LATER', mrp=120)
        make_batch(med, 10, days_to_expiry=30, batch_number='SOONER', mrp=90)
        self.assertEqual(med.sell_mrp, 90)  # earliest-expiring batch's MRP


class FefoTests(TestCase):
    def test_fefo_issues_earliest_expiry_first(self):
        med = make_medicine()
        make_batch(med, 10, days_to_expiry=300, batch_number='LATER')
        sooner = make_batch(med, 10, days_to_expiry=30, batch_number='SOONER')
        allocations = allocate_fefo(med, 5)
        self.assertEqual(allocations[0][0].id, sooner.id)
        self.assertEqual(allocations[0][1], 5)

    def test_fefo_splits_across_batches(self):
        med = make_medicine()
        make_batch(med, 4, days_to_expiry=30, batch_number='A')
        make_batch(med, 10, days_to_expiry=60, batch_number='B')
        allocations = allocate_fefo(med, 7)
        self.assertEqual([(a[0].batch_number, a[1]) for a in allocations], [('A', 4), ('B', 3)])

    def test_fefo_skips_expired_batches(self):
        med = make_medicine()
        make_batch(med, 100, days_to_expiry=-1, batch_number='EXPIRED')
        make_batch(med, 5, days_to_expiry=30, batch_number='GOOD')
        allocations = allocate_fefo(med, 5)
        self.assertEqual(len(allocations), 1)
        self.assertEqual(allocations[0][0].batch_number, 'GOOD')

    def test_fefo_raises_on_insufficient_stock(self):
        med = make_medicine()
        make_batch(med, 3, batch_number='ONLY')
        with self.assertRaises(ValidationError):
            allocate_fefo(med, 10)
