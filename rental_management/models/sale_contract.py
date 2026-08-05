# -*- coding: utf-8 -*-
# Copyright 2020-Today TechKhedut.
# Part of TechKhedut. See LICENSE file for full copyright and licensing details.
from dateutil.relativedelta import relativedelta
from odoo import fields, api, models, _
from odoo.fields import Command
from odoo.exceptions import UserError, ValidationError

import logging

_logger = logging.getLogger(__name__)


class PropertyVendor(models.Model):
    _name = 'property.vendor'
    _description = 'Stored Data About Sold Property'
    _rec_name = 'sold_seq'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _check_company_auto = True

    # Sale Contract Details
    sold_seq = fields.Char(string='Sequence',
                           required=True,
                           readonly=True, copy=False, default=lambda self: ('New'),
                           translate=True)
    stage = fields.Selection(
        [('booked', 'Booked'), ('refund', 'Refund'), ('sold', 'Sold')],
        string='Stage', required=True, default='booked', tracking=True,
    )
    company_id = fields.Many2one(
        'res.company', string='Company', required=True, index=True,
        default=lambda self: self.env.company,
    )
    currency_id = fields.Many2one('res.currency',
                                  related='company_id.currency_id',
                                  string='Currency')
    date = fields.Date(string='Create Date', default=fields.Date.today)

    # Property Detail
    property_id = fields.Many2one(
        'property.details', string='Property', check_company=True,
        domain=[('stage', '=', 'sale')],
    )
    price = fields.Monetary(related="property_id.price",
                            string="Price")
    type = fields.Selection(related="property_id.type", store=True)
    property_subtype_id = fields.Many2one(store=True,
                                          related="property_id.property_subtype_id")
    property_project_id = fields.Many2one(related="property_id.property_project_id",
                                          string="Project",store=True)
    subproject_id = fields.Many2one(related="property_id.subproject_id",
                                    string="Sub Project",store=True)
    total_area = fields.Float(related="property_id.total_area")
    usable_area = fields.Float(related="property_id.usable_area")
    measure_unit = fields.Selection(related="property_id.measure_unit")
    region_id = fields.Many2one(related="property_id.region_id")
    zip = fields.Char(related="property_id.zip")
    street = fields.Char(related="property_id.street", translate=True)
    street2 = fields.Char(related="property_id.street2", translate=True)
    city_id = fields.Many2one(related="property_id.city_id", string='City')
    country_id = fields.Many2one(related="property_id.country_id",
                                 string='Country')
    state_id = fields.Many2one(related="property_id.state_id")

    # Broker Details
    is_any_broker = fields.Boolean(string='Any Broker')
    broker_id = fields.Many2one('res.partner', string='Broker',
                                domain=[('user_type', '=', 'broker')])
    broker_final_commission = fields.Monetary(string='Commission',
                                              compute="_compute_broker_final_commission")
    broker_commission = fields.Monetary(string='Commission ')
    commission_type = fields.Selection([('f', 'Fix'),
                                        ('p', 'Percentage')],
                                       string="Commission Type")
    broker_commission_percentage = fields.Float(string='Percentage')
    commission_from = fields.Selection([('customer', 'Customer'),
                                        ('landlord', 'Landlord',)],
                                       string="Commission From")
    broker_bill_id = fields.Many2one('account.move',
                                     string='Broker Bill',
                                     readonly=True)
    broker_bill_payment_state = fields.Selection(related='broker_bill_id.payment_state',
                                                 string="Payment Status ")
    broker_invoice_id = fields.Many2one('account.move',
                                        string="Broker Invoice")
    broker_invoice_payment_state = fields.Selection(string="Broker Invoice Payment State",
                                                    related="broker_invoice_id.payment_state")

    # Customer Detail
    customer_id = fields.Many2one('res.partner', string='Customer',
                                  domain=[('user_type', '=', 'customer')])
    customer_phone = fields.Char(string="Phone", related="customer_id.phone")
    customer_email = fields.Char(string="Email", related="customer_id.email")

    # Landlord Details
    landlord_id = fields.Many2one(related="property_id.landlord_id",
                                  store=True)
    landlord_phone = fields.Char(related="landlord_id.phone",
                                 string="Landlord Phone")
    landlord_email = fields.Char(related="landlord_id.email",
                                 string="Landlord Email")

    # Payment Details & Remaining Payment
    payment_term = fields.Selection([('monthly', 'Monthly'),
                                     ('full_payment', 'Full Payment'),
                                     ('quarterly', 'Quarterly')],
                                    string='Payment Term')
    sale_invoice_ids = fields.One2many('sale.invoice',
                                       'property_sold_id',
                                       string="Invoices")
    book_price = fields.Monetary(string='Book Price')
    sale_price = fields.Monetary(string='Confirmed Sale Price', store=True)
    ask_price = fields.Monetary(string='Customer Ask Price')
    book_invoice_id = fields.Many2one('account.move',
                                      string='Advance',
                                      readonly=True)
    book_invoice_payment_state = fields.Selection(related='book_invoice_id.payment_state',
                                                  string="Payment Status")
    book_invoice_state = fields.Boolean(string='Invoice State')
    remain_invoice_id = fields.Many2one('account.move', string="Invoice")
    remain_check = fields.Boolean(compute="_compute_remain_check")
    # Maintenance and utility Service
    is_any_maintenance = fields.Boolean(
        related="property_id.is_maintenance_service")
    total_maintenance = fields.Monetary(
        related="property_id.total_maintenance")
    is_utility_service = fields.Boolean(related="property_id.is_extra_service")
    total_service = fields.Monetary(related="property_id.extra_service_cost")
    # Total Amount Calculation
    total_sell_amount = fields.Monetary(string="Total Amount",
                                        compute="compute_sell_price")
    payable_amount = fields.Monetary(string="Total Payable Amount",
                                     compute="compute_sell_price")

    # Invoice Payment Calculation
    total_untaxed_amount = fields.Monetary(
        string="Untaxed Amount", compute="_compute_remain_amount")
    tax_amount = fields.Monetary(
        string="Tax Amount", compute="_compute_remain_amount")
    total_amount = fields.Monetary(
        string="Total Amount ", compute="_compute_remain_amount")
    remaining_amount = fields.Monetary(
        string="Remaining Amount", compute="_compute_remain_amount")
    paid_amount = fields.Monetary(
        string="Paid", compute="_compute_remain_amount")

    # Documents
    sold_document = fields.Binary(string='Sold Document')
    file_name = fields.Char('File Name', translate=True)

    # Terms & Conditions
    term_condition = fields.Html(string='Term and Condition')

    # Item & Taxes
    booking_item_id = fields.Many2one('product.product',
                                      string="Booking Item",
                                      default=lambda self: self.env.ref('rental_management.property_product_2',
                                                                        raise_if_not_found=False))
    broker_item_id = fields.Many2one('product.product',
                                     string="Broker Item",
                                     default=lambda self: self.env.ref('rental_management.property_product_1').id)
    installment_item_id = fields.Many2one('product.product',
                                          string="Installment Item",
                                          default=lambda self: self.env.ref('rental_management.property_product_1').id)
    is_taxes = fields.Boolean(string="Taxes ?")
    taxes_ids = fields.Many2many('account.tax', string="Taxes")

    # DEPRECATED START---------------------------------------------------
    sold_invoice_id = fields.Many2one('account.move',
                                      string='Sold Invoice',
                                      readonly=True)
    sold_invoice_state = fields.Boolean(string='Sold Invoice State')
    sold_invoice_payment_state = fields.Selection(related='sold_invoice_id.payment_state',
                                                  string="Payment Status  ")

    # --------------------------------------------------------DEPRECATED END

    # Create Write, Scheduler, Name-get
    # Create
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('sold_seq', _('New')) == _('New'):
                vals['sold_seq'] = self.env['ir.sequence'].next_by_code(
                    'property.vendor') or _('New')
        res = super(PropertyVendor, self).create(vals_list)
        return res

    @api.depends("sold_seq", "customer_id.name")
    def _compute_display_name(self):
        for record in self:
            parts = [record.sold_seq, record.customer_id.display_name]
            record.display_name = " - ".join(filter(None, parts)) or _("Property Sale")

    # Scheduler
    @api.model
    def sale_recurring_invoice(self, batch_size=200):
        """Create all due sale installment invoices without duplicating them."""
        reminder_days = int(
            self.env['ir.config_parameter'].sudo().get_param(
                'rental_management.sale_reminder_days', '0'
            )
            or 0
        )
        today_date = fields.Date.context_today(self)
        due_limit = today_date + relativedelta(days=max(reminder_days, 0))
        sale_invoices = self.env['sale.invoice'].search(
            [
                ('invoice_created', '=', False),
                ('invoice_date', '!=', False),
                ('invoice_date', '<=', due_limit),
            ],
            order='invoice_date, id',
            limit=batch_size,
        )
        invoice_post_type = self.env['ir.config_parameter'].sudo().get_param(
            'rental_management.invoice_post_type'
        )
        for data in sale_invoices:
            try:
                with self.env.cr.savepoint():
                    if data.invoice_id:
                        data.write({'invoice_created': True, 'reminder_processed': True})
                        continue
                    product = data.property_sold_id.installment_item_id
                    if not product:
                        continue
                    record = {
                        'product_id': product.id,
                        'name': (data.name or _("Sale installment")) + "\n" + (data.desc or ""),
                        'quantity': 1.0,
                        'price_unit': data.amount,
                    }
                    if data.tax_ids:
                        record['tax_ids'] = [Command.set(data.tax_ids.ids)]
                    invoice_id = self.env['account.move'].with_company(
                        data.property_sold_id.company_id
                    ).create({
                        'partner_id': data.property_sold_id.customer_id.id,
                        'move_type': 'out_invoice',
                        'sold_id': data.property_sold_id.id,
                        'sale_schedule_id': data.id,
                        'company_id': data.property_sold_id.company_id.id,
                        'currency_id': data.property_sold_id.currency_id.id,
                        'invoice_date': data.invoice_date,
                        'invoice_origin': data.property_sold_id.sold_seq,
                        'invoice_line_ids': [Command.create(record)],
                    })
                    if invoice_post_type == 'automatically':
                        invoice_id.action_post()
                    data.write({
                        'invoice_id': invoice_id.id,
                        'invoice_created': True,
                        'reminder_processed': True,
                    })
            except Exception:
                _logger.exception('Sale installment invoicing failed for schedule %s', data.display_name)
        return len(sale_invoices)

    # Compute
    # Total amount paid amount, remaining amount
    @api.depends(
        'sale_invoice_ids.amount', 'sale_invoice_ids.tax_amount',
        'sale_invoice_ids.invoice_created', 'sale_invoice_ids.payment_state',
        'sale_invoice_ids.invoice_id.amount_total',
    )
    def _compute_remain_amount(self):
        for rec in self:
            paid_amount = 0.0
            tax_amount = 0.0
            total_untaxed_amount = 0.0
            if rec.sale_invoice_ids:
                for data in rec.sale_invoice_ids:
                    total_untaxed_amount = total_untaxed_amount + data.amount
                    tax_amount = tax_amount + data.tax_amount
                    if data.invoice_created and data.payment_state == "paid":
                        paid_amount = paid_amount + data.invoice_id.amount_total
            rec.tax_amount = tax_amount
            rec.total_untaxed_amount = total_untaxed_amount
            rec.total_amount = tax_amount + total_untaxed_amount
            rec.paid_amount = paid_amount
            rec.remaining_amount = tax_amount + total_untaxed_amount - paid_amount

    # Remain Check
    @api.depends('sale_invoice_ids.is_remain_invoice')
    def _compute_remain_check(self):
        for rec in self:
            rec.remain_check = any(rec.sale_invoice_ids.mapped('is_remain_invoice'))

    # Broker Commission
    @api.depends(
        'is_any_broker', 'broker_id', 'commission_type', 'sale_price',
        'broker_commission_percentage', 'broker_commission',
    )
    def _compute_broker_final_commission(self):
        for rec in self:
            if rec.is_any_broker:
                if rec.commission_type == 'p':
                    rec.broker_final_commission = rec.sale_price * \
                        rec.broker_commission_percentage / 100
                else:
                    rec.broker_final_commission = rec.broker_commission
            else:
                rec.broker_final_commission = 0.0

    # Sell Price Calculation
    @api.depends('sale_price',
                 'book_price',
                 'total_service',
                 'is_utility_service',
                 'total_maintenance',
                 'is_any_maintenance')
    def compute_sell_price(self):
        for rec in self:
            total_sell_amount = 0.0
            if rec.is_any_maintenance:
                total_sell_amount = total_sell_amount + rec.total_maintenance
            if rec.is_utility_service:
                total_sell_amount = total_sell_amount + rec.total_service
            total_sell_amount = total_sell_amount + rec.sale_price
            rec.payable_amount = total_sell_amount + rec.book_price
            rec.total_sell_amount = total_sell_amount

    @api.constrains("broker_commission", "broker_commission_percentage", "commission_type")
    def _check_broker_commission_values(self):
        for record in self:
            if record.broker_commission < 0:
                raise ValidationError(_("Broker commission cannot be negative."))
            if record.commission_type == "p" and not 0 <= record.broker_commission_percentage <= 100:
                raise ValidationError(_("Broker commission percentage must be between 0 and 100."))

    @api.constrains("property_id", "company_id")
    def _check_property_company(self):
        for record in self:
            if record.property_id and record.property_id.company_id != record.company_id:
                raise ValidationError(_("The sold property and sale contract must belong to the same company."))

    def _get_invoice_action(self, invoice, title):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": title,
            "res_model": "account.move",
            "res_id": invoice.id,
            "view_mode": "form",
            "target": "current",
        }

    # Mail Template
    # Sold Mail
    def send_sold_mail(self):
        self.ensure_one()
        if not self.customer_id.email:
            raise UserError(_("The customer must have an email address before sending the sold-property notice."))
        mail_template = self.env.ref(
            'rental_management.property_sold_mail_template', raise_if_not_found=False)
        if mail_template:
            mail_template.send_mail(self.id, force_send=True)
        return True

    # Button
    # Advance Payment Invoice
    def action_book_invoice(self):
        self.ensure_one()
        if self.book_invoice_id:
            return self._get_invoice_action(self.book_invoice_id, _("Booking Invoice"))
        if not self.property_id or not self.customer_id:
            raise UserError(_("Property and customer are required before creating the booking invoice."))
        if self.book_price <= 0:
            raise UserError(_("The booking amount must be greater than zero."))
        product = self.booking_item_id
        if not product:
            raise UserError(_("Configure a booking product before creating the booking invoice."))
        invoice = self.env['account.move'].with_company(self.company_id).create({
            'partner_id': self.customer_id.id,
            'move_type': 'out_invoice',
            'sold_id': self.id,
            'company_id': self.company_id.id,
            'currency_id': self.currency_id.id,
            'invoice_origin': self.sold_seq,
            'invoice_date': fields.Date.context_today(self),
            'invoice_line_ids': [Command.create({
                'product_id': product.id,
                'name': _("Booking amount for %s") % self.property_id.display_name,
                'quantity': 1.0,
                'price_unit': self.book_price,
                'tax_ids': [Command.set(self.taxes_ids.ids)] if self.taxes_ids else [],
            })],
        })
        invoice_post_type = self.env['ir.config_parameter'].sudo().get_param(
            'rental_management.invoice_post_type'
        )
        if invoice_post_type == 'automatically':
            invoice.action_post()
        self.write({
            'book_invoice_id': invoice.id,
            'book_invoice_state': True,
            'stage': 'booked',
        })
        self.property_id.stage = 'booked'
        mail_template = self.env.ref(
            'rental_management.property_book_mail_template', raise_if_not_found=False)
        if mail_template and self.customer_id.email:
            mail_template.send_mail(self.id, force_send=True)
        return self._get_invoice_action(invoice, _("Booking Invoice"))

    # Refund Amount
    def action_refund_amount(self):
        for rec in self:
            rec.stage = 'refund'
            rec.property_id.stage = "available"
            rec.property_id.sold_booking_id = None

    # Receive Remain Payment and Create Invoice
    def action_receive_remaining(self):
        self.ensure_one()
        existing = self.sale_invoice_ids.filtered(lambda line: line.is_remain_invoice)[:1]
        if existing:
            return {
                "type": "ir.actions.act_window",
                "name": _("Remaining Payment"),
                "res_model": "sale.invoice",
                "res_id": existing.id,
                "view_mode": "form",
                "target": "current",
            }
        pending = self.sale_invoice_ids.filtered(
            lambda line: not line.invoice_created and not line.is_remain_invoice
        )
        amount = sum(pending.mapped('amount'))
        if amount <= 0:
            raise UserError(_("There is no positive uninvoiced balance to consolidate."))
        remaining = self.env['sale.invoice'].create({
            'name': _("Remaining Invoice Payment"),
            'property_sold_id': self.id,
            'company_id': self.company_id.id,
            'invoice_date': fields.Date.context_today(self),
            'amount': amount,
            'tax_ids': [Command.set(self.taxes_ids.ids)] if self.taxes_ids else [],
            'is_remain_invoice': True,
        })
        pending.unlink()
        return {
            "type": "ir.actions.act_window",
            "name": _("Remaining Payment"),
            "res_model": "sale.invoice",
            "res_id": remaining.id,
            "view_mode": "form",
            "target": "current",
        }


