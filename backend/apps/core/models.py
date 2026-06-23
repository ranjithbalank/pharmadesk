from django.db import models


class ShopSetting(models.Model):
    """Single-row table holding the pharmacy's identity and configurable
    defaults (FR-40). Loaded everywhere GST/licence details are printed.
    """

    shop_name = models.CharField(max_length=200, default='Sri Sakthi Medicals')
    gstin = models.CharField('GSTIN', max_length=15, blank=True)
    drug_licence_no = models.CharField('Drug licence no.', max_length=60, blank=True)
    address = models.TextField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)

    # Operational defaults
    near_expiry_days = models.PositiveIntegerField(
        default=90, help_text='Warn when a batch expires within this many days.'
    )
    default_reorder_level = models.PositiveIntegerField(default=10)
    default_reorder_qty = models.PositiveIntegerField(default=50)
    default_gst_rate = models.DecimalField(max_digits=5, decimal_places=2, default=12)

    # SEC-2: a simple admin password protects sensitive settings.
    admin_password = models.CharField(max_length=128, blank=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Shop setting'
        verbose_name_plural = 'Shop settings'

    def __str__(self):
        return self.shop_name

    @classmethod
    def load(cls):
        """Return the singleton settings row, creating it on first access."""
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)


class Notification(models.Model):
    """In-app alert (FR-27..32). Computed from stock thresholds and expiry;
    persisted so it survives until actioned or dismissed. Fully offline.
    """

    class Kind(models.TextChoices):
        LOW_STOCK = 'low_stock', 'Low stock'
        OUT_OF_STOCK = 'out_of_stock', 'Out of stock'
        NEAR_EXPIRY = 'near_expiry', 'Near expiry'
        REORDER = 'reorder', 'Reorder'

    class Severity(models.TextChoices):
        INFO = 'info', 'Info'
        WARNING = 'warning', 'Warning'
        CRITICAL = 'critical', 'Critical'

    kind = models.CharField(max_length=20, choices=Kind.choices)
    severity = models.CharField(
        max_length=10, choices=Severity.choices, default=Severity.WARNING
    )
    title = models.CharField(max_length=200)
    message = models.TextField(blank=True)

    # Loose link to the subject (e.g. a medicine or batch) for navigation.
    medicine = models.ForeignKey(
        'inventory.Medicine', null=True, blank=True,
        on_delete=models.CASCADE, related_name='notifications',
    )
    batch = models.ForeignKey(
        'inventory.Batch', null=True, blank=True,
        on_delete=models.CASCADE, related_name='notifications',
    )

    # Stable key so we don't create duplicate alerts for the same condition.
    dedupe_key = models.CharField(max_length=120, unique=True)

    is_read = models.BooleanField(default=False)
    is_dismissed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'[{self.get_kind_display()}] {self.title}'


class AuditLog(models.Model):
    """Audit trail of sensitive actions (FR-39). Lightweight for v1 — single
    shared login — but attributable where a user is known.
    """

    action = models.CharField(max_length=80)
    detail = models.TextField(blank=True)
    actor = models.CharField(max_length=80, default='counter')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.created_at:%Y-%m-%d %H:%M} {self.action}'
