from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestRentalViewArchitecture(TransactionCase):
    def test_mail_thread_forms_use_odoo19_chatter_component(self):
        form_view_xmlids = (
            "rental_management.property_project_view_form",
            "rental_management.property_sub_project_view_form",
            "rental_management.rent_invoice_form_view",
            "rental_management.property_vendor_form_view",
        )
        for xmlid in form_view_xmlids:
            view = self.env.ref(xmlid)
            arch = view.arch_db or ""
            self.assertIn("<chatter", arch, f"{xmlid} must use the Odoo 19 chatter component")
            self.assertNotIn("oe_chatter", arch, f"{xmlid} still contains the legacy chatter block")
            self.assertNotIn("message_follower_ids", arch, f"{xmlid} exposes raw mail follower fields")
            self.assertNotIn("message_ids", arch, f"{xmlid} exposes raw mail message fields")
