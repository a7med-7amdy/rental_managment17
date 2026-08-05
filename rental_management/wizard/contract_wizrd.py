# -*- coding: utf-8 -*-
# Copyright 2020-Today TechKhedut.
# Part of TechKhedut. See LICENSE file for full copyright and licensing details.

from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.fields import Command


class ContractWizard(models.TransientModel):
    """Create exactly one draft rental contract from a property or inquiry."""

    _name = "contract.wizard"
    _description = "Create Rental Contract"
    _check_company_auto = True

    customer_id = fields.Many2one(
        "res.partner", string="Customer", domain="[('user_type', '=', 'customer')]", required=True
    )
    currency_id = fields.Many2one("res.currency", related="company_id.currency_id")
    company_id = fields.Many2one(
        "res.company", string="Company", required=True, default=lambda self: self.env.company
    )

    is_any_deposit = fields.Boolean(string="Deposit")
    deposit_amount = fields.Monetary(string="Security Deposit")

    property_id = fields.Many2one(
        "property.details",
        string="Property",
        required=True,
        check_company=True,
        domain="[('stage', '=', 'available'), ('company_id', '=', company_id)]",
    )
    rent_unit = fields.Selection(related="property_id.rent_unit")
    total_rent = fields.Monetary(related="property_id.price", string="Rent", readonly=False)
    is_extra_service = fields.Boolean(related="property_id.is_extra_service")
    services = fields.Text(string="Utility Services", compute="_compute_services", translate=True)
    is_any_maintenance = fields.Boolean(related="property_id.is_maintenance_service")
    maintenance_rent_type = fields.Selection(related="property_id.maintenance_rent_type")
    total_maintenance = fields.Monetary(related="property_id.total_maintenance")

    payment_term = fields.Selection(
        [
            ("monthly", "Monthly"),
            ("quarterly", "Quarterly"),
            ("year", "Yearly"),
            ("full_payment", "Full Payment"),
        ],
        string="Payment Term",
        required=True,
        default="monthly",
    )
    duration_ids = fields.Many2many("contract.duration", compute="compute_durations")
    duration_id = fields.Many2one(
        "contract.duration", string="Duration", required=True, domain="[('id', 'in', duration_ids)]"
    )
    start_date = fields.Date(string="Start Date", required=True, default=fields.Date.context_today)
    invoice_start_date = fields.Date(
        string="Invoice Start From", required=True, default=fields.Date.context_today
    )
    installment_mode = fields.Selection(
        [("automatic", "Automatic Installments"), ("manual", "Manual Installments")],
        default="automatic",
        required=True,
    )

    is_any_broker = fields.Boolean(string="Any Broker?")
    broker_id = fields.Many2one("res.partner", string="Broker", domain="[('user_type', '=', 'broker')]")
    rent_type = fields.Selection(
        [("once", "One Period"), ("e_rent", "All Contract Periods")], string="Brokerage Type"
    )
    commission_type = fields.Selection([("f", "Fixed"), ("p", "Percentage")])
    commission_from = fields.Selection(
        [
            ("both", "Landlord and Tenant"),
            ("customer", "Tenant"),
            ("landlord", "Landlord"),
            ("landlord_and_customer", "Landlord and Tenant (Legacy)"),
        ],
        default="both",
        string="Commission From",
    )
    broker_commission = fields.Monetary(string="Commission")
    broker_commission_percentage = fields.Float(string="Percentage")

    from_inquiry = fields.Boolean("From Enquiry")
    lead_id = fields.Many2one("crm.lead", string="Enquiry", domain="[('property_id', '=', property_id)]")
    inquiry_id = fields.Many2one("tenancy.inquiry", string="Inquiry")
    note = fields.Text(string="Note", translate=True)

    agreement = fields.Html(string="Agreement")
    agreement_template_id = fields.Many2one(
        "agreement.template", string="Agreement Template", domain="[('company_id', '=', company_id)]"
    )
    installment_item_id = fields.Many2one("product.product", string="Installment Item", check_company=True)
    deposit_item_id = fields.Many2one("product.product", string="Deposit Item", check_company=True)
    broker_item_id = fields.Many2one("product.product", string="Broker Item", check_company=True)
    maintenance_item_id = fields.Many2one(
        "product.product",
        string="Maintenance Item",
        check_company=True,
        domain="[('product_tmpl_id.is_maintenance', '=', True)]",
    )

    instalment_tax = fields.Boolean(string="Taxes on Installment?")
    deposit_tax = fields.Boolean(string="Taxes on Deposit?")
    service_tax = fields.Boolean(string="Taxes on Services?")
    tax_ids = fields.Many2many(
        "account.tax",
        string="Taxes",
        check_company=True,
        domain="[('type_tax_use', '=', 'sale'), ('company_id', '=', company_id)]",
    )
    term_condition = fields.Html(string="Term and Condition")
    is_contract_extend = fields.Boolean(string="Extend Contract")

    @api.model
    def default_get(self, field_names):
        values = super().default_get(field_names)
        active_model = self.env.context.get("active_model")
        active_id = self.env.context.get("active_id")
        rent_product = self.env.ref("rental_management.property_product_1", raise_if_not_found=False)
        deposit_product = self.env.ref("rental_management.property_product_2", raise_if_not_found=False)
        values.setdefault("installment_item_id", rent_product.id if rent_product else False)
        values.setdefault("deposit_item_id", deposit_product.id if deposit_product else False)
        values.setdefault("broker_item_id", rent_product.id if rent_product else False)

        if active_model == "property.details" and active_id:
            property_record = self.env["property.details"].browse(active_id).exists()
            if property_record:
                values.update(
                    {
                        "property_id": property_record.id,
                        "company_id": property_record.company_id.id,
                        "total_rent": property_record.price,
                    }
                )
                if property_record.rent_unit == "Day":
                    values["payment_term"] = "full_payment"
                elif property_record.rent_unit == "Year":
                    values["payment_term"] = "year"
        elif active_model == "tenancy.details" and active_id:
            old = self.env["tenancy.details"].browse(active_id).exists()
            if old:
                values.update(
                    {
                        "property_id": old.property_id.id,
                        "company_id": old.company_id.id,
                        "customer_id": old.tenancy_id.id,
                        "start_date": old.end_date + relativedelta(days=1),
                        "invoice_start_date": old.end_date + relativedelta(days=1),
                        "is_contract_extend": True,
                        "installment_item_id": old.installment_item_id.id,
                        "deposit_item_id": old.deposit_item_id.id,
                        "broker_item_id": old.broker_item_id.id,
                        "maintenance_item_id": old.maintenance_item_id.id,
                        "is_any_deposit": old.is_any_deposit,
                        "deposit_amount": old.deposit_amount,
                        "payment_term": old.payment_term,
                        "is_any_broker": old.is_any_broker,
                        "broker_id": old.broker_id.id,
                        "commission_from": old.commission_from,
                        "rent_type": old.rent_type,
                        "commission_type": old.commission_type,
                        "broker_commission_percentage": old.broker_commission_percentage,
                        "broker_commission": old.broker_commission,
                        "term_condition": old.term_condition,
                        "agreement": old.agreement,
                        "total_rent": old.total_rent,
                        "installment_mode": old.type,
                    }
                )
        return values

    @api.depends("payment_term", "rent_unit")
    def compute_durations(self):
        duration_model = self.env["contract.duration"]
        for wizard in self:
            domain = [("month", ">", 0)]
            if wizard.rent_unit:
                domain.append(("rent_unit", "=", wizard.rent_unit))
            if wizard.payment_term == "quarterly" and wizard.rent_unit == "Month":
                domain.append(("month", ">=", 3))
            wizard.duration_ids = duration_model.search(domain)

    @api.onchange("payment_term", "property_id")
    def onchange_payment_term(self):
        for wizard in self:
            wizard.duration_id = False
            if wizard.property_id:
                wizard.company_id = wizard.property_id.company_id
                wizard.total_rent = wizard.property_id.price
                if not wizard.start_date:
                    wizard.start_date = fields.Date.context_today(wizard)
                if not wizard.invoice_start_date:
                    wizard.invoice_start_date = wizard.start_date

    @api.onchange("agreement_template_id")
    def _onchange_agreement_template_id(self):
        for wizard in self:
            wizard.agreement = wizard.agreement_template_id.agreement

    @api.onchange("lead_id")
    def _onchange_tenancy_inquiry(self):
        for wizard in self:
            if wizard.from_inquiry and wizard.lead_id:
                wizard.note = wizard.lead_id.description
                wizard.customer_id = wizard.lead_id.partner_id

    @api.depends("property_id", "property_id.extra_service_ids")
    def _compute_services(self):
        for wizard in self:
            lines = []
            for service in wizard.property_id.extra_service_ids:
                kind = _("Once") if service.service_type == "once" else _("Recurring")
                lines.append(
                    "%s [%s] - %s %s"
                    % (
                        service.service_id.display_name,
                        kind,
                        wizard.currency_id.symbol or "",
                        service.price,
                    )
                )
            wizard.services = "\n".join(lines)

    @api.constrains("broker_commission", "broker_commission_percentage", "deposit_amount")
    def _check_non_negative_values(self):
        for wizard in self:
            if wizard.deposit_amount < 0 or wizard.broker_commission < 0:
                raise ValidationError(_("Deposit and commission values cannot be negative."))
            if not 0 <= wizard.broker_commission_percentage <= 100:
                raise ValidationError(_("Commission percentage must be between 0 and 100."))

    def check_contract_start_date(self):
        self.ensure_one()
        if self.start_date and self.start_date < fields.Date.context_today(self):
            return True
        return True

    def get_contract_info(self):
        self.ensure_one()
        commission_from = "both" if self.commission_from == "landlord_and_customer" else self.commission_from
        services = [
            Command.create(
                {
                    "service_id": line.service_id.id,
                    "price": line.price,
                    "service_type": line.service_type,
                }
            )
            for line in self.property_id.extra_service_ids
        ]
        vals = {
            "tenancy_id": self.customer_id.id,
            "company_id": self.company_id.id,
            "property_id": self.property_id.id,
            "duration_id": self.duration_id.id,
            "start_date": self.start_date,
            "invoice_start_date": self.invoice_start_date,
            "total_rent": self.total_rent,
            "payment_term": self.payment_term,
            "type": self.installment_mode,
            "contract_type": "new_contract",
            "is_any_deposit": self.is_any_deposit,
            "deposit_amount": self.deposit_amount,
            "is_any_broker": self.is_any_broker,
            "broker_id": self.broker_id.id,
            "rent_type": self.rent_type,
            "commission_type": self.commission_type,
            "commission_from": commission_from,
            "broker_commission": self.broker_commission,
            "broker_commission_percentage": self.broker_commission_percentage,
            "agreement": self.agreement,
            "term_condition": self.term_condition,
            "installment_item_id": self.installment_item_id.id,
            "deposit_item_id": self.deposit_item_id.id,
            "broker_item_id": self.broker_item_id.id,
            "maintenance_item_id": self.maintenance_item_id.id,
            "instalment_tax": self.instalment_tax,
            "deposit_tax": self.deposit_tax,
            "service_tax": self.service_tax,
            "tax_ids": [Command.set(self.tax_ids.ids)],
            "extra_services_ids": services,
        }
        old = self.env["tenancy.details"].browse(self.env.context.get("active_id")).exists()
        if self.is_contract_extend and old and self.env.context.get("active_model") == "tenancy.details":
            vals.update(
                {
                    "previous_contract_id": old.id,
                    "is_extended": True,
                    "extend_from": old.tenancy_seq,
                }
            )
        return vals

    def contract_action(self):
        self.ensure_one()
        if self.property_id.stage != "available" and not self.is_contract_extend:
            raise UserError(_("Only an available property can be selected for a new rental contract."))
        if self.property_id.company_id != self.company_id:
            raise ValidationError(_("Property and contract company must match."))
        contract = self.env["tenancy.details"].create(self.get_contract_info())
        old = contract.previous_contract_id
        if old:
            old.write(
                {
                    "extended": True,
                    "new_contract_id": contract.id,
                    "extend_ref": contract.tenancy_seq,
                }
            )
        self.customer_id.user_type = "customer"
        if self.lead_id:
            self.lead_id.message_post(body=_("A draft rental contract was created from this enquiry."))
        return {
            "type": "ir.actions.act_window",
            "name": _("Rental Contract"),
            "res_model": "tenancy.details",
            "res_id": contract.id,
            "view_mode": "form",
            "target": "current",
        }

    def action_create_full_payment_invoice(self, contract_id):
        """Legacy compatibility: activate the single supplied contract using the unified engine."""
        contract = self.env["tenancy.details"].browse(contract_id).exists()
        if not contract:
            raise UserError(_("The rental contract no longer exists."))
        contract.action_activate_contract()
        return contract.rent_invoice_ids.mapped("rent_invoice_id")[:1]
