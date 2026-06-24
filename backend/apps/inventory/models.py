from decimal import Decimal

from django.db import models
from django.db.models import Sum
from django.utils import timezone


class Medicine(models.Model):
    """Medicine master (FR-1). One row per product the pharmacy stocks;
    physical stock is tracked per-batch via the related Batch rows.
    """

    class Schedule(models.TextChoices):
        OTC = 'OTC', 'OTC (over the counter)'
        H = 'H', 'Schedule H'
        H1 = 'H1', 'Schedule H1'
        X = 'X', 'Schedule X'

    class MedType(models.TextChoices):
        TABLET = 'tablet', 'Tablet / capsule'
        SYRUP = 'syrup', 'Syrup / liquid'
        INJECTION = 'injection', 'Injection'
        DROPS = 'drops', 'Drops'
        OINTMENT = 'ointment', 'Ointment / cream'
        COMMERCIAL = 'commercial', 'Commercial product'
        OTHER = 'other', 'Other'

    name = models.CharField(max_length=200, db_index=True)
    generic_name = models.CharField('Generic / composition', max_length=300, blank=True)
    manufacturer = models.CharField(max_length=200, blank=True)
    med_type = models.CharField('Type', max_length=12, choices=MedType.choices, default=MedType.TABLET)
    hsn_code = models.CharField('HSN code', max_length=10, blank=True)
    gst_rate = models.DecimalField(max_digits=5, decimal_places=2, default=12)
    schedule = models.CharField(max_length=3, choices=Schedule.choices, default=Schedule.OTC)

    pack_unit = models.CharField(
        max_length=40, blank=True, help_text='e.g. "Strip of 10", "Bottle 100ml"'
    )
    # How many sellable units are in one pack (e.g. 10 tablets per strip). 1 for
    # items sold whole (syrups, commercial). Enables loose-unit sales at billing.
    units_per_pack = models.PositiveIntegerField(default=1)
    rack_location = models.CharField(max_length=40, blank=True)
    barcode = models.CharField(max_length=64, blank=True, db_index=True)

    # Reorder configuration (FR-5)
    reorder_level = models.PositiveIntegerField(default=10)
    reorder_qty = models.PositiveIntegerField(default=50)
    min_stock = models.PositiveIntegerField(null=True, blank=True)
    max_stock = models.PositiveIntegerField(null=True, blank=True)

    preferred_supplier = models.ForeignKey(
        'purchasing.Supplier', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='preferred_medicines',
    )

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    @property
    def total_stock(self):
        """Sellable quantity = sum of all non-expired batch quantities."""
        agg = self.batches.filter(expiry_date__gte=timezone.localdate()).aggregate(
            q=Sum('quantity')
        )
        return agg['q'] or 0

    @property
    def stock_status(self):
        qty = self.total_stock
        if qty <= 0:
            return 'out_of_stock'
        if qty <= self.reorder_level:
            return 'low_stock'
        return 'in_stock'

    @property
    def is_scheduled(self):
        """Scheduled drug requiring prescription capture (H/H1/X)."""
        return self.schedule in {self.Schedule.H, self.Schedule.H1, self.Schedule.X}

    @property
    def fefo_batch(self):
        """The batch that billing will issue next: earliest-expiring stock."""
        return (
            self.batches.filter(quantity__gt=0, expiry_date__gte=timezone.localdate())
            .order_by('expiry_date', 'received_at')
            .first()
        )

    @property
    def sell_mrp(self):
        """MRP of the next batch to be issued — the price shown at billing."""
        batch = self.fefo_batch
        return batch.mrp if batch else 0

    @property
    def sells_loose(self):
        """True when this item can be sold in loose units (e.g. 2 tablets)."""
        return self.units_per_pack > 1

    @property
    def unit_price(self):
        """Per-unit (e.g. per-tablet) price = pack MRP / units per pack."""
        upp = self.units_per_pack or 1
        return (self.sell_mrp / upp) if upp else self.sell_mrp

    @property
    def total_units(self):
        """Total loose-equivalent units in stock = packs*upp + opened remainders."""
        upp = self.units_per_pack or 1
        agg = self.batches.filter(expiry_date__gte=timezone.localdate()).aggregate(
            packs=Sum('quantity'), loose=Sum('loose_units'))
        return (agg['packs'] or 0) * upp + (agg['loose'] or 0)


class Batch(models.Model):
    """A received lot of a medicine (FR-2). Stock lives here so expiry and
    cost can be tracked per lot; FEFO issues the earliest expiry first.
    """

    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE, related_name='batches')
    batch_number = models.CharField(max_length=60)
    mfg_date = models.DateField('Manufacturing date', null=True, blank=True)
    expiry_date = models.DateField(db_index=True)

    quantity = models.IntegerField(default=0)
    # Loose units left from an opened pack (0 .. units_per_pack-1). Lets the
    # counter dispense a few tablets from a strip without losing the rest.
    loose_units = models.PositiveIntegerField(default=0)
    purchase_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    mrp = models.DecimalField('MRP', max_digits=10, decimal_places=2, default=0)

    received_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['expiry_date']  # FEFO default ordering
        constraints = [
            models.UniqueConstraint(
                fields=['medicine', 'batch_number', 'expiry_date'],
                name='unique_batch_per_medicine',
            )
        ]

    def __str__(self):
        return f'{self.medicine.name} · {self.batch_number} · exp {self.expiry_date}'

    def clean(self):
        """Validate expiry on stock addition (item 12): a batch must not be
        already expired, and expiry must come after the manufacturing date.
        """
        from django.core.exceptions import ValidationError
        errors = {}
        if self.expiry_date and self.expiry_date < timezone.localdate():
            errors['expiry_date'] = 'Expiry date is in the past — cannot add expired stock.'
        if self.mfg_date and self.expiry_date and self.expiry_date <= self.mfg_date:
            errors['expiry_date'] = 'Expiry date must be after the manufacturing date.'
        if errors:
            raise ValidationError(errors)

    @property
    def is_expired(self):
        return self.expiry_date < timezone.localdate()

    @property
    def days_to_expiry(self):
        return (self.expiry_date - timezone.localdate()).days

    @property
    def available_units(self):
        """Loose-equivalent units available in this batch (packs*upp + loose)."""
        upp = self.medicine.units_per_pack or 1
        return self.quantity * upp + self.loose_units


class StockMovement(models.Model):
    """Append-only ledger of every stock change (FR-6). Sales, purchases,
    returns and adjustments all post here so movement is fully traceable.
    """

    class Reason(models.TextChoices):
        PURCHASE = 'purchase', 'Goods receipt'
        SALE = 'sale', 'Sale'
        SALE_RETURN = 'sale_return', 'Sales return'
        PURCHASE_RETURN = 'purchase_return', 'Purchase return'
        DAMAGE = 'damage', 'Damage'
        EXPIRY = 'expiry', 'Expiry write-off'
        COUNT = 'count', 'Count correction'

    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name='movements')
    reason = models.CharField(max_length=20, choices=Reason.choices)
    # Positive = stock in, negative = stock out.
    quantity = models.IntegerField()
    note = models.CharField(max_length=200, blank=True)
    actor = models.CharField(max_length=80, default='counter')
    # Set when an adjustment has been reversed, so it can't be reversed twice.
    reversed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.get_reason_display()} {self.quantity:+d} · {self.batch}'

    def save(self, *args, **kwargs):
        """Apply the movement to the batch's running quantity on creation."""
        is_new = self._state.adding
        super().save(*args, **kwargs)
        if is_new:
            Batch.objects.filter(pk=self.batch_id).update(
                quantity=models.F('quantity') + self.quantity
            )
