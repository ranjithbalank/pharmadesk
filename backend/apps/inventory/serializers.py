from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from .models import Batch, Medicine, StockMovement


class BatchSerializer(serializers.ModelSerializer):
    is_expired = serializers.BooleanField(read_only=True)
    days_to_expiry = serializers.IntegerField(read_only=True)
    medicine_name = serializers.CharField(source='medicine.name', read_only=True)

    available_units = serializers.IntegerField(read_only=True)

    class Meta:
        model = Batch
        fields = [
            'id', 'medicine', 'medicine_name', 'batch_number', 'mfg_date',
            'expiry_date', 'quantity', 'loose_units', 'available_units',
            'purchase_cost', 'mrp', 'is_expired', 'days_to_expiry', 'received_at',
        ]
        read_only_fields = ['quantity', 'loose_units', 'received_at']

    def validate(self, attrs):
        """Run the model's expiry validation (item 12) on add/edit so expired
        stock can never be entered through the API."""
        instance = Batch(**{**self._instance_data(), **attrs})
        try:
            instance.clean()
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.message_dict)
        return attrs

    def _instance_data(self):
        if not self.instance:
            return {}
        return {'mfg_date': self.instance.mfg_date, 'expiry_date': self.instance.expiry_date}


class MedicineSerializer(serializers.ModelSerializer):
    total_stock = serializers.IntegerField(read_only=True)
    total_units = serializers.IntegerField(read_only=True)
    stock_status = serializers.CharField(read_only=True)
    is_scheduled = serializers.BooleanField(read_only=True)
    sells_loose = serializers.BooleanField(read_only=True)
    sell_mrp = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    unit_price = serializers.DecimalField(max_digits=10, decimal_places=4, read_only=True)
    schedule_display = serializers.CharField(source='get_schedule_display', read_only=True)
    med_type_display = serializers.CharField(source='get_med_type_display', read_only=True)
    batches = BatchSerializer(many=True, read_only=True)

    class Meta:
        model = Medicine
        fields = [
            'id', 'name', 'generic_name', 'manufacturer', 'med_type', 'med_type_display',
            'hsn_code', 'gst_rate', 'schedule', 'schedule_display', 'pack_unit',
            'units_per_pack', 'rack_location', 'barcode',
            'reorder_level', 'reorder_qty', 'min_stock', 'max_stock',
            'preferred_supplier', 'is_active', 'total_stock', 'total_units', 'stock_status',
            'is_scheduled', 'sells_loose', 'sell_mrp', 'unit_price', 'batches', 'created_at',
        ]


class MedicineListSerializer(serializers.ModelSerializer):
    """Lighter payload for list/lookup screens (no nested batches)."""

    total_stock = serializers.IntegerField(read_only=True)
    total_units = serializers.IntegerField(read_only=True)
    stock_status = serializers.CharField(read_only=True)
    is_scheduled = serializers.BooleanField(read_only=True)
    sells_loose = serializers.BooleanField(read_only=True)
    sell_mrp = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    unit_price = serializers.DecimalField(max_digits=10, decimal_places=4, read_only=True)
    med_type_display = serializers.CharField(source='get_med_type_display', read_only=True)

    class Meta:
        model = Medicine
        fields = [
            'id', 'name', 'generic_name', 'manufacturer', 'med_type', 'med_type_display',
            'hsn_code', 'gst_rate', 'schedule', 'pack_unit', 'units_per_pack',
            'rack_location', 'barcode', 'reorder_level', 'reorder_qty', 'is_active',
            'total_stock', 'total_units', 'stock_status', 'is_scheduled', 'sells_loose',
            'sell_mrp', 'unit_price',
        ]


class StockMovementSerializer(serializers.ModelSerializer):
    reason_display = serializers.CharField(source='get_reason_display', read_only=True)
    batch_label = serializers.CharField(source='batch.__str__', read_only=True)

    class Meta:
        model = StockMovement
        fields = [
            'id', 'batch', 'batch_label', 'reason', 'reason_display',
            'quantity', 'note', 'actor', 'reversed', 'created_at',
        ]
