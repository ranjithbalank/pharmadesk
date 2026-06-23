"""Tests for billing — the place where mistakes cost money (BRD §12.4).

Covers GST correctness, scheduled-drug Rx enforcement, sales returns and
credit handling.
"""
from decimal import Decimal

from django.test import TestCase
from rest_framework.exceptions import ValidationError

from apps.billing.models import Invoice
from apps.billing.services import create_invoice
from apps.customers.models import Customer, Prescription
from apps.inventory.models import Batch
from apps.inventory.tests import make_batch, make_medicine


class InvoiceMathTests(TestCase):
    def test_gst_split_is_correct(self):
        # MRP 112 at 12% GST → taxable 100, CGST 6, SGST 6, total 112.
        med = make_medicine(gst_rate=12)
        make_batch(med, 10, mrp=112)
        inv = create_invoice(customer=None, payment_mode='cash',
                             bill_discount=0, items=[{'medicine': med, 'quantity': 1}])
        self.assertEqual(inv.subtotal, Decimal('100.00'))
        self.assertEqual(inv.cgst, Decimal('6.00'))
        self.assertEqual(inv.sgst, Decimal('6.00'))
        self.assertEqual(inv.total, Decimal('112.00'))

    def test_gst_components_sum_to_total_on_odd_paise(self):
        # MRP 12 at 12% gives a non-clean split; the parts must still reconcile.
        med = make_medicine(gst_rate=12)
        make_batch(med, 10, mrp=12)
        inv = create_invoice(customer=None, payment_mode='cash',
                             bill_discount=0, items=[{'medicine': med, 'quantity': 2}])
        # Stored to 2 dp and internally consistent.
        self.assertEqual(inv.total, Decimal('24.00'))
        self.assertEqual(inv.subtotal + inv.cgst + inv.sgst - inv.discount, inv.total)
        line = inv.lines.first()
        self.assertEqual(line.taxable_value + line.cgst_amount + line.sgst_amount,
                         line.line_total)
        # No runaway precision — every money field is 2 dp.
        for val in (inv.subtotal, inv.cgst, inv.sgst, inv.total):
            self.assertLessEqual(abs(val.as_tuple().exponent), 2)

    def test_quantity_and_bill_discount(self):
        med = make_medicine(gst_rate=12)
        make_batch(med, 10, mrp=112)
        inv = create_invoice(customer=None, payment_mode='cash',
                             bill_discount=Decimal('12'),
                             items=[{'medicine': med, 'quantity': 2}])
        # gross 224, less 12 bill discount = 212
        self.assertEqual(inv.total, Decimal('212.00'))

    def test_sale_decrements_stock_via_fefo(self):
        med = make_medicine()
        b1 = make_batch(med, 4, days_to_expiry=30, batch_number='A', mrp=100)
        b2 = make_batch(med, 10, days_to_expiry=90, batch_number='B', mrp=100)
        create_invoice(customer=None, payment_mode='cash', bill_discount=0,
                       items=[{'medicine': med, 'quantity': 7}])
        b1.refresh_from_db(); b2.refresh_from_db()
        self.assertEqual(b1.quantity, 0)   # earliest fully consumed
        self.assertEqual(b2.quantity, 7)   # remainder from next batch


class ScheduledDrugTests(TestCase):
    def test_scheduled_drug_requires_prescription(self):
        med = make_medicine(name='Azithromycin', schedule='H1')
        make_batch(med, 10, mrp=100)
        with self.assertRaises(ValidationError):
            create_invoice(customer=None, payment_mode='cash', bill_discount=0,
                           items=[{'medicine': med, 'quantity': 1}])

    def test_scheduled_drug_with_rx_creates_register_entry(self):
        med = make_medicine(name='Azithromycin', schedule='H1')
        make_batch(med, 10, mrp=100)
        inv = create_invoice(
            customer=None, payment_mode='cash', bill_discount=0,
            items=[{'medicine': med, 'quantity': 1}],
            prescriptions=[{'medicine': med, 'patient_name': 'A', 'prescriber_name': 'Dr B'}],
        )
        self.assertEqual(Prescription.objects.filter(invoice=inv).count(), 1)

    def test_otc_drug_needs_no_prescription(self):
        med = make_medicine(schedule='OTC')
        make_batch(med, 10, mrp=100)
        inv = create_invoice(customer=None, payment_mode='cash', bill_discount=0,
                             items=[{'medicine': med, 'quantity': 1}])
        self.assertEqual(inv.lines.count(), 1)


class ReturnAndCreditTests(TestCase):
    def test_credit_sale_increases_balance(self):
        cust = Customer.objects.create(name='Murugan', allow_credit=True)
        med = make_medicine(gst_rate=12)
        make_batch(med, 10, mrp=112)
        inv = create_invoice(customer=cust, payment_mode='credit', bill_discount=0,
                             items=[{'medicine': med, 'quantity': 1}])
        cust.refresh_from_db()
        self.assertEqual(cust.credit_balance, inv.total)
        self.assertEqual(inv.status, Invoice.Status.CREDIT)

    def test_refund_restores_stock(self):
        med = make_medicine()
        batch = make_batch(med, 10, mrp=100)
        inv = create_invoice(customer=None, payment_mode='cash', bill_discount=0,
                             items=[{'medicine': med, 'quantity': 3}])
        batch.refresh_from_db()
        self.assertEqual(batch.quantity, 7)
        # Simulate the refund action's stock restore.
        from apps.inventory.models import StockMovement
        for line in inv.lines.all():
            StockMovement.objects.create(batch=line.batch,
                                         reason=StockMovement.Reason.SALE_RETURN,
                                         quantity=line.quantity)
        batch.refresh_from_db()
        self.assertEqual(batch.quantity, 10)
