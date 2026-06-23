"""Central DRF router — all module endpoints register here under /api/."""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.billing.views import InvoiceViewSet
from apps.core.views import (
    AuditLogViewSet,
    DashboardView,
    DayCloseView,
    NotificationViewSet,
    ShopSettingView,
)
from apps.customers.views import CustomerViewSet, PrescriptionViewSet
from apps.inventory.views import BatchViewSet, MedicineViewSet, StockMovementViewSet
from apps.purchasing.views import (
    LeadTimeViewSet,
    PaymentTermViewSet,
    PurchaseOrderViewSet,
    SupplierViewSet,
)
from apps.reports.views import report_view

router = DefaultRouter()
router.register('medicines', MedicineViewSet)
router.register('batches', BatchViewSet)
router.register('stock-movements', StockMovementViewSet)
router.register('suppliers', SupplierViewSet)
router.register('payment-terms', PaymentTermViewSet)
router.register('lead-times', LeadTimeViewSet)
router.register('purchase-orders', PurchaseOrderViewSet)
router.register('customers', CustomerViewSet)
router.register('prescriptions', PrescriptionViewSet)
router.register('invoices', InvoiceViewSet)
router.register('notifications', NotificationViewSet)
router.register('audit-logs', AuditLogViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('settings/', ShopSettingView.as_view(), name='settings'),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('day-close/', DayCloseView.as_view(), name='day-close'),
    path('reports/<str:key>/', report_view, name='report'),
]
