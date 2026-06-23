"""Prepare a clean database for handover to the pharmacy (go-live).

Wipes all demo/transactional data so the counter starts from zero, while
keeping (or setting) the shop's identity. Run this once before the pharmacy
begins real billing — after this, import the real opening stock with
`import_stock`.

Usage:
    python manage.py prepare_golive --shop "Sri Sakthi Medicals" \
        --gstin 33ABCFS1234K1Z9 --licence TN/ERD/20B/2021/0456
    python manage.py prepare_golive --yes        # wipe, keep existing settings
"""
from django.core.management.base import BaseCommand

from apps.billing.models import Invoice, InvoiceLine
from apps.core.models import AuditLog, Notification, ShopSetting
from apps.customers.models import Customer, Prescription
from apps.inventory.models import Batch, Medicine, StockMovement
from apps.purchasing.models import PurchaseOrder, PurchaseOrderLine, Supplier


class Command(BaseCommand):
    help = 'Wipe demo/transactional data for go-live; optionally set shop details.'

    def add_arguments(self, parser):
        parser.add_argument('--yes', action='store_true', help='Skip confirmation.')
        parser.add_argument('--keep-masters', action='store_true',
                            help='Keep medicines, suppliers and customers; clear only transactions.')
        parser.add_argument('--shop')
        parser.add_argument('--gstin')
        parser.add_argument('--licence')
        parser.add_argument('--address')
        parser.add_argument('--phone')

    def handle(self, *args, **options):
        if not options['yes']:
            self.stdout.write(self.style.WARNING(
                'This permanently deletes demo/transactional data. '
                'Re-run with --yes to proceed.'
            ))
            return

        # Always clear transactions and computed alerts.
        for model in (Prescription, InvoiceLine, Invoice, StockMovement,
                      PurchaseOrderLine, PurchaseOrder, Notification, AuditLog):
            model.objects.all().delete()

        if not options['keep_masters']:
            for model in (Batch, Medicine, Supplier, Customer):
                model.objects.all().delete()
        else:
            # Keep masters but zero out credit balances carried by demo data.
            Customer.objects.update(credit_balance=0)

        shop = ShopSetting.load()
        for field, key in (('shop_name', 'shop'), ('gstin', 'gstin'),
                           ('drug_licence_no', 'licence'), ('address', 'address'),
                           ('phone', 'phone')):
            if options.get(key):
                setattr(shop, field, options[key])
        shop.save()

        self.stdout.write(self.style.SUCCESS(
            'Go-live prep complete. Database cleaned'
            + (' (masters kept).' if options['keep_masters'] else '.')
            + f' Shop: {shop.shop_name}, GSTIN {shop.gstin or "—"}.'
        ))
        self.stdout.write('Next: python manage.py import_stock <opening_stock.csv>')
