"""Notification engine (FR-27..32).

Alerts are *computed* from current stock and expiry, then reconciled into the
Notification table. Re-running is idempotent thanks to ``dedupe_key``: an
active condition keeps its row, a resolved one is cleared. Runs fully offline.
"""
from django.utils import timezone

from apps.inventory.models import Batch, Medicine

from .models import Notification, ShopSetting


def recompute_notifications():
    """Rebuild the active alert set. Returns the count of live notifications."""
    settings = ShopSetting.load()
    window = settings.near_expiry_days
    today = timezone.localdate()
    active_keys = set()

    # --- Stock-level alerts (low / out-of-stock / reorder) -------------------
    for med in Medicine.objects.filter(is_active=True):
        qty = med.total_stock
        if qty <= 0:
            key = f'oos:{med.id}'
            _upsert(
                key, Notification.Kind.OUT_OF_STOCK, Notification.Severity.CRITICAL,
                f'Out of stock: {med.name}',
                'Normally stocked item is at zero quantity.', med,
            )
            active_keys.add(key)
        elif qty <= med.reorder_level:
            key = f'low:{med.id}'
            _upsert(
                key, Notification.Kind.LOW_STOCK, Notification.Severity.WARNING,
                f'Low stock: {med.name}',
                f'{qty} left — at or below reorder level ({med.reorder_level}). '
                f'Suggested reorder: {med.reorder_qty}.', med,
            )
            active_keys.add(key)

    # --- Near-expiry alerts --------------------------------------------------
    near_batches = Batch.objects.filter(
        quantity__gt=0, expiry_date__gte=today,
    ).select_related('medicine')
    for batch in near_batches:
        if batch.days_to_expiry <= window:
            key = f'exp:{batch.id}'
            _upsert(
                key, Notification.Kind.NEAR_EXPIRY, Notification.Severity.WARNING,
                f'Near expiry: {batch.medicine.name}',
                f'Batch {batch.batch_number} ({batch.quantity} units) expires '
                f'{batch.expiry_date} — in {batch.days_to_expiry} days.',
                batch.medicine, batch,
            )
            active_keys.add(key)

    # Clear notifications whose condition no longer holds.
    Notification.objects.exclude(dedupe_key__in=active_keys).delete()
    return Notification.objects.filter(is_dismissed=False).count()


def _upsert(key, kind, severity, title, message, medicine=None, batch=None):
    Notification.objects.update_or_create(
        dedupe_key=key,
        defaults={
            'kind': kind, 'severity': severity, 'title': title,
            'message': message, 'medicine': medicine, 'batch': batch,
        },
    )
