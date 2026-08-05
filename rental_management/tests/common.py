from datetime import timedelta

from odoo import Command, fields
from odoo.addons.account.tests.common import AccountTestInvoicingCommon


class RentalCommon(AccountTestInvoicingCommon):
    """Shared, accounting-ready rental test data."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env["ir.config_parameter"].sudo().set_param(
            "rental_management.invoice_post_type", "manual"
        )
        cls.landlord = cls.partner_a.copy({"name": "Rental Landlord", "user_type": "landlord"})
        cls.tenant = cls.partner_b.copy({"name": "Rental Tenant", "user_type": "customer"})
        cls.tenant_b = cls.partner_b.copy({"name": "Second Rental Tenant", "user_type": "customer"})
        cls.broker = cls.partner_a.copy({"name": "Rental Broker", "user_type": "broker"})
        cls.rent_product = cls._create_product(
            name="Rent Product", lst_price=1000.0, type="service"
        )
        cls.deposit_product = cls._create_product(
            name="Deposit Product", lst_price=500.0, type="service"
        )
        cls.broker_product = cls._create_product(
            name="Broker Product", lst_price=250.0, type="service"
        )
        cls.service_product = cls._create_product(
            name="Recurring Service", lst_price=100.0, type="service",
            is_extra_service_product=True,
        )
        cls.maintenance_product = cls._create_product(
            name="Maintenance", lst_price=75.0, type="service"
        )
        cls.maintenance_product.product_tmpl_id.is_maintenance = True

        cls.duration_1m = cls.env["contract.duration"].create(
            {"duration": "1 Month", "month": 1, "rent_unit": "Month"}
        )
        cls.duration_3m = cls.env["contract.duration"].create(
            {"duration": "3 Months", "month": 3, "rent_unit": "Month"}
        )
        cls.duration_4m = cls.env["contract.duration"].create(
            {"duration": "4 Months", "month": 4, "rent_unit": "Month"}
        )
        cls.duration_12m = cls.env["contract.duration"].create(
            {"duration": "12 Months", "month": 12, "rent_unit": "Month"}
        )
        cls.duration_1y = cls.env["contract.duration"].create(
            {"duration": "1 Year", "month": 1, "rent_unit": "Year"}
        )
        cls.property = cls._create_property("Rental Unit A")

    @classmethod
    def _create_property(cls, name, company=None, stage="available"):
        company = company or cls.env.company
        return cls.env["property.details"].with_company(company).create(
            {
                "name": name,
                "type": "residential",
                "sale_lease": "for_tenancy",
                "stage": stage,
                "company_id": company.id,
                "responsible_id": cls.env.user.id,
                "landlord_id": cls.landlord.id,
                "rent_unit": "Month",
                "price": 1000.0,
            }
        )

    @classmethod
    def _contract_values(cls, **overrides):
        start = overrides.pop("start_date", fields.Date.today() - timedelta(days=60))
        property_record = overrides.pop("property_id", cls.property)
        values = {
            "property_id": property_record.id,
            "tenancy_id": cls.tenant.id,
            "company_id": property_record.company_id.id,
            "responsible_id": cls.env.user.id,
            "duration_id": cls.duration_3m.id,
            "start_date": start,
            "invoice_start_date": start,
            "total_rent": 1000.0,
            "payment_term": "monthly",
            "type": "manual",
            "installment_item_id": cls.rent_product.id,
            "deposit_item_id": cls.deposit_product.id,
            "broker_item_id": cls.broker_product.id,
            "maintenance_item_id": cls.maintenance_product.id,
            "invoice_payment_term_id": cls.pay_terms_a.id,
        }
        values.update(overrides)
        return values

    @classmethod
    def _create_contract(cls, activate=False, **overrides):
        contract = cls.env["tenancy.details"].create(cls._contract_values(**overrides))
        if activate:
            contract.action_activate_contract()
        return contract

    @staticmethod
    def yesterday():
        return fields.Date.today() - timedelta(days=1)
