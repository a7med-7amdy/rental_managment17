# -*- coding: utf-8 -*-
# Copyright 2020-Today TechKhedut.
# Part of TechKhedut. See LICENSE file for full copyright and licensing details.
from odoo import models, fields, api


class RentalConfig(models.TransientModel):
    _inherit = 'res.config.settings'

    reminder_days = fields.Integer(string='Days', default=5,
                                   config_parameter='rental_management.reminder_days')
    sale_reminder_days = fields.Integer(string="Days ", default=3,
                                        config_parameter='rental_management.sale_reminder_days')

    invoice_post_type = fields.Selection(
        [('manual', 'Invoice Post Manually'), ('automatically', 'Invoice Post Automatically')], string="Invoice Post",
        default='manual', config_parameter='rental_management.invoice_post_type')
