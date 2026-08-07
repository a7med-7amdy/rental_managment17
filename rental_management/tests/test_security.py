from odoo import Command
from odoo.exceptions import AccessError, UserError
from odoo.tests import tagged
from odoo.tests.common import new_test_user

from .common import RentalCommon


@tagged("post_install", "-at_install")
class TestRentalAccessRights(RentalCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.officer = new_test_user(
            cls.env,
            login="rental_officer_test",
            groups="rental_management.property_rental_officer",
            name="Rental Officer",
            company_id=cls.env.company.id,
            company_ids=[Command.set(cls.env.company.ids)],
        )
        cls.manager = new_test_user(
            cls.env,
            login="rental_manager_test",
            groups="rental_management.property_rental_manager",
            name="Rental Manager",
            company_id=cls.env.company.id,
            company_ids=[Command.set(cls.env.company.ids)],
        )
        cls.internal = new_test_user(
            cls.env,
            login="rental_internal_test",
            groups="base.group_user",
            name="Internal No Rental Group",
            company_id=cls.env.company.id,
            company_ids=[Command.set(cls.env.company.ids)],
        )

    def test_officer_cannot_delete_active_contract(self):
        contract = self._create_contract(activate=True)
        with self.assertRaises(AccessError):
            contract.with_user(self.officer).check_access('unlink')
        with self.assertRaises(UserError):
            contract.unlink()

    def test_officer_cannot_close_or_cancel_contract(self):
        contract = self._create_contract(activate=True)
        with self.assertRaises(AccessError):
            contract.with_user(self.officer).action_close_contract()
        with self.assertRaises(AccessError):
            contract.with_user(self.officer).action_cancel_contract(reason="Not authorized")

    def test_manager_can_close_without_accounting_group(self):
        contract = self._create_contract(activate=True)
        self.assertFalse(self.manager.has_group("account.group_account_invoice"))
        contract.with_user(self.manager).action_close_contract()
        self.assertEqual(contract.contract_type, "close_contract")

    def test_manager_can_cancel_without_accounting_group(self):
        property_record = self._create_property("Manager Cancel Unit")
        contract = self._create_contract(property_id=property_record, activate=True)
        contract.with_user(self.manager).action_cancel_contract(reason="Manager cancellation")
        self.assertEqual(contract.contract_type, "cancel_contract")
        self.assertEqual(contract.property_id.stage, "available")


    def test_rental_manager_does_not_gain_maintenance_team_admin(self):
        with self.assertRaises(AccessError):
            self.env["maintenance.team"].with_user(self.manager).create(
                {"name": "Forbidden Rental Team", "company_id": self.env.company.id}
            )

    def test_rental_officer_can_create_maintenance_request_with_default_team(self):
        property_record = self._create_property("Officer Maintenance Unit")
        contract = self._create_contract(property_id=property_record, activate=True)
        request = self.env["maintenance.request"].with_user(self.officer).create(
            {
                "name": "Officer Rental Maintenance",
                "tenancy_id": contract.id,
                "property_id": property_record.id,
                "company_id": self.env.company.id,
            }
        )
        self.assertTrue(request.maintenance_team_id)
        self.assertEqual(request.tenancy_id, contract)

    def test_rental_manager_can_create_maintenance_request_with_default_team(self):
        property_record = self._create_property("Manager Maintenance Unit")
        contract = self._create_contract(property_id=property_record, activate=True)
        request = self.env["maintenance.request"].with_user(self.manager).create(
            {
                "name": "Manager Rental Maintenance",
                "tenancy_id": contract.id,
                "property_id": property_record.id,
                "company_id": self.env.company.id,
            }
        )
        self.assertTrue(request.maintenance_team_id)
        self.assertEqual(request.tenancy_id, contract)

    def test_manager_has_officer_privilege(self):
        self.assertTrue(self.manager.has_group("rental_management.property_rental_officer"))
        self.assertTrue(self.manager.has_group("rental_management.property_rental_manager"))

    def test_internal_user_has_no_rental_access(self):
        with self.assertRaises(AccessError):
            self.env["tenancy.details"].with_user(self.internal).search([])

    def test_public_user_has_no_rental_access(self):
        public_user = self.env.ref("base.public_user")
        with self.assertRaises(AccessError):
            self.env["tenancy.details"].with_user(public_user).search([])
