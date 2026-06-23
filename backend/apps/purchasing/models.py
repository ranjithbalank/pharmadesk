from django.db import models


class Supplier(models.Model):
    """Distributor master (FR-9)."""

    name = models.CharField(max_length=200, db_index=True)
    gstin = models.CharField('GSTIN', max_length=15, blank=True)
    contact_person = models.CharField(max_length=120, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    payment_terms = models.CharField(max_length=120, blank=True)
    lead_time_days = models.PositiveIntegerField(default=3)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class PurchaseOrder(models.Model):
    """A purchase order / indent to a supplier (FR-10..14)."""

    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        PLACED = 'placed', 'Placed'
        PARTIAL = 'partial', 'Partially received'
        RECEIVED = 'received', 'Received'
        CANCELLED = 'cancelled', 'Cancelled'

    number = models.CharField(max_length=30, unique=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, related_name='orders')
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.DRAFT)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    placed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.number

    @property
    def total_value(self):
        return sum((line.quantity * line.unit_cost for line in self.lines.all()), 0)


class PurchaseOrderLine(models.Model):
    order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='lines')
    medicine = models.ForeignKey('inventory.Medicine', on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    received_qty = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f'{self.medicine.name} x{self.quantity}'

    @property
    def outstanding_qty(self):
        return max(self.quantity - self.received_qty, 0)
