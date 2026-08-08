from odoo import models, api, fields, _
from odoo.exceptions import UserError


class BookingInquiry(models.TransientModel):
    _name = "booking.inquiry"
    _description = "Booking Inquiry"
    _rec_name = "customer_id"
    _check_company_auto = True

    property_id = fields.Many2one('property.details', string="Property", check_company=True)
    customer_id = fields.Many2one('res.partner', string="Customer", check_company=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', string='Currency')
    ask_price = fields.Monetary(string="Ask Price")
    note = fields.Text(string="Note", translate=True)
    sale_inquiry = fields.Boolean()
    duration_id = fields.Many2one('contract.duration', string="Duration of")
    total_rent = fields.Monetary(string="Total Rent", compute="_compute_total_rent")
    sale_price = fields.Monetary(related="property_id.sale_price")

    @api.depends('duration_id')
    def _compute_total_rent(self):
        for rec in self:
            if rec.duration_id.month:
                rec.total_rent = rec.duration_id.month * rec.property_id.tenancy_price
            else:
                rec.total_rent = 0.0

    def action_property_inquiry_booking(self):
        self.ensure_one()
        rec = self.env.context.get('active_id')
        lead_id = self.env['crm.lead'].browse(rec).exists()
        if not lead_id:
            return {"type": "ir.actions.act_window_close"}
        lead_id.check_access("write")
        if not self.property_id or not self.customer_id:
            message = {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'type': 'danger',
                    'title': _('Customer or property not Found !'),
                    'sticky': False,
                }
            }
            return message
        effective_company = lead_id.company_id or self.company_id
        if self.property_id.company_id != effective_company or self.company_id != effective_company:
            raise UserError(_("The lead, inquiry and property must belong to the same company."))
        if self.customer_id.company_id and self.customer_id.company_id != effective_company:
            raise UserError(_("The selected customer belongs to a different company."))
        if self.sale_inquiry and self.property_id.sale_lease != "for_sale":
            raise UserError(_("The selected property is not configured for sale."))
        if not self.sale_inquiry and self.property_id.sale_lease != "for_tenancy":
            raise UserError(_("The selected property is not configured for rent."))

        self.customer_id.user_type = "customer"
        if self.sale_inquiry:
            data = {
                'property_id': self.property_id.id,
                'customer_id': self.customer_id.id,
                'ask_price': self.ask_price,
                'note': self.note,
                'lead_id': lead_id.id,
                'company_id': self.company_id.id,
            }
            sale_inquiry_id = self.env['sale.inquiry'].create(data)
            lead_id.sale_inquiry_id = sale_inquiry_id.id
        else:
            data = {
                'property_id': self.property_id.id,
                'customer_id': self.customer_id.id,
                'duration_id': self.duration_id.id,
                'note': self.note,
                'lead_id': lead_id.id,
            }
            tenancy_inquiry_id = self.env['tenancy.inquiry'].create(data)
            lead_id.tenancy_inquiry_id = tenancy_inquiry_id.id

