from datetime import timedelta

from django.db.models import Sum
from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.billing.models import Invoice
from apps.inventory.models import Batch, Medicine

from .models import AuditLog, Notification, ShopSetting
from .serializers import (
    AuditLogSerializer,
    NotificationSerializer,
    ShopSettingSerializer,
)
from .services import recompute_notifications


class ShopSettingView(APIView):
    """Singleton settings (FR-40). GET returns the row; PUT updates it."""

    def get(self, request):
        return Response(ShopSettingSerializer(ShopSetting.load()).data)

    def put(self, request):
        settings = ShopSetting.load()
        serializer = ShopSettingSerializer(settings, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        AuditLog.objects.create(action='settings_update', detail='Shop settings changed')
        return Response(serializer.data)


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    filterset_fields = ['kind', 'severity', 'is_read', 'is_dismissed']

    @action(detail=False, methods=['post'])
    def refresh(self, request):
        """Recompute alerts from current stock/expiry and return them."""
        recompute_notifications()
        qs = self.get_queryset().filter(is_dismissed=False)
        return Response(self.get_serializer(qs, many=True).data)

    @action(detail=True, methods=['post'])
    def dismiss(self, request, pk=None):
        n = self.get_object()
        n.is_dismissed = True
        n.is_read = True
        n.save(update_fields=['is_dismissed', 'is_read'])
        return Response(self.get_serializer(n).data)

    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        self.get_queryset().update(is_read=True)
        return Response({'status': 'ok'})


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer


class DashboardView(APIView):
    """Aggregated counters for the dashboard cards and alert badge."""

    def get(self, request):
        recompute_notifications()
        today = timezone.localdate()
        month_start = today.replace(day=1)

        todays_invoices = Invoice.objects.filter(created_at__date=today)
        meds = Medicine.objects.filter(is_active=True)
        low = sum(1 for m in meds if m.stock_status == 'low_stock')
        oos = sum(1 for m in meds if m.stock_status == 'out_of_stock')
        near = Batch.objects.filter(
            quantity__gt=0, expiry_date__gte=today,
            expiry_date__lte=today + timedelta(days=ShopSetting.load().near_expiry_days),
        ).count()
        expired = Batch.objects.filter(quantity__gt=0, expiry_date__lt=today).count()

        return Response({
            'today_sales_total': todays_invoices.aggregate(s=Sum('total'))['s'] or 0,
            'today_invoice_count': todays_invoices.count(),
            'month_sales_total': Invoice.objects.filter(
                created_at__date__gte=month_start
            ).aggregate(s=Sum('total'))['s'] or 0,
            'medicine_count': meds.count(),
            'low_stock_count': low,
            'out_of_stock_count': oos,
            'near_expiry_count': near,
            'expired_count': expired,
            'alert_count': Notification.objects.filter(is_dismissed=False).count(),
        })
