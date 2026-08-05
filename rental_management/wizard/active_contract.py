# -*- coding: utf-8 -*-
# Copyright 2020-Today TechKhedut.
# Part of TechKhedut. See LICENSE file for full copyright and licensing details.

from odoo import _, fields, models
from odoo.exceptions import UserError


class ActiveContract(models.TransientModel):
    """Choose the installment mode and activate a draft rental contract."""

    _name = "active.contract"
    _description = "Activate Rental Contract"
    _rec_name = "type"

    type = fields.Selection(
        [
            ("automatic", "Automatic Installments"),
            ("manual", "Manual Installments"),
        ],
        default="automatic",
        required=True,
    )

    def action_create_contract(self):
        self.ensure_one()
        contract = self.env["tenancy.details"].browse(self.env.context.get("active_id")).exists()
        if not contract:
            raise UserError(_("The rental contract no longer exists."))
        contract.type = self.type
        contract.action_activate_contract()
        return {
            "type": "ir.actions.act_window",
            "res_model": "tenancy.details",
            "res_id": contract.id,
            "view_mode": "form",
            "target": "current",
        }
