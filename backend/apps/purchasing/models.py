from django.db import models


class PaymentTerm(models.Model):
    """Payment-terms master (e.g. "30 days credit", "Cash on delivery").
    Referenced by suppliers so terms are picked from a list, not retyped.
    """

    name = models.CharField(max_length=80, unique=True)
    days = models.PositiveIntegerField(default=0, help_text='Credit period in days (0 = immediate).')
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class LeadTime(models.Model):
    """Lead-time master — standard supply lead times to choose from."""

    label = models.CharField(max_length=60, unique=True, help_text='e.g. "Next day", "2-3 days".')
    days = models.PositiveIntegerField(default=3)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['days']

    def __str__(self):
        return self.label


class Supplier(models.Model):
    """Distributor master (FR-9)."""

    code = models.CharField('Supplier code', max_length=20, blank=True, db_index=True)
    name = models.CharField(max_length=200, db_index=True)
    gstin = models.CharField('GSTIN', max_length=15, blank=True)
    contact_person = models.CharField(max_length=120, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)

    # Drug/medical supply licence (a distributor of scheduled drugs must hold one).
    has_drug_license = models.BooleanField('Has medical supply licence', default=False)
    drug_license_no = models.CharField('Drug licence no.', max_length=60, blank=True)

    # Master-driven terms (free-text fields kept for back-compat / display).
    payment_term = models.ForeignKey(
        PaymentTerm, null=True, blank=True, on_delete=models.SET_NULL, related_name='suppliers')
    lead_time = models.ForeignKey(
        LeadTime, null=True, blank=True, on_delete=models.SET_NULL, related_name='suppliers')
    payment_terms = models.CharField(max_length=120, blank=True)
    lead_time_days = models.PositiveIntegerField(default=3)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f'{self.code} · {self.name}' if self.code else self.name


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

    # Separate bill-to / ship-to so deliveries can differ from the billing party.
    bill_to = models.TextField(blank=True)
    ship_to = models.TextField(blank=True)

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
