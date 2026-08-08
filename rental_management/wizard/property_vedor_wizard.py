# -*- coding: utf-8 -*-
# Copyright 2020-Today TechKhedut.
# Part of TechKhedut. See LICENSE file for full copyright and licensing details.

import math

from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.fields import Command


class PropertySold(models.TransientModel):
    _name = "property.vendor.wizard"
    _description = "Complete Property Sale"
    _check_company_auto = True

    company_id = fields.Many2one(
        "res.company", string="Company", required=True, default=lambda self: self.env.company
    )
    currency_id = fields.Many2one("res.currency", related="company_id.currency_id", string="Currency")
    property_id = fields.Many2one(
        "property.details", string="Property", required=True, check_company=True
    )
    customer_id = fields.Many2one(
        "property.vendor", string="Customer", required=True, check_company=True
    )
    final_price = fields.Monetary(string="Final Price", required=True)
    sold_invoice_id = fields.Many2one("account.move", check_company=True)
    broker_id = fields.Many2one(related="customer_id.broker_id")
    is_any_broker = fields.Boolean(related="customer_id.is_any_broker")
    # Legacy field retained for XML/data compatibility. Quarterly count is now
    # derived from duration rather than this arbitrary value.
    quarter = fields.Integer(string="Quarter", default=4)

    duration_id = fields.Many2one(
        "contract.duration", string="Duration", domain="[('rent_unit','=','Month')]"
    )
    payment_term = fields.Selection(
        [("monthly", "Monthly"), ("full_payment", "Full Payment"), ("quarterly", "Quarterly")],
        string="Payment Term",
        required=True,
    )
    start_date = fields.Date(string="Start From")

    installment_item_id = fields.Many2one(
        "product.product",
        string="Installment Item",
        required=True,
        check_company=True,
        default=lambda self: self.env.ref(
            "rental_management.property_product_1", raise_if_not_found=False
        ),
    )
    is_taxes = fields.Boolean(string="Taxes ?")
    taxes_ids = fields.Many2many(
        "account.tax",
        string="Taxes",
        check_company=True,
        domain="[('type_tax_use', '=', 'sale'), ('company_id', '=', company_id)]",
    )

    @api.model
    def default_get(self, field_list):
        res = super().default_get(field_list)
        sale = self.env["property.vendor"].browse(self.env.context.get("active_id")).exists()
        if sale:
            res.update(
                {
                    "customer_id": sale.id,
                    "company_id": sale.company_id.id,
                    "final_price": sale.ask_price or sale.property_id.price,
                    "is_taxes": sale.is_taxes,
                    "taxes_ids": [Command.set(sale.taxes_ids.ids)],
                    "property_id": sale.property_id.id,
                    "installment_item_id": sale.installment_item_id.id,
                }
            )
        return res

    @api.onchange("payment_term")
    def _onchange_payment_term(self):
        if self.payment_term == "quarterly":
            return {"domain": {"duration_id": [("rent_unit", "=", "Month"), ("month", ">=", 3)]}}
        return {"domain": {"duration_id": [("rent_unit", "=", "Month")]}}

    def _create_broker_accounting_documents(self, sale):
        self.ensure_one()
        if not sale.is_any_broker:
            return
        if not sale.broker_id or not sale.broker_item_id or not sale.commission_from:
            raise ValidationError(_("Complete broker, commission source and broker product information."))
        if sale.broker_final_commission <= 0:
            raise ValidationError(_("Broker commission must be greater than zero."))
        move_model = self.env["account.move"].with_company(sale.company_id)
        if not move_model.browse().has_access("create"):
            raise UserError(
                _("Billing invoice creation access is required to create sale broker accounting documents.")
            )
        today = fields.Date.context_today(self)
        line_vals = {
            "product_id": sale.broker_item_id.id,
            "name": _("Commission of %s") % sale.property_id.display_name,
            "quantity": 1.0,
            "price_unit": sale.broker_final_commission,
        }
        if not sale.broker_bill_id:
            bill = move_model.create(
                {
                    "partner_id": sale.broker_id.id,
                    "move_type": "in_invoice",
                    "invoice_date": today,
                    "company_id": sale.company_id.id,
                    "currency_id": sale.currency_id.id,
                    "invoice_origin": sale.sold_seq,
                    "sold_id": sale.id,
                    "invoice_line_ids": [Command.create(line_vals)],
                }
            )
            sale.broker_bill_id = bill
        source_partner = sale.customer_id if sale.commission_from == "customer" else sale.landlord_id
        if not source_partner:
            raise ValidationError(_("The selected commission source partner is missing."))
        if not sale.broker_invoice_id:
            charge_vals = {
                "partner_id": source_partner.id,
                "move_type": "out_invoice",
                "invoice_date": today,
                "company_id": sale.company_id.id,
                "currency_id": sale.currency_id.id,
                "invoice_origin": sale.sold_seq,
                "sold_id": sale.id,
                "invoice_line_ids": [Command.create(line_vals)],
            }
            fiscal_position = source_partner.with_company(sale.company_id).property_account_position_id
            if fiscal_position:
                charge_vals["fiscal_position_id"] = fiscal_position.id
            sale.broker_invoice_id = move_model.create(charge_vals)

        if self.env["ir.config_parameter"].sudo().get_param(
            "rental_management.invoice_post_type", "manual"
        ) == "automatically":
            for move in (sale.broker_bill_id | sale.broker_invoice_id).filtered(
                lambda record: record.state == "draft"
            ):
                move.action_post()

    def _prepare_installment_values(self, sale):
        self.ensure_one()
        amount_total = sale.payable_amount
        if amount_total < 0:
            raise ValidationError(_("The remaining sale amount cannot be negative."))
        if sale.currency_id.is_zero(amount_total):
            return []
        values = []
        if self.payment_term == "full_payment":
            values.append(
                {
                    "name": _("Full Payment"),
                    "property_sold_id": sale.id,
                    "company_id": sale.company_id.id,
                    "invoice_date": self.start_date or fields.Date.context_today(self),
                    "amount": amount_total,
                    "tax_ids": [Command.set(self.taxes_ids.ids if self.is_taxes else [])],
                    "is_remain_invoice": True,
                }
            )
            return values

        if not self.duration_id or not self.start_date:
            raise ValidationError(_("Select a duration and installment start date."))
        months = self.duration_id.month
        if months <= 0:
            raise ValidationError(_("Sale installment duration must be greater than zero."))
        step_months = 1 if self.payment_term == "monthly" else 3
        count = months if step_months == 1 else math.ceil(months / 3.0)
        if count <= 0:
            raise ValidationError(_("The selected payment term produced no installments."))
        base_amount = sale.currency_id.round(amount_total / count) if count else amount_total
        allocated = 0.0
        for index in range(count):
            installment_amount = (
                amount_total - allocated if index == count - 1 else base_amount
            )
            allocated += installment_amount
            values.append(
                {
                    "name": _("%(number)s %(kind)s")
                    % {
                        "number": index + 1,
                        "kind": _("Installment") if step_months == 1 else _("Quarter Payment"),
                    },
                    "property_sold_id": sale.id,
                    "company_id": sale.company_id.id,
                    "invoice_date": self.start_date + relativedelta(months=index * step_months),
                    "amount": installment_amount,
                    "tax_ids": [Command.set(self.taxes_ids.ids if self.is_taxes else [])],
                }
            )
        return values

    def property_sale_action(self):
        self.ensure_one()
        sale = self.customer_id
        if not sale:
            raise UserError(_("No property sale record was selected."))
        self.env.cr.execute("SELECT id FROM property_vendor WHERE id = %s FOR UPDATE", (sale.id,))
        sale.invalidate_recordset(["stage", "sale_invoice_ids"])
        if sale.stage == "sold":
            raise UserError(_("This property sale is already completed."))
        if sale.property_id != self.property_id or sale.company_id != self.company_id:
            raise ValidationError(_("The property sale, property and wizard must belong together."))
        if sale.property_id.sale_lease != "for_sale":
            raise ValidationError(_("The property is not configured for sale."))
        if self.final_price <= 0:
            raise ValidationError(_("The final sale price must be greater than zero."))
        if self.taxes_ids.filtered(lambda tax: tax.company_id != self.company_id):
            raise ValidationError(_("All selected taxes must belong to the sale company."))
        if sale.sale_invoice_ids:
            raise UserError(
                _("Sale installment schedules already exist. Review them instead of generating a second plan.")
            )

        with self.env.cr.savepoint():
            sale.write(
                {
                    "installment_item_id": self.installment_item_id.id,
                    "is_taxes": self.is_taxes,
                    "taxes_ids": [Command.set(self.taxes_ids.ids)],
                    "sale_price": self.final_price,
                    "payment_term": self.payment_term,
                }
            )
            if sale.book_price > sale.total_sell_amount:
                raise ValidationError(
                    _("The booking amount cannot exceed the final property sale amount.")
                )
            self._create_broker_accounting_documents(sale)
            schedule_vals = self._prepare_installment_values(sale)
            schedules = self.env["sale.invoice"].create(schedule_vals) if schedule_vals else self.env["sale.invoice"]

            # For full payment, create immediately when the operator has Billing
            # access; otherwise the normal sale cron will pick up the due schedule.
            if self.payment_term == "full_payment" and schedules and self.env["account.move"].browse().has_access("create"):
                schedules[0].action_create_invoice()

            sale.customer_id.is_sold_customer = True
            sale.with_context(allow_sale_state_write=True).write({"stage": "sold"})
            sale.property_id.write({"stage": "sold", "sold_booking_id": sale.id})
            if sale.customer_id.email:
                sale.send_sold_mail()

        return {
            "type": "ir.actions.act_window",
            "name": _("Property Sale"),
            "res_model": "property.vendor",
            "res_id": sale.id,
            "view_mode": "form",
            "target": "current",
        }
