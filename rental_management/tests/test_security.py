from odoo import Command
from odoo.exceptions import AccessError, UserError
from odoo.tests import tagged

from .common import RentalCommon


@tagged("post_install", "-at_install")
class TestRentalAccessRights(RentalCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.officer = cls.env["res.users"].create(
            {
                "name": "Rental Officer",
                "login": "rental_officer_test",
                "company_id": cls.env.company.id,
                "company_ids": [Command.set(cls.env.company.ids)],
                "group_ids": [Command.link(cls.env.ref("rental_management.property_rental_officer").id)],
            }
        )
        cls.manager = cls.env["res.users"].create(
            {
                "name": "Rental Manager",
                "login": "rental_manager_test",
                "company_id": cls.env.company.id,
                "company_ids": [Command.set(cls.env.company.ids)],
                "group_ids": [Command.link(cls.env.ref("rental_management.property_rental_manager").id)],
            }
        )
        cls.internal = cls.env["res.users"].create(
            {
                "name": "Internal No Rental Group",
                "login": "rental_internal_test",
                "company_id": cls.env.company.id,
                "company_ids": [Command.set(cls.env.company.ids)],
                "group_ids": [Command.link(cls.env.ref("base.group_user").id)],
            }
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
