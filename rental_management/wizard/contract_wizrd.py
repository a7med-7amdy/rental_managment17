# -*- coding: utf-8 -*-
# Copyright 2020-Today TechKhedut.
# Part of TechKhedut. See LICENSE file for full copyright and licensing details.
import datetime
from email.policy import default

from odoo import fields, models, api, _
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError, ValidationError


class ContractWizard(models.TransientModel):
    _name = 'contract.wizard'
    _description = 'Create Contract of rent in property'

    # Customer Details
    customer_id = fields.Many2one('res.partner', string='Customer',
                                  domain=[('user_type', '=', 'customer')])

    # Company & Currency
    currency_id = fields.Many2one('res.currency', string='Currency',
                                  related='company_id.currency_id')
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env.company)

    # Deposit
    is_any_deposit = fields.Boolean(string="Deposit")
    deposit_amount = fields.Monetary(string="Security Deposit")

    # Property Details
    property_id = fields.Many2one('property.details', string='Property')
    rent_unit = fields.Selection(related="property_id.rent_unit")
    total_rent = fields.Monetary(related='property_id.price',
                                 string='Related')
    is_extra_service = fields.Boolean(related="property_id.is_extra_service",
                                      string="Any Extra Services")
    services = fields.Text(string="Utility Services",
                           compute="_compute_services", translate=True)
    is_any_maintenance = fields.Boolean(string="Any Maintenance",
                                        related="property_id.is_maintenance_service")
    maintenance_rent_type = fields.Selection(
        related="property_id.maintenance_rent_type")
    total_maintenance = fields.Monetary(
        related='property_id.total_maintenance')

    # Contract Detail
    payment_term = fields.Selection([('monthly', 'Monthly'),
                                     ('full_payment', 'Full Payment'),
                                     ('quarterly', 'Quarterly'),
                                     ('year', 'Yearly')],
                                    string='Payment Term')
    duration_ids = fields.Many2many('contract.duration', string="Durations",
                                    compute="compute_durations")
    duration_id = fields.Many2one('contract.duration', string='Duration',
                                  domain="[('id','in',duration_ids)]")
    start_date = fields.Date(string='Start Date')

    # Broker Details
    is_any_broker = fields.Boolean(string='Any Broker?')
    broker_id = fields.Many2one('res.partner', string='Broker',
                                domain=[('user_type', '=', 'broker')])
    rent_type = fields.Selection([('once', 'First Month'),
                                  ('e_rent', 'All Month')],
                                 string='Brokerage Type')
    commission_type = fields.Selection([('f', 'Fix'), ('p', 'Percentage')],
                                       string="Commission Type")
    commission_from = fields.Selection([
        ('landlord_and_customer', 'Landlord & Customer',),
        ('customer', 'Customer'),
        ('landlord', 'Landlord',)
    ],
        string="Commission From", default='landlord_and_customer')
    broker_commission = fields.Monetary(string='Commission')
    broker_commission_percentage = fields.Float(string='Percentage')

    # Leads
    from_inquiry = fields.Boolean('From Enquiry')
    lead_id = fields.Many2one('crm.lead', string="Enquiry",
                              domain="[('property_id','=',property_id)]")
    inquiry_id = fields.Many2one('tenancy.inquiry', string="Inquiry")
    note = fields.Text(string="Note", translate=True)

    # Agreement
    agreement = fields.Html(string="Agreement")
    agreement_template_id = fields.Many2one('agreement.template',
                                            string="Agreement Template",
                                            domain="[('company_id','=',company_id)]")

    # Instalment Item
    installment_item_id = fields.Many2one('product.product',
                                          string="Installment Item")
    deposit_item_id = fields.Many2one('product.product', string="Deposit Item")
    broker_item_id = fields.Many2one('product.product', string="Broker Item")

    # Taxes
    instalment_tax = fields.Boolean(string="Taxes on Installment ?")
    deposit_tax = fields.Boolean(string="Taxes on Deposit ?")
    service_tax = fields.Boolean(string="Taxes on Services ?")
    tax_ids = fields.Many2many('account.tax', string="Taxes")

    # Terms & Conditions
    term_condition = fields.Html(string='Term and Condition')

    # Extend Contract
    is_contract_extend = fields.Boolean(string="Extend Contract")

    # Default Get
    @api.model
    def default_get(self, fields):
        res = super(ContractWizard, self).default_get(fields)
        active_id = self._context.get('active_id')
        active_model = self._context.get('active_model')
        if active_model == 'property.details':
            property_id = self.env['property.details'].browse(active_id)
            res['installment_item_id'] = self.env.ref(
                'rental_management.property_product_1').id
            res['deposit_item_id'] = self.env.ref(
                'rental_management.property_product_2').id
            res['broker_item_id'] = self.env.ref(
                'rental_management.property_product_1').id
            res['property_id'] = active_id
            if property_id.rent_unit == 'Day':
                res['payment_term'] = 'full_payment'
            if property_id.rent_unit == 'Year':
                res['payment_term'] = 'year'
        if active_model == 'tenancy.details':
            tenancy_id = self.env['tenancy.details'].browse(active_id)
            res['property_id'] = tenancy_id.property_id.id
            res['customer_id'] = tenancy_id.tenancy_id.id
            res['start_date'] = tenancy_id.end_date + relativedelta(days=1)
            res['is_contract_extend'] = True
            res['installment_item_id'] = tenancy_id.installment_item_id.id
            res['deposit_item_id'] = tenancy_id.deposit_item_id.id
            res['broker_item_id'] = tenancy_id.broker_item_id.id
            res['is_any_deposit'] = tenancy_id.is_any_deposit
            res['deposit_amount'] = tenancy_id.deposit_amount
            if tenancy_id.rent_unit == 'Day':
                res['payment_term'] = 'full_payment'
            if tenancy_id.rent_unit == 'Year':
                res['payment_term'] = 'year'
            # Broker Detail
            res['is_any_broker'] = tenancy_id.is_any_broker
            res['broker_id'] = tenancy_id.broker_id.id
            res['commission_from'] = tenancy_id.commission_from
            res['rent_type'] = tenancy_id.rent_type
            res['commission_type'] = tenancy_id.commission_type
            res['broker_commission_percentage'] = tenancy_id.broker_commission_percentage
            res['broker_commission'] = tenancy_id.broker_commission
            res['term_condition'] = tenancy_id.term_condition
        return res

    # Domain
    @api.depends('payment_term', 'rent_unit')
    def compute_durations(self):
        for rec in self:
            duration_record = self.env['contract.duration'].sudo()
            ids = []
            if rec.rent_unit == 'Day':
                domain = [('rent_unit', '=', 'Day')]
                ids = duration_record.search(domain).mapped('id')
            if rec.rent_unit == "Year":
                domain = [('rent_unit', '=', 'Year')]
                ids = duration_record.search(domain).mapped('id')
            if rec.rent_unit == "Month":
                if rec.payment_term == 'quarterly':
                    domain = [('month', '>=', 3), ('rent_unit', '=', 'Month')]
                    ids = duration_record.search(domain).mapped('id')
                elif rec.payment_term == 'year':
                    domain = [('rent_unit', '=', 'Year')]
                    ids = duration_record.search(domain).mapped('id')
                else:
                    domain = [('month', '>', 0), ('rent_unit', '=', 'Month')]
                    ids = duration_record.search(domain).mapped('id')
            rec.duration_ids = ids

    # Onchange
    # Payment Term
    @api.onchange('payment_term')
    def onchange_payment_term(self):
        for rec in self:
            rec.duration_id = False

    # Agreement
    @api.onchange('agreement_template_id')
    def _onchange_agreement_template_id(self):
        for rec in self:
            rec.agreement = rec.agreement_template_id.agreement

    # Leads Info
    @api.onchange('lead_id')
    def _onchange_tenancy_inquiry(self):
        for rec in self:
            if rec.from_inquiry and rec.lead_id:
                rec.note = rec.lead_id.description
                rec.customer_id = rec.lead_id.partner_id.id

    # Compute
    # Services
    @api.depends('property_id')
    def _compute_services(self):
        for rec in self:
            services = ""
            if rec.property_id and rec.is_extra_service:
                for data in rec.property_id.extra_service_ids:
                    services = services + str(data.service_id.name) + "[" + str(
                        "Once" if data.service_type == "once" else "Recurring") + "] - " + str(
                        rec.currency_id.symbol) + " " + str(data.price) + "\n"
            rec.services = services

    # Contract Creation
    def contract_action(self):
        commission_from_lst = ['customer', 'landlord'] if self.commission_from == 'landlord_and_customer' else [self.commission_from]
        created_contract_ids = self.env['tenancy.details']
        active_model = self._context.get('active_model')
        active_id = self._context.get('active_id')
        self.customer_id.user_type = "customer"
        if active_model == 'tenancy.details':
            tenancy_id = self.env['tenancy.details'].browse(active_id)
            tenancy_id.contract_type = 'close_contract'
            tenancy_id.close_contract_state = True
        service_line = []
        for rec in self:
            if rec.property_id.is_extra_service:
                for data in rec.property_id.extra_service_ids:
                    service_record = {
                        'service_id': data.service_id.id,
                        'service_type': data.service_type,
                        'from_contract': True,
                        'price': data.price
                    }
                    service_line.append((0, 0, service_record))
        record = self.get_contract_info()
        # Utilities
        if service_line:
            record['extra_services_ids'] = service_line
        # Payment Term : Full Payment
        if self.payment_term == 'full_payment':
            record['last_invoice_payment_date'] = fields.Date.today()
            record['active_contract_state'] = True
            record['contract_type'] = 'running_contract'
            contract_id = self.env['tenancy.details']
            for comm in commission_from_lst:
                record['commission_from'] = comm
                contract_id = self.env['tenancy.details'].create(record)
                created_contract_ids += contract_id
            if contract_id.is_any_broker:
                contract_id.action_broker_invoice()
            # Full Payment Invoice
            self.action_create_full_payment_invoice(contract_id=contract_id)
            self.customer_id.is_tenancy = True
            self.property_id.write({'stage': 'on_lease'})
            if active_model == 'tenancy.details':
                old_tenancy_id = self.env['tenancy.details'].browse(active_id)
                old_tenancy_id.extended = True
                old_tenancy_id.extend_ref = contract_id.tenancy_seq
                old_tenancy_id.new_contract_id = contract_id.id
                contract_id.is_extended = True
                contract_id.extend_from = old_tenancy_id.tenancy_seq
            # return {
            #     'type': 'ir.actions.act_window',
            #     'name': 'Contract',
            #     'res_model': 'tenancy.details',
            #     'res_id': contract_id.id,
            #     'view_mode': 'form,tree',
            #     'target': 'current'
            # }
        # Payment Term : Monthly Quarterly, Year
        elif self.payment_term in ['monthly', 'quarterly', 'year']:
            record['contract_type'] = 'new_contract'
            if self.payment_term == 'year' and not self.rent_unit == "Year":
                message = {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'type': 'info',
                        'title': ('Please select rent unit year to create contract with payment term year'),
                        'sticky': True,
                    }
                }
                return message
            contract_id = self.env['tenancy.details']
            for comm in commission_from_lst:
                record['commission_from'] = comm
                contract_id = self.env['tenancy.details'].create(record)
                created_contract_ids += contract_id
            self.customer_id.is_tenancy = True
            self.property_id.write({'stage': 'on_lease'})
            if active_model == 'tenancy.details':
                old_tenancy_id = self.env['tenancy.details'].browse(active_id)
                old_tenancy_id.extended = True
                old_tenancy_id.extend_ref = contract_id.tenancy_seq
                old_tenancy_id.new_contract_id = contract_id.id
                contract_id.is_extended = True
                contract_id.extend_from = old_tenancy_id.tenancy_seq
        return {
            'type': 'ir.actions.act_window',
            'name': 'Contract',
            'res_model': 'tenancy.details',
            # 'res_id': contract_id.id,
            'domain': [('id', 'in', created_contract_ids.ids)],
            'view_mode': 'tree,form',
            'target': 'current'
        }

    @api.constrains('is_contract_extend')
    def check_contract_start_date(self):
        for rec in self:
            if rec.is_contract_extend:
                active_model = self._context.get('active_model')
                active_id = self._context.get('active_id')
                if active_model == 'tenancy.details':
                    tenancy_id = self.env['tenancy.details'].sudo().browse(
                        active_id)
                    if rec.start_date < tenancy_id.end_date:
                        raise ValidationError(
                            _("Contract start date must be greater than previous contract end date"))

    def get_contract_info(self):
        data = {
            # Customer
            'tenancy_id': self.customer_id.id,
            # Property
            'property_id': self.property_id.id,
            'total_rent': self.total_rent,
            # Broker
            'is_any_broker': self.is_any_broker,
            'broker_id': self.broker_id.id,
            'rent_type': self.rent_type,
            'commission_type': self.commission_type,
            'broker_commission': self.broker_commission,
            'broker_commission_percentage': self.broker_commission_percentage,
            'commission_from': self.commission_from,
            # Contract Details
            'duration_id': self.duration_id.id,
            'start_date': self.start_date,
            'invoice_start_date': self.start_date,
            'payment_term': self.payment_term,
            # Deposit
            'is_any_deposit': self.is_any_deposit,
            'deposit_amount': self.deposit_amount,
            # agreement
            'agreement': self.agreement,
            # Installment Item
            'installment_item_id': self.installment_item_id.id,
            'broker_item_id': self.broker_item_id.id,
            'deposit_item_id': self.deposit_item_id.id,
            # Taxes
            'tax_ids': self.tax_ids.ids,
            'instalment_tax': self.instalment_tax,
            'service_tax': self.service_tax,
            'deposit_tax': self.deposit_tax,
            # Terms Conditions
            'term_condition': self.term_condition
        }
        return data

    def action_create_full_payment_invoice(self, contract_id):
        invoice_post_type = self.env['ir.config_parameter'].sudo(
        ).get_param('rental_management.invoice_post_type')
        service_invoice_line = []
        desc = ""
        full_payment_record = {
            'product_id': self.installment_item_id.id,
            'name': 'Full Payment of ' + self.property_id.name,
            'quantity': 1,
            'price_unit': self.total_rent * self.duration_id.month,
            'tax_ids': self.tax_ids.ids if self.instalment_tax else False
        }
        service_invoice_line.append((0, 0, full_payment_record))
        if self.is_any_deposit:
            deposit_record = {
                'product_id': self.deposit_item_id.id,
                'name': 'Deposit of ' + self.property_id.name,
                'quantity': 1,
                'price_unit': self.deposit_amount,
                'tax_ids': self.tax_ids.ids if self.deposit_tax else False
            }
            service_invoice_line.append((0, 0, deposit_record))
        if self.is_any_maintenance:
            maintenance_record = {
                'product_id': self.installment_item_id.id,
                'name': 'Maintenance of ' + self.property_id.name,
                'quantity': 1,
                'price_unit': self.total_maintenance if self.maintenance_rent_type == 'once' else self.total_maintenance * self.duration_id.month,
            }
            service_invoice_line.append((0, 0, maintenance_record))
        for rec in self:
            if rec.property_id.is_extra_service:
                for line in rec.property_id.extra_service_ids:
                    if line.service_type == "once":
                        desc = "Service Type : Once" + \
                               "\n" "Service : " + str(line.service_id.name)
                    if line.service_type == "monthly":
                        desc = "Service Type : Recurring" + \
                               "\n" "Service : " + str(line.service_id.name)
                    service_invoice_record = {
                        'product_id': line.service_id.id,
                        'name': desc,
                        'quantity': 1 if line.service_type == 'once' else self.duration_id.month,
                        'price_unit': line.price,
                        'tax_ids': self.tax_ids.ids if self.service_tax else False
                    }
                    service_invoice_line.append(
                        (0, 0, service_invoice_record))
        data = {
            'partner_id': self.customer_id.id,
            'move_type': 'out_invoice',
            'invoice_date': contract_id.invoice_start_date,
            'invoice_line_ids': service_invoice_line
        }
        invoice_id = self.env['account.move'].sudo().create(data)
        invoice_id.tenancy_id = contract_id.id
        if invoice_post_type == 'automatically':
            invoice_id.action_post()
        #  Rent Invoice Entry
        rent_invoice = {
            'tenancy_id': contract_id.id,
            'type': 'full_rent',
            'invoice_date': contract_id.invoice_start_date,
            'amount': invoice_id.amount_total,
            'description': 'Full Payment Of Rent',
            'rent_invoice_id': invoice_id.id,
            'rent_amount': invoice_id.amount_total
        }
        if self.is_any_deposit:
            rent_invoice['description'] = 'Full Payment Of Rent + Deposit'
        else:
            rent_invoice['description'] = 'Full Payment Of Rent'
        self.env['rent.invoice'].create(rent_invoice)
        contract_id.action_send_active_contract()
