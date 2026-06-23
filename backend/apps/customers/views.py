from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.billing.models import InvoiceLine

from .models import Customer, Prescription
from .serializers import CustomerSerializer, PrescriptionSerializer


class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    filterset_fields = ['is_regular', 'allow_credit']
    search_fields = ['name', 'phone', 'id']
    ordering_fields = ['name', 'created_at']

    @action(detail=False)
    def lookup(self, request):
        """Fetch a customer at the billing counter by exact customer ID or
        phone number (item 3). e.g. /customers/lookup/?q=9445566778
        """
        q = (request.query_params.get('q') or '').strip()
        if not q:
            return Response({'detail': 'Provide ?q=<customer id or phone>.'}, status=400)
        customer = Customer.objects.filter(phone=q).first()
        if not customer and q.isdigit():
            customer = Customer.objects.filter(pk=int(q)).first()
        if not customer:
            return Response({'detail': f'No customer found for "{q}".'}, status=404)
        return Response(CustomerSerializer(customer).data)

    @action(detail=True)
    def usual_items(self, request, pk=None):
        """FR-22b quick re-bill: the medicines this regular buys most often,
        ready to drop into a new bill.
        """
        customer = self.get_object()
        lines = (
            InvoiceLine.objects.filter(invoice__customer=customer)
            .values('batch__medicine', 'medicine_name')
            .distinct()[:50]
        )
        items = [
            {'medicine': l['batch__medicine'], 'name': l['medicine_name']}
            for l in lines if l['batch__medicine']
        ]
        return Response(items)

    @action(detail=True)
    def history(self, request, pk=None):
        """FR-22a one-tap purchase history for a regular customer."""
        from apps.billing.serializers import InvoiceSerializer
        customer = self.get_object()
        invoices = customer.invoices.all()[:100]
        return Response(InvoiceSerializer(invoices, many=True).data)


class PrescriptionViewSet(viewsets.ModelViewSet):
    queryset = Prescription.objects.select_related('medicine', 'customer').all()
    serializer_class = PrescriptionSerializer
    filterset_fields = ['customer', 'medicine']
    search_fields = ['patient_name', 'prescriber_name']
    ordering_fields = ['rx_date', 'created_at']
