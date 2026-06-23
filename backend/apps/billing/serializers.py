from rest_framework import serializers

from apps.customers.models import Customer
from apps.inventory.models import Medicine

from .models import Invoice, InvoiceLine
from .services import create_invoice


class InvoiceLineSerializer(serializers.ModelSerializer):
    taxable_value = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    cgst_amount = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    sgst_amount = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    line_total = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = InvoiceLine
        fields = [
            'id', 'medicine_name', 'hsn_code', 'batch_number', 'expiry_date',
            'quantity', 'mrp', 'rate', 'discount', 'gst_rate',
            'taxable_value', 'cgst_amount', 'sgst_amount', 'line_total',
        ]


class InvoiceSerializer(serializers.ModelSerializer):
    lines = InvoiceLineSerializer(many=True, read_only=True)
    customer_name = serializers.CharField(source='customer.name', read_only=True, default='')
    payment_mode_display = serializers.CharField(source='get_payment_mode_display', read_only=True)

    class Meta:
        model = Invoice
        fields = [
            'id', 'number', 'customer', 'customer_name', 'payment_mode',
            'payment_mode_display', 'status', 'subtotal', 'discount',
            'cgst', 'sgst', 'total', 'irn', 'note', 'lines', 'created_at',
        ]


class _CartItemSerializer(serializers.Serializer):
    medicine = serializers.PrimaryKeyRelatedField(queryset=Medicine.objects.all())
    quantity = serializers.IntegerField(min_value=1)
    discount = serializers.DecimalField(
        max_digits=10, decimal_places=2, required=False, default=0
    )


class InvoiceCreateSerializer(serializers.Serializer):
    """Input for the billing screen: a cart of items plus payment details.
    Delegates to the FEFO billing service and returns the saved invoice.
    """

    customer = serializers.PrimaryKeyRelatedField(
        queryset=Customer.objects.all(), required=False, allow_null=True
    )
    payment_mode = serializers.ChoiceField(
        choices=Invoice.PaymentMode.choices, default=Invoice.PaymentMode.CASH
    )
    discount = serializers.DecimalField(
        max_digits=12, decimal_places=2, required=False, default=0
    )
    note = serializers.CharField(required=False, allow_blank=True, default='')
    items = _CartItemSerializer(many=True)

    def validate_items(self, items):
        if not items:
            raise serializers.ValidationError('At least one item is required.')
        return items

    def create(self, validated_data):
        return create_invoice(
            customer=validated_data.get('customer'),
            payment_mode=validated_data['payment_mode'],
            bill_discount=validated_data.get('discount', 0),
            items=validated_data['items'],
            note=validated_data.get('note', ''),
        )

    def to_representation(self, instance):
        return InvoiceSerializer(instance, context=self.context).data
