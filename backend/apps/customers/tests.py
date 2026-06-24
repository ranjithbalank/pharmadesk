"""Tests for customer lookup (item 3) and drug-licence validation (item 4)."""
from apps.core.testbase import AuthedAPITestCase

from .models import Customer


class CustomerLookupTests(AuthedAPITestCase):
    def setUp(self):
        super().setUp()
        self.cust = Customer.objects.create(name='Murugan', phone='9445566778')

    def test_lookup_by_phone(self):
        resp = self.client.get('/api/customers/lookup/?q=9445566778')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()['name'], 'Murugan')

    def test_lookup_by_id(self):
        resp = self.client.get(f'/api/customers/lookup/?q={self.cust.id}')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()['id'], self.cust.id)

    def test_lookup_not_found(self):
        resp = self.client.get('/api/customers/lookup/?q=0000000000')
        self.assertEqual(resp.status_code, 404)


class CustomerLicenceTests(AuthedAPITestCase):
    def test_licence_number_required_when_flagged(self):
        resp = self.client.post('/api/customers/', data={
            'name': 'City Clinic', 'has_drug_license': True, 'drug_license_no': '',
        }, format='json')
        self.assertEqual(resp.status_code, 400)
        self.assertIn('drug_license_no', resp.json())

    def test_licence_ok_with_number(self):
        resp = self.client.post('/api/customers/', data={
            'name': 'City Clinic', 'has_drug_license': True, 'drug_license_no': 'TN-CL-99',
        }, format='json')
        self.assertEqual(resp.status_code, 201)
