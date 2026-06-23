from rest_framework import serializers

from .models import Customer, Prescription


class CustomerSerializer(serializers.ModelSerializer):
    invoice_count = serializers.IntegerField(source='invoices.count', read_only=True)

    class Meta:
        model = Customer
        fields = [
            'id', 'name', 'phone', 'address', 'is_regular', 'allow_credit',
            'credit_balance', 'consent_given', 'invoice_count', 'created_at',
        ]
        read_only_fields = ['credit_balance']


class PrescriptionSerializer(serializers.ModelSerializer):
    medicine_name = serializers.CharField(source='medicine.name', read_only=True)
    customer_name = serializers.CharField(source='customer.name', read_only=True)

    class Meta:
        model = Prescription
        fields = [
            'id', 'customer', 'customer_name', 'invoice', 'patient_name',
            'prescriber_name', 'prescriber_reg_no', 'medicine', 'medicine_name',
            'quantity', 'rx_date', 'image', 'created_at',
        ]
