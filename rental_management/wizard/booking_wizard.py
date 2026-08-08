# -*- coding: utf-8 -*-
# Copyright 2020-Today TechKhedut.
# Part of TechKhedut. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class BookingWizard(models.TransientModel):
    _name = "booking.wizard"
    _description = "Create Property Sale Booking"
    _check_company_auto = True

    customer_id = fields.Many2one(
        "res.partner",
        string="Customer",
        required=True,
        domain="[('user_type','=','customer')]",
        check_company=True,
    )
    property_id = fields.Many2one(
        "property.details",
        string="Property",
        required=True,
        check_company=True,
        domain="[('sale_lease', '=', 'for_sale'), ('stage', '=', 'sale'), ('company_id', '=', company_id)]",
    )
    price = fields.Monetary(related="property_id.price")
    company_id = fields.Many2one(
        "res.company", string="Company", required=True, default=lambda self: self.env.company
    )
    currency_id = fields.Many2one(
        "res.currency", related="company_id.currency_id", string="Currency"
    )
    book_price = fields.Monetary(string="Advance")
    ask_price = fields.Monetary(string="Customer Price")
    sale_price = fields.Monetary(related="property_id.sale_price", string="Sale Price")
    is_any_broker = fields.Boolean(string="Any Broker?")
    broker_id = fields.Many2one(
        "res.partner", string="Broker", domain="[('user_type', '=', 'broker')]", check_company=True
    )
    commission_type = fields.Selection(
        [("f", "Fixed"), ("p", "Percentage")], string="Commission Type"
    )
    broker_commission = fields.Monetary(string="Commission")
    broker_commission_percentage = fields.Float(string="Percentage")
    commission_from = fields.Selection(
        [("customer", "Customer"), ("landlord", "Landlord")],
        default="customer",
        string="Commission From",
    )
    from_inquiry = fields.Boolean("From Enquiry")
    note = fields.Text(string="Note", translate=True)
    lead_id = fields.Many2one(
        "crm.lead", string="CRM Enquiry", check_company=True, domain="[('property_id','=',property_id)]"
    )

    is_any_maintenance = fields.Boolean(related="property_id.is_maintenance_service")
    total_maintenance = fields.Monetary(related="property_id.total_maintenance")
    is_utility_service = fields.Boolean(related="property_id.is_extra_service")
    total_service = fields.Monetary(related="property_id.extra_service_cost")

    booking_item_id = fields.Many2one(
        "product.product",
        string="Booking Item",
        required=True,
        check_company=True,
        default=lambda self: self.env.ref(
            "rental_management.property_product_2", raise_if_not_found=False
        ),
    )
    broker_item_id = fields.Many2one(
        "product.product",
        string="Broker Item",
        check_company=True,
        default=lambda self: self.env.ref(
            "rental_management.property_product_1", raise_if_not_found=False
        ),
    )

    # Legacy compatibility field retained for existing XML/data references.
    inquiry_id = fields.Many2one("sale.inquiry", string="Sale Enquiry", check_company=True)

    @api.model
    def default_get(self, field_list):
        res = super().default_get(field_list)
        property_record = self.env["property.details"].browse(
            self.env.context.get("active_id")
        ).exists()
        if property_record:
            res.update(
                {
                    "property_id": property_record.id,
                    "company_id": property_record.company_id.id,
                    "ask_price": property_record.price,
                }
            )
        return res

    @api.constrains(
        "book_price",
        "broker_commission",
        "broker_commission_percentage",
        "commission_type",
    )
    def _check_booking_amounts(self):
        for wizard in self:
            if wizard.book_price < 0:
                raise ValidationError(_("The booking amount cannot be negative."))
            if wizard.ask_price > 0 and wizard.book_price > wizard.ask_price:
                raise ValidationError(_("The booking amount cannot exceed the customer price."))
            if wizard.broker_commission < 0:
                raise ValidationError(_("Broker commission cannot be negative."))
            if wizard.commission_type == "p" and not 0 <= wizard.broker_commission_percentage <= 100:
                raise ValidationError(_("Broker commission percentage must be between 0 and 100."))

    def create_booking_action(self):
        self.ensure_one()
        property_record = self.property_id
        if property_record.company_id != self.company_id:
            raise ValidationError(_("The booking and property must belong to the same company."))
        if property_record.sale_lease != "for_sale" or property_record.stage != "sale":
            raise UserError(_("Only a property currently marked For Sale can be booked."))
        if property_record.sold_booking_id and property_record.sold_booking_id.stage in ("booked", "sold"):
            raise UserError(_("This property already has an active booking or completed sale."))
        if self.is_any_broker:
            if not self.broker_id or not self.broker_item_id or not self.commission_type or not self.commission_from:
                raise ValidationError(_("Complete the broker and commission information before booking."))

        # Serialize competing booking attempts for the same property.
        self.env.cr.execute(
            "SELECT id FROM property_details WHERE id = %s FOR UPDATE",
            (property_record.id,),
        )
        property_record.invalidate_recordset(["stage", "sold_booking_id"])
        if property_record.stage != "sale" or (
            property_record.sold_booking_id
            and property_record.sold_booking_id.stage in ("booked", "sold")
        ):
            raise UserError(_("This property was booked by another transaction."))

        booking = self.env["property.vendor"].with_company(self.company_id).create(
            {
                "customer_id": self.customer_id.id,
                "property_id": property_record.id,
                "company_id": self.company_id.id,
                "book_price": self.book_price,
                "ask_price": self.ask_price,
                "is_any_broker": self.is_any_broker,
                "broker_id": self.broker_id.id,
                "commission_type": self.commission_type,
                "broker_commission": self.broker_commission,
                "broker_commission_percentage": self.broker_commission_percentage,
                "stage": "booked",
                "commission_from": self.commission_from,
                "booking_item_id": self.booking_item_id.id,
                "broker_item_id": self.broker_item_id.id,
            }
        )
        property_record.write({"sold_booking_id": booking.id, "stage": "booked"})

        if self.book_price > 0:
            booking.action_book_invoice()
        else:
            template = self.env.ref(
                "rental_management.property_book_mail_template", raise_if_not_found=False
            )
            if template and booking.customer_id.email:
                template.send_mail(booking.id, force_send=False)

        return {
            "type": "ir.actions.act_window",
            "name": _("Property Booking"),
            "res_model": "property.vendor",
            "res_id": booking.id,
            "view_mode": "form",
            "target": "current",
        }

    @api.onchange("from_inquiry", "property_id")
    def _onchange_property_sale_inquiry(self):
        if not self.from_inquiry or not self.property_id:
            return {"domain": {"inquiry_id": [("id", "=", False)]}}
        inquiry_ids = self.env["sale.inquiry"].search(
            [("property_id", "=", self.property_id.id)]
        ).ids
        return {"domain": {"inquiry_id": [("id", "in", inquiry_ids)]}}

    @api.onchange("lead_id")
    def _onchange_ask_price(self):
        for wizard in self:
            if wizard.from_inquiry and wizard.lead_id:
                wizard.ask_price = wizard.lead_id.ask_price
                wizard.note = wizard.lead_id.description
                wizard.customer_id = wizard.lead_id.partner_id
