# -*- coding: utf-8 -*-
# Copyright 2020-Today TechKhedut.
# Part of TechKhedut. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class PropertyMaintenance(models.TransientModel):
    _name = "maintenance.wizard"
    _description = "Create Property Maintenance Request"
    _check_company_auto = True

    name = fields.Char(string="Request", required=True, translate=True)
    property_id = fields.Many2one(
        "property.details", string="Property", required=True, check_company=True
    )
    maintenance_type_id = fields.Many2one(
        "product.template",
        string="Type",
        check_company=True,
        domain="[('is_maintenance', '=', True), '|', ('company_id', '=', False), ('company_id', '=', company_id)]",
    )
    maintenance_team_id = fields.Many2one(
        "maintenance.team",
        string="Team",
        check_company=True,
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
    )
    company_id = fields.Many2one(
        "res.company",
        related="property_id.company_id",
        readonly=True,
    )

    @api.model
    def default_get(self, field_list):
        res = super().default_get(field_list)
        property_record = self.env["property.details"].browse(
            self.env.context.get("active_id")
        ).exists()
        if property_record:
            res["property_id"] = property_record.id
            res.setdefault("name", _("Maintenance Request - %s") % property_record.display_name)
        return res

    def maintenance_request(self):
        self.ensure_one()
        if not self.property_id:
            raise UserError(_("Select a property before creating a maintenance request."))
        property_record = self.property_id
        landlord = (
            property_record.parent_landlord_id
            if property_record.is_parent_property
            else property_record.landlord_id
        )
        vals = {
            "name": self.name,
            "maintenance_type_id": self.maintenance_type_id.id,
            "landlord_id": landlord.id,
            "property_id": property_record.id,
            "company_id": property_record.company_id.id,
            "request_date": fields.Date.context_today(self),
        }
        if self.maintenance_team_id:
            vals["maintenance_team_id"] = self.maintenance_team_id.id
        request_record = self.env["maintenance.request"].create(vals)
        return {
            "type": "ir.actions.act_window",
            "name": _("Maintenance Request"),
            "res_model": "maintenance.request",
            "res_id": request_record.id,
            "view_mode": "form",
            "target": "current",
        }
