"""Seed realistic demo data so the pilot can be demonstrated without the
full opening-stock entry. Idempotent-ish: clears domain tables first.
"""
import random
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.billing.models import Invoice
from apps.billing.services import create_invoice
from apps.core.models import ShopSetting
from apps.core.services import recompute_notifications
from apps.customers.models import Customer
from apps.inventory.models import Batch, Medicine, StockMovement
from apps.purchasing.models import Supplier

MEDICINES = [
    # name, generic, manufacturer, hsn, gst, schedule, pack
    ('Paracetamol 500mg', 'Paracetamol', 'Cipla', '3004', 12, 'OTC', 'Strip of 10'),
    ('Amoxicillin 250mg', 'Amoxicillin', 'Sun Pharma', '3004', 12, 'H', 'Strip of 10'),
    ('Azithromycin 500mg', 'Azithromycin', 'Alkem', '3004', 12, 'H1', 'Strip of 5'),
    ('Cetirizine 10mg', 'Cetirizine', 'Dr Reddy', '3004', 12, 'OTC', 'Strip of 10'),
    ('Pantoprazole 40mg', 'Pantoprazole', 'Intas', '3004', 12, 'H', 'Strip of 15'),
    ('Metformin 500mg', 'Metformin', 'USV', '3004', 12, 'H', 'Strip of 15'),
    ('Amlodipine 5mg', 'Amlodipine', 'Cipla', '3004', 12, 'H', 'Strip of 10'),
    ('Cough Syrup 100ml', 'Dextromethorphan', 'Mankind', '3004', 12, 'OTC', 'Bottle 100ml'),
    ('ORS Sachet', 'Oral rehydration salts', 'FDC', '3004', 5, 'OTC', 'Sachet'),
    ('Vitamin C 500mg', 'Ascorbic acid', 'HealthVit', '2106', 18, 'OTC', 'Bottle 60'),
    ('Insulin Glargine', 'Insulin glargine', 'Sanofi', '3004', 5, 'H1', 'Vial 10ml'),
    ('Diclofenac Gel 30g', 'Diclofenac', 'Voveran', '3004', 12, 'OTC', 'Tube 30g'),
]

SUPPLIERS = [
    ('MediSupply Distributors', '33ABCDE1234F1Z5', 'Ravi Kumar', '9876543210', 2),
    ('Erode Pharma Agencies', '33XYZAB6789K1Z2', 'Suresh M', '9123456780', 3),
    ('Kongu Medical Wholesale', '33PQRST4567L1Z8', 'Lakshmi N', '9988776655', 4),
]


