from rest_framework import serializers

from .models import AuditLog, Notification, ShopSetting


class ShopSettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShopSetting
        fields = [
            'shop_name', 'gstin', 'drug_licence_no', 'has_drug_license', 'logo',
            'address', 'phone', 'email',
            'near_expiry_days', 'default_reorder_level', 'default_reorder_qty',
            'default_gst_rate', 'po_prefix', 'po_next_number', 'invoice_prefix',
            'updated_at',
        ]
        # admin_password is write-only / managed separately; never expose it.


class NotificationSerializer(serializers.ModelSerializer):
    kind_display = serializers.CharField(source='get_kind_display', read_only=True)
    medicine_name = serializers.CharField(source='medicine.name', read_only=True, default='')

    class Meta:
        model = Notification
        fields = [
            'id', 'kind', 'kind_display', 'severity', 'title', 'message',
            'medicine', 'medicine_name', 'batch', 'is_read', 'is_dismissed', 'created_at',
        ]


class AuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditLog
        fields = ['id', 'action', 'detail', 'actor', 'created_at']
