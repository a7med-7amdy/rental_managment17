from odoo.tests import tagged

from .common import RentalCommon


@tagged("post_install", "-at_install")
class TestPropertyLifecycle(RentalCommon):
    def test_property_lifecycle(self):
        property_record = self._create_property("Lifecycle Unit", stage="draft")
        property_record.action_in_available()
        self.assertEqual(property_record.stage, "available")

        contract = self._create_contract(property_id=property_record)
        contract.action_activate_contract()
        self.assertEqual(contract.contract_type, "running_contract")
        self.assertEqual(property_record.stage, "on_lease")

        contract.action_close_contract()
        self.assertEqual(contract.contract_type, "close_contract")
        self.assertEqual(property_record.stage, "available")
