from odoo.tests import tagged

from .common import RentalCommon


@tagged("post_install", "-at_install")
class TestUpgradeDataIntegrity(RentalCommon):
    """Regression checks for legacy-state records after module upgrade.

    Database migration scripts themselves are exercised by the real ``-u`` command;
    this class verifies that supported pre-existing states remain readable and that
    the lifecycle reconciliation does not delete accounting history.
    """

    def test_existing_states_and_accounting_history_are_preserved(self):
        draft = self._create_contract()
        running_property = self._create_property("Legacy Running Unit")
        running = self._create_contract(property_id=running_property, activate=True)
        schedule = running.rent_invoice_ids[:1]
        move = schedule.action_create_invoice()

        self.env["tenancy.details"]._cron_process_rental_lifecycle()

        self.assertTrue(draft.exists())
        self.assertTrue(running.exists())
        self.assertTrue(schedule.exists())
        self.assertTrue(move.exists())
        self.assertIn(draft.contract_type, ("new_contract", "running_contract"))
        self.assertIn(
            running.contract_type,
            ("running_contract", "expire_contract", "close_contract"),
        )
