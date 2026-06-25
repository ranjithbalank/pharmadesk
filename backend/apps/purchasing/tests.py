"""Tests for purchasing: goods receipt updates stock and PO status (FR-12).

Locks in the fix where a full receipt was wrongly left as 'partial' due to a
stale prefetch cache.
"""
from apps.core.testbase import AuthedAPITestCase
from apps.inventory.tests import make_medicine
from apps.purchasing.models import PurchaseOrder, PurchaseOrderLine, Supplier


class GoodsReceiptTests(AuthedAPITestCase):
    def setUp(self):
        super().setUp()
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
            format='json',
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
        resp = self.client.post('/api/purchase-orders/suggest/', format='json')
        self.assertEqual(resp.status_code, 200)
        suggestions = resp.json()
        self.assertTrue(any(low.id in [ln['medicine'] for ln in s['lines']] for s in suggestions))


class PoNumberingTests(AuthedAPITestCase):
    def test_po_uses_configurable_prefix_and_increments(self):
        from apps.core.models import ShopSetting
        s = ShopSetting.load()
        s.po_prefix = 'PURORD'
        s.po_next_number = 7
        s.save()
        sup = Supplier.objects.create(name='X')
        med = make_medicine()
        payload = {'supplier': sup.id, 'lines': [{'medicine': med.id, 'quantity': 1, 'unit_cost': 1}]}
        r1 = self.client.post('/api/purchase-orders/', data=payload, format='json')
        r2 = self.client.post('/api/purchase-orders/', data=payload, format='json')
        self.assertEqual(r1.json()['number'], 'PURORD-00007')
        self.assertEqual(r2.json()['number'], 'PURORD-00008')


class SupplierLicenceTests(AuthedAPITestCase):
    def test_licence_number_required_when_flagged(self):
        resp = self.client.post('/api/suppliers/', data={
            'name': 'PharmaDist', 'has_drug_license': True, 'drug_license_no': '',
        }, format='json')
        self.assertEqual(resp.status_code, 400)
        self.assertIn('drug_license_no', resp.json())

    def test_supplier_code_saved(self):
        resp = self.client.post('/api/suppliers/', data={
            'name': 'PharmaDist', 'code': 'SUP001',
        }, format='json')
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.json()['code'], 'SUP001')
