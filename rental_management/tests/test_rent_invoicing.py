from datetime import timedelta

from odoo.fields import Command
from odoo.tests import tagged

from .common import RentalCommon


@tagged("post_install", "-at_install")
class TestRentInvoicing(RentalCommon):
    def test_monthly_invoice_is_idempotent(self):
        contract = self._create_contract(activate=True)
        schedule = contract.rent_invoice_ids.sorted("due_date")[:1]
        first = schedule._create_account_move()
        second = schedule._create_account_move()
        self.assertEqual(first, second)
        self.assertEqual(self.env["account.move"].search_count([("rental_schedule_id", "=", schedule.id)]), 1)
        self.assertAlmostEqual(schedule.rent_amount, 1000.0, places=2)

    def test_missed_cron_catches_up_once(self):
        contract = self._create_contract(activate=True)
        contract.type = "automatic"
        schedule = contract.rent_invoice_ids.sorted("due_date")[:1]
        schedule.rent_invoice_id = False
        schedule.due_date = self.yesterday()
        self.env["rent.invoice"]._cron_create_due_invoices()
        invoice = schedule.rent_invoice_id
        self.assertTrue(invoice)
        self.env["rent.invoice"]._cron_create_due_invoices()
        self.assertEqual(schedule.rent_invoice_id, invoice)

    def test_quarterly_and_partial_final_period(self):
        contract = self._create_contract(
            duration_id=self.duration_4m.id,
            payment_term="quarterly",
            activate=False,
        )
        contract.action_activate_contract()
        schedules = contract.rent_invoice_ids.sorted("period_start")
        self.assertEqual(len(schedules), 2)
        self.assertAlmostEqual(schedules[0].rent_amount, 3000.0, places=2)
        self.assertAlmostEqual(schedules[1].rent_amount, 1000.0, places=2)

    def test_quarterly_service_not_multiplied_twice(self):
        contract = self._create_contract(
            duration_id=self.duration_3m.id,
            payment_term="quarterly",
            extra_services_ids=[
                Command.create({"service_id": self.service_product.id, "price": 100.0, "service_type": "monthly"})
            ],
        )
        contract.action_activate_contract()
        schedule = contract.rent_invoice_ids[:1]
        _lines, breakdown = contract._prepare_period_invoice_lines(schedule)
        self.assertAlmostEqual(breakdown["services"], 300.0, places=2)

    def test_yearly_invoice(self):
        property_record = self._create_property("Yearly Unit")
        property_record.rent_unit = "Year"
        contract = self._create_contract(
            property_id=property_record,
            duration_id=self.duration_1y.id,
            payment_term="year",
            total_rent=12000.0,
        )
        contract.action_activate_contract()
        self.assertEqual(len(contract.rent_invoice_ids), 1)
        self.assertAlmostEqual(contract.rent_invoice_ids.rent_amount, 12000.0, places=2)

    def test_full_payment_and_manual_installments(self):
        full = self._create_contract(payment_term="full_payment")
        full.action_activate_contract()
        self.assertEqual(len(full.rent_invoice_ids), 1)
        self.assertAlmostEqual(full.rent_invoice_ids.rent_amount, 3000.0, places=2)

        other_property = self._create_property("Manual Unit")
        manual = self._create_contract(property_id=other_property, duration_id=self.duration_4m.id)
        manual.action_activate_contract()
        self.assertEqual(len(manual.rent_invoice_ids), 4)
