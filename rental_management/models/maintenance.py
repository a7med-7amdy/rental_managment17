# -*- coding: utf-8 -*-
# Copyright 2020-Today TechKhedut.
# Part of TechKhedut. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.fields import Command


class PropertyMaintenance(models.Model):
    _inherit = "maintenance.request"
    _check_company_auto = True

    property_id = fields.Many2one(
        "property.details", string="Property", index=True, check_company=True, tracking=True
    )
    tenancy_id = fields.Many2one(
        "tenancy.details", string="Rental Contract", index=True, check_company=True, tracking=True
    )
    company_id = fields.Many2one(
        "res.company", string="Company", required=True, default=lambda self: self.env.company, index=True
    )
    currency_id = fields.Many2one("res.currency", related="company_id.currency_id", store=True)
    landlord_id = fields.Many2one("res.partner", string="Landlord", index=True)
    maintenance_type_id = fields.Many2one(
        "product.template",
        string="Type",
        domain="[('is_maintenance', '=', True), '|', ('company_id', '=', False), ('company_id', '=', company_id)]",
    )
    price = fields.Float(related="maintenance_type_id.list_price", string="Price")
    invoice_id = fields.Many2one("account.move", string="Invoice", copy=False, check_company=True)
    invoice_state = fields.Boolean(string="Invoice Created", compute="_compute_invoice_state", store=True)

    @api.depends("invoice_id")
    def _compute_invoice_state(self):
        for request_record in self:
            request_record.invoice_state = bool(request_record.invoice_id)

    @api.onchange("tenancy_id")
    def _onchange_tenancy_id(self):
        for request_record in self:
            if request_record.tenancy_id:
                request_record.property_id = request_record.tenancy_id.property_id
                request_record.company_id = request_record.tenancy_id.company_id
                request_record.landlord_id = request_record.tenancy_id.property_landlord_id

    @api.constrains("tenancy_id", "property_id", "company_id")
    def _check_rental_links(self):
        for request_record in self:
            if request_record.tenancy_id:
                if request_record.tenancy_id.company_id != request_record.company_id:
                    raise ValidationError(_("Maintenance request and contract companies must match."))
                if request_record.property_id != request_record.tenancy_id.property_id:
                    raise ValidationError(_("Maintenance property must match the rental contract property."))

    def action_crete_invoice(self):
        """Create the maintenance invoice once; method name retained for XML compatibility."""
        self.ensure_one()
        if self.invoice_id:
            return {
                "type": "ir.actions.act_window",
                "res_model": "account.move",
                "res_id": self.invoice_id.id,
                "view_mode": "form",
            }
        if not self.maintenance_type_id:
            raise UserError(_("Select a maintenance type before creating the invoice."))
        partner = self.landlord_id or self.tenancy_id.property_landlord_id
        if not partner:
            raise UserError(_("Set a landlord before creating the maintenance invoice."))
        move = self.env["account.move"].with_company(self.company_id).create(
            {
                "partner_id": partner.id,
                "move_type": "out_invoice",
                "invoice_date": fields.Date.context_today(self),
                "company_id": self.company_id.id,
                "currency_id": self.currency_id.id,
                "maintenance_request_id": self.id,
                "tenancy_id": self.tenancy_id.id,
                "invoice_origin": self.name,
                "invoice_line_ids": [
                    Command.create(
                        {
                            "product_id": self.maintenance_type_id.product_variant_id.id,
                            "name": _("Maintenance: %s") % self.display_name,
                            "quantity": 1.0,
                            "price_unit": self.price,
                        }
                    )
                ],
            }
        )
        if self.env["ir.config_parameter"].sudo().get_param(
            "rental_management.invoice_post_type"
        ) == "automatically":
            move.action_post()
        self.invoice_id = move
        return {
            "type": "ir.actions.act_window",
            "name": _("Invoice"),
            "res_model": "account.move",
            "res_id": move.id,
            "view_mode": "form",
            "target": "current",
        }


class MaintenanceProduct(models.Model):
    _inherit = "product.template"

    is_maintenance = fields.Boolean(string="Maintenance")
