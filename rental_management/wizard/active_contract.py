import datetime
from dateutil.relativedelta import relativedelta
from odoo import fields, api, models


class ActiveContract(models.Model):
    _name = 'active.contract'
    _description = "Active Contract"
    _rec_name = 'type'

    type = fields.Selection(
        [('automatic', 'Auto Installment'),
         ('manual', 'Manual Installment (List out all rent installment)')],
        default='automatic')

    def action_create_contract(self):
        active_id = self._context.get('active_id')
        tenancy_id = self.env['tenancy.details'].browse(active_id)
        if self.type == "automatic":
            tenancy_id.write({'type': 'automatic',
                              'contract_type': 'running_contract',
                              'active_contract_state': True})
            tenancy_id.action_active_contract()
        if self.type == "manual":
            if tenancy_id.rent_unit == "Month":
                if tenancy_id.payment_term == "monthly":
                    self.action_monthly_month_active()
                if tenancy_id.payment_term == "quarterly":
                    self.action_quarterly_month_active()
            if tenancy_id.rent_unit == "Year":
                if tenancy_id.payment_term == "year":
                    self.action_yearly_year()
            if tenancy_id.is_any_broker:
                tenancy_id.action_broker_invoice()
            tenancy_id.write(
                {'type': 'manual',
                 'contract_type': 'running_contract',
                 'active_contract_state': True})
            tenancy_id.action_send_active_contract()

    def action_monthly_month_active(self):
        invoice_post_type = self.env['ir.config_parameter'].sudo().get_param(
            'rental_management.invoice_post_type')
        service = 0.0
        active_id = self._context.get('active_id')
        tenancy_id = self.env['tenancy.details'].browse(active_id)
        invoice_lines = []
        month = tenancy_id.month
        invoice_date = tenancy_id.invoice_start_date + relativedelta(months=1)
        for i in range(month):
            if i == 0:
                record = {
                    'product_id': tenancy_id.installment_item_id.id,
                    'name': 'First Invoice of ' + tenancy_id.property_id.name,
                    'quantity': 1,
                    'price_unit': tenancy_id.total_rent,
                    'tax_ids': tenancy_id.tax_ids.ids if tenancy_id.instalment_tax else False
                }
                invoice_lines.append((0, 0, record))
                if tenancy_id.is_any_deposit:
                    deposit_record = {
                        'product_id': tenancy_id.deposit_item_id.id,
                        'name': 'Deposit of ' + tenancy_id.property_id.name,
                        'quantity': 1,
                        'price_unit': tenancy_id.deposit_amount,
                        'tax_ids': tenancy_id.tax_ids.ids if tenancy_id.deposit_tax else False
                    }
                    invoice_lines.append((0, 0, deposit_record))
                if tenancy_id.is_maintenance_service:
                    invoice_lines.append((0, 0, {
                        'product_id': tenancy_id.installment_item_id.id,
                        'name': 'Maintenance of ' + tenancy_id.property_id.name,
                        'quantity': 1,
                        'price_unit': tenancy_id.total_maintenance,
                        'tax_ids': tenancy_id.tax_ids.ids if tenancy_id.instalment_tax else False
                    }))
                desc = ""
                if tenancy_id.is_extra_service:
                    for line in tenancy_id.extra_services_ids:
                        service = service + line.price
                        service_invoice_record = {
                            'product_id': line.service_id.id,
                            'name': ("Service Type : Once" + "\n" "Service : " + str(line.service_id.name)) if line.service_type == "once" else ("Service Type : Recurring" + "\n" "Service : " + str(line.service_id.name)),
                            'quantity': 1,
                            'price_unit': line.price,
                            'tax_ids': tenancy_id.tax_ids.ids if tenancy_id.service_tax else False
                        }
                        invoice_lines.append((0, 0, service_invoice_record))
                data = {
                    'partner_id': tenancy_id.tenancy_id.id,
                    'move_type': 'out_invoice',
                    'invoice_date': tenancy_id.invoice_start_date,
                    'invoice_line_ids': invoice_lines
                }
                invoice_id = self.env['account.move'].sudo().create(data)
                invoice_id.tenancy_id = tenancy_id.id
                if invoice_post_type == 'automatically':
                    invoice_id.action_post()
                amount_total = invoice_id.amount_total
                rent_invoice = {
                    'tenancy_id': tenancy_id.id,
                    'type': 'rent',
                    'invoice_date': tenancy_id.invoice_start_date,
                    'description': 'First Rent',
                    'rent_invoice_id': invoice_id.id,
                    'amount': amount_total,
                    'rent_amount': tenancy_id.total_rent,
                    'service_amount': service
                }
                if tenancy_id.is_any_deposit:
                    rent_invoice['description'] = 'First Rent + Deposit'
                else:
                    rent_invoice['description'] = 'First Rent'
                self.env['rent.invoice'].create(rent_invoice)
            if not i == 0:
                rent_invoice = {
                    'tenancy_id': tenancy_id.id,
                    'type': 'rent',
                    'invoice_date': invoice_date,
                    'description': 'Installment of ' + tenancy_id.property_id.name,
                    'amount': tenancy_id.total_rent,
                    'rent_amount': tenancy_id.total_rent
                }
                self.env['rent.invoice'].create(rent_invoice)
                invoice_date = invoice_date + relativedelta(months=1)

    def action_quarterly_month_active(self):
        invoice_post_type = self.env['ir.config_parameter'].sudo(
        ).get_param('rental_management.invoice_post_type')
        service_amount = 0.0
        active_id = self._context.get('active_id')
        tenancy_id = self.env['tenancy.details'].browse(active_id)
        invoice_lines = []
        full_quarter = tenancy_id.month // 3
        reminder_quarter = tenancy_id.month % 3
        invoice_date = tenancy_id.invoice_start_date + relativedelta(months=3)
        if full_quarter >= 1:
            for i in range(full_quarter):
                if i == 0:
                    record = {
                        'product_id': tenancy_id.installment_item_id.id,
                        'name': 'First Quarter Invoice of ' + tenancy_id.property_id.name,
                        'quantity': 1,
                        'price_unit': tenancy_id.total_rent * 3,
                        'tax_ids': tenancy_id.tax_ids.ids if tenancy_id.instalment_tax else False
                    }
                    invoice_lines.append((0, 0, record))
                    if tenancy_id.is_any_deposit:
                        deposit_record = {
                            'product_id': tenancy_id.deposit_item_id.id,
                            'name': 'Deposit of ' + tenancy_id.property_id.name,
                            'quantity': 1,
                            'price_unit': tenancy_id.deposit_amount,
                            'tax_ids': tenancy_id.tax_ids.ids if tenancy_id.deposit_tax else False
                        }
                        invoice_lines.append((0, 0, deposit_record))
                    if tenancy_id.is_maintenance_service:
                        invoice_lines.append((0, 0, {
                            'product_id': tenancy_id.installment_item_id.id,
                            'name': 'Maintenance of ' + tenancy_id.property_id.name,
                            'quantity': 3,
                            'price_unit': tenancy_id.total_maintenance,
                            'tax_ids': tenancy_id.tax_ids.ids if tenancy_id.instalment_tax else False
                        }))
                    if tenancy_id.is_extra_service:
                        for line in tenancy_id.extra_services_ids:
                            if line.service_type == "once":
                                service_amount = service_amount + line.price
                                service_invoice_record = {
                                    'product_id': line.service_id.id,
                                    'name': "Service Type : Once" + "\n" "Service : " + str(line.service_id.name),
                                    'quantity': 1,
                                    'price_unit': line.price,
                                    'tax_ids': tenancy_id.tax_ids.ids if tenancy_id.service_tax else False
                                }
                                invoice_lines.append(
                                    (0, 0, service_invoice_record))
                            if line.service_type == "monthly":
                                service_amount = service_amount + \
                                    (line.price * 3)
                                service_invoice_record = {
                                    'product_id': line.service_id.id,
                                    'name': "Service Type : Recurring" + "\n" "Service : " + str(line.service_id.name),
                                    'quantity': 3,
                                    'price_unit': line.price,
                                    'tax_ids': tenancy_id.tax_ids.ids if tenancy_id.service_tax else False
                                }
                                invoice_lines.append(
                                    (0, 0, service_invoice_record))
                    data = {
                        'partner_id': tenancy_id.tenancy_id.id,
                        'move_type': 'out_invoice',
                        'invoice_date': tenancy_id.invoice_start_date,
                        'invoice_line_ids': invoice_lines
                    }
                    invoice_id = self.env['account.move'].sudo().create(data)
                    invoice_id.tenancy_id = tenancy_id.id
                    if invoice_post_type == 'automatically':
                        invoice_id.action_post()
                    rent_invoice = {
                        'tenancy_id': tenancy_id.id,
                        'type': 'rent',
                        'invoice_date': tenancy_id.invoice_start_date,
                        'description': 'First Quarter Rent',
                        'rent_invoice_id': invoice_id.id,
                        'amount': invoice_id.amount_total,
                        'rent_amount': tenancy_id.total_rent * 3,
                        'service_amount': service_amount
                    }
                    if tenancy_id.is_any_deposit:
                        rent_invoice['description'] = 'First Quarter Rent + Deposit'
                    else:
                        rent_invoice['description'] = 'First Quarter Rent'
                    self.env['rent.invoice'].create(rent_invoice)
                if not i == 0:
                    rent_invoice = {
                        'tenancy_id': tenancy_id.id,
                        'type': 'rent',
                        'invoice_date': invoice_date,
                        'description': 'Installment of ' + tenancy_id.property_id.name,
                        'amount': tenancy_id.total_rent * 3,
                        'rent_amount': tenancy_id.total_rent * 3
                    }
                    self.env['rent.invoice'].create(rent_invoice)
                    invoice_date = invoice_date + relativedelta(months=3)

            if reminder_quarter > 0:
                rent_invoice_reminder = {
                    'tenancy_id': tenancy_id.id,
                    'type': 'rent',
                    'invoice_date': invoice_date,
                    'description': 'Installment of ' + tenancy_id.property_id.name,
                    'amount': tenancy_id.total_rent * reminder_quarter,
                    'rent_amount': tenancy_id.total_rent * reminder_quarter,
                    'remain': reminder_quarter
                }
                self.env['rent.invoice'].create(rent_invoice_reminder)

    def action_yearly_year(self):
        invoice_post_type = self.env['ir.config_parameter'].sudo(
        ).get_param('rental_management.invoice_post_type')
        service_amount = 0
        active_id = self._context.get('active_id')
        tenancy_id = self.env['tenancy.details'].browse(active_id)
        invoice_lines = []
        year = tenancy_id.month
        invoice_date = tenancy_id.invoice_start_date + relativedelta(years=1)
        for i in range(year):
            if i == 0:
                record = {
                    'product_id': tenancy_id.installment_item_id.id,
                    'name': 'First Year Invoice of ' + tenancy_id.property_id.name,
                    'quantity': 1,
                    'price_unit': tenancy_id.total_rent,
                    'tax_ids': tenancy_id.tax_ids.ids if tenancy_id.instalment_tax else False
                }
                invoice_lines.append((0, 0, record))
                if tenancy_id.is_any_deposit:
                    deposit_record = {
                        'product_id': tenancy_id.deposit_item_id.id,
                        'name': 'Deposit of ' + tenancy_id.property_id.name,
                        'quantity': 1,
                        'price_unit': tenancy_id.deposit_amount,
                        'tax_ids': tenancy_id.tax_ids.ids if tenancy_id.deposit_tax else False
                    }
                    invoice_lines.append((0, 0, deposit_record))
                if tenancy_id.is_maintenance_service:
                    invoice_lines.append((0, 0, {
                        'product_id': tenancy_id.installment_item_id.id,
                        'name': 'Maintenance of ' + tenancy_id.property_id.name,
                        'quantity': 12,
                        'price_unit': tenancy_id.total_maintenance,
                        'tax_ids': tenancy_id.tax_ids.ids if tenancy_id.instalment_tax else False
                    }))
                if tenancy_id.is_extra_service:
                    for line in tenancy_id.extra_services_ids:
                        if line.service_type == "once":
                            service_amount = service_amount + line.price
                            service_invoice_record = {
                                'product_id': line.service_id.id,
                                'name': "Service Type : Once" + "\n" "Service : " + str(line.service_id.name),
                                'quantity': 1,
                                'price_unit': line.price,
                                'tax_ids': tenancy_id.tax_ids.ids if tenancy_id.service_tax else False
                            }
                            invoice_lines.append(
                                (0, 0, service_invoice_record))
                        if line.service_type == "monthly":
                            service_amount = service_amount + (line.price * 12)
                            service_invoice_record = {
                                'product_id': line.service_id.id,
                                'name': "Service Type : Recurring" + "\n" "Service : " + str(line.service_id.name),
                                'quantity': 12,
                                'price_unit': line.price,
                                'tax_ids': tenancy_id.tax_ids.ids if tenancy_id.service_tax else False
                            }
                            invoice_lines.append(
                                (0, 0, service_invoice_record))
                data = {
                    'partner_id': tenancy_id.tenancy_id.id,
                    'move_type': 'out_invoice',
                    'invoice_date': tenancy_id.invoice_start_date,
                    'invoice_line_ids': invoice_lines
                }
                invoice_id = self.env['account.move'].sudo().create(data)
                invoice_id.tenancy_id = tenancy_id.id
                if invoice_post_type == 'automatically':
                    invoice_id.action_post()
                rent_invoice = {
                    'tenancy_id': tenancy_id.id,
                    'type': 'rent',
                    'invoice_date': tenancy_id.invoice_start_date,
                    'description': 'First Rent',
                    'rent_invoice_id': invoice_id.id,
                    'amount': invoice_id.amount_total,
                    'rent_amount': tenancy_id.total_rent,
                    'service_amount': service_amount
                }
                if tenancy_id.is_any_deposit:
                    rent_invoice['description'] = 'First Rent + Deposit'
                else:
                    rent_invoice['description'] = 'First Rent'
                self.env['rent.invoice'].create(rent_invoice)
            if not i == 0:
                rent_invoice = {
                    'tenancy_id': tenancy_id.id,
                    'type': 'rent',
                    'invoice_date': invoice_date,
                    'description': 'Installment of ' + tenancy_id.property_id.name,
                    'amount': tenancy_id.total_rent,
                    'rent_amount': tenancy_id.total_rent
                }
                self.env['rent.invoice'].create(rent_invoice)
                invoice_date = invoice_date + relativedelta(years=1)
