from datetime import timedelta

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

    def test_future_running_contract_marks_property_reserved(self):
        property_record = self._create_property("Future Reserved Unit")
        future_start = self.yesterday() + timedelta(days=10)
        contract = self._create_contract(
            property_id=property_record,
            start_date=future_start,
            invoice_start_date=future_start,
        )
        contract.action_activate_contract()
        self.assertEqual(contract.contract_type, "running_contract")
        self.assertEqual(property_record.stage, "booked")

    def test_current_contract_precedes_future_reservation(self):
        property_record = self._create_property("Current And Future Unit")
        current = self._create_contract(property_id=property_record, activate=True)
        future_start = current.end_date + timedelta(days=1)
        future = self._create_contract(
            property_id=property_record,
            tenancy_id=self.tenant_b.id,
            start_date=future_start,
            invoice_start_date=future_start,
            activate=True,
        )

        self.assertEqual(property_record.stage, "on_lease")
        current.action_close_contract()
        self.assertEqual(property_record.stage, "booked")
        self.assertEqual(future.contract_type, "running_contract")

