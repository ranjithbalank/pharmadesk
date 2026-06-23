"""Tests for purchasing: goods receipt updates stock and PO status (FR-12).

Locks in the fix where a full receipt was wrongly left as 'partial' due to a
stale prefetch cache.
"""
from django.test import TestCase

from apps.inventory.tests import make_medicine
from apps.purchasing.models import PurchaseOrder, PurchaseOrderLine, Supplier


class GoodsReceiptTests(TestCase):
    def setUp(self):
        self.supplier = Supplier.objects.create(name='MediSupply')
        self.med = make_medicine()
        self.po = PurchaseOrder.objects.create(number='PO-TEST-1', supplier=self.supplier)
        self.line = PurchaseOrderLine.objects.create(
            order=self.po, medicine=self.med, quantity=20, unit_cost=8,
        )

    def _receive(self, qty, batch='GRN-1'):
        return self.client.post(
            f'/api/purchase-orders/{self.po.id}/receive/',
            data={'lines': [{
                'line': self.line.id, 'quantity': qty,
                'batch_number': batch, 'expiry_date': '2027-12-31', 'mrp': 18,
            }]},
            content_type='application/json',
        )

    def test_full_receipt_marks_received_and_adds_stock(self):
        resp = self._receive(20)
        self.assertEqual(resp.status_code, 200)
        self.po.refresh_from_db()
        self.med.refresh_from_db()
        self.assertEqual(self.po.status, PurchaseOrder.Status.RECEIVED)
        self.assertEqual(self.med.total_stock, 20)

    def test_partial_receipt_marks_partial(self):
        resp = self._receive(12)
        self.assertEqual(resp.status_code, 200)
        self.po.refresh_from_db()
        self.line.refresh_from_db()
        self.assertEqual(self.po.status, PurchaseOrder.Status.PARTIAL)
        self.assertEqual(self.line.outstanding_qty, 8)

    def test_suggest_reorder_groups_low_items(self):
        low = make_medicine(name='LowItem', reorder_level=10, reorder_qty=40)
        low.preferred_supplier = self.supplier
        low.save()
        resp = self.client.post('/api/purchase-orders/suggest/', content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        suggestions = resp.json()
        self.assertTrue(any(low.id in [ln['medicine'] for ln in s['lines']] for s in suggestions))
