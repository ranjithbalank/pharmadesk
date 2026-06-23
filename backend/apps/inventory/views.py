from datetime import timedelta

from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Batch, Medicine, StockMovement
from .serializers import (
    BatchSerializer,
    MedicineListSerializer,
    MedicineSerializer,
    StockMovementSerializer,
)


class MedicineViewSet(viewsets.ModelViewSet):
    queryset = Medicine.objects.all()
    filterset_fields = ['schedule', 'is_active', 'preferred_supplier']
    search_fields = ['name', 'generic_name', 'manufacturer', 'barcode', 'hsn_code']
    ordering_fields = ['name', 'created_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return MedicineListSerializer
        return MedicineSerializer

    @action(detail=False)
    def low_stock(self, request):
        """Items at or below reorder level (FR-27), for the reorder screen."""
        meds = [m for m in self.get_queryset().filter(is_active=True)
                if m.stock_status in ('low_stock', 'out_of_stock')]
        return Response(MedicineListSerializer(meds, many=True).data)

    @action(detail=True, methods=['post'])
    def adjust(self, request, pk=None):
        """Stock adjustment against a batch (FR-6): damage, expiry, count."""
        medicine = self.get_object()
        batch_id = request.data.get('batch')
        qty = int(request.data.get('quantity', 0))
        reason = request.data.get('reason', StockMovement.Reason.COUNT)
        note = request.data.get('note', '')
        try:
            batch = medicine.batches.get(pk=batch_id)
        except Batch.DoesNotExist:
            return Response({'detail': 'Batch not found for this medicine.'},
                            status=status.HTTP_400_BAD_REQUEST)
        StockMovement.objects.create(batch=batch, reason=reason, quantity=qty, note=note)
        return Response(MedicineSerializer(medicine).data)


class BatchViewSet(viewsets.ModelViewSet):
    queryset = Batch.objects.select_related('medicine').all()
    serializer_class = BatchSerializer
    filterset_fields = ['medicine']
    ordering_fields = ['expiry_date', 'received_at']

    def perform_create(self, serializer):
        """A new batch books its opening quantity through the ledger so the
        running total and movement history stay consistent.
        """
        opening = int(self.request.data.get('quantity', 0) or 0)
        batch = serializer.save()
        if opening:
            StockMovement.objects.create(
                batch=batch, reason=StockMovement.Reason.PURCHASE,
                quantity=opening, note='Opening / manual batch entry',
            )

    @action(detail=False)
    def near_expiry(self, request):
        days = int(request.query_params.get('days', 90))
        cutoff = timezone.localdate() + timedelta(days=days)
        qs = self.get_queryset().filter(
            quantity__gt=0, expiry_date__gte=timezone.localdate(), expiry_date__lte=cutoff,
        )
        return Response(self.get_serializer(qs, many=True).data)


class StockMovementViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = StockMovement.objects.select_related('batch', 'batch__medicine').all()
    serializer_class = StockMovementSerializer
    filterset_fields = ['reason', 'batch']
