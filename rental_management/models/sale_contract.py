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
    property_subtype_name = fields.Char(
        related="property_id.property_subtype_id.name", string="Property Subtype Name", store=True, readonly=True, translate=False
    )
    property_project_name = fields.Char(
        related="property_id.property_project_id.name", string="Project Name", store=True, readonly=True, translate=False
    )
    subproject_name = fields.Char(
        related="property_id.subproject_id.name", string="Subproject Name", store=True, readonly=True, translate=False
    )
    region_name = fields.Char(related="property_id.region_id.name", string="Region Name", store=True, readonly=True, translate=False)
    city_name = fields.Char(related="property_id.city_id.name", string="City Name", store=True, readonly=True, translate=False)
    state_name = fields.Char(related="property_id.state_id.name", string="State Name", store=True, readonly=True, translate=False)
    country_name = fields.Char(related="property_id.country_id.name", string="Country Name", store=True, readonly=True, translate=False)

    # Broker Details
    is_any_broker = fields.Boolean(string='Any Broker')
    broker_id = fields.Many2one(
        'res.partner', string='Broker', domain=[('user_type', '=', 'broker')], check_company=True
    )
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
    broker_bill_id = fields.Many2one(
        'account.move', string='Broker Bill', readonly=True, check_company=True
    )
    broker_bill_payment_state = fields.Selection(related='broker_bill_id.payment_state',
                                                 string="Payment Status ")
    broker_invoice_id = fields.Many2one('account.move', string="Broker Invoice", check_company=True)
    broker_invoice_payment_state = fields.Selection(string="Broker Invoice Payment State",
                                                    related="broker_invoice_id.payment_state")

    # Customer Detail
    customer_id = fields.Many2one(
        'res.partner', string='Customer', domain=[('user_type', '=', 'customer')], check_company=True
    )
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
    book_invoice_id = fields.Many2one(
        'account.move', string='Advance', readonly=True, check_company=True
    )
    book_invoice_payment_state = fields.Selection(related='book_invoice_id.payment_state',
                                                  string="Payment Status")
    book_invoice_state = fields.Boolean(string='Invoice State')
    remain_invoice_id = fields.Many2one('account.move', string="Invoice", check_company=True)
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
    booking_item_id = fields.Many2one(
        'product.product', string="Booking Item", check_company=True,
        default=lambda self: self.env.ref(
            'rental_management.property_product_2', raise_if_not_found=False
        ),
    )
    broker_item_id = fields.Many2one(
        'product.product', string="Broker Item", check_company=True,
        default=lambda self: self.env.ref(
            'rental_management.property_product_1', raise_if_not_found=False
        ),
    )
    installment_item_id = fields.Many2one(
        'product.product', string="Installment Item", check_company=True,
        default=lambda self: self.env.ref(
            'rental_management.property_product_1', raise_if_not_found=False
        ),
    )
    is_taxes = fields.Boolean(string="Taxes ?")
    taxes_ids = fields.Many2many(
        'account.tax', string="Taxes", check_company=True,
        domain="[('type_tax_use', '=', 'sale'), ('company_id', '=', company_id)]",
    )

    # Legacy compatibility fields retained for existing databases
    sold_invoice_id = fields.Many2one(
        'account.move', string='Sold Invoice', readonly=True, check_company=True
    )
    sold_invoice_state = fields.Boolean(string='Sold Invoice State')
    sold_invoice_payment_state = fields.Selection(related='sold_invoice_id.payment_state',
                                                  string="Payment Status  ")

    # End legacy compatibility fields

    # Create Write, Scheduler, Name-get
    # Create
    @api.model_create_multi
    def create(self, vals_list):
        property_ids = sorted({vals.get("property_id") for vals in vals_list if vals.get("property_id")})
        if property_ids:
            self.env.cr.execute(
                "SELECT id FROM property_details WHERE id = ANY(%s) ORDER BY id FOR UPDATE",
                (property_ids,),
            )
        for vals in vals_list:
            requested_stage = vals.get("stage", "booked")
            if requested_stage != "booked" and not self.env.context.get("allow_sale_state_write"):
                raise UserError(_("Property sale records must start as Booked and use the sale workflow actions."))
            property_record = self.env['property.details'].browse(vals.get('property_id')).exists()
            if property_record:
                vals.setdefault('company_id', property_record.company_id.id)
                property_record.invalidate_recordset(["stage", "sold_booking_id"])
                if property_record.sale_lease != "for_sale" or property_record.stage != "sale":
                    raise UserError(_("Only a property currently marked For Sale can be booked."))
                if property_record.sold_booking_id and property_record.sold_booking_id.stage in ("booked", "sold"):
                    raise UserError(_("This property already has an active booking or completed sale."))
            if vals.get('sold_seq', 'New') in ('New', _('New')):
                vals['sold_seq'] = self.env['ir.sequence'].next_by_code(
                    'property.vendor') or _('New')
        records = super().create(vals_list)
        records._check_property_company()
        for sale in records.filtered(lambda record: record.stage == "booked" and record.property_id):
            sale.property_id.write({"sold_booking_id": sale.id, "stage": "booked"})
        return records

    def write(self, vals):
        if "stage" in vals and not self.env.context.get("allow_sale_state_write"):
            changing = self.filtered(lambda sale: sale.stage != vals["stage"])
            if changing:
                raise UserError(_("Property sale status can only be changed through the sale workflow actions."))
        protected = {
            "property_id", "customer_id", "company_id", "sale_price", "book_price",
            "payment_term", "booking_item_id", "installment_item_id", "taxes_ids",
            "is_any_broker", "broker_id", "broker_item_id", "commission_from",
            "commission_type", "broker_commission", "broker_commission_percentage",
        }
        if protected.intersection(vals) and any(sale.stage == "sold" for sale in self):
            if not self.env.context.get("allow_sale_structural_write"):
                raise UserError(_("Completed property sale commercial terms cannot be changed."))
        return super().write(vals)

    def unlink(self):
        """Preserve the complete booking/sale/refund audit history."""
        if self:
            raise UserError(
                _("Property sale history cannot be deleted. Use the Refund workflow when a booking is cancelled.")
            )
        return super().unlink()

    @api.depends("sold_seq", "customer_id.name")
    def _compute_display_name(self):
        for record in self:
            parts = [record.sold_seq, record.customer_id.display_name]
            record.display_name = " - ".join(filter(None, parts)) or _("Property Sale")

    # Scheduler
    @api.model
    def sale_recurring_invoice(self, batch_size=200):
        """Create every due sale installment once, in stable cursor batches."""
        today_date = fields.Date.context_today(self)
        schedule_model = self.env["sale.invoice"]
        last_id = 0
        processed = 0
        while True:
            schedules = schedule_model.search(
                [
                    ("invoice_id", "=", False),
                    ("invoice_date", "!=", False),
                    ("invoice_date", "<=", today_date),
                    ("is_consolidated", "=", False),
                    ("id", ">", last_id),
                ],
                order="id",
                limit=batch_size,
            )
            if not schedules:
                break
            last_id = schedules[-1].id
            for schedule in schedules:
                processed += 1
                try:
                    with self.env.cr.savepoint():
                        schedule.action_create_invoice()
                        schedule.reminder_processed = True
                except Exception:
                    _logger.exception(
                        "Sale installment invoicing failed for schedule %s",
                        schedule.display_name,
                    )
        return processed

    # Compute
    # Total amount paid amount, remaining amount
    @api.depends(
        'sale_invoice_ids.amount', 'sale_invoice_ids.tax_amount',
        'sale_invoice_ids.invoice_created', 'sale_invoice_ids.payment_state',
        'sale_invoice_ids.invoice_id.amount_total',
        'sale_invoice_ids.invoice_id.amount_residual',
        'sale_invoice_ids.invoice_id.state',
        'sale_invoice_ids.is_consolidated',
    )
    def _compute_remain_amount(self):
        can_read_moves = self.env["account.move"].browse().has_access("read")
        for rec in self:
            active_schedules = rec.sale_invoice_ids.filtered(lambda line: not line.is_consolidated)
            tax_amount = sum(active_schedules.mapped("tax_amount"))
            total_untaxed_amount = sum(active_schedules.mapped("amount"))
            paid_amount = 0.0
            if can_read_moves:
                posted_moves = active_schedules.mapped("invoice_id").filtered(
                    lambda move: move.state == "posted"
                )
                paid_amount = sum(
                    max(move.amount_total - move.amount_residual, 0.0) for move in posted_moves
                )
            rec.tax_amount = tax_amount
            rec.total_untaxed_amount = total_untaxed_amount
            rec.total_amount = tax_amount + total_untaxed_amount
            rec.paid_amount = paid_amount
            rec.remaining_amount = max(rec.total_amount - paid_amount, 0.0)

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
            rec.total_sell_amount = total_sell_amount
            rec.payable_amount = max(total_sell_amount - max(rec.book_price, 0.0), 0.0)

    @api.constrains("broker_commission", "broker_commission_percentage", "commission_type")
    def _check_broker_commission_values(self):
        for record in self:
            if record.broker_commission < 0:
                raise ValidationError(_("Broker commission cannot be negative."))
            if record.commission_type == "p" and not 0 <= record.broker_commission_percentage <= 100:
                raise ValidationError(_("Broker commission percentage must be between 0 and 100."))

    @api.constrains("property_id", "company_id", "taxes_ids", "book_price", "stage")
    def _check_property_company(self):
        for record in self:
            if record.property_id and record.property_id.company_id != record.company_id:
                raise ValidationError(_("The sold property and sale contract must belong to the same company."))
            if record.property_id and record.property_id.sale_lease != "for_sale":
                raise ValidationError(_("A property sale record can only be linked to a property configured For Sale."))
            if record.taxes_ids.filtered(lambda tax: tax.company_id != record.company_id):
                raise ValidationError(_("All sale taxes must belong to the sale contract company."))
            if record.book_price < 0:
                raise ValidationError(_("The booking amount cannot be negative."))
            if record.property_id and record.stage in ("booked", "sold"):
                conflict = self.search(
                    [
                        ("id", "!=", record.id),
                        ("property_id", "=", record.property_id.id),
                        ("stage", "in", ["booked", "sold"]),
                    ],
                    limit=1,
                )
                if conflict:
                    raise ValidationError(
                        _("Property %(property)s already has active sale %(sale)s.")
                        % {"property": record.property_id.display_name, "sale": conflict.display_name}
                    )

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
            return False
        mail_template = self.env.ref(
            'rental_management.property_sold_mail_template', raise_if_not_found=False
        )
        if mail_template:
            mail_template.send_mail(self.id, force_send=False)
        return True

    # Button
    # Advance Payment Invoice
    def action_book_invoice(self):
        self.ensure_one()
        self.env.cr.execute(
            "SELECT id FROM property_vendor WHERE id = %s FOR UPDATE", (self.id,)
        )
        self.invalidate_recordset(["book_invoice_id"])
        if self.book_invoice_id:
            return self._get_invoice_action(self.book_invoice_id, _("Booking Invoice"))
        if not self.property_id or not self.customer_id:
            raise UserError(_("Property and customer are required before creating the booking invoice."))
        if self.property_id.sale_lease != "for_sale":
            raise UserError(_("The selected property is not configured for sale."))
        if self.book_price <= 0:
            raise UserError(_("The booking amount must be greater than zero."))
        product = self.booking_item_id
        if not product:
            raise UserError(_("Configure a booking product before creating the booking invoice."))
        move_model = self.env['account.move'].with_company(self.company_id)
        if not move_model.browse().has_access("create"):
            raise UserError(_("Billing invoice creation access is required to create the booking invoice."))
        fiscal_position = self.customer_id.with_company(self.company_id).property_account_position_id
        taxes = self.taxes_ids.filtered(lambda tax: tax.company_id == self.company_id)
        if fiscal_position and taxes:
            taxes = fiscal_position.map_tax(taxes)
        invoice_vals = {
            'partner_id': self.customer_id.id,
            'move_type': 'out_invoice',
            'sold_id': self.id,
            'company_id': self.company_id.id,
            'currency_id': self.currency_id.id,
            'invoice_origin': self.sold_seq,
            'ref': self.sold_seq,
            'invoice_date': fields.Date.context_today(self),
            'invoice_line_ids': [Command.create({
                'product_id': product.id,
                'name': _("Booking amount for %s") % self.property_id.display_name,
                'quantity': 1.0,
                'price_unit': self.book_price,
                'tax_ids': [Command.set(taxes.ids)] if taxes else [],
            })],
        }
        if fiscal_position:
            invoice_vals['fiscal_position_id'] = fiscal_position.id
        invoice = move_model.create(invoice_vals)
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
        self.property_id.write({"sold_booking_id": self.id, "stage": "booked"})
        mail_template = self.env.ref(
            'rental_management.property_book_mail_template', raise_if_not_found=False)
        if mail_template and self.customer_id.email:
            mail_template.send_mail(self.id, force_send=True)
        return self._get_invoice_action(invoice, _("Booking Invoice"))

    # Refund Amount
    def action_refund_amount(self):
        for rec in self:
            if rec.stage == "sold":
                raise UserError(_("A completed property sale cannot be refunded through the booking action."))
            if rec.book_invoice_id and rec.book_invoice_id.state == "posted":
                raise UserError(
                    _("A posted booking invoice exists. Create the required credit note or accounting "
                      "adjustment before marking the booking as refunded.")
                )
            rec.with_context(allow_sale_state_write=True).write({"stage": "refund"})
            if rec.property_id:
                rec.property_id.write({"stage": "sale", "sold_booking_id": False})
        return True

    # Receive Remain Payment and Create Invoice
    def action_receive_remaining(self):
        self.ensure_one()
        self.env.cr.execute("SELECT id FROM property_vendor WHERE id = %s FOR UPDATE", (self.id,))
        self.invalidate_recordset(["sale_invoice_ids"])
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
            lambda line: not line.invoice_created
            and not line.is_remain_invoice
            and not line.is_consolidated
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
        pending.write({
            "is_consolidated": True,
            "consolidated_into_id": remaining.id,
        })
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
    is_consolidated = fields.Boolean(
        string="Consolidated", copy=False, index=True,
        help="Historical schedule was rolled into a remaining-payment schedule and is kept for audit history.",
    )
    consolidated_into_id = fields.Many2one(
        "sale.invoice", string="Consolidated Into", copy=False, ondelete="set null", check_company=True
    )
    tax_ids = fields.Many2many(
        'account.tax', string="Taxes", check_company=True,
        domain="[('type_tax_use', '=', 'sale'), ('company_id', '=', company_id)]",
    )
    tax_amount = fields.Monetary(string="Tax Amount",
                                 compute="compute_tax_amount")
    tax_names = fields.Char(string="Tax Names", compute="_compute_tax_names", store=True, readonly=True)

    @api.depends("tax_ids.name")
    def _compute_tax_names(self):
        for schedule in self:
            schedule.tax_names = ", ".join(schedule.tax_ids.mapped("name"))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            sale = self.env["property.vendor"].browse(vals.get("property_sold_id")).exists()
            if sale:
                vals.setdefault("company_id", sale.company_id.id)
        return super().create(vals_list)

    @api.constrains(
        "property_sold_id", "company_id", "tax_ids", "amount",
        "consolidated_into_id", "is_consolidated",
    )
    def _check_sale_schedule_consistency(self):
        for schedule in self:
            if schedule.property_sold_id and schedule.property_sold_id.company_id != schedule.company_id:
                raise ValidationError(_("Sale schedule and property sale must belong to the same company."))
            if schedule.tax_ids.filtered(lambda tax: tax.company_id != schedule.company_id):
                raise ValidationError(_("All sale schedule taxes must belong to its company."))
            if schedule.amount < 0:
                raise ValidationError(_("Sale installment amount cannot be negative."))
            if schedule.consolidated_into_id:
                target = schedule.consolidated_into_id
                if target == schedule or target.property_sold_id != schedule.property_sold_id:
                    raise ValidationError(_("A consolidated schedule must point to another schedule of the same sale."))
                if target.company_id != schedule.company_id:
                    raise ValidationError(_("Consolidated sale schedules must belong to the same company."))
            if schedule.is_consolidated and not schedule.consolidated_into_id:
                raise ValidationError(_("A consolidated schedule must identify the schedule it was consolidated into."))

    @api.depends('tax_ids', 'amount', 'currency_id', 'property_sold_id.customer_id', 'property_sold_id.company_id')
    def compute_tax_amount(self):
        for rec in self:
            if not rec.tax_ids or not rec.amount or not rec.property_sold_id:
                rec.tax_amount = 0.0
                continue
            sale = rec.property_sold_id
            taxes = rec.tax_ids.filtered(lambda tax: tax.company_id == sale.company_id)
            fiscal_position = sale.customer_id.with_company(sale.company_id).property_account_position_id
            if fiscal_position and taxes:
                taxes = fiscal_position.map_tax(taxes)
            result = taxes.compute_all(
                rec.amount,
                currency=rec.currency_id,
                quantity=1.0,
                product=sale.installment_item_id,
                partner=sale.customer_id,
            ) if taxes else {"total_included": rec.amount, "total_excluded": rec.amount}
            rec.tax_amount = result['total_included'] - result['total_excluded']

    def action_create_invoice(self):
        self.ensure_one()
        self.env.cr.execute("SELECT id FROM sale_invoice WHERE id = %s FOR UPDATE", (self.id,))
        self.invalidate_recordset(["invoice_id", "invoice_created"])
        if self.invoice_id:
            if not self.invoice_created:
                self.invoice_created = True
            return self.invoice_id
        if self.is_consolidated:
            raise UserError(_("This historical installment was consolidated into another schedule and cannot be invoiced separately."))
        if self.invoice_created:
            # Preserve legacy data but recover safely from an orphaned flag.
            self.invoice_created = False
        if not self.property_sold_id.customer_id or not self.property_sold_id.installment_item_id:
            raise UserError(_("Customer and installment product are required before invoicing."))
        if self.amount <= 0:
            raise UserError(_("The sale installment amount must be greater than zero."))
        invoice_post_type = self.env['ir.config_parameter'].sudo(
        ).get_param('rental_management.invoice_post_type')
        move_model = self.env['account.move'].with_company(self.property_sold_id.company_id)
        if not move_model.browse().has_access("create"):
            raise UserError(_("Billing invoice creation access is required to create the sale invoice."))
        fiscal_position = self.property_sold_id.customer_id.with_company(
            self.property_sold_id.company_id
        ).property_account_position_id
        taxes = self.tax_ids.filtered(lambda tax: tax.company_id == self.property_sold_id.company_id)
        if fiscal_position and taxes:
            taxes = fiscal_position.map_tax(taxes)
        move_vals = {
            'partner_id': self.property_sold_id.customer_id.id,
            'move_type': 'out_invoice',
            'sold_id': self.property_sold_id.id,
            'sale_schedule_id': self.id,
            'company_id': self.property_sold_id.company_id.id,
            'currency_id': self.property_sold_id.currency_id.id,
            'invoice_origin': self.property_sold_id.sold_seq,
            'ref': self.property_sold_id.sold_seq,
            'invoice_date': self.invoice_date or fields.Date.context_today(self),
            'invoice_line_ids': [Command.create({
                'product_id': self.property_sold_id.installment_item_id.id,
                'name': (self.name or _("Sale installment")) + "\n" + (self.desc or ""),
                'quantity': 1.0,
                'price_unit': self.amount,
                'tax_ids': [Command.set(taxes.ids)] if taxes else [],
            })],
        }
        if fiscal_position:
            move_vals['fiscal_position_id'] = fiscal_position.id
        invoice_id = move_model.create(move_vals)
        if invoice_post_type == 'automatically':
            invoice_id.action_post()
        self.invoice_id = invoice_id.id
        self.invoice_created = True
        self.action_send_sale_invoice(invoice_id.id)
        return invoice_id

    def action_send_sale_invoice(self, invoice_id):
        self.ensure_one()
        mail_template = self.env.ref(
            'rental_management.sale_invoice_payment_mail_template', raise_if_not_found=False)
        if mail_template and self.property_sold_id.customer_id.email:
            mail_template.send_mail(invoice_id, force_send=True)
        return True
