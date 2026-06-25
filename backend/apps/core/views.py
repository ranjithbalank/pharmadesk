from datetime import timedelta

from django.contrib.auth import authenticate
from django.db.models import Count, Sum
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
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


class LoginView(APIView):
    """SEC-1 single shared login. Exchanges username + password for a token."""
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        username = (request.data.get('username') or '').strip()
        password = request.data.get('password') or ''
        user = authenticate(username=username, password=password)
        if not user:
            return Response({'detail': 'Incorrect username or password.'},
                            status=status.HTTP_400_BAD_REQUEST)
        token, _ = Token.objects.get_or_create(user=user)
        AuditLog.objects.create(action='login', actor=user.username)
        return Response({'token': token.key, 'username': user.username,
                         'shop_name': ShopSetting.load().shop_name})


class LogoutView(APIView):
    def post(self, request):
        Token.objects.filter(user=request.user).delete()
        return Response({'status': 'ok'})


class MeView(APIView):
    """Returns the logged-in user — the SPA uses it to validate a saved token."""
    def get(self, request):
        return Response({'username': request.user.username,
                         'shop_name': ShopSetting.load().shop_name})


class ChangePasswordView(APIView):
    def post(self, request):
        current = request.data.get('current_password') or ''
        new = request.data.get('new_password') or ''
        if not request.user.check_password(current):
            return Response({'detail': 'Current password is incorrect.'},
                            status=status.HTTP_400_BAD_REQUEST)
        if len(new) < 4:
            return Response({'detail': 'New password is too short.'},
                            status=status.HTTP_400_BAD_REQUEST)
        request.user.set_password(new)
        request.user.save()
        Token.objects.filter(user=request.user).delete()
        token = Token.objects.create(user=request.user)
        AuditLog.objects.create(action='password_change', actor=request.user.username)
        return Response({'token': token.key})


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
        week_start = today - timedelta(days=6)  # last 7 days inclusive

        non_returned = Invoice.objects.exclude(status=Invoice.Status.RETURNED)
        todays_invoices = non_returned.filter(created_at__date=today)
        meds = Medicine.objects.filter(is_active=True)
        low = sum(1 for m in meds if m.stock_status == 'low_stock')
        oos = sum(1 for m in meds if m.stock_status == 'out_of_stock')
        near = Batch.objects.filter(
            quantity__gt=0, expiry_date__gte=today,
            expiry_date__lte=today + timedelta(days=ShopSetting.load().near_expiry_days),
        ).count()
        expired = Batch.objects.filter(quantity__gt=0, expiry_date__lt=today).count()

        # Total outstanding credit/khata across all customers.
        from apps.customers.models import Customer
        credit_outstanding = Customer.objects.aggregate(
            s=Sum('credit_balance'))['s'] or 0

        # Optional custom date range (?start=YYYY-MM-DD&end=YYYY-MM-DD).
        range_total = range_count = None
        start, end = request.query_params.get('start'), request.query_params.get('end')
        if start and end:
            ranged = non_returned.filter(created_at__date__gte=start, created_at__date__lte=end)
            range_total = ranged.aggregate(s=Sum('total'))['s'] or 0
            range_count = ranged.count()

        return Response({
            'today_sales_total': todays_invoices.aggregate(s=Sum('total'))['s'] or 0,
            'today_invoice_count': todays_invoices.count(),
            'week_sales_total': non_returned.filter(
                created_at__date__gte=week_start).aggregate(s=Sum('total'))['s'] or 0,
            'month_sales_total': non_returned.filter(
                created_at__date__gte=month_start).aggregate(s=Sum('total'))['s'] or 0,
            'credit_outstanding': credit_outstanding,
            'range_sales_total': range_total,
            'range_invoice_count': range_count,
            'medicine_count': meds.count(),
            'low_stock_count': low,
            'out_of_stock_count': oos,
            'near_expiry_count': near,
            'expired_count': expired,
            'alert_count': Notification.objects.filter(is_dismissed=False).count(),
        })


class DayCloseView(APIView):
    """End-of-day sales summary / cash reconciliation (FR-20).

    Returns the day's takings split by payment mode so the counter can
    reconcile the cash drawer. Pass ?date=YYYY-MM-DD for any past day.
    """

    def get(self, request):
        date_str = request.query_params.get('date')
        day = (
            timezone.datetime.fromisoformat(date_str).date()
            if date_str else timezone.localdate()
        )
        invoices = Invoice.objects.filter(created_at__date=day)

        by_mode = {
            row['payment_mode']: {
                'count': row['n'], 'total': row['t'] or 0,
            }
            for row in invoices.values('payment_mode').annotate(
                n=Count('id'), t=Sum('total')
            )
        }
        modes = {
            mode: by_mode.get(mode, {'count': 0, 'total': 0})
            for mode, _ in Invoice.PaymentMode.choices
        }
        returned = invoices.filter(status=Invoice.Status.RETURNED)

        return Response({
            'date': day.isoformat(),
            'invoice_count': invoices.count(),
            'gross_total': invoices.aggregate(s=Sum('total'))['s'] or 0,
            'by_mode': modes,
            'cash_total': modes['cash']['total'],
            'returned_count': returned.count(),
            'returned_total': returned.aggregate(s=Sum('total'))['s'] or 0,
            'tax_collected': (invoices.aggregate(c=Sum('cgst'))['c'] or 0)
            + (invoices.aggregate(s=Sum('sgst'))['s'] or 0),
        })
