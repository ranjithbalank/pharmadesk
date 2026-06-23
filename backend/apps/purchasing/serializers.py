from rest_framework import serializers

from .models import PurchaseOrder, PurchaseOrderLine, Supplier


class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = [
            'id', 'name', 'gstin', 'contact_person', 'phone', 'email',
            'address', 'payment_terms', 'lead_time_days', 'is_active', 'created_at',
        ]


class PurchaseOrderLineSerializer(serializers.ModelSerializer):
    medicine_name = serializers.CharField(source='medicine.name', read_only=True)
    outstanding_qty = serializers.IntegerField(read_only=True)

    class Meta:
        model = PurchaseOrderLine
        fields = [
            'id', 'medicine', 'medicine_name', 'quantity',
            'unit_cost', 'received_qty', 'outstanding_qty',
        ]


class PurchaseOrderSerializer(serializers.ModelSerializer):
    lines = PurchaseOrderLineSerializer(many=True)
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    total_value = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = PurchaseOrder
        fields = [
            'id', 'number', 'supplier', 'supplier_name', 'status', 'status_display',
            'notes', 'total_value', 'lines', 'created_at', 'placed_at',
        ]
        read_only_fields = ['number', 'placed_at']

    def create(self, validated_data):
        lines = validated_data.pop('lines', [])
        order = PurchaseOrder.objects.create(**validated_data)
        for line in lines:
            PurchaseOrderLine.objects.create(order=order, **line)
        return order

    def update(self, instance, validated_data):
        lines = validated_data.pop('lines', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if lines is not None:
            instance.lines.all().delete()
            for line in lines:
                PurchaseOrderLine.objects.create(order=instance, **line)
        return instance
