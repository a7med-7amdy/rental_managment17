from odoo.exceptions import UserError
from odoo.tests import tagged

from .common import RentalCommon


@tagged("post_install", "-at_install")
class TestPropertySaleLifecycle(RentalCommon):
    def _sale_property(self, name="Sale Unit"):
        property_record = self._create_property(name)
        property_record.write({"sale_lease": "for_sale", "price": 500000.0})
        property_record.action_in_sale()
        return property_record

    def test_booking_is_atomic_and_direct_sold_write_is_blocked(self):
        property_record = self._sale_property()
        sale = self.env["property.vendor"].create(
            {
                "property_id": property_record.id,
                "customer_id": self.tenant.id,
                "company_id": self.env.company.id,
                "sale_price": 500000.0,
                "book_price": 50000.0,
                "payment_term": "monthly",
            }
        )
        self.assertEqual(sale.stage, "booked")
        self.assertEqual(property_record.stage, "booked")
        self.assertEqual(property_record.sold_booking_id, sale)
        self.assertAlmostEqual(sale.payable_amount, 450000.0, places=2)
        with self.assertRaises(UserError):
            sale.write({"stage": "sold"})

    def test_refund_releases_property_without_deleting_history(self):
        property_record = self._sale_property("Refund Unit")
        sale = self.env["property.vendor"].create(
            {
                "property_id": property_record.id,
                "customer_id": self.tenant.id,
                "company_id": self.env.company.id,
                "sale_price": 400000.0,
                "book_price": 40000.0,
            }
        )
        sale.action_refund_amount()
        self.assertEqual(sale.stage, "refund")
        self.assertEqual(property_record.stage, "sale")
        self.assertFalse(property_record.sold_booking_id)
        self.assertTrue(sale.exists())
