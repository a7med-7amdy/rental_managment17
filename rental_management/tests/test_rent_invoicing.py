from datetime import date, timedelta

from dateutil.relativedelta import relativedelta

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
        contract = self._create_contract(activate=True, type="automatic")
        schedule = contract.rent_invoice_ids.sorted("due_date")[:1]
        schedule.due_date = self.yesterday()
        self.assertEqual(schedule.installment_type, "automatic")
        self.env["rent.invoice"]._cron_create_due_invoices()
        invoice = schedule.rent_invoice_id
        self.assertTrue(invoice)
        self.env["rent.invoice"]._cron_create_due_invoices()
        self.assertEqual(schedule.rent_invoice_id, invoice)


    def test_month_end_anchor_does_not_create_extra_installment(self):
        property_record = self._create_property("Month End Unit")
        contract = self._create_contract(
            property_id=property_record,
            duration_id=self.duration_4m.id,
            start_date=date(2026, 1, 31),
            invoice_start_date=date(2026, 1, 31),
        )
        contract.action_activate_contract()
        schedules = contract.rent_invoice_ids.sorted("period_start")
        self.assertEqual(len(schedules), 4)
        self.assertEqual(schedules.mapped("rent_amount"), [1000.0] * 4)

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

    def test_duration_unit_is_independent_from_rate_unit(self):
        property_record = self._create_property("Annual Price One Month")
        property_record.rent_unit = "Year"
        one_month = self._create_contract(
            property_id=property_record,
            duration_id=self.duration_1m.id,
            payment_term="monthly",
            total_rent=12000.0,
        )
        one_month.action_activate_contract()
        self.assertEqual(one_month.end_date, one_month.start_date + relativedelta(months=1) - timedelta(days=1))
        self.assertAlmostEqual(one_month.rent_invoice_ids.rent_amount, 1000.0, places=2)

        monthly_property = self._create_property("Monthly Price One Year")
        yearly = self._create_contract(
            property_id=monthly_property,
            duration_id=self.duration_1y.id,
            payment_term="year",
            total_rent=1000.0,
        )
        yearly.action_activate_contract()
        self.assertEqual(len(yearly.rent_invoice_ids), 1)
        self.assertAlmostEqual(yearly.rent_invoice_ids.rent_amount, 12000.0, places=2)

    def test_daily_rate_full_payment_uses_contract_days(self):
        property_record = self._create_property("Daily Rate Unit")
        property_record.rent_unit = "Day"
        contract = self._create_contract(
            property_id=property_record,
            duration_id=self.duration_3d.id,
            payment_term="full_payment",
            total_rent=100.0,
        )
        contract.action_activate_contract()
        self.assertEqual((contract.end_date - contract.start_date).days + 1, 3)
        self.assertAlmostEqual(contract.rent_invoice_ids.rent_amount, 300.0, places=2)

    def test_manual_service_schedule_recovers_service_only(self):
        contract = self._create_contract(activate=True)
        service = self.env["tenancy.service.line"].create(
            {
                "tenancy_id": contract.id,
                "service_id": self.service_product.id,
                "price": 125.0,
                "service_type": "once",
            }
        )
        today = date.today()
        schedule = self.env["rent.invoice"].create(
            {
                "tenancy_id": contract.id,
                "company_id": contract.company_id.id,
                "type": "other",
                "invoice_type": "service",
                "period_start": today,
                "period_end": today,
                "due_date": today,
                "invoice_date": today,
                "description": "Recovered service",
                "amount": 125.0,
                "charge_amount": 125.0,
                "charge_product_id": self.service_product.id,
                "service_line_id": service.id,
            }
        )
        move = schedule._create_account_move()
        self.assertEqual(len(move.invoice_line_ids), 1)
        self.assertEqual(move.invoice_line_ids.product_id, self.service_product)
        self.assertAlmostEqual(move.invoice_line_ids.price_unit, 125.0, places=2)
        self.assertAlmostEqual(schedule.rent_amount, 0.0, places=2)
