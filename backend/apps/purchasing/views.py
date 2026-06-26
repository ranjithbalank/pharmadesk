from django.db import transaction
from django.http import HttpResponse
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.core.models import ShopSetting
from apps.inventory.models import Batch, Medicine, StockMovement

from .models import LeadTime, PaymentTerm, PurchaseOrder, PurchaseOrderLine, Supplier
from .pdf import purchase_order_pdf
from .serializers import (
    LeadTimeSerializer,
    PaymentTermSerializer,
    PurchaseOrderSerializer,
    SupplierSerializer,
)


class PaymentTermViewSet(viewsets.ModelViewSet):
    queryset = PaymentTerm.objects.all()
    serializer_class = PaymentTermSerializer
    filterset_fields = ['is_active']


class LeadTimeViewSet(viewsets.ModelViewSet):
    queryset = LeadTime.objects.all()
    serializer_class = LeadTimeSerializer
    filterset_fields = ['is_active']


class SupplierViewSet(viewsets.ModelViewSet):
    queryset = Supplier.objects.select_related('payment_term', 'lead_time').all()
    serializer_class = SupplierSerializer
    filterset_fields = ['is_active']
    search_fields = ['code', 'name', 'gstin', 'contact_person', 'phone']
    ordering_fields = ['name', 'code', 'created_at']


class PurchaseOrderViewSet(viewsets.ModelViewSet):
    queryset = PurchaseOrder.objects.prefetch_related('lines__medicine').select_related('supplier').all()
    serializer_class = PurchaseOrderSerializer
    filterset_fields = ['status', 'supplier']
    ordering_fields = ['created_at']

    def perform_create(self, serializer):
        # Document number from the configurable prefix + running counter.
        serializer.save(number=ShopSetting.load().next_po_number())

    @action(detail=True, methods=['get'])
    def pdf(self, request, pk=None):
        """PO document PDF with shop logo, address, GST and per-line HSN."""
        po = self.get_object()
        resp = HttpResponse(purchase_order_pdf(po), content_type='application/pdf')
        resp['Content-Disposition'] = f'inline; filename="{po.number}.pdf"'
        return resp

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
    def close(self, request, pk=None):
        """FR-13: close a partially-received PO when the rest won't be supplied
        (short supply). Finalises the order; whatever was received stays in
        stock and the unfulfilled quantity is simply not delivered.
        """
        po = self.get_object()
        if po.status not in (PurchaseOrder.Status.PLACED, PurchaseOrder.Status.PARTIAL):
            return Response({'detail': 'Only a placed or partially-received order can be closed.'},
                            status=status.HTTP_400_BAD_REQUEST)
        short = sum(line.outstanding_qty for line in po.lines.all())
        note = (request.data.get('note') or '').strip() or f'Closed — short supply ({short} units undelivered)'
        po.notes = (po.notes + '\n' if po.notes else '') + note
        po.status = PurchaseOrder.Status.RECEIVED
        po.save(update_fields=['notes', 'status'])
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