class SaleInvoice(models.Model):
    _name = 'sale.invoice'
    _description = "Sale Invoice"
    _check_company_auto = True

    name = fields.Char(string="Title", translate=True)
    property_sold_id = fields.Many2one(
        'property.vendor', string="Property Sold",
        ondelete='cascade', check_company=True,
    )
    invoice_id = fields.Many2one('account.move', string="Invoice", check_company=True)
    invoice_date = fields.Date(string="Date")
    payment_state = fields.Selection(related="invoice_id.payment_state")
    company_id = fields.Many2one(
        'res.company', string='Company', required=True, index=True,
        default=lambda self: self.env.company,
    )
    currency_id = fields.Many2one('res.currency',
                                  related='company_id.currency_id',
                                  string='Currency')
    amount = fields.Monetary(string="Amount")
    invoice_created = fields.Boolean(copy=False, index=True)
    reminder_processed = fields.Boolean(copy=False, index=True)
    desc = fields.Text(string="Description", translate=True)
    is_remain_invoice = fields.Boolean()
    tax_ids = fields.Many2many('account.tax', string="Taxes")
    tax_amount = fields.Monetary(string="Tax Amount",
                                 compute="compute_tax_amount")

    @api.depends('tax_ids', 'amount', 'currency_id', 'property_sold_id.customer_id')
    def compute_tax_amount(self):
        for rec in self:
            if not rec.tax_ids or not rec.amount:
                rec.tax_amount = 0.0
                continue
            result = rec.tax_ids.compute_all(
                rec.amount,
                currency=rec.currency_id,
                quantity=1.0,
                product=rec.property_sold_id.installment_item_id,
                partner=rec.property_sold_id.customer_id,
            )
            rec.tax_amount = result['total_included'] - result['total_excluded']

    def action_create_invoice(self):
        self.ensure_one()
        if not self.property_sold_id.customer_id or not self.property_sold_id.installment_item_id:
            raise UserError(_("Customer and installment product are required before invoicing."))
        if self.amount <= 0:
            raise UserError(_("The sale installment amount must be greater than zero."))
        invoice_post_type = self.env['ir.config_parameter'].sudo(
        ).get_param('rental_management.invoice_post_type')
        if self.invoice_created or self.invoice_id:
            return self.invoice_id
        invoice_id = self.env['account.move'].with_company(
            self.property_sold_id.company_id
        ).create({
            'partner_id': self.property_sold_id.customer_id.id,
            'move_type': 'out_invoice',
            'sold_id': self.property_sold_id.id,
            'sale_schedule_id': self.id,
            'company_id': self.property_sold_id.company_id.id,
            'currency_id': self.property_sold_id.currency_id.id,
            'invoice_origin': self.property_sold_id.sold_seq,
            'invoice_date': self.invoice_date or fields.Date.context_today(self),
            'invoice_line_ids': [Command.create({
                'product_id': self.property_sold_id.installment_item_id.id,
                'name': (self.name or _("Sale installment")) + "\n" + (self.desc or ""),
                'quantity': 1,
                'price_unit': self.amount,
                'tax_ids': [Command.set(self.tax_ids.ids)] if self.tax_ids else [],
            })]
        })
        if invoice_post_type == 'automatically':
            invoice_id.action_post()
        self.invoice_id = invoice_id.id
        self.invoice_created = True
        self.action_send_sale_invoice(invoice_id.id)

    def action_send_sale_invoice(self, invoice_id):
        self.ensure_one()
        mail_template = self.env.ref(
            'rental_management.sale_invoice_payment_mail_template', raise_if_not_found=False)
        if mail_template and self.property_sold_id.customer_id.email:
            mail_template.send_mail(invoice_id, force_send=True)
        return True
