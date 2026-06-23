from rest_framework import serializers

from .models import Batch, Medicine, StockMovement


class BatchSerializer(serializers.ModelSerializer):
    is_expired = serializers.BooleanField(read_only=True)
    days_to_expiry = serializers.IntegerField(read_only=True)
    medicine_name = serializers.CharField(source='medicine.name', read_only=True)

    class Meta:
        model = Batch
        fields = [
            'id', 'medicine', 'medicine_name', 'batch_number', 'mfg_date',
            'expiry_date', 'quantity', 'purchase_cost', 'mrp',
            'is_expired', 'days_to_expiry', 'received_at',
        ]
        read_only_fields = ['quantity', 'received_at']


class MedicineSerializer(serializers.ModelSerializer):
    total_stock = serializers.IntegerField(read_only=True)
    stock_status = serializers.CharField(read_only=True)
    is_scheduled = serializers.BooleanField(read_only=True)
    schedule_display = serializers.CharField(source='get_schedule_display', read_only=True)
    batches = BatchSerializer(many=True, read_only=True)

    class Meta:
        model = Medicine
        fields = [
            'id', 'name', 'generic_name', 'manufacturer', 'hsn_code', 'gst_rate',
            'schedule', 'schedule_display', 'pack_unit', 'rack_location', 'barcode',
            'reorder_level', 'reorder_qty', 'min_stock', 'max_stock',
            'preferred_supplier', 'is_active', 'total_stock', 'stock_status',
            'is_scheduled', 'batches', 'created_at',
        ]


class MedicineListSerializer(serializers.ModelSerializer):
    """Lighter payload for list/lookup screens (no nested batches)."""

    total_stock = serializers.IntegerField(read_only=True)
    stock_status = serializers.CharField(read_only=True)

    class Meta:
        model = Medicine
        fields = [
            'id', 'name', 'generic_name', 'manufacturer', 'hsn_code', 'gst_rate',
            'schedule', 'pack_unit', 'rack_location', 'barcode',
            'reorder_level', 'reorder_qty', 'is_active', 'total_stock', 'stock_status',
        ]


class StockMovementSerializer(serializers.ModelSerializer):
    reason_display = serializers.CharField(source='get_reason_display', read_only=True)
    batch_label = serializers.CharField(source='batch.__str__', read_only=True)

    class Meta:
        model = StockMovement
        fields = [
            'id', 'batch', 'batch_label', 'reason', 'reason_display',
            'quantity', 'note', 'actor', 'created_at',
        ]
