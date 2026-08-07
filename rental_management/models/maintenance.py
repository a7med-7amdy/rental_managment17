# -*- coding: utf-8 -*-
# Copyright 2020-Today TechKhedut.
# Part of TechKhedut. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError
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


    @api.model
    def _get_rental_maintenance_team(self, company):
        """Return a deterministic, company-compatible team for rental requests.

        Odoo 19 intentionally lets normal internal users *read* maintenance teams but
        reserves team creation to Maintenance/Equipment Managers.  Rental users and
        portal users therefore reuse existing configuration.  The lookup is sudoed
        only for the team lookup; the maintenance request itself is still created
        with the caller's normal ACLs and record rules.
        """
        company.ensure_one()
        team_model = self.env["maintenance.team"].sudo().with_company(company)

        # Prefer a team explicitly configured for the request company.
        team = team_model.search(
            [("company_id", "=", company.id), ("active", "=", True)],
            order="id",
            limit=1,
        )
        if team:
            return team

        # Fall back deterministically to the module-owned shared team.
        rental_team = self.env.ref(
            "rental_management.maintenance_team_rental", raise_if_not_found=False
        )
        if rental_team and rental_team.active and (
            not rental_team.company_id or rental_team.company_id == company
        ):
            return rental_team.sudo().with_company(company)

        # Legacy databases may not yet have the new XML ID. Reuse any shared team
        # rather than creating configuration behind the user's back.
        return team_model.search(
            [("company_id", "=", False), ("active", "=", True)],
            order="id",
            limit=1,
        )

    @api.model
    def _prepare_rental_request_security(self, vals):
        """Validate rental ownership/role before creating a linked request.

        Odoo's core maintenance ACLs can differ between deployed 19.0 builds.
        This module therefore grants the base model permission explicitly, then
        applies rental-specific authorization here whenever ``tenancy_id`` is used.
        Non-rental maintenance requests keep the standard Maintenance behavior.
        """
        vals = dict(vals)
        user = self.env.user
        is_portal = user.has_group("base.group_portal")
        tenancy_id = vals.get("tenancy_id")

        if is_portal and not tenancy_id:
            raise AccessError(_("Portal users can only create maintenance requests from one of their rental contracts."))

        if not tenancy_id:
            return vals

        tenancy = self.env["tenancy.details"].browse(tenancy_id).exists()
        if not tenancy:
            raise ValidationError(_("The selected rental contract does not exist."))

        # check_access includes both model ACLs and record rules. For portal users
        # this is the ownership check; for internal rental users it also enforces
        # allowed-company isolation.
        tenancy.check_access("read")

        if is_portal:
            if tenancy.tenancy_id.commercial_partner_id != user.partner_id.commercial_partner_id:
                raise AccessError(_("You can only create maintenance requests for your own rental contracts."))
            if tenancy.contract_type != "running_contract":
                raise ValidationError(_("Maintenance requests can only be created for an active rental contract."))
        elif not (
            user.has_group("rental_management.property_rental_officer")
            or user.has_group("rental_management.property_rental_manager")
        ):
            raise AccessError(_("Only Rental Officers or Rental Managers can create maintenance requests linked to rental contracts."))

        if vals.get("property_id") and vals["property_id"] != tenancy.property_id.id:
            raise ValidationError(_("Maintenance property must match the rental contract property."))
        if vals.get("company_id") and vals["company_id"] != tenancy.company_id.id:
            raise ValidationError(_("Maintenance request and contract companies must match."))

        vals.setdefault("property_id", tenancy.property_id.id)
        vals.setdefault("company_id", tenancy.company_id.id)
        if tenancy.property_landlord_id:
            vals.setdefault("landlord_id", tenancy.property_landlord_id.id)
        return vals

    @api.model_create_multi
    def create(self, vals_list):
        prepared_vals = []
        for incoming in vals_list:
            vals = self._prepare_rental_request_security(incoming)
            if not vals.get("maintenance_team_id"):
                company = self.env["res.company"].browse(vals.get("company_id")).exists() or self.env.company
                team = self._get_rental_maintenance_team(company)
                if not team:
                    raise UserError(
                        _("Configure at least one Maintenance Team for company %s before creating a maintenance request.")
                        % company.display_name
                    )
                vals["maintenance_team_id"] = team.id
            prepared_vals.append(vals)
        return super().create(prepared_vals)

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
