from odoo.tests import tagged

from .common import RentalCommon


@tagged("post_install", "-at_install")
class TestBrokerCommission(RentalCommon):
    def _broker_contract(self, source="both", commission_type="f"):
        property_record = self._create_property(
            f"Broker Unit {source} {commission_type}"
        )
        values = {
            "property_id": property_record,
            "is_any_broker": True,
            "broker_id": self.broker.id,
            "broker_item_id": self.broker_product.id,
            "commission_from": source,
            "commission_type": commission_type,
            "rent_type": "once",
            "broker_commission": 250.0 if commission_type == "f" else 0.0,
            "broker_commission_percentage": 10.0 if commission_type == "p" else 0.0,
        }
        return self._create_contract(activate=True, **values)

    def test_tenant_only_fixed_commission(self):
        contract = self._broker_contract(source="customer", commission_type="f")
        self.assertEqual(len(contract.commission_ids), 1)
        self.assertEqual(contract.commission_ids.source, "customer")
        self.assertAlmostEqual(contract.commission_ids.amount, 250.0, places=2)
        self.assertTrue(contract.commission_ids.broker_bill_id)
        self.assertTrue(contract.commission_ids.charge_invoice_id)

    def test_landlord_only_percentage_commission(self):
        contract = self._broker_contract(source="landlord", commission_type="p")
        self.assertEqual(len(contract.commission_ids), 1)
        self.assertEqual(contract.commission_ids.source, "landlord")
        self.assertAlmostEqual(contract.commission_ids.amount, 100.0, places=2)

    def test_both_sources_create_two_commissions_and_one_contract(self):
        before = self.env["tenancy.details"].search_count([])
        contract = self._broker_contract(source="both", commission_type="f")
        after = self.env["tenancy.details"].search_count([])
        self.assertEqual(after, before + 1)
        self.assertEqual(len(contract.commission_ids), 2)
        self.assertEqual(set(contract.commission_ids.mapped("source")), {"customer", "landlord"})
        self.assertEqual(
            self.env["rental.commission"].search_count([("contract_id", "=", contract.id)]),
            2,
        )
