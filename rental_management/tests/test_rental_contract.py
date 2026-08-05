from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged

from .common import RentalCommon


@tagged("post_install", "-at_install")
class TestRentalContract(RentalCommon):
    def test_required_fields_before_activation(self):
        contract = self.env["tenancy.details"].new(
            {
                "company_id": self.env.company.id,
                "start_date": self.yesterday(),
                "total_rent": 0.0,
            }
        )
        with self.assertRaises(UserError):
            contract._check_required_for_activation()

    def test_contract_overlap_is_blocked(self):
        first = self._create_contract(activate=True)
        second = self._create_contract(tenancy_id=self.tenant_b.id)
        with self.assertRaises(ValidationError):
            second.action_activate_contract()

        after = self._create_contract(
            tenancy_id=self.tenant_b.id,
            start_date=first.end_date + __import__("datetime").timedelta(days=1),
            invoice_start_date=first.end_date + __import__("datetime").timedelta(days=1),
        )
        first.action_close_contract()
        after.action_activate_contract()
        self.assertEqual(after.contract_type, "running_contract")

    def test_close_and_cancel_preserve_invoices(self):
        contract = self._create_contract(activate=True)
        schedule = contract.rent_invoice_ids[:1]
        move = schedule._create_account_move()
        unbilled_schedule = contract.rent_invoice_ids.filtered(
            lambda line: not line.rent_invoice_id
        )[:1]
        contract.action_close_contract()
        self.assertTrue(move.exists())
        self.assertEqual(contract.property_id.stage, "available")
        self.assertTrue(unbilled_schedule)
        with self.assertRaises(UserError):
            unbilled_schedule._create_account_move()

    def test_cancel_rejects_posted_invoice(self):
        contract = self._create_contract(activate=True)
        schedule = contract.rent_invoice_ids[:1]
        move = schedule._create_account_move()
        move.action_post()
        with self.assertRaises(UserError):
            contract.action_cancel_contract(reason="Cancellation requested")
        self.assertEqual(contract.contract_type, "running_contract")
        self.assertTrue(move.exists())
