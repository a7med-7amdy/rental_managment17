from odoo import Command
from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged
from odoo.tests.common import new_test_user

from .common import RentalCommon


@tagged("post_install", "-at_install")
class TestRentalMultiCompany(RentalCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company_b_data = cls.setup_other_company(name="Rental Company B")
        cls.company_b = cls.company_b_data["company"]
        cls.property_b = cls._create_property("Company B Unit", company=cls.company_b)
        cls.user_a = new_test_user(
            cls.env,
            login="company_a_rental_user",
            groups="rental_management.property_rental_manager",
            name="Company A Rental User",
            company_id=cls.env.company.id,
            company_ids=[Command.set(cls.env.company.ids)],
        )

    def test_company_rule_hides_other_company(self):
        visible = self.env["property.details"].with_user(self.user_a).search([])
        self.assertNotIn(self.property_b, visible)

    def test_cross_company_contract_is_rejected(self):
        values = self._contract_values(property_id=self.property_b)
        values["company_id"] = self.env.company.id
        rejected = False
        try:
            self.env["tenancy.details"].with_context(
                allowed_company_ids=(self.env.company | self.company_b).ids
            ).create(values)
        except (UserError, ValidationError):
            rejected = True
        self.assertTrue(
            rejected,
            "A rental contract cannot link a property from another company.",
        )

    def test_dashboard_respects_allowed_companies(self):
        stats = self.env["property.details"].with_user(self.user_a).get_property_stats()
        all_company_total = self.env["property.details"].with_context(
            allowed_company_ids=(self.env.company | self.company_b).ids
        ).search_count([])
        self.assertLess(stats["total_property"], all_company_total)
