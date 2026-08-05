from odoo import Command
from odoo.exceptions import AccessError, ValidationError
from odoo.tests import tagged

from .common import RentalCommon


@tagged("post_install", "-at_install")
class TestRentalMultiCompany(RentalCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company_b_data = cls.setup_other_company(name="Rental Company B")
        cls.company_b = cls.company_b_data["company"]
        cls.property_b = cls._create_property("Company B Unit", company=cls.company_b)
        cls.user_a = cls.env["res.users"].create(
            {
                "name": "Company A Rental User",
                "login": "company_a_rental_user",
                "company_id": cls.env.company.id,
                "company_ids": [Command.set(cls.env.company.ids)],
                "group_ids": [Command.link(cls.env.ref("rental_management.property_rental_manager").id)],
            }
        )

    def test_company_rule_hides_other_company(self):
        visible = self.env["property.details"].with_user(self.user_a).search([])
        self.assertNotIn(self.property_b, visible)

    def test_cross_company_contract_is_rejected(self):
        values = self._contract_values(property_id=self.property_b)
        values["company_id"] = self.env.company.id
        with self.assertRaises((ValidationError, AccessError)):
            self.env["tenancy.details"].create(values)

    def test_dashboard_respects_allowed_companies(self):
        stats = self.env["property.details"].with_user(self.user_a).get_property_stats()
        self.assertLess(stats["total_property"], self.env["property.details"].search_count([]))
