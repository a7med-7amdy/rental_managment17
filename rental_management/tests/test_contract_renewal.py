from datetime import timedelta

from odoo.tests import tagged

from .common import RentalCommon


@tagged("post_install", "-at_install")
class TestContractRenewal(RentalCommon):
    def test_renewal_starts_next_day_and_links_contracts(self):
        old = self._create_contract(activate=True)
        wizard = self.env["extend.contract.wizard"].with_context(active_id=old.id).create(
            {
                "tenancy_id": old.id,
                "duration_id": self.duration_3m.id,
                "start_date": old.end_date + timedelta(days=1),
                "invoice_start_date": old.end_date + timedelta(days=1),
                "revised_price": 1100.0,
                "payment_term": "monthly",
                "installment_mode": "manual",
                "new_broker_id": False,
            }
        )
        action = wizard.extend_contract_action()
        renewed = self.env["tenancy.details"].browse(action["res_id"])
        self.assertEqual(renewed.start_date, old.end_date + timedelta(days=1))
        self.assertEqual(renewed.previous_contract_id, old)
        self.assertEqual(old.new_contract_id, renewed)
        self.assertEqual(renewed.contract_type, "new_contract")
        self.assertEqual(old.contract_type, "running_contract")
        renewed._check_no_overlap()
