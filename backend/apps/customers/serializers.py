from rest_framework import serializers

from .models import Customer, Prescription


class CustomerSerializer(serializers.ModelSerializer):
    invoice_count = serializers.IntegerField(source='invoices.count', read_only=True)

    class Meta:
        model = Customer
        fields = [
            'id', 'name', 'phone', 'address', 'is_regular', 'allow_credit',
            'credit_balance', 'has_drug_license', 'drug_license_no',
            'consent_given', 'invoice_count', 'created_at',
        ]
        read_only_fields = ['credit_balance']

    def validate(self, attrs):
        has = attrs.get('has_drug_license', getattr(self.instance, 'has_drug_license', False))
        if has and not (attrs.get('drug_license_no') or getattr(self.instance, 'drug_license_no', '')):
            raise serializers.ValidationError(
                {'drug_license_no': 'Licence number is required when the customer holds a medical supply licence.'})
        return attrs


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
