# -*- coding: utf-8 -*-

from odoo import _, fields, models
from odoo.exceptions import UserError


class CancelContractWizard(models.TransientModel):
    _name = "cancel.contract.wizard"
    _description = "Cancel Rental Contract"

    tenancy_id = fields.Many2one("tenancy.details", required=True, readonly=True)
    reason = fields.Text(string="Cancellation Reason", required=True)

    def action_confirm_cancel(self):
        self.ensure_one()
        if not self.tenancy_id.exists():
            raise UserError(_("The rental contract no longer exists."))
        self.tenancy_id.action_cancel_contract(reason=self.reason)
        return {"type": "ir.actions.act_window_close"}