class Command(BaseCommand):
    help = 'Seed demo data for the PharmaDesk pilot.'

    def handle(self, *args, **options):
        from apps.customers.models import Prescription
        from apps.purchasing.models import (
            LeadTime, PaymentTerm, PurchaseOrder, PurchaseOrderLine,
        )
        self.stdout.write('Clearing existing demo data...')
        for model in (Prescription, Invoice, StockMovement, PurchaseOrderLine,
                      PurchaseOrder, Batch, Medicine, Supplier, Customer,
                      PaymentTerm, LeadTime):
            model.objects.all().delete()

        shop = ShopSetting.load()
        shop.shop_name = 'Sri Sakthi Medicals'
        shop.gstin = '33ABCFS1234K1Z9'
        shop.drug_licence_no = 'TN/ERD/20B/2021/0456'
        shop.address = 'Perundurai, Erode District, Tamil Nadu'
        shop.phone = '04294 222333'
        shop.has_drug_license = True
        shop.save()

        # Masters: payment terms & lead times.
        terms = [PaymentTerm.objects.create(name=n, days=d) for n, d in
                 [('Cash on delivery', 0), ('15 days credit', 15), ('30 days credit', 30)]]
        leads = [LeadTime.objects.create(label=l, days=d) for l, d in
                 [('Next day', 1), ('2-3 days', 3), ('Weekly', 7)]]

        suppliers = []
        for i, (n, g, c, p, lt) in enumerate(SUPPLIERS):
            suppliers.append(Supplier.objects.create(
                code=f'SUP{i + 1:03d}', name=n, gstin=g, contact_person=c, phone=p,
                lead_time_days=lt, payment_terms='30 days credit',
                payment_term=terms[2], lead_time=leads[min(i, 2)],
                has_drug_license=True, drug_license_no=f'TN/ERD/21B/{1000 + i}',
            ))

        today = timezone.localdate()
        meds = []
        for name, generic, mfr, hsn, gst, sch, pack in MEDICINES:
            # Strip/tablet packs sell loose (10 per strip); bottles/sachets whole.
            if 'Strip' in pack:
                med_type, upp = 'tablet', int(pack.split('of')[-1].strip() or 10)
            elif 'Bottle' in pack or 'Syrup' in name:
                med_type, upp = 'syrup', 1
            elif 'Vial' in pack:
                med_type, upp = 'injection', 1
            elif 'Tube' in pack:
                med_type, upp = 'ointment', 1
            elif 'Sachet' in pack:
                med_type, upp = 'commercial', 1
            else:
                med_type, upp = 'other', 1
            med = Medicine.objects.create(
                name=name, generic_name=generic, manufacturer=mfr, hsn_code=hsn,
                gst_rate=gst, schedule=sch, pack_unit=pack,
                med_type=med_type, units_per_pack=upp,
                rack_location=f'R{random.randint(1, 8)}-{random.randint(1, 6)}',
                reorder_level=random.choice([10, 15, 20]),
                reorder_qty=random.choice([50, 100]),
                preferred_supplier=random.choice(suppliers),
            )
            meds.append(med)

            # 1-2 batches each, a mix of healthy / near-expiry / low stock.
            for b in range(random.randint(1, 2)):
                exp_days = random.choice([20, 45, 80, 200, 400, 600])
                qty = random.choice([5, 8, 40, 80, 150])
                mrp = round(random.uniform(15, 350), 2)
                batch = Batch.objects.create(
                    medicine=med,
                    batch_number=f'B{random.randint(1000, 9999)}',
                    mfg_date=today - timedelta(days=365),
                    expiry_date=today + timedelta(days=exp_days),
                    purchase_cost=round(mrp * 0.7, 2),
                    mrp=mrp,
                )
                StockMovement.objects.create(
                    batch=batch, reason=StockMovement.Reason.PURCHASE,
                    quantity=qty, note='Opening stock (demo)',
                )

        customers = [
            Customer.objects.create(name=n, phone=p, is_regular=r, consent_given=True,
                                    allow_credit=r)
            for n, p, r in [
                ('Murugan S', '9445566778', True),
                ('Priya R', '9332211445', True),
                ('Anand Kumar', '9776655443', False),
                ('Fathima B', '9001122334', True),
            ]
        ]

        # A few sales across the last week to populate reports. Use OTC items
        # only so the demo doesn't trip the scheduled-drug prescription guard.
        sellable = [m for m in meds if m.total_stock > 5 and m.schedule == 'OTC']
        for d in range(7):
            for _ in range(random.randint(1, 4)):
                picks = random.sample(sellable, k=min(len(sellable), random.randint(1, 3)))
                items = [{'medicine': m, 'quantity': random.randint(1, 3), 'discount': 0}
                         for m in picks if m.total_stock > 3]
                if not items:
                    continue
                try:
                    inv = create_invoice(
                        customer=random.choice(customers + [None]),
                        payment_mode=random.choice(['cash', 'upi', 'card']),
                        bill_discount=0, items=items,
                    )
                    # Backdate for a realistic spread.
                    Invoice.objects.filter(pk=inv.pk).update(
                        created_at=timezone.now() - timedelta(days=d)
                    )
                except Exception:
                    pass

        count = recompute_notifications()
        self.stdout.write(self.style.SUCCESS(
            f'Seeded {Medicine.objects.count()} medicines, '
            f'{Supplier.objects.count()} suppliers, '
            f'{Customer.objects.count()} customers, '
            f'{Invoice.objects.count()} invoices, {count} active alerts.'
        ))
