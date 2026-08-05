# -*- coding: utf-8 -*-
# Copyright 2020-Today TechKhedut.
# Part of TechKhedut. See LICENSE file for full copyright and licensing details.

import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.fields import Command

_logger = logging.getLogger(__name__)


class RentInvoice(models.Model):
    """A unique rental installment or charge period linked to an Odoo invoice."""

    _name = "rent.invoice"
    _description = "Rental Invoice Schedule"
    _rec_name = "tenancy_id"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "due_date, period_start, id"

    tenancy_id = fields.Many2one(
        "tenancy.details",
        string="Rental Contract",
        required=True,
        ondelete="cascade",
        index=True,
        check_company=True,
        tracking=True,
    )
    customer_id = fields.Many2one(
        related="tenancy_id.tenancy_id",
        string="Customer",
        store=True,
        index=True,
    )
    type = fields.Selection(
        [
            ("deposit", "Deposit"),
            ("rent", "Rent"),
            ("maintenance", "Maintenance"),
            ("penalty", "Penalty"),
            ("full_rent", "Full Rent"),
            ("broker", "Broker Commission"),
            ("other", "Other"),
        ],
        string="Payment",
        default="rent",
        required=True,
        index=True,
        tracking=True,
    )
    invoice_type = fields.Selection(
        [
            ("rent", "Rent Period"),
            ("full_rent", "Full Contract"),
            ("deposit", "Security Deposit"),
            ("service", "Extra Service"),
            ("maintenance", "Maintenance"),
            ("broker", "Broker Commission"),
            ("other", "Other"),
        ],
        string="Logical Invoice Type",
        default="rent",
        required=True,
        index=True,
        help="Used with the contract period to prevent duplicate invoices.",
    )
    period_start = fields.Date(string="Period Start", index=True)
    period_end = fields.Date(string="Period End", index=True)
    due_date = fields.Date(string="Due Date", index=True)
    invoice_date = fields.Date(string="Invoice Date", index=True)
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        required=True,
        default=lambda self: self.env.company,
        index=True,
    )
    currency_id = fields.Many2one(
        "res.currency",
        related="company_id.currency_id",
        string="Currency",
        store=True,
    )
    installment_type = fields.Selection(related="tenancy_id.type", store=True)

    amount = fields.Monetary(string="Rent Amount", tracking=True)
    rent_amount = fields.Monetary(string="Base Rent Amount")
    description = fields.Char(string="Description", translate=True)
    rent_invoice_id = fields.Many2one(
        "account.move",
        string="Invoice",
        copy=False,
        index=True,
        check_company=True,
        tracking=True,
    )
    payment_state = fields.Selection(
        related="rent_invoice_id.payment_state",
        string="Payment Status",
        store=True,
    )
    landlord_id = fields.Many2one(
        related="tenancy_id.property_id.landlord_id",
        store=True,
        index=True,
    )
    is_yearly = fields.Boolean()
    remain = fields.Integer(
        help="Legacy partial-period quantity retained for upgrade compatibility."
    )
    tenancy_type = fields.Selection(related="tenancy_id.type", string="Rent Type")
    service_amount = fields.Monetary(
        string="Extra Amount",
        help="Recurring utility and maintenance services included in the invoice.",
    )
    is_extra_service = fields.Boolean(related="tenancy_id.is_extra_service")

    _rental_period_unique = models.Constraint(
        "UNIQUE(tenancy_id, period_start, period_end, invoice_type)",
        "An invoice schedule already exists for this contract, period, and type.",
    )
    _rental_period_dates_valid = models.Constraint(
        "CHECK(period_end IS NULL OR period_start IS NULL OR period_end >= period_start)",
        "The rental invoice period end must not be before its start.",
    )

    @api.model_create_multi
    def create(self, vals_list):
        """Normalize company, dates and logical type for legacy and new callers."""
        for vals in vals_list:
            tenancy = self.env["tenancy.details"].browse(vals.get("tenancy_id")).exists()
            if tenancy:
                vals.setdefault("company_id", tenancy.company_id.id)
                vals.setdefault("invoice_date", vals.get("due_date") or tenancy.invoice_start_date)
                vals.setdefault("due_date", vals.get("invoice_date") or tenancy.invoice_start_date)
            vals.setdefault(
                "invoice_type",
                "full_rent" if vals.get("type") == "full_rent" else vals.get("type", "rent"),
            )
        return super().create(vals_list)

    @api.constrains("tenancy_id", "company_id", "rent_invoice_id")
    def _check_company_consistency(self):
        for record in self:
            if record.tenancy_id and record.company_id != record.tenancy_id.company_id:
                raise ValidationError(_("The installment company must match the contract company."))
            if record.rent_invoice_id and record.rent_invoice_id.company_id != record.company_id:
                raise ValidationError(_("The accounting invoice company must match the installment company."))

    def action_create_invoice(self):
        """Create one accounting invoice for this schedule line, idempotently."""
        for schedule in self:
            schedule._create_account_move()
        return True

    def _create_account_move(self):
        self.ensure_one()
        if self.rent_invoice_id:
            return self.rent_invoice_id
        if self.tenancy_id.contract_type in ("close_contract", "cancel_contract"):
            raise UserError(_("New rental invoices cannot be created for a closed or cancelled contract."))
        if not self.customer_id:
            raise UserError(_("Set a tenant before creating the rental invoice."))

        lines, breakdown = self.tenancy_id._prepare_period_invoice_lines(self)
        if not lines:
            raise UserError(_("There are no invoiceable amounts for this rental period."))

        move_vals = self.tenancy_id._prepare_rent_invoice_vals(self, lines)
        move = self.env["account.move"].with_company(self.company_id).create(move_vals)
        self.write(
            {
                "rent_invoice_id": move.id,
                "invoice_date": move.invoice_date,
                "amount": move.amount_total,
                "rent_amount": breakdown.get("rent", 0.0),
                "service_amount": breakdown.get("services", 0.0)
                + breakdown.get("maintenance", 0.0),
            }
        )
        if self.tenancy_id._get_invoice_post_type() == "automatically":
            move.action_post()
        self.tenancy_id.last_invoice_payment_date = self.due_date or move.invoice_date
        self.tenancy_id.message_post(
            body=_("Rental invoice %(invoice)s created for %(start)s to %(end)s.")
            % {
                "invoice": move.display_name,
                "start": self.period_start or "-",
                "end": self.period_end or "-",
            }
        )
        return move

    @api.model
    def _cron_create_due_invoices(self, batch_size=200):
        """Create every missed automatic installment whose due date is today or earlier."""
        today = fields.Date.context_today(self)
        contracts = self.env["tenancy.details"].search(
            [
                ("contract_type", "in", ["running_contract", "expire_contract"]),
                ("type", "=", "automatic"),
                ("start_date", "<=", today),
            ],
            order="id",
        )
        for contract in contracts:
            try:
                with self.env.cr.savepoint():
                    contract._ensure_installment_schedule()
            except Exception:
                _logger.exception("Unable to prepare invoice schedule for contract %s", contract.display_name)

        domain = [
            ("rent_invoice_id", "=", False),
            ("installment_type", "=", "automatic"),
            ("due_date", "<=", today),
            ("tenancy_id.contract_type", "in", ["running_contract", "expire_contract"]),
        ]
        due_lines = self.search(domain, order="due_date, id", limit=batch_size)
        for line in due_lines:
            try:
                with self.env.cr.savepoint():
                    line._create_account_move()
                    line.tenancy_id._send_invoice_reminder_once(line)
            except Exception:
                _logger.exception("Unable to create due rental invoice schedule line %s", line.id)
        return len(due_lines)


