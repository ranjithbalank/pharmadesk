from django.db import models


class Customer(models.Model):
    """Customer master (FR-22). 'Regular' customers (FR-22a) get quick re-bill
    and credit/khata tracking (FR-22b/c).
    """

    name = models.CharField(max_length=200, db_index=True)
    phone = models.CharField(max_length=20, blank=True, db_index=True)
    address = models.TextField(blank=True)

    is_regular = models.BooleanField(default=False)
    # FR-22c: credit / khata for trusted regulars.
    allow_credit = models.BooleanField(default=False)
    credit_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # Institutional buyers (clinics/other pharmacies) may hold a medical-supply
    # licence — captured for scheduled-drug sale records.
    has_drug_license = models.BooleanField('Has medical supply licence', default=False)
    drug_license_no = models.CharField('Drug licence no.', max_length=60, blank=True)

    # FR-26: consent notice for storing personal data (DPDP).
    consent_given = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name or self.phone


class Prescription(models.Model):
    """Prescription record for scheduled-drug sales (FR-23). The Schedule H1
    register (FR-24) is generated from these rows.
    """

    customer = models.ForeignKey(
        Customer, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='prescriptions',
    )
    invoice = models.ForeignKey(
        'billing.Invoice', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='prescriptions',
    )
    patient_name = models.CharField(max_length=200)
    prescriber_name = models.CharField(max_length=200)
    prescriber_reg_no = models.CharField('Prescriber registration no.', max_length=80, blank=True)

    medicine = models.ForeignKey('inventory.Medicine', on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)
    rx_date = models.DateField()
    image = models.ImageField(upload_to='prescriptions/', null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-rx_date']

    def __str__(self):
        return f'Rx {self.patient_name} · {self.medicine}'
