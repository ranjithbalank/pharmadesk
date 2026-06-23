from rest_framework import serializers

from .models import LeadTime, PaymentTerm, PurchaseOrder, PurchaseOrderLine, Supplier


class PaymentTermSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentTerm
        fields = ['id', 'name', 'days', 'is_active']


class LeadTimeSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeadTime
        fields = ['id', 'label', 'days', 'is_active']


class SupplierSerializer(serializers.ModelSerializer):
    payment_term_name = serializers.CharField(source='payment_term.name', read_only=True, default='')
    lead_time_label = serializers.CharField(source='lead_time.label', read_only=True, default='')

    class Meta:
        model = Supplier
        fields = [
            'id', 'code', 'name', 'gstin', 'contact_person', 'phone', 'email', 'address',
            'has_drug_license', 'drug_license_no',
            'payment_term', 'payment_term_name', 'lead_time', 'lead_time_label',
            'payment_terms', 'lead_time_days', 'is_active', 'created_at',
        ]

    def validate(self, attrs):
        # Capture a licence number only when the supplier holds a licence.
        has = attrs.get('has_drug_license', getattr(self.instance, 'has_drug_license', False))
        if has and not (attrs.get('drug_license_no') or getattr(self.instance, 'drug_license_no', '')):
            raise serializers.ValidationError(
                {'drug_license_no': 'Licence number is required when the supplier holds a medical supply licence.'})
        return attrs


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
            'bill_to', 'ship_to', 'notes', 'total_value', 'lines', 'created_at', 'placed_at',
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
