# -*- coding: utf-8 -*-
# Copyright 2020-Today TechKhedut.
# Part of TechKhedut. See LICENSE file for full copyright and licensing details.
import datetime
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _


class TenancyDetails(models.Model):
    _name = 'tenancy.details'
    _description = 'Information Related To customer Tenancy while Creating Contract'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'tenancy_seq'

    # Tenancy Details
    tenancy_seq = fields.Char(string='Sequence', required=True,
                              readonly=True, copy=False,
                              default=lambda self: ('New'))
    close_contract_state = fields.Boolean(string='Contract State')
    active_contract_state = fields.Boolean(string='Active State')
    contract_type = fields.Selection([('new_contract', 'Draft'),
                                      ('running_contract', 'Running'),
                                      ('cancel_contract', 'Cancel'),
                                      ('close_contract', 'Close'),
                                      ('expire_contract', 'Expire')],
                                     string='Contract Type')
    days_left = fields.Integer(string="Days Left", compute="compute_days_left")
    responsible_id = fields.Many2one('res.users',
                                     default=lambda self: self.env.user and self.env.user.id or False,
                                     string="Responsible")

    # Company & Currency
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency',
                                  related='company_id.currency_id', string='Currency')

    # Property Information
    property_id = fields.Many2one('property.details', string='Property',
                                  domain=[('stage', '=', 'available')])
    property_type = fields.Selection(related='property_id.type',
                                     string='Type ', store=True)
    property_subtype_id = fields.Many2one(related="property_id.property_subtype_id",
                                          string="Sub Type", store=True)
    property_project_id = fields.Many2one(related="property_id.property_project_id",
                                          string="Project", store=True)
    subproject_id = fields.Many2one(related="property_id.subproject_id",
                                    string="Sub Project", store=True)
    region_id = fields.Many2one(related="property_id.region_id")
    street = fields.Char(related="property_id.street")
    street2 = fields.Char(related="property_id.street2")
    city_id = fields.Many2one(related="property_id.city_id")
    zip = fields.Char(related="property_id.zip")
    state_id = fields.Many2one(related="property_id.state_id")
    country_id = fields.Many2one(related="property_id.country_id")

    # Landlord
    property_landlord_id = fields.Many2one(related='property_id.landlord_id',
                                           string='Landlord', store=True)
    landlord_phone = fields.Char(related='property_landlord_id.phone',
                                 string="Landlord Phone")
    landlord_email = fields.Char(related='property_landlord_id.email',
                                 string="Landlord Email")
    # Customer / Tenant
    tenancy_id = fields.Many2one('res.partner', string='Tenant',
                                 domain=[('user_type', '=', 'customer')])
    customer_phone = fields.Char(related="tenancy_id.phone",
                                 string="Customer Phone")
    customer_email = fields.Char(related="tenancy_id.email",
                                 string="Customer Email")

    # Extend Contract Ref.
    extended = fields.Boolean(string="Is Extended")
    is_extended = fields.Boolean(string='Is Extended Contract')
    extend_from = fields.Char(string="Extend From.")
    extend_ref = fields.Char(string="Extend Ref.")
    new_contract_id = fields.Many2one('tenancy.details', string="Contract Ref")

    # Contract & Payment Details
    payment_term = fields.Selection([('monthly', 'Monthly'),
                                     ('full_payment', 'Full Payment'),
                                     ('quarterly', 'Quarterly'),
                                     ('year', 'Yearly')],
                                    string='Payment Term')
    duration_id = fields.Many2one('contract.duration', string='Duration')
    month = fields.Integer(related='duration_id.month', string='Month')
    total_rent = fields.Monetary(string='Rent')
    rent_unit = fields.Selection(related="property_id.rent_unit")
    start_date = fields.Date(string='Start Date', default=fields.date.today())
    end_date = fields.Date(string='End Date', compute='_compute_end_date')
    invoice_start_date = fields.Date(string="Invoice Start From",
                                     default=fields.date.today())
    last_invoice_payment_date = fields.Date(string='Last Invoice Payment Date')
    rent_invoice_ids = fields.One2many('rent.invoice', 'tenancy_id',
                                       string='Invoices')
    total_area = fields.Float(related="property_id.total_area")
    usable_area = fields.Float(related="property_id.usable_area")
    measure_unit = fields.Selection(related="property_id.measure_unit")
    type = fields.Selection(
        [('automatic', 'Auto Installment'),
         ('manual', 'Manual Installment (List out all rent installment)')],
        default='automatic')
    is_any_deposit = fields.Boolean(string="Deposit")
    deposit_amount = fields.Monetary(string="Security Deposit")

    # Maintenance & Utility Service
    is_extra_service = fields.Boolean(related="property_id.is_extra_service",
                                      string="Any Extra Services")
    extra_services_ids = fields.One2many('tenancy.service.line', 'tenancy_id',
                                         string="Services")
    is_maintenance_service = fields.Boolean(related="property_id.is_maintenance_service",
                                            string="Is Any Maintenance")
    maintenance_rent_type = fields.Selection(related='property_id.maintenance_rent_type',
                                             string="Maintenance Type")
    total_maintenance = fields.Monetary(related="property_id.total_maintenance",
                                        string="Total Maintenance")
    maintenance_type = fields.Selection(related="property_id.maintenance_type")
    per_area_maintenance = fields.Monetary(
        related="property_id.per_area_maintenance")

    # Broker details
    is_any_broker = fields.Boolean(string='Any Broker')
    broker_invoice_state = fields.Boolean(string='Broker invoice State')
    broker_invoice_id = fields.Many2one('account.move', string='Bill')
    broker_id = fields.Many2one('res.partner', string='Broker',
                                domain=[('user_type', '=', 'broker')])
    commission = fields.Monetary(string='Commission ',
                                 compute='_compute_broker_commission')
    rent_type = fields.Selection([('once', 'One Month'),
                                  ('e_rent', 'All Month')],
                                 string='Brokerage Type')
    commission_type = fields.Selection([('f', 'Fix'),
                                        ('p', 'Percentage')],
                                       string="Commission Type")
    broker_commission = fields.Monetary(string='Commission')
    broker_commission_percentage = fields.Float(string='Percentage')
    commission_from = fields.Selection([('customer', 'Customer'),
                                        ('landlord', 'Landlord',)],
                                       string="Commission From")

    # Instalment Item
    installment_item_id = fields.Many2one('product.product', string="Installment Item",
                                          default=lambda self: self.env.ref('rental_management.property_product_1').id)
    deposit_item_id = fields.Many2one('product.product', string="Deposit Item",
                                      default=lambda self: self.env.ref('rental_management.property_product_2',
                                                                        raise_if_not_found=False))
    broker_item_id = fields.Many2one('product.product', string="Broker Item",
                                     default=lambda self: self.env.ref('rental_management.property_product_1').id)

    # Taxes
    instalment_tax = fields.Boolean(string="Taxes on Installment ?")
    deposit_tax = fields.Boolean(string="Taxes on Deposit ?")
    service_tax = fields.Boolean(string="Taxes on Services ?")
    tax_ids = fields.Many2many('account.tax', string="Taxes")

    # Agreement
    agreement = fields.Html(string="Agreement")
    contract_agreement = fields.Binary(string='Contract Agreement')
    file_name = fields.Char(string='File Name', translate=True)

    # Terms  & Conditions
    term_condition = fields.Html(string='Term and Condition')

    # Tenancy Calculation
    total_tenancy = fields.Monetary(string="Untaxed Amount",
                                    compute="_compute_tenancy_calculation")
    tax_amount = fields.Monetary(string="Tax Amount",
                                 compute="_compute_tenancy_calculation")
    total_amount = fields.Monetary(string="Total Amount",
                                   compute="_compute_tenancy_calculation")
    paid_tenancy = fields.Monetary(string="Paid Amount",
                                   compute="_compute_tenancy_calculation")
    remain_tenancy = fields.Monetary(string="Remaining Amount",
                                     compute="_compute_tenancy_calculation")

    # Count
    invoice_count = fields.Integer(string='Invoice Count',
                                   compute="_compute_invoice_count")

    # Create, Write, Name get...
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('tenancy_seq', 'New') == 'New':
                vals['tenancy_seq'] = self.env['ir.sequence'].next_by_code(
                    'tenancy.details') or 'New'
        res = super(TenancyDetails, self).create(vals_list)
        return res

    # Compute
    # Contract End Date
    @api.depends('start_date', 'month', 'rent_unit', 'payment_term')
    def _compute_end_date(self):
        for rec in self:
            if rec.rent_unit == "Day":
                end_date = rec.start_date + relativedelta(days=rec.month)
            elif rec.rent_unit == "Year":
                end_date = rec.start_date + \
                    relativedelta(years=rec.month) - relativedelta(days=1)
            else:
                if rec.payment_term == "year":
                    end_date = rec.start_date + \
                        relativedelta(years=rec.month) - relativedelta(days=1)
                else:
                    end_date = rec.start_date + \
                        relativedelta(months=rec.month) - relativedelta(days=1)
            rec.end_date = end_date

    # Broker Commission
    @api.depends('is_any_broker', 'month', 'broker_commission', 'broker_commission_percentage', 'commission_type',
                 'rent_type', 'total_rent')
    def _compute_broker_commission(self):
        for rec in self:
            commission = 0.0
            total_commission = 0.0
            if rec.is_any_broker:
                if rec.commission_type == 'f':
                    commission = rec.broker_commission
                if rec.commission_type == 'p':
                    commission = rec.broker_commission_percentage * rec.total_rent / 100
                if rec.rent_type == 'once':
                    total_commission = commission
                if rec.rent_type == 'e_rent':
                    total_commission = commission * rec.month
            rec.commission = total_commission

    # Days Left
    @api.depends('start_date', 'end_date', 'contract_type')
    def compute_days_left(self):
        for rec in self:
            days_left = 0
            days = 0
            todays_date = fields.Date.today()
            if rec.contract_type == 'running_contract':
                days = (rec.end_date - todays_date).days
                days_left = days if days > 0 else 0
            rec.days_left = days_left

    # Tenancy Calculation
    @api.depends("rent_invoice_ids", 'rent_invoice_ids.rent_invoice_id', 'contract_type')
    def _compute_tenancy_calculation(self):
        for rec in self:
            untaxed = 0.0
            tax_amount = 0.0
            paid = 0.0
            for data in rec.rent_invoice_ids:
                if data.rent_invoice_id:
                    untaxed = untaxed + data.rent_invoice_id.amount_untaxed
                    tax_amount = tax_amount + \
                        (data.rent_invoice_id.amount_total -
                         data.rent_invoice_id.amount_untaxed)
                    if data.rent_invoice_id.payment_state == 'paid':
                        paid = paid + data.rent_invoice_id.amount_total
            rec.total_amount = untaxed + tax_amount
            rec.total_tenancy = untaxed
            rec.tax_amount = tax_amount
            rec.paid_tenancy = paid
            if rec.contract_type == 'running_contract':
                rec.remain_tenancy = untaxed + tax_amount - paid
            else:
                rec.remain_tenancy = 0.0

    # Count
    @api.depends('rent_invoice_ids')
    def _compute_invoice_count(self):
        for rec in self:
            rec.invoice_count = self.env['rent.invoice'].search_count(
                [('tenancy_id', '=', rec.id)])

    # Button
    # Smart Button
    def action_invoices(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Invoice',
            'res_model': 'rent.invoice',
            'domain': [('tenancy_id', '=', self.id)],
            'view_mode': 'tree,form',
            'target': 'current'
        }

    #  Close Contract
    def action_close_contract(self):
        if self.contract_type == 'running_contract' and self.remain_tenancy > 0:
            message = {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                        'type': 'info',
                        'title': (_('Invoice Pending !')),
                        'message': (_('To close the contract, please settle all outstanding installment invoices for this contract.')),
                        'next': {'type': 'ir.actions.act_window_close'},
                        'sticky': False,
                }
            }
            return message
        self.close_contract_state = True
        self.property_id.write({'stage': 'available'})
        self.contract_type = 'close_contract'
        return True

    # Active Contract
    def action_active_contract(self):
        invoice_post_type = self.env['ir.config_parameter'].sudo().get_param(
            'rental_management.invoice_post_type')
        invoice_lines = []
        if self.is_any_broker:
            self.action_broker_invoice()
        self.write({
            'contract_type': 'running_contract',
            'active_contract_state': True,
        })
        if self.is_any_deposit:
            invoice_lines.append((0, 0, {
                'product_id': self.deposit_item_id.id,
                'name': 'Deposit of ' + self.property_id.name,
                'quantity': 1,
                'price_unit': self.deposit_amount,
                'tax_ids': self.tax_ids.ids if self.deposit_tax else False
            }))
        invoice_record = {
            'product_id': self.installment_item_id.id,
            'quantity': 1,
            'tax_ids': self.tax_ids.ids if self.instalment_tax else False
        }
        if self.payment_term == 'monthly':
            invoice_record['name'] = 'First Invoice of ' + \
                self.property_id.name
            invoice_record['price_unit'] = self.total_rent
        if self.payment_term == 'quarterly':
            invoice_record['name'] = 'First Quarter Invoice of ' + \
                self.property_id.name
            invoice_record['price_unit'] = self.total_rent * 3
        if self.payment_term == 'year':
            invoice_record['name'] = 'First Year Invoice of ' + \
                self.property_id.name
            invoice_record['price_unit'] = self.total_rent
        invoice_lines.append((0, 0, invoice_record))
        data = {
            'partner_id': self.tenancy_id.id,
            'move_type': 'out_invoice',
            'invoice_date': self.invoice_start_date,
            'invoice_line_ids': invoice_lines,
            'tenancy_id': self.id
        }
        if self.is_maintenance_service:
            maintenance_record = {
                'product_id': self.installment_item_id.id,
                'name': 'Maintenance of ' + self.property_id.name,
                'quantity': 1,
                'price_unit': self.total_maintenance,
            }
            if self.maintenance_rent_type == 'recurring':
                if self.payment_term == 'quarterly':
                    maintenance_record['quantity'] = 3
                if self.payment_term == 'year':
                    maintenance_record['quantity'] = 12
            invoice_lines.append((0, 0, maintenance_record))
        if self.is_extra_service:
            service_lines = self.action_utility_service_invoice()
            data['invoice_line_ids'] = invoice_lines + service_lines
        invoice_id = self.env['account.move'].sudo().create(data)
        if invoice_post_type == 'automatically':
            invoice_id.action_post()
        self.last_invoice_payment_date = invoice_id.invoice_date
        self.action_create_rent_invoice_entry(
            amount=invoice_id.amount_total, invoice_id=invoice_id)
        self.action_send_active_contract()

    # Rent Invoice Record
    def action_create_rent_invoice_entry(self, amount, invoice_id):
        rent_invoice = {
            'tenancy_id': self.id,
            'type': 'rent',
            'invoice_date': self.invoice_start_date,
            'rent_invoice_id': invoice_id.id,
            'amount': amount,
        }
        if self.payment_term == 'monthly':
            rent_invoice['description'] = 'First Rent + Deposit' if self.is_any_deposit else "First Rent"
        if self.payment_term == 'quarterly':
            rent_invoice['description'] = 'First Quarter Rent + Deposit' if self.is_any_deposit else 'First Quarter Rent'
        if self.payment_term == 'year':
            rent_invoice['description'] = 'First Year Rent'
        self.env['rent.invoice'].create(rent_invoice)

    # Active Contract : Utility Service Invoice
    def action_utility_service_invoice(self):
        service_line = []
        for line in self.extra_services_ids:
            rec = {
                'product_id': line.service_id.id,
                'name': ("Service Type : Once" + "\n" "Service : " + str(line.service_id.name)) if line.service_type == "once" else ("Service Type : Recurring" + "\n" "Service : " + str(line.service_id.name)),
                'quantity': 1,
                'price_unit': line.price,
                'tax_ids': self.tax_ids.ids if self.service_tax else False
            }
            if self.payment_term == 'quarterly' and line.service_type == 'monthly':
                rec['quantity'] = 3
            if self.payment_term == 'year' and line.service_type == 'monthly':
                rec['quantity'] = 12
            service_line.append((0, 0, rec))
        return service_line

    # Cancel Contract

    def action_cancel_contract(self):
        self.close_contract_state = True
        self.property_id.write({'stage': 'available'})
        self.contract_type = 'cancel_contract'

    # Send active Contract Mail
    def action_send_active_contract(self):
        mail_template = self.env.ref(
            'rental_management.active_contract_mail_template')
        if mail_template:
            mail_template.send_mail(self.id, force_send=True)

    # Send Tenancy reminder Mail
    def action_send_tenancy_reminder(self):
        mail_template = self.env.ref(
            'rental_management.tenancy_reminder_mail_template')
        if mail_template:
            mail_template.send_mail(self.id, force_send=True)

    # Broker Invoice
    def action_broker_invoice(self):
        invoice_post_type = self.env['ir.config_parameter'].sudo().get_param(
            'rental_management.invoice_post_type')
        record = {
            'product_id': self.broker_item_id.id,
            'name': 'Brokerage of ' + self.property_id.name,
            'quantity': 1,
            'price_unit': self.commission
        }
        invoice_lines = [(0, 0, record)]
        data = {
            'partner_id': self.broker_id.id,
            'move_type': 'in_invoice',
            'invoice_date': self.invoice_start_date,
            'invoice_line_ids': invoice_lines
        }
        invoice_id = self.env['account.move'].sudo().create(data)
        invoice_id.tenancy_id = self.id
        invoice_id.action_post()
        self.broker_invoice_state = True
        self.broker_invoice_id = invoice_id.id
        if self.commission_from == 'customer':
            customer_invoice_id = self.env['account.move'].create(
                {
                    'partner_id': self.tenancy_id.id,
                    'move_type': 'out_invoice',
                    'invoice_date': self.invoice_start_date,
                    'invoice_line_ids': [(0, 0, {
                        'product_id': self.broker_item_id.id,
                        'name': 'Broker Brokerage of' + self.property_id.name,
                        'quantity': 1,
                        'price_unit': self.commission
                    })]
                })
            if invoice_post_type == 'automatically':
                customer_invoice_id.action_post()
            self.env['rent.invoice'].create({
                'tenancy_id': self.id,
                'type': 'rent',
                'invoice_date': customer_invoice_id.invoice_date,
                'description': "Broker Brokerage",
                'rent_invoice_id': customer_invoice_id.id,
                'amount': customer_invoice_id.amount_total,
                'rent_amount': customer_invoice_id.amount_total
            })

    # Scheduler
    # Monthly Recurring Invoice
    @api.model
    def tenancy_recurring_invoice(self):
        # today_date = datetime.date(2023, 8, 1)
        today_date = fields.Date.today()
        reminder_days = self.env['ir.config_parameter'].sudo(
        ).get_param('rental_management.reminder_days')
        invoice_post_type = self.env['ir.config_parameter'].sudo(
        ).get_param('rental_management.invoice_post_type')
        tenancy_contracts = self.env['tenancy.details'].sudo().search(
            [('contract_type', '=', 'running_contract'), ('payment_term', '=', 'monthly'),
             ('rent_unit', '=', 'Month'),
             ('type', '=', 'automatic')])
        for rec in tenancy_contracts:
            if rec.contract_type == 'running_contract' and rec.payment_term == 'monthly':
                if today_date < rec.end_date:
                    invoice_date = rec.last_invoice_payment_date + \
                        relativedelta(months=1)
                    next_invoice_date = rec.last_invoice_payment_date + relativedelta(months=1) - relativedelta(
                        days=int(reminder_days))
                    if today_date == next_invoice_date:
                        record = {
                            'product_id': rec.installment_item_id.id,
                            'name': 'Installment of ' + rec.property_id.name,
                            'quantity': 1,
                            'price_unit': rec.total_rent,
                            'tax_ids': rec.tax_ids.ids if rec.instalment_tax else False
                        }
                        invoice_lines = [(0, 0, record)]
                        if rec.is_extra_service:
                            for line in rec.extra_services_ids:
                                if line.service_type == "monthly":
                                    desc = "Service Type : Monthly" + "\n" + \
                                        "Service : " + \
                                        str(line.service_id.name)
                                    service_invoice_record = {
                                        'product_id': line.service_id.id,
                                        'name': desc,
                                        'quantity': 1,
                                        'price_unit': line.price,
                                        'tax_ids': rec.tax_ids.ids if rec.service_tax else False
                                    }
                                    invoice_lines.append(
                                        (0, 0, service_invoice_record))
                        if rec.is_maintenance_service and rec.maintenance_rent_type == 'recurring':
                            invoice_lines.append((0, 0, {
                                'product_id': rec.installment_item_id.id,
                                'name': 'Recurring Monthly Maintenance of ' + rec.property_id.name,
                                'quantity': 1,
                                'price_unit': rec.total_maintenance,
                                'tax_ids': False
                            }))
                        data = {
                            'partner_id': rec.tenancy_id.id,
                            'move_type': 'out_invoice',
                            'invoice_date': invoice_date,
                            'invoice_line_ids': invoice_lines
                        }
                        invoice_id = self.env['account.move'].sudo().create(
                            data)
                        invoice_id.tenancy_id = rec.id
                        if invoice_post_type == 'automatically':
                            invoice_id.action_post()
                        rec.last_invoice_payment_date = invoice_id.invoice_date
                        rent_invoice = {
                            'tenancy_id': rec.id,
                            'type': 'rent',
                            'invoice_date': invoice_date,
                            'description': 'Installment of ' + rec.property_id.name,
                            'rent_invoice_id': invoice_id.id,
                            'amount': invoice_id.amount_total,
                            'rent_amount': self.total_rent
                        }
                        self.env['rent.invoice'].create(rent_invoice)
                        rec.action_send_tenancy_reminder()

    # Expire Contract Scheduler
    @api.model
    def tenancy_expire(self):
        today_date = fields.Date.today()
        tenancy_contracts = self.env['tenancy.details'].sudo().search(
            [('contract_type', '=', 'running_contract')])
        for rec in tenancy_contracts:
            if rec.contract_type == 'running_contract' and today_date > rec.end_date:
                rec.contract_type = 'expire_contract'

    # Quarterly Recurring Invoice
    @api.model
    def tenancy_recurring_quarterly_invoice(self):
        today_date = fields.Date.today()
        # today_date = datetime.date(2024, 4, 1)
        reminder_days = self.env['ir.config_parameter'].sudo(
        ).get_param('rental_management.reminder_days')
        invoice_post_type = self.env['ir.config_parameter'].sudo(
        ).get_param('rental_management.invoice_post_type')
        tenancy_contracts = self.env['tenancy.details'].sudo().search(
            [('contract_type', '=', 'running_contract'), ('payment_term', '=', 'quarterly'),
             ('type', '=', 'automatic'), ('rent_unit', '=', 'Month')])
        for rec in tenancy_contracts:
            if rec.contract_type == 'running_contract' and rec.payment_term == 'quarterly':
                if today_date < rec.end_date:
                    invoice_date = rec.last_invoice_payment_date + \
                        relativedelta(months=3)
                    next_next_invoice_date = invoice_date + \
                        relativedelta(months=3)
                    next_invoice_date = rec.last_invoice_payment_date + relativedelta(months=3) - relativedelta(
                        days=int(reminder_days))
                    if rec.end_date < next_next_invoice_date:
                        delta = relativedelta(
                            next_next_invoice_date, rec.end_date)
                        diff = delta.months
                    else:
                        diff = 0
                    if today_date == next_invoice_date:
                        record = {
                            'product_id': rec.installment_item_id.id,
                            'name': 'Quarterly Installment of ' + rec.property_id.name,
                            'quantity': 1,
                            'price_unit': rec.total_rent * (3 - diff),
                            'tax_ids': rec.tax_ids.ids if rec.instalment_tax else False
                        }
                        invoice_lines = [(0, 0, record)]
                        if rec.is_extra_service:
                            for line in rec.extra_services_ids:
                                if line.service_type == "monthly":
                                    desc = "Service Type : Quarterly" + "\n" + \
                                        "Service : " + \
                                        str(line.service_id.name)
                                    service_invoice_record = {
                                        'product_id': line.service_id.id,
                                        'name': desc,
                                        'quantity': (3 - diff),
                                        'price_unit': line.price * (3 - diff),
                                        'tax_ids': rec.tax_ids.ids if rec.service_tax else False
                                    }
                                    invoice_lines.append(
                                        (0, 0, service_invoice_record))
                        if rec.is_maintenance_service and rec.maintenance_rent_type == 'recurring':
                            invoice_lines.append((0, 0, {
                                'product_id': rec.installment_item_id.id,
                                'name': 'Recurring Quarterly Maintenance of ' + rec.property_id.name,
                                'quantity': 1,
                                'price_unit': rec.total_maintenance,
                                'tax_ids': False
                            }))
                        data = {
                            'partner_id': rec.tenancy_id.id,
                            'move_type': 'out_invoice',
                            'invoice_date': invoice_date,
                            'invoice_line_ids': invoice_lines
                        }
                        invoice_id = self.env['account.move'].sudo().create(
                            data)
                        invoice_id.tenancy_id = rec.id
                        if invoice_post_type == 'automatically':
                            invoice_id.action_post()
                        rec.last_invoice_payment_date = invoice_id.invoice_date
                        rent_invoice = {
                            'tenancy_id': rec.id,
                            'type': 'rent',
                            'invoice_date': invoice_date,
                            'description': 'Quarterly Installment of ' + rec.property_id.name,
                            'rent_invoice_id': invoice_id.id,
                            'amount': invoice_id.amount_total,
                            'rent_amount': self.total_rent * (3 - diff)
                        }
                        self.env['rent.invoice'].create(rent_invoice)
                        rec.action_send_tenancy_reminder()

    # Yearly Recurring Invoice
    @api.model
    def tenancy_yearly_invoice(self):
        today_date = fields.Date.today()
        # today_date = datetime.date(2024, 7, 1)
        reminder_days = self.env['ir.config_parameter'].sudo(
        ).get_param('rental_management.reminder_days')
        invoice_post_type = self.env['ir.config_parameter'].sudo(
        ).get_param('rental_management.invoice_post_type')
        tenancy_contracts = self.env['tenancy.details'].sudo().search(
            [('contract_type', '=', 'running_contract'), ('type', '=', 'automatic'), ('payment_term', '=', 'year'),
             ('rent_unit', '=', 'Year')])
        for rec in tenancy_contracts:
            if today_date < rec.end_date:
                invoice_date = rec.last_invoice_payment_date + \
                    relativedelta(years=1)
                next_invoice_date = rec.last_invoice_payment_date + relativedelta(years=1) - relativedelta(
                    days=int(reminder_days))
                if today_date == next_invoice_date:
                    record = {
                        'product_id': rec.installment_item_id.id,
                        'name': "Service Type : Yearly" + "\n" + "Service : " + str(line.service_id.name),
                        'quantity': 1,
                        'price_unit': rec.total_rent,
                        'tax_ids': rec.tax_ids.ids if rec.instalment_tax else False
                    }
                    invoice_lines = [(0, 0, record)]
                    if rec.is_extra_service:
                        for line in rec.extra_services_ids:
                            if line.service_type == "monthly":
                                desc = "Monthly"
                                service_invoice_record = {
                                    'product_id': line.service_id.id,
                                    'name': desc,
                                    'quantity': 12,
                                    'price_unit': line.price,
                                    'tax_ids': rec.tax_ids.ids if rec.service_tax else False
                                }
                                invoice_lines.append(
                                    (0, 0, service_invoice_record))

                    if rec.is_maintenance_service and rec.maintenance_rent_type == 'recurring':
                        invoice_lines.append((0, 0, {
                            'product_id': rec.installment_item_id.id,
                            'name': 'Recurring Monthly Maintenance of ' + rec.property_id.name,
                            'quantity': 12,
                            'price_unit': rec.total_maintenance,
                            'tax_ids': False
                        }))
                    data = {
                        'partner_id': rec.tenancy_id.id,
                        'move_type': 'out_invoice',
                        'invoice_date': invoice_date,
                        'invoice_line_ids': invoice_lines
                    }
                    invoice_id = self.env['account.move'].sudo().create(data)
                    invoice_id.tenancy_id = rec.id
                    if invoice_post_type == 'automatically':
                        invoice_id.action_post()
                    rec.last_invoice_payment_date = invoice_id.invoice_date
                    rent_invoice = {
                        'tenancy_id': rec.id,
                        'type': 'rent',
                        'invoice_date': invoice_date,
                        'description': 'Installment of ' + rec.property_id.name,
                        'rent_invoice_id': invoice_id.id,
                        'amount': invoice_id.amount_total,
                        'rent_amount': self.total_rent
                    }
                    self.env['rent.invoice'].create(rent_invoice)
                    rec.action_send_tenancy_reminder()

    # Manual Invoice Rent Invoice Line
    @api.model
    def tenancy_manual_invoice(self):
        today_date = fields.Date.today()
        # today_date = datetime.date(2023, 8, 2)
        reminder_days = self.env['ir.config_parameter'].sudo(
        ).get_param('rental_management.reminder_days')
        tenancy_contracts = self.env['tenancy.details'].sudo().search(
            [('contract_type', '=', 'running_contract'), ('type', '=', 'manual')])
        for data in tenancy_contracts:
            for rec in data.rent_invoice_ids:
                if not rec.rent_invoice_id:
                    invoice_date = rec.invoice_date - \
                        relativedelta(days=int(reminder_days))
                    if today_date == invoice_date:
                        rec.action_create_invoice()
            data.action_send_tenancy_reminder()


