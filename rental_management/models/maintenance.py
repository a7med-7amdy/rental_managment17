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
    landlord_id = fields.Many2one(
        "res.partner", string="Landlord", index=True, check_company=True
    )
    maintenance_type_id = fields.Many2one(
        "product.template",
        string="Type",
        check_company=True,
        domain="[('is_maintenance', '=', True), '|', ('company_id', '=', False), ('company_id', '=', company_id)]",
    )
    maintenance_type_name = fields.Char(
        related="maintenance_type_id.name", string="Maintenance Type Name", store=True, readonly=True, translate=False
    )
    rental_stage_name = fields.Char(
        related="stage_id.name", string="Maintenance Stage Name", store=True, readonly=True, translate=False
    )
    price = fields.Float(related="maintenance_type_id.list_price", string="Price")
    invoice_id = fields.Many2one("account.move", string="Invoice", copy=False, check_company=True)
    invoice_state = fields.Boolean(string="Invoice Created", compute="_compute_invoice_state", store=True)


    @api.model
    def _get_rental_maintenance_team(self, company):
        """Return an existing, company-compatible team for a rental request."""
        company.ensure_one()
        team_model = self.env["maintenance.team"].sudo().with_company(company)
        team = team_model.search(
            [("company_id", "=", company.id), ("active", "=", True)],
            order="id",
            limit=1,
        )
        if team:
            return team
        rental_team = self.env.ref(
            "rental_management.maintenance_team_rental", raise_if_not_found=False
        )
        if rental_team and rental_team.active and (
            not rental_team.company_id or rental_team.company_id == company
        ):
            return rental_team.sudo().with_company(company)
        return team_model.search(
            [("company_id", "=", False), ("active", "=", True)],
            order="id",
            limit=1,
        )

    @api.model
    def _get_rental_maintenance_stage(self):
        """Return the first maintenance stage without leaking configuration access."""
        return self.env["maintenance.stage"].sudo().search([], order="sequence, id", limit=1)

    @api.model
    def _prepare_rental_request_security(self, vals):
        """Authorize and normalize a request linked to rental/property data.

        Core Maintenance ACLs and defaults are intentionally not used as the
        authorization boundary for rental-linked requests.  Ownership, rental
        role, company and property consistency are checked here first.
        """
        vals = dict(vals)
        user = self.env.user
        is_portal = user.has_group("base.group_portal")
        is_rental_user = (
            user.has_group("rental_management.property_rental_officer")
            or user.has_group("rental_management.property_rental_manager")
        )
        tenancy_id = vals.get("tenancy_id")
        property_id = vals.get("property_id")

        if is_portal and not tenancy_id:
            raise AccessError(
                _("Portal users can only create maintenance requests from one of their rental contracts.")
            )

        tenancy = self.env["tenancy.details"]
        property_record = self.env["property.details"]
        if tenancy_id:
            tenancy = self.env["tenancy.details"].browse(tenancy_id).exists()
            if not tenancy:
                raise ValidationError(_("The selected rental contract does not exist."))
            tenancy.check_access("read")

            if is_portal:
                if tenancy.tenancy_id.commercial_partner_id != user.partner_id.commercial_partner_id:
                    raise AccessError(
                        _("You can only create maintenance requests for your own rental contracts.")
                    )
                if tenancy.contract_type != "running_contract":
                    raise ValidationError(
                        _("Maintenance requests can only be created for an active rental contract.")
                    )
            elif not (is_rental_user or self.env.su):
                raise AccessError(
                    _("Only Rental Officers or Rental Managers can create maintenance requests linked to rental contracts.")
                )

            property_record = tenancy.property_id
            if property_id and property_id != property_record.id:
                raise ValidationError(_("Maintenance property must match the rental contract property."))
            if vals.get("company_id") and vals["company_id"] != tenancy.company_id.id:
                raise ValidationError(_("Maintenance request and contract companies must match."))

            vals["property_id"] = property_record.id
            vals["company_id"] = tenancy.company_id.id
            if tenancy.property_landlord_id:
                vals.setdefault("landlord_id", tenancy.property_landlord_id.id)
        elif property_id:
            property_record = self.env["property.details"].browse(property_id).exists()
            if not property_record:
                raise ValidationError(_("The selected property does not exist."))
            property_record.check_access("read")
            if is_portal:
                raise AccessError(
                    _("Portal users must create maintenance requests from an active rental contract.")
                )
            if not (is_rental_user or self.env.su):
                raise AccessError(
                    _("Only Rental Officers or Rental Managers can create maintenance requests linked to rental properties.")
                )
            if vals.get("company_id") and vals["company_id"] != property_record.company_id.id:
                raise ValidationError(_("Maintenance request and property companies must match."))
            vals["company_id"] = property_record.company_id.id
            landlord = property_record.parent_landlord_id if property_record.is_parent_property else property_record.landlord_id
            if landlord:
                vals.setdefault("landlord_id", landlord.id)

            # Link the current running contract automatically when there is exactly
            # one.  This keeps property-created requests visible in the tenant portal.
            today = fields.Date.context_today(self)
            active_contract = self.env["tenancy.details"].search(
                [
                    ("property_id", "=", property_record.id),
                    ("contract_type", "=", "running_contract"),
                    ("start_date", "<=", today),
                    ("end_date", ">=", today),
                ],
                order="start_date desc, id desc",
                limit=1,
            )
            if active_contract:
                vals["tenancy_id"] = active_contract.id

        linked_to_rental = bool(vals.get("tenancy_id") or vals.get("property_id"))
        return vals, linked_to_rental

    @api.model
    def _prepare_rental_maintenance_defaults(self, vals):
        """Fill required core Maintenance defaults using read-only sudo lookups."""
        vals = dict(vals)
        company = self.env["res.company"].browse(vals.get("company_id")).exists() or self.env.company
        if not vals.get("maintenance_team_id"):
            team = self._get_rental_maintenance_team(company)
            if not team:
                raise UserError(
                    _("Configure at least one Maintenance Team for company %s before creating a maintenance request.")
                    % company.display_name
                )
            vals["maintenance_team_id"] = team.id
        if not vals.get("stage_id"):
            stage = self._get_rental_maintenance_stage()
            if not stage:
                raise UserError(_("Configure at least one Maintenance Stage before creating a maintenance request."))
            vals["stage_id"] = stage.id
        vals.setdefault("owner_user_id", self.env.user.id)
        return vals

    @api.model_create_multi
    def create(self, vals_list):
        """Create rental-linked requests after explicit authorization.

        Odoo 19 Maintenance performs defaults and a post-create access check on
        configuration models which Portal and rental-only users may not read.
        For a request that has passed the rental ownership/role checks above,
        core creation is therefore executed in superuser mode.  ``sudo()`` keeps
        the original user id in Odoo, so ``create_uid`` remains the caller while
        ACL/record-rule bypass is narrowly limited to this authorized creation.
        Unrelated Maintenance requests always use standard core security.
        """
        prepared = []
        linked_flags = []
        for incoming in vals_list:
            vals, linked = self._prepare_rental_request_security(incoming)
            if linked:
                vals = self._prepare_rental_maintenance_defaults(vals)
            prepared.append(vals)
            linked_flags.append(linked)

        if all(linked_flags):
            records = super(PropertyMaintenance, self.sudo()).create(prepared)
            return records.sudo(False)
        if not any(linked_flags):
            return super().create(prepared)

        # Mixed batches are uncommon but must preserve the security policy of each
        # item.  Keep input order and elevate only rental-linked entries.
        records = self.browse()
        for vals, linked in zip(prepared, linked_flags):
            if linked:
                record = super(PropertyMaintenance, self.sudo()).create([vals]).sudo(False)
            else:
                record = super().create([vals])
            records |= record
        return records

    def write(self, vals):
        """Protect rental linkage on direct RPC writes as well as on creation."""
        security_fields = {"tenancy_id", "property_id", "company_id"}
        if security_fields.intersection(vals):
            for request_record in self:
                merged = {
                    "tenancy_id": vals.get("tenancy_id", request_record.tenancy_id.id),
                    "property_id": vals.get("property_id", request_record.property_id.id),
                    "company_id": vals.get("company_id", request_record.company_id.id),
                }
                self._prepare_rental_request_security(merged)
        return super().write(vals)

    def unlink(self):
        """Rental-linked requests are deletable only by a Rental Manager."""
        linked = self.filtered(lambda request: request.tenancy_id or request.property_id)
        if linked and not (
            self.env.su
            or self.env.user.has_group("rental_management.property_rental_manager")
        ):
            raise AccessError(_("Only a Rental Manager can delete rental-linked maintenance requests."))
        return super().unlink()

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
        """Create the maintenance invoice idempotently.

        The legacy method name is retained because existing XML buttons reference
        it, but accounting creation follows Odoo's normal access, fiscal-position
        and tax engine rules.
        """
        self.ensure_one()
        self.env.cr.execute(
            "SELECT id FROM maintenance_request WHERE id = %s FOR UPDATE",
            (self.id,),
        )
        self.invalidate_recordset(["invoice_id"])
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
        product = self.maintenance_type_id.product_variant_id
        if not product:
            raise UserError(_("The selected maintenance type has no product variant."))
        move_model = self.env["account.move"].with_company(self.company_id)
        if not move_model.browse().has_access("create"):
            raise AccessError(
                _("Billing invoice creation access is required to create the maintenance invoice.")
            )
        fiscal_position = partner.with_company(self.company_id).property_account_position_id
        taxes = product.taxes_id.filtered(lambda tax: tax.company_id == self.company_id)
        if fiscal_position and taxes:
            taxes = fiscal_position.map_tax(taxes)
        move_vals = {
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
                        "product_id": product.id,
                        "name": _("Maintenance: %s") % self.display_name,
                        "quantity": 1.0,
                        "price_unit": self.price,
                        "tax_ids": [Command.set(taxes.ids)],
                    }
                )
            ],
        }
        if fiscal_position:
            move_vals["fiscal_position_id"] = fiscal_position.id
        move = move_model.create(move_vals)
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
