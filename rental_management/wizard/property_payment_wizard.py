# -*- coding: utf-8 -*-
# Copyright 2020-Today TechKhedut.
# Part of TechKhedut. See LICENSE file for full copyright and licensing details.
from odoo import fields, models, api


class PropertyPayment(models.TransientModel):
    _name = 'property.payment.wizard'
    _description = 'Create Invoice For Rent'

    tenancy_id = fields.Many2one('tenancy.details', string='Tenancy No.')
    customer_id = fields.Many2one(related='tenancy_id.tenancy_id',
                                  string='Customer')
    company_id = fields.Many2one('res.company',
                                 string='Company',
                                 default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency',
                                  related='company_id.currency_id',
                                  string='Currency')
    type = fields.Selection([('deposit', 'Deposit'),
                             ('maintenance', 'Maintenance'),
                             ('penalty', 'Penalty'),
                             ('other', 'Other')],
                            string='Payment For')
    description = fields.Char(string='Description', translate=True)
    invoice_date = fields.Date(string='Date', default=fields.Date.today())
    rent_amount = fields.Monetary(string='Rent Amount',
                                  related='tenancy_id.total_rent')
    amount = fields.Monetary(string='Amount')
    rent_invoice_id = fields.Many2one('account.move', string='Invoice')
    # service
    service_id = fields.Many2one('product.product', string="Service",
                                 default=lambda self: self.env.ref('rental_management.property_product_1').id)
    tax_ids = fields.Many2many('account.tax', string="Taxes")

    # Default Get
    @api.model
    def default_get(self, fields):
        res = super(PropertyPayment, self).default_get(fields)
        active_id = self._context.get('active_id')
        res['tenancy_id'] = active_id
        return res

    def property_payment_action(self):
        invoice_post_type = self.env['ir.config_parameter'].sudo(
        ).get_param('rental_management.invoice_post_type')
        data = {
            'partner_id': self.customer_id.id,
            'move_type': 'out_invoice',
            'invoice_date': self.invoice_date,
            'invoice_line_ids': [(0, 0, {
                'product_id': self.service_id.id,
                'name': self.description,
                'quantity': 1,
                'price_unit': self.amount,
                'tax_ids': self.tax_ids.ids
            })]
        }
        invoice_id = self.env['account.move'].sudo().create(data)
        if invoice_post_type == 'automatically':
            invoice_id.action_post()
        self.env['rent.invoice'].create({
            'tenancy_id': self.tenancy_id.id,
            'type': self.type,
            'invoice_date': self.invoice_date,
            'amount': self.amount,
            'description': self.description,
            'rent_invoice_id': invoice_id.id
        })
