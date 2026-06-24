"""Tests for alerts (FR-27..30) and the day-close summary (FR-20)."""
from django.test import TestCase

from apps.billing.services import create_invoice
from apps.core.models import Notification
from apps.core.services import recompute_notifications
from apps.core.testbase import AuthedAPITestCase
from apps.inventory.tests import make_batch, make_medicine


class NotificationTests(TestCase):
    def test_low_stock_alert_raised(self):
        med = make_medicine(reorder_level=10)
        make_batch(med, 5)
        recompute_notifications()
        self.assertTrue(
            Notification.objects.filter(kind='low_stock', medicine=med).exists()
        )

    def test_out_of_stock_alert_raised(self):
        med = make_medicine()  # no batches -> zero stock
        recompute_notifications()
        self.assertTrue(Notification.objects.filter(kind='out_of_stock', medicine=med).exists())

    def test_near_expiry_alert_raised(self):
        med = make_medicine()
        make_batch(med, 20, days_to_expiry=30)  # inside default 90-day window
        recompute_notifications()
        self.assertTrue(Notification.objects.filter(kind='near_expiry', medicine=med).exists())

    def test_resolved_condition_clears_alert(self):
        med = make_medicine(reorder_level=10)
        make_batch(med, 5, batch_number='LOW')
        recompute_notifications()
        self.assertTrue(Notification.objects.filter(kind='low_stock').exists())
        # Top up stock above reorder level, recompute → alert gone.
        make_batch(med, 50, batch_number='TOPUP')
        recompute_notifications()
        self.assertFalse(Notification.objects.filter(kind='low_stock', medicine=med).exists())

    def test_recompute_is_idempotent(self):
        med = make_medicine(reorder_level=10)
        make_batch(med, 5)
        recompute_notifications()
        recompute_notifications()
        self.assertEqual(Notification.objects.filter(kind='low_stock', medicine=med).count(), 1)


class DayCloseApiTests(AuthedAPITestCase):
    def test_day_close_totals_by_mode(self):
        med = make_medicine(gst_rate=12)
        make_batch(med, 100, mrp=112)
        create_invoice(customer=None, payment_mode='cash', bill_discount=0,
                       items=[{'medicine': med, 'quantity': 1}])
        create_invoice(customer=None, payment_mode='upi', bill_discount=0,
                       items=[{'medicine': med, 'quantity': 1}])
        resp = self.client.get('/api/day-close/')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data['invoice_count'], 2)
        self.assertEqual(float(data['cash_total']), 112.0)
        self.assertEqual(data['by_mode']['upi']['count'], 1)
