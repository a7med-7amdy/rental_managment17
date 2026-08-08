# -*- coding: utf-8 -*-
# Copyright 2020-Today TechKhedut.
# Part of TechKhedut. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models


class PropertyInquiry(models.Model):
    _inherit = 'crm.lead'

    property_id = fields.Many2one(
        'property.details',
        string='Property',
        check_company=True,
        domain="[('company_id', '=', company_id), '|', ('stage', '=', 'available'), ('stage', '=', 'sale')]",
    )
    sale_lease = fields.Selection(related='property_id.sale_lease', string='Selected Property For')
    price = fields.Monetary(related="property_id.price", string="Selected Property Price")

    # For sale. company_id is inherited unchanged from crm.lead so Odoo's
    # native computed/stored multi-company behavior remains intact.
    currency_id = fields.Many2one('res.currency',
                                  related='company_id.currency_id',
                                  string='Currency ')
    ask_price = fields.Monetary(string="Ask Price")

    # Legacy compatibility field retained for existing databases
    duration_id = fields.Many2one('contract.duration', string='Duration')
    booking_id = fields.Many2one("property.vendor", string="Booking")
    tenancy_inquiry_id = fields.Many2one('tenancy.inquiry',
                                         string="Rent Enquiry")
    sale_inquiry_id = fields.Many2one('sale.inquiry', string="Sale Enquiry")
    property_type = fields.Selection([('land', 'Land'),
                                      ('residential', 'Residential'),
                                      ('commercial', 'Commercial'),
                                      ('industrial', 'Industrial')
                                      ], string='Property Type',
                                     required=True,
                                     default="residential")
    property_subtype_id = fields.Many2one('property.sub.type',
                                          string="Property Sub Type",
                                          domain="[('type','=',property_type)]")
    total_area = fields.Float(string="Total Area")
    usable_area = fields.Float(string="Usable Area")
    property_price = fields.Monetary(string="Requested Property Price")
    rent_unit = fields.Selection([('Day', "Day"),
                                  ('Month', "Month"),
                                  ('Year', "Year")],
                                 default='Month',
                                 string="Rent Unit")
    pricing_type = fields.Selection([('fixed', 'Fixed'),
                                     ('area_wise', 'Area Wise')],
                                    string="Pricing Type",
                                    default='fixed')
    domain_sale_lease = fields.Selection([
        ('for_sale', 'Sale'),
        ('for_tenancy', 'Rent')],
        string='Requested Property For',
        default='for_tenancy',
        required=True)
    price_per_area = fields.Monetary(string="Price / Area")
    measure_unit = fields.Selection([('sq_ft', 'ft²'),
                                     ('sq_m', 'm²'),
                                     ('sq_yd', 'yd²'),
                                     ('cu_ft', 'ft³'),
                                     ('cu_m', 'm³')],
                                    default='sq_ft',
                                    string="Area Measurement Unit")
    available_property_ids = fields.Many2many(
        comodel_name='property.details',
        string='Available Properties', compute='get_available_property_ids')

    property_domain_fields = [
        'company_id', 'measure_unit', 'price_per_area', 'domain_sale_lease',
        'pricing_type', 'rent_unit', 'property_price', 'usable_area',
        'total_area', 'property_subtype_id', 'property_type',
    ]
    property_domain_equal_field_dict = {
        'company_id': 'company_id',
        'domain_sale_lease': 'sale_lease',
        'property_price': 'price',
        'property_type': 'type',
    }
    property_domain_field_operator_dict = {}

    @api.depends(*property_domain_fields)
    def get_available_property_ids(self):
        for rec in self:
            domain = [('stage', 'in', ['available', 'sale'])]
            for f in self.property_domain_fields:
                f_value = rec[f]
                if f in ('property_subtype_id', 'company_id'):
                    f_value = f_value.id
                if f_value:
                    domain += [(f"{self.property_domain_equal_field_dict.get(f, f) or f}",
                                f"{self.property_domain_field_operator_dict.get(f, '=') or '='}", f_value)]
            available_property_ids = self.env['property.details'].search(domain)
            rec.available_property_ids = available_property_ids


