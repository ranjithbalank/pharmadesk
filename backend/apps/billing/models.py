from decimal import Decimal

from django.db import models


class Invoice(models.Model):
    """GST-compliant tax invoice (FR-16). Header carries seller/customer and
    rolled-up totals; per-line tax detail lives on InvoiceLine.
    """

    class PaymentMode(models.TextChoices):
        CASH = 'cash', 'Cash'
        CARD = 'card', 'Card'
        UPI = 'upi', 'UPI'
        CREDIT = 'credit', 'Credit / khata'

    class Status(models.TextChoices):
        PAID = 'paid', 'Paid'
        CREDIT = 'credit', 'On credit'
        RETURNED = 'returned', 'Returned'

    number = models.CharField(max_length=30, unique=True)
    customer = models.ForeignKey(
        'customers.Customer', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='invoices',
    )
    payment_mode = models.CharField(
        max_length=10, choices=PaymentMode.choices, default=PaymentMode.CASH
    )
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PAID)

    # Money rolled up from lines at save time so reports stay fast.
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    cgst = models.DecimalField('CGST', max_digits=12, decimal_places=2, default=0)
    sgst = models.DecimalField('SGST', max_digits=12, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # FR-21: room for e-invoice (IRN/QR) later without rework.
    irn = models.CharField('IRN', max_length=64, blank=True)

    note = models.CharField(max_length=200, blank=True)
    actor = models.CharField(max_length=80, default='counter')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.number

    def recalculate(self):
        """Roll line totals up to the header. Call after lines change."""
        lines = self.lines.all()
        self.subtotal = sum((l.taxable_value for l in lines), Decimal('0'))
        self.cgst = sum((l.cgst_amount for l in lines), Decimal('0'))
        self.sgst = sum((l.sgst_amount for l in lines), Decimal('0'))
        self.total = self.subtotal + self.cgst + self.sgst - self.discount


class InvoiceLine(models.Model):
    """One medicine/batch line on an invoice. Records the batch issued (FEFO)
    and HSN/expiry so the printed invoice is statutorily complete.
    """

    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='lines')
    batch = models.ForeignKey('inventory.Batch', on_delete=models.PROTECT)

    # Snapshot fields — keep the invoice readable even if the master changes.
    medicine_name = models.CharField(max_length=200)
    hsn_code = models.CharField('HSN', max_length=10, blank=True)
    batch_number = models.CharField(max_length=60, blank=True)
    expiry_date = models.DateField(null=True, blank=True)

    quantity = models.PositiveIntegerField(default=1)
    mrp = models.DecimalField('MRP', max_digits=10, decimal_places=2, default=0)
    rate = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    gst_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    def __str__(self):
        return f'{self.medicine_name} x{self.quantity}'

    @property
    def gross(self):
        return self.rate * self.quantity

    @property
    def taxable_value(self):
        """Net of line discount, GST extracted as exclusive of this value."""
        net = self.gross - self.discount
        divisor = Decimal('1') + (self.gst_rate / Decimal('100'))
        return (net / divisor) if divisor else net

    @property
    def gst_amount(self):
        return (self.gross - self.discount) - self.taxable_value

    @property
    def cgst_amount(self):
        return self.gst_amount / Decimal('2')

    @property
    def sgst_amount(self):
        return self.gst_amount / Decimal('2')

    @property
    def line_total(self):
        return self.gross - self.discount
