from decimal import Decimal

from django.db import models, transaction
from django.http import HttpResponse
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.inventory.models import StockMovement

from .models import Invoice, InvoiceLine
from .pdf import invoice_pdf
from .serializers import InvoiceCreateSerializer, InvoiceSerializer


class InvoiceViewSet(viewsets.ModelViewSet):
    queryset = Invoice.objects.prefetch_related('lines').select_related('customer').all()
    filterset_fields = ['payment_mode', 'status', 'customer']
    search_fields = ['number', 'customer__name', 'customer__phone']
    ordering_fields = ['created_at', 'total']
    http_method_names = ['get', 'post', 'head', 'options']  # invoices are immutable

    def get_serializer_class(self):
        if self.action == 'create':
            return InvoiceCreateSerializer
        return InvoiceSerializer

    @action(detail=True, methods=['get'])
    def pdf(self, request, pk=None):
        """FR-17: render the tax invoice as a PDF for print/share."""
        invoice = self.get_object()
        pdf_bytes = invoice_pdf(invoice)
        resp = HttpResponse(pdf_bytes, content_type='application/pdf')
        resp['Content-Disposition'] = f'inline; filename="{invoice.number}.pdf"'
        return resp

    @action(detail=True, methods=['post'])
    def refund(self, request, pk=None):
        """FR-18: sales return — restore stock to the original batches."""
        invoice = self.get_object()
        if invoice.status == Invoice.Status.RETURNED:
            return Response({'detail': 'Invoice already returned.'},
                            status=status.HTTP_400_BAD_REQUEST)
        with transaction.atomic():
            for line in invoice.lines.all():
                if line.unit_mode == 'loose':
                    # Restore loose units to the batch (no whole packs to add back).
                    from apps.inventory.models import Batch
                    Batch.objects.filter(pk=line.batch_id).update(
                        loose_units=models.F('loose_units') + line.quantity)
                else:
                    StockMovement.objects.create(
                        batch=line.batch, reason=StockMovement.Reason.SALE_RETURN,
                        quantity=line.quantity, note=f'Return {invoice.number} line {line.id}',
                    )
            invoice.status = Invoice.Status.RETURNED
            invoice.save(update_fields=['status'])
            if invoice.customer and invoice.payment_mode == Invoice.PaymentMode.CREDIT:
                invoice.customer.credit_balance -= invoice.total
                invoice.customer.save(update_fields=['credit_balance'])
        return Response(InvoiceSerializer(invoice).data)