class TenancyInvoice(models.Model):
    _inherit = "account.move"

    tenancy_id = fields.Many2one(
        "tenancy.details",
        readonly=True,
        string="Rent Contract Ref.",
        store=True,
        index=True,
        check_company=True,
    )
    rental_schedule_id = fields.Many2one(
        "rent.invoice",
        string="Rental Schedule",
        readonly=True,
        copy=False,
        index=True,
        check_company=True,
    )
    sale_schedule_id = fields.Many2one(
        "sale.invoice",
        string="Sale Installment Schedule",
        readonly=True,
        copy=False,
        index=True,
        check_company=True,
    )
    sold_id = fields.Many2one(
        "property.vendor",
        string="Sold Information",
        readonly=True,
        store=True,
        index=True,
        check_company=True,
    )
    tenancy_property_id = fields.Many2one(
        related="tenancy_id.property_id", string="Property", store=True
    )
    sold_property_id = fields.Many2one(related="sold_id.property_id", string="Property ")
    maintenance_request_id = fields.Many2one(
        "maintenance.request", string="Maintenance Ref.", check_company=True
    )

    _rental_schedule_unique = models.UniqueIndex(
        "(rental_schedule_id) WHERE rental_schedule_id IS NOT NULL",
        "A rental schedule can be linked to only one accounting invoice.",
    )
    _sale_schedule_unique = models.UniqueIndex(
        "(sale_schedule_id) WHERE sale_schedule_id IS NOT NULL",
        "A sale installment schedule can be linked to only one accounting invoice.",
    )
