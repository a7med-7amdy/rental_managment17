# -*- coding: utf-8 -*-
# Copyright 2020-Today TechKhedut.
# Part of TechKhedut. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.fields import Command


class PropertyPayment(models.TransientModel):
    _name = "property.payment.wizard"
    _description = "Create Additional Rental Invoice"
    _check_company_auto = True

    tenancy_id = fields.Many2one("tenancy.details", string="Tenancy No.", required=True, check_company=True)
    customer_id = fields.Many2one(related="tenancy_id.tenancy_id")
    company_id = fields.Many2one(related="tenancy_id.company_id", store=True)
    currency_id = fields.Many2one(related="company_id.currency_id")
    type = fields.Selection(
        [("deposit", "Deposit"), ("maintenance", "Maintenance"), ("penalty", "Penalty"), ("other", "Other")],
        string="Payment For",
        required=True,
        default="other",
    )
    description = fields.Char(string="Description", required=True, translate=True)
    invoice_date = fields.Date(string="Date", required=True, default=fields.Date.context_today)
    rent_amount = fields.Monetary(related="tenancy_id.total_rent")
    amount = fields.Monetary(string="Amount", required=True)
    rent_invoice_id = fields.Many2one(
        "account.move", string="Invoice", readonly=True, check_company=True
    )
    service_id = fields.Many2one("product.product", string="Product", required=True, check_company=True)
    tax_ids = fields.Many2many(
        "account.tax",
        string="Taxes",
        check_company=True,
        domain="[('type_tax_use', '=', 'sale'), ('company_id', '=', company_id)]",
    )

    @api.model
    def default_get(self, field_names):
        values = super().default_get(field_names)
        contract = self.env["tenancy.details"].browse(self.env.context.get("active_id")).exists()
        if contract:
            values["tenancy_id"] = contract.id
            values["service_id"] = contract.installment_item_id.id
        return values

    @api.constrains("amount", "tax_ids", "company_id")
    def _check_amount(self):
        for wizard in self:
            if wizard.amount <= 0:
                raise ValidationError(_("Invoice amount must be greater than zero."))
            if wizard.tax_ids.filtered(lambda tax: tax.company_id != wizard.company_id):
                raise ValidationError(_("All selected taxes must belong to the rental contract company."))

    def property_payment_action(self):
        self.ensure_one()
        self.env.cr.execute(
            "SELECT id FROM property_payment_wizard WHERE id = %s FOR UPDATE",
            (self.id,),
        )
        self.invalidate_recordset(["rent_invoice_id"])
        if self.rent_invoice_id:
            return {
                "type": "ir.actions.act_window",
                "res_model": "account.move",
                "res_id": self.rent_invoice_id.id,
                "view_mode": "form",
            }
        contract = self.tenancy_id
        if contract.contract_type != "running_contract":
            raise UserError(_("Additional invoices can only be created for a running contract."))
        move_model = self.env["account.move"].with_company(contract.company_id)
        if not move_model.browse().has_access("create"):
            raise UserError(_("Billing invoice creation access is required to create this invoice."))
        schedule = self.env["rent.invoice"].create(
            {
                "tenancy_id": contract.id,
                "company_id": contract.company_id.id,
                "type": self.type,
                "invoice_type": self.type if self.type in ("deposit", "maintenance") else "other",
                "period_start": self.invoice_date,
                "period_end": self.invoice_date,
                "due_date": self.invoice_date,
                "invoice_date": self.invoice_date,
                "amount": self.amount,
                "charge_amount": self.amount,
                "charge_product_id": self.service_id.id,
                "charge_tax_ids": [Command.set(self.tax_ids.ids)],
                "description": self.description,
            }
        )
        move = schedule._create_account_move()
        self.rent_invoice_id = move
        return {
            "type": "ir.actions.act_window",
            "res_model": "account.move",
            "res_id": move.id,
            "view_mode": "form",
        }