# Contract Duration
class ContractDuration(models.Model):
    _name = 'contract.duration'
    _description = 'Contract Duration and Month'
    _rec_name = 'duration'

    duration = fields.Char(string='Duration', required=True, translate=True)
    month = fields.Integer(string='Unit')
    rent_unit = fields.Selection([('Day', "Day"),
                                  ('Month', "Month"),
                                  ('Year', "Year")],
                                 default='Month',
                                 string="Rent Unit")


# Tenancy Utility Service Line
class TenancyExtraServiceLine(models.Model):
    _name = "tenancy.service.line"
    _description = "Tenancy Service Line"

    service_id = fields.Many2one('product.product', string="Service",
                                 domain=[('is_extra_service_product', '=', True)])
    price = fields.Float(string="Cost")
    service_type = fields.Selection(
        [('once', 'Once'), ('monthly', 'Recurring')], string="Type", default="once")
    tenancy_id = fields.Many2one('tenancy.details', string="Tenancies")
    from_contract = fields.Boolean()

    @api.onchange('service_id')
    def _onchange_service_id_price(self):
        for rec in self:
            if rec.service_id:
                rec.price = rec.service_id.lst_price

    def action_create_service_invoice(self):
        invoice_post_type = self.env['ir.config_parameter'].sudo(
        ).get_param('rental_management.invoice_post_type')
        self.from_contract = True
        record = {
            'product_id': self.service_id.id,
            'name': "Extra Added Service",
            'quantity': 1,
            'price_unit': self.service_id.lst_price,
            'tax_ids': self.tenancy_id.tax_ids.ids if self.tenancy_id.service_tax else False
        }
        invoice_lines = [(0, 0, record)]
        data = {
            'partner_id': self.tenancy_id.tenancy_id.id,
            'move_type': 'out_invoice',
            'invoice_date': fields.Date.today(),
            'invoice_line_ids': invoice_lines
        }
        invoice_id = self.env['account.move'].sudo().create(data)
        invoice_id.tenancy_id = self.tenancy_id.id
        if invoice_post_type == 'automatically':
            invoice_id.action_post()
        rent_invoice = {
            'tenancy_id': self.tenancy_id.id,
            'type': 'maintenance',
            'amount': self.service_id.lst_price,
            'invoice_date': fields.Date.today(),
            'description': 'New Service',
            'rent_invoice_id': invoice_id.id
        }
        self.env['rent.invoice'].create(rent_invoice)


# Agreement Template
class AgreementTemplate(models.Model):
    _name = "agreement.template"
    _description = "Agreement Template"

    name = fields.Char(string="Title", translate=True)
    company_id = fields.Many2one(
        'res.company', string='Company', default=lambda self: self.env.company)
    agreement = fields.Html(string="Agreement")
