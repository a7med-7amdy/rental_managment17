from odoo import Command
from odoo.exceptions import AccessError
from odoo.tests import HttpCase, tagged

from .common import RentalCommon


@tagged("post_install", "-at_install")
class TestPortalOwnership(RentalCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.portal_a = cls.env["res.users"].create(
            {
                "name": "Portal Tenant A",
                "login": "portal_tenant_a",
                "password": "portal_tenant_a",
                "partner_id": cls.tenant.id,
                "company_id": cls.env.company.id,
                "company_ids": [Command.set(cls.env.company.ids)],
                "group_ids": [Command.link(cls.env.ref("base.group_portal").id)],
            }
        )
        cls.portal_b = cls.env["res.users"].create(
            {
                "name": "Portal Tenant B",
                "login": "portal_tenant_b",
                "password": "portal_tenant_b",
                "partner_id": cls.tenant_b.id,
                "company_id": cls.env.company.id,
                "company_ids": [Command.set(cls.env.company.ids)],
                "group_ids": [Command.link(cls.env.ref("base.group_portal").id)],
            }
        )
        cls.contract_a = cls._create_contract(activate=True)
        cls.property_b = cls._create_property("Portal B Unit")
        cls.contract_b = cls._create_contract(
            property_id=cls.property_b,
            tenancy_id=cls.tenant_b.id,
            activate=True,
        )
        cls.maintenance_b = cls.env["maintenance.request"].create(
            {
                "name": "Private B Request",
                "tenancy_id": cls.contract_b.id,
                "property_id": cls.property_b.id,
                "company_id": cls.env.company.id,
            }
        )

    def test_portal_user_reads_only_own_contract(self):
        visible = self.env["tenancy.details"].with_user(self.portal_a).search([])
        self.assertIn(self.contract_a, visible)
        self.assertNotIn(self.contract_b, visible)
        with self.assertRaises(AccessError):
            self.contract_b.with_user(self.portal_a).check_access("read")

    def test_portal_cannot_access_other_maintenance(self):
        with self.assertRaises(AccessError):
            self.maintenance_b.with_user(self.portal_a).check_access("read")

    def test_portal_cannot_create_request_for_other_contract(self):
        with self.assertRaises(AccessError):
            self.env["maintenance.request"].with_user(self.portal_a).create(
                {
                    "name": "Forbidden",
                    "tenancy_id": self.contract_b.id,
                    "property_id": self.property_b.id,
                    "company_id": self.env.company.id,
                }
            )


@tagged("post_install", "-at_install")
class TestRentalPortalRoutes(HttpCase):
    def test_portal_routes_require_authentication(self):
        response = self.url_open("/my/rent-contract/", allow_redirects=False)
        self.assertIn(response.status_code, (302, 303))
