# -*- coding: utf-8 -*-
# Copyright 2020-Today TechKhedut.
# Part of TechKhedut. See LICENSE file for full copyright and licensing details.
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class RentalConfig(models.TransientModel):
    _inherit = 'res.config.settings'

    reminder_days = fields.Integer(string='Days', default=5,
                                   config_parameter='rental_management.reminder_days')
    sale_reminder_days = fields.Integer(string="Days ", default=3,
                                        config_parameter='rental_management.sale_reminder_days')

    invoice_post_type = fields.Selection(
        [('manual', 'Invoice Post Manually'), ('automatically', 'Invoice Post Automatically')],
        string="Invoice Post", default='manual',
        config_parameter='rental_management.invoice_post_type',
    )

    @api.constrains('reminder_days', 'sale_reminder_days')
    def _check_non_negative_reminder_days(self):
        for settings in self:
            if settings.reminder_days < 0 or settings.sale_reminder_days < 0:
                raise ValidationError(_("Reminder days cannot be negative."))
