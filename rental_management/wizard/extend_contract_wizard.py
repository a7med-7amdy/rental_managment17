# -*- coding: utf-8 -*-
# Copyright 2020-Today TechKhedut.
# Part of TechKhedut. See LICENSE file for full copyright and licensing details.

from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.fields import Command


class ExtendContract(models.TransientModel):
    _name = "extend.contract.wizard"
    _description = "Renew Rental Contract"
    _check_company_auto = True

    tenancy_id = fields.Many2one("tenancy.details", string="Tenancy", required=True, check_company=True)
    customer_id = fields.Many2one(related="tenancy_id.tenancy_id", string="Customer")
    property_id = fields.Many2one(related="tenancy_id.property_id", string="Property")
    duration_id = fields.Many2one("contract.duration", string="Renewal Duration", required=True)
    month = fields.Integer(related="duration_id.month")
    start_date = fields.Date(string="Start Date", required=True)
    invoice_start_date = fields.Date(string="Invoice Start From", required=True)
    company_id = fields.Many2one(related="tenancy_id.company_id", store=True)
    currency_id = fields.Many2one(related="company_id.currency_id")
    revised_price = fields.Monetary(string="Revised Rent", required=True)
    is_any_broker = fields.Boolean(related="tenancy_id.is_any_broker")
    new_broker_id = fields.Many2one("res.partner", string="Broker", domain="[('user_type', '=', 'broker')]")
    payment_term = fields.Selection(related="tenancy_id.payment_term", readonly=False, required=True)
    installment_mode = fields.Selection(related="tenancy_id.type", readonly=False, required=True)

    @api.model
    def default_get(self, field_names):
        values = super().default_get(field_names)
        contract = self.env["tenancy.details"].browse(self.env.context.get("active_id")).exists()
        if contract:
            next_day = contract.end_date + relativedelta(days=1)
            values.update(
                {
                    "tenancy_id": contract.id,
                    "duration_id": contract.duration_id.id,
                    "start_date": next_day,
                    "invoice_start_date": next_day,
                    "revised_price": contract.total_rent,
                    "new_broker_id": contract.broker_id.id,
                    "payment_term": contract.payment_term,
                    "installment_mode": contract.type,
                }
            )
        return values

    @api.onchange("tenancy_id")
    def revised_price_relate(self):
        for wizard in self:
            if wizard.tenancy_id:
                wizard.revised_price = wizard.tenancy_id.total_rent
                wizard.duration_id = wizard.tenancy_id.duration_id
                wizard.new_broker_id = wizard.tenancy_id.broker_id
                wizard.start_date = wizard.tenancy_id.end_date + relativedelta(days=1)
                wizard.invoice_start_date = wizard.start_date

    @api.constrains("start_date", "invoice_start_date", "revised_price")
    def _check_renewal_values(self):
        for wizard in self:
            if wizard.revised_price <= 0:
                raise ValidationError(_("Revised rent must be greater than zero."))
            if wizard.tenancy_id and wizard.start_date <= wizard.tenancy_id.end_date:
                raise ValidationError(_("A renewed contract must start after the old contract end date."))
            if wizard.invoice_start_date < wizard.start_date:
                raise ValidationError(_("Invoice start date cannot be before the renewal start date."))

    def extend_contract_action(self):
        self.ensure_one()
        old = self.tenancy_id
        if old.contract_type not in ("running_contract", "expire_contract", "close_contract"):
            raise UserError(_("Only running, expired, or closed contracts can be renewed."))

        service_commands = [
            Command.create(
                {
                    "service_id": line.service_id.id,
                    "price": line.price,
                    "service_type": line.service_type,
                }
            )
            for line in old.extra_services_ids
        ]
        vals = {
            "tenancy_id": old.tenancy_id.id,
            "property_id": old.property_id.id,
            "company_id": old.company_id.id,
            "responsible_id": old.responsible_id.id,
            "duration_id": self.duration_id.id,
            "start_date": self.start_date,
            "invoice_start_date": self.invoice_start_date,
            "total_rent": self.revised_price,
            "payment_term": self.payment_term,
            "invoice_payment_term_id": old.invoice_payment_term_id.id,
            "type": self.installment_mode,
            "contract_type": "new_contract",
            "previous_contract_id": old.id,
            "is_extended": True,
            "extend_from": old.tenancy_seq,
            "is_any_deposit": old.is_any_deposit,
            "deposit_amount": old.deposit_amount,
            "is_any_broker": old.is_any_broker,
            "broker_id": self.new_broker_id.id,
            "rent_type": old.rent_type,
            "commission_type": old.commission_type,
            "commission_from": old.commission_from,
            "broker_commission": old.broker_commission,
            "broker_commission_percentage": old.broker_commission_percentage,
            "installment_item_id": old.installment_item_id.id,
            "deposit_item_id": old.deposit_item_id.id,
            "broker_item_id": old.broker_item_id.id,
            "maintenance_item_id": old.maintenance_item_id.id,
            "instalment_tax": old.instalment_tax,
            "deposit_tax": old.deposit_tax,
            "service_tax": old.service_tax,
            "tax_ids": [Command.set(old.tax_ids.ids)],
            "extra_services_ids": service_commands,
            "agreement": old.agreement,
            "term_condition": old.term_condition,
        }
        new_contract = self.env["tenancy.details"].create(vals)
        new_contract._check_no_overlap()
        old.write(
            {
                "extended": True,
                "new_contract_id": new_contract.id,
                "extend_ref": new_contract.tenancy_seq,
            }
        )
        old.message_post(body=_("Renewal draft %s created.") % new_contract.tenancy_seq)
        new_contract.message_post(body=_("Created as a renewal of %s.") % old.tenancy_seq)
        return {
            "type": "ir.actions.act_window",
            "name": _("Renewed Contract"),
            "res_model": "tenancy.details",
            "res_id": new_contract.id,
            "view_mode": "form",
            "target": "current",
        }
