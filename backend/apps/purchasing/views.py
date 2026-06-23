from django.db import transaction
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.inventory.models import Batch, Medicine, StockMovement

from .models import PurchaseOrder, PurchaseOrderLine, Supplier
from .serializers import PurchaseOrderSerializer, SupplierSerializer


class SupplierViewSet(viewsets.ModelViewSet):
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    filterset_fields = ['is_active']
    search_fields = ['name', 'gstin', 'contact_person', 'phone']
    ordering_fields = ['name', 'created_at']


def _next_po_number():
    today = timezone.localdate()
    prefix = f'PO-{today:%Y%m%d}-'
    last = (
        PurchaseOrder.objects.filter(number__startswith=prefix)
        .order_by('-number').values_list('number', flat=True).first()
    )
    seq = int(last.split('-')[-1]) + 1 if last else 1
    return f'{prefix}{seq:04d}'


class PurchaseOrderViewSet(viewsets.ModelViewSet):
    queryset = PurchaseOrder.objects.prefetch_related('lines__medicine').all()
    serializer_class = PurchaseOrderSerializer
    filterset_fields = ['status', 'supplier']
    ordering_fields = ['created_at']

    def perform_create(self, serializer):
        serializer.save(number=_next_po_number())

    @action(detail=False, methods=['post'])
    def suggest(self, request):
        """FR-10: auto-build draft POs from items at/below reorder level,
        grouped by preferred supplier. Returns drafts without saving.
        """
        by_supplier = {}
        for med in Medicine.objects.filter(is_active=True):
            if med.stock_status not in ('low_stock', 'out_of_stock'):
                continue
            sup_id = med.preferred_supplier_id
            by_supplier.setdefault(sup_id, []).append({
                'medicine': med.id,
                'medicine_name': med.name,
                'quantity': med.reorder_qty,
                'unit_cost': 0,
            })
        suggestions = [
            {'supplier': sup_id, 'lines': lines}
            for sup_id, lines in by_supplier.items()
        ]
        return Response(suggestions)

    @action(detail=True, methods=['post'])
    def place(self, request, pk=None):
        po = self.get_object()
        po.status = PurchaseOrder.Status.PLACED
        po.placed_at = timezone.now()
        po.save(update_fields=['status', 'placed_at'])
        return Response(self.get_serializer(po).data)

    @action(detail=True, methods=['post'])
    def receive(self, request, pk=None):
        """FR-12: goods receipt against a PO. Body: list of received lines with
        batch number, expiry, cost, qty — each creates a Batch + stock-in.
        """
        po = self.get_object()
        received = request.data.get('lines', [])
        with transaction.atomic():
            for r in received:
                line = po.lines.get(pk=r['line'])
                qty = int(r['quantity'])
                batch, _ = Batch.objects.get_or_create(
                    medicine=line.medicine,
                    batch_number=r['batch_number'],
                    expiry_date=r['expiry_date'],
                    defaults={
                        'mfg_date': r.get('mfg_date'),
                        'purchase_cost': r.get('purchase_cost', line.unit_cost),
                        'mrp': r.get('mrp', 0),
                    },
                )
                StockMovement.objects.create(
                    batch=batch, reason=StockMovement.Reason.PURCHASE,
                    quantity=qty, note=f'GRN {po.number} line {line.id}',
                )
                line.received_qty += qty
                line.save(update_fields=['received_qty'])

            # Re-read lines from the DB — the viewset prefetches `lines`, so
            # po.lines.all() would otherwise serve a stale (pre-receipt) cache.
            fresh_lines = PurchaseOrderLine.objects.filter(order=po)
            fully = all(l.outstanding_qty == 0 for l in fresh_lines)
            po.status = PurchaseOrder.Status.RECEIVED if fully else PurchaseOrder.Status.PARTIAL
            po.save(update_fields=['status'])

        # Return a fresh instance so received quantities reflect the receipt.
        po = self.get_queryset().get(pk=po.pk)
        return Response(self.get_serializer(po).data)
