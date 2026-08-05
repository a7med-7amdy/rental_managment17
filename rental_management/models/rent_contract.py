# -*- coding: utf-8 -*-
# Copyright 2020-Today TechKhedut.
# Part of TechKhedut. See LICENSE file for full copyright and licensing details.

import calendar
import logging
from datetime import timedelta

from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.fields import Command

_logger = logging.getLogger(__name__)


class TenancyDetails(models.Model):
    """Rental contract and the authoritative rental lifecycle state."""

    _name = "tenancy.details"
    _description = "Rental Contract"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _rec_name = "tenancy_seq"
    _order = "start_date desc, id desc"
    _check_company_auto = True

    tenancy_seq = fields.Char(
        string="Sequence", required=True, readonly=True, copy=False, default="New", index=True
    )
    close_contract_state = fields.Boolean(
        string="Contract State",
        compute="_compute_legacy_state_flags",
        store=True,
        readonly=False,
        help="Legacy compatibility field. Contract Status remains the source of truth.",
    )
    active_contract_state = fields.Boolean(
        string="Active State",
        compute="_compute_legacy_state_flags",
        store=True,
        readonly=False,
        help="Legacy compatibility field. Contract Status remains the source of truth.",
    )
    contract_type = fields.Selection(
        [
            ("new_contract", "Draft"),
            ("running_contract", "Running"),
            ("expire_contract", "Expired"),
            ("close_contract", "Closed"),
            ("cancel_contract", "Cancelled"),
        ],
        string="Contract Status",
        default="new_contract",
        required=True,
        copy=False,
        index=True,
        tracking=True,
        group_expand="_expand_contract_states",
    )
    days_left = fields.Integer(string="Days Left", compute="compute_days_left")
    responsible_id = fields.Many2one(
        "res.users",
        default=lambda self: self.env.user,
        string="Responsible",
        required=True,
        index=True,
        tracking=True,
    )
    activation_date = fields.Datetime(readonly=True, copy=False, tracking=True)
    activated_by_id = fields.Many2one("res.users", readonly=True, copy=False)
    close_date = fields.Datetime(readonly=True, copy=False, tracking=True)
    closed_by_id = fields.Many2one("res.users", readonly=True, copy=False)
    cancel_date = fields.Datetime(readonly=True, copy=False, tracking=True)
    cancelled_by_id = fields.Many2one("res.users", readonly=True, copy=False)
    cancel_reason = fields.Text(readonly=True, copy=False, tracking=True)
    activation_email_sent = fields.Boolean(copy=False)
    expiry_reminder_sent = fields.Boolean(copy=False)
    expiry_email_sent = fields.Boolean(copy=False)
    last_reminder_schedule_id = fields.Many2one("rent.invoice", copy=False)

    company_id = fields.Many2one(
        "res.company",
        string="Company",
        required=True,
        default=lambda self: self.env.company,
        index=True,
        tracking=True,
    )
    currency_id = fields.Many2one(
        "res.currency", related="company_id.currency_id", string="Currency", store=True
    )

    property_id = fields.Many2one(
        "property.details",
        string="Property",
        domain="[('stage', '=', 'available'), ('company_id', 'in', allowed_company_ids)]",
        index=True,
        check_company=True,
        tracking=True,
    )
    property_type = fields.Selection(related="property_id.type", string="Type", store=True)
    property_subtype_id = fields.Many2one(
        related="property_id.property_subtype_id", string="Sub Type", store=True
    )
    property_project_id = fields.Many2one(
        related="property_id.property_project_id", string="Project", store=True
    )
    subproject_id = fields.Many2one(related="property_id.subproject_id", string="Sub Project", store=True)
    region_id = fields.Many2one(related="property_id.region_id", store=True)
    street = fields.Char(related="property_id.street")
    street2 = fields.Char(related="property_id.street2")
    city_id = fields.Many2one(related="property_id.city_id")
    zip = fields.Char(related="property_id.zip")
    state_id = fields.Many2one(related="property_id.state_id")
    country_id = fields.Many2one(related="property_id.country_id")

    property_landlord_id = fields.Many2one(
        related="property_id.landlord_id", string="Landlord", store=True, index=True
    )
    landlord_phone = fields.Char(related="property_landlord_id.phone", string="Landlord Phone")
    landlord_email = fields.Char(related="property_landlord_id.email", string="Landlord Email")
    tenancy_id = fields.Many2one(
        "res.partner",
        string="Tenant",
        domain="[('user_type', '=', 'customer')]",
        index=True,
        tracking=True,
        check_company=True,
    )
    customer_phone = fields.Char(related="tenancy_id.phone", string="Customer Phone")
    customer_email = fields.Char(related="tenancy_id.email", string="Customer Email")

    extended = fields.Boolean(string="Is Extended", copy=False)
    is_extended = fields.Boolean(string="Is Extended Contract", copy=False)
    extend_from = fields.Char(string="Extend From.", copy=False)
    extend_ref = fields.Char(string="Extend Ref.", copy=False)
    new_contract_id = fields.Many2one(
        "tenancy.details", string="Renewed Contract", copy=False, check_company=True
    )
    previous_contract_id = fields.Many2one(
        "tenancy.details", string="Previous Contract", copy=False, check_company=True, index=True
    )
    renewal_ids = fields.One2many("tenancy.details", "previous_contract_id", string="Renewals")
    renewal_count = fields.Integer(compute="_compute_related_counts")

    payment_term = fields.Selection(
        [
            ("monthly", "Monthly"),
            ("quarterly", "Quarterly"),
            ("year", "Yearly"),
            ("full_payment", "Full Payment"),
        ],
        string="Payment Term",
        default="monthly",
        tracking=True,
    )
    invoice_payment_term_id = fields.Many2one(
        "account.payment.term", string="Accounting Payment Terms", check_company=True
    )
    duration_id = fields.Many2one("contract.duration", string="Duration", tracking=True)
    month = fields.Integer(related="duration_id.month", string="Duration Units", store=True)
    total_rent = fields.Monetary(string="Rent", tracking=True)
    rent_unit = fields.Selection(related="property_id.rent_unit", store=True)
    start_date = fields.Date(
        string="Start Date", default=fields.Date.context_today, tracking=True, index=True
    )
    end_date = fields.Date(
        string="End Date", compute="_compute_end_date", store=True, readonly=True, tracking=True, index=True
    )
    invoice_start_date = fields.Date(
        string="Invoice Start From", default=fields.Date.context_today, tracking=True
    )
    last_invoice_payment_date = fields.Date(string="Last Invoice Payment Date", copy=False)
    rent_invoice_ids = fields.One2many("rent.invoice", "tenancy_id", string="Invoices")
    total_area = fields.Float(related="property_id.total_area")
    usable_area = fields.Float(related="property_id.usable_area")
    measure_unit = fields.Selection(related="property_id.measure_unit")
    type = fields.Selection(
        [
            ("automatic", "Automatic Installments"),
            ("manual", "Manual Installments"),
        ],
        default="automatic",
        required=True,
        string="Installment Mode",
        tracking=True,
    )
    is_any_deposit = fields.Boolean(string="Deposit", tracking=True)
    deposit_amount = fields.Monetary(string="Security Deposit", tracking=True)

    is_extra_service = fields.Boolean(related="property_id.is_extra_service", string="Any Extra Services")
    extra_services_ids = fields.One2many("tenancy.service.line", "tenancy_id", string="Services")
    is_maintenance_service = fields.Boolean(
        related="property_id.is_maintenance_service", string="Is Any Maintenance"
    )
    maintenance_rent_type = fields.Selection(
        related="property_id.maintenance_rent_type", string="Maintenance Type"
    )
    total_maintenance = fields.Monetary(
        related="property_id.total_maintenance", string="Total Maintenance"
    )
    maintenance_type = fields.Selection(related="property_id.maintenance_type")
    per_area_maintenance = fields.Monetary(related="property_id.per_area_maintenance")

    is_any_broker = fields.Boolean(string="Any Broker", tracking=True)
    broker_invoice_state = fields.Boolean(string="Broker Invoice State", compute="_compute_broker_state")
    broker_invoice_id = fields.Many2one("account.move", string="Broker Bill", copy=False, check_company=True)
    broker_id = fields.Many2one(
        "res.partner", string="Broker", domain="[('user_type', '=', 'broker')]", tracking=True
    )
    commission = fields.Monetary(string="Calculated Broker Commission", compute="_compute_broker_commission", store=True)
    rent_type = fields.Selection(
        [("once", "One Period"), ("e_rent", "All Contract Periods")],
        string="Brokerage Type",
    )
    commission_type = fields.Selection(
        [("f", "Fixed"), ("p", "Percentage")], string="Commission Type"
    )
    broker_commission = fields.Monetary(string="Fixed Broker Commission")
    broker_commission_percentage = fields.Float(string="Percentage")
    commission_from = fields.Selection(
        [("customer", "Tenant"), ("landlord", "Landlord"), ("both", "Tenant and Landlord")],
        string="Commission From",
    )
    commission_ids = fields.One2many("rental.commission", "contract_id", string="Commission Records")
    commission_count = fields.Integer(compute="_compute_related_counts")

    installment_item_id = fields.Many2one(
        "product.product",
        string="Installment Item",
        default=lambda self: self.env.ref(
            "rental_management.property_product_1", raise_if_not_found=False
        ),
        check_company=True,
    )
    deposit_item_id = fields.Many2one(
        "product.product",
        string="Deposit Item",
        default=lambda self: self.env.ref(
            "rental_management.property_product_2", raise_if_not_found=False
        ),
        check_company=True,
    )
    broker_item_id = fields.Many2one(
        "product.product",
        string="Broker Item",
        default=lambda self: self.env.ref(
            "rental_management.property_product_1", raise_if_not_found=False
        ),
        check_company=True,
    )
    maintenance_item_id = fields.Many2one(
        "product.product",
        string="Maintenance Item",
        domain="[('product_tmpl_id.is_maintenance', '=', True)]",
        check_company=True,
    )

    instalment_tax = fields.Boolean(string="Taxes on Installment?")
    deposit_tax = fields.Boolean(string="Taxes on Deposit?")
    service_tax = fields.Boolean(string="Taxes on Services?")
    tax_ids = fields.Many2many(
        "account.tax",
        string="Taxes",
        check_company=True,
        domain="[('type_tax_use', '=', 'sale'), ('company_id', '=', company_id)]",
    )

    agreement = fields.Html(string="Agreement")
    contract_agreement = fields.Binary(string="Contract Agreement")
    file_name = fields.Char(string="File Name", translate=True)
    term_condition = fields.Html(string="Term and Condition")

    total_tenancy = fields.Monetary(string="Untaxed Amount", compute="_compute_tenancy_calculation")
    tax_amount = fields.Monetary(string="Tax Amount", compute="_compute_tenancy_calculation")
    total_amount = fields.Monetary(string="Total Amount", compute="_compute_tenancy_calculation")
    paid_tenancy = fields.Monetary(string="Paid Amount", compute="_compute_tenancy_calculation")
    remain_tenancy = fields.Monetary(string="Remaining Amount", compute="_compute_tenancy_calculation")

    invoice_count = fields.Integer(string="Invoice Count", compute="_compute_related_counts")
    accounting_invoice_count = fields.Integer(compute="_compute_related_counts")
    maintenance_count = fields.Integer(compute="_compute_related_counts")
    document_count = fields.Integer(compute="_compute_related_counts")

    @api.model
    def _expand_contract_states(self, states, domain):
        return [key for key, _label in self._fields["contract_type"].selection]

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("tenancy_seq", "New") == "New":
                vals["tenancy_seq"] = self.env["ir.sequence"].next_by_code("tenancy.details") or "New"
            vals.setdefault("contract_type", "new_contract")
        records = super().create(vals_list)
        records._check_company_consistency()
        for contract in records.filtered(lambda record: record.contract_type == "running_contract"):
            contract._check_no_overlap()
        return records

    def write(self, vals):
        protected = {"property_id", "tenancy_id", "company_id", "start_date", "duration_id"}
        if protected.intersection(vals) and any(
            record.contract_type in ("running_contract", "expire_contract", "close_contract")
            for record in self
        ):
            if not self.env.context.get("allow_contract_structural_write"):
                raise UserError(_("Core contract parties, property, company and dates cannot be changed after activation."))
        result = super().write(vals)
        if {"property_id", "tenancy_id", "company_id", "start_date", "duration_id", "invoice_start_date"}.intersection(vals):
            self._check_company_consistency()
        if vals.get("contract_type") == "running_contract":
            for contract in self:
                contract._check_no_overlap()
        return result

    def unlink(self):
        if any(record.contract_type != "new_contract" for record in self):
            raise UserError(_("Only draft rental contracts can be deleted."))
        return super().unlink()

    @api.depends("contract_type")
    def _compute_legacy_state_flags(self):
        for contract in self:
            contract.active_contract_state = contract.contract_type == "running_contract"
            contract.close_contract_state = contract.contract_type in (
                "close_contract",
                "cancel_contract",
                "expire_contract",
            )

    @api.depends("start_date", "month", "rent_unit")
    def _compute_end_date(self):
        for contract in self:
            contract.end_date = False
            if not contract.start_date or not contract.month or contract.month <= 0:
                continue
            if contract.rent_unit == "Day":
                contract.end_date = contract.start_date + relativedelta(days=contract.month - 1)
            elif contract.rent_unit == "Year":
                contract.end_date = contract.start_date + relativedelta(years=contract.month) - timedelta(days=1)
            else:
                contract.end_date = contract.start_date + relativedelta(months=contract.month) - timedelta(days=1)

    @api.depends(
        "is_any_broker",
        "month",
        "broker_commission",
        "broker_commission_percentage",
        "commission_type",
        "rent_type",
        "total_rent",
        "payment_term",
    )
    def _compute_broker_commission(self):
        for contract in self:
            base = 0.0
            if contract.is_any_broker:
                if contract.commission_type == "f":
                    base = contract.broker_commission
                elif contract.commission_type == "p":
                    base = contract.total_rent * contract.broker_commission_percentage / 100.0
                if contract.rent_type == "e_rent":
                    base *= contract._get_contract_charge_units()
            contract.commission = base

    @api.depends("commission_ids.broker_bill_id", "commission_ids.broker_bill_id.state")
    def _compute_broker_state(self):
        for contract in self:
            bills = contract.commission_ids.mapped("broker_bill_id")
            contract.broker_invoice_state = bool(bills)

    @api.depends("start_date", "end_date", "contract_type")
    def compute_days_left(self):
        today = fields.Date.context_today(self)
        for contract in self:
            contract.days_left = max((contract.end_date - today).days, 0) if (
                contract.contract_type == "running_contract" and contract.end_date
            ) else 0

    @api.depends(
        "rent_invoice_ids.rent_invoice_id.amount_untaxed",
        "rent_invoice_ids.rent_invoice_id.amount_total",
        "rent_invoice_ids.rent_invoice_id.amount_residual",
        "rent_invoice_ids.rent_invoice_id.state",
    )
    def _compute_tenancy_calculation(self):
        for contract in self:
            moves = contract.rent_invoice_ids.mapped("rent_invoice_id").filtered(
                lambda move: move.state != "cancel"
            )
            contract.total_tenancy = sum(moves.mapped("amount_untaxed"))
            contract.total_amount = sum(moves.mapped("amount_total"))
            contract.tax_amount = contract.total_amount - contract.total_tenancy
            contract.remain_tenancy = sum(moves.mapped("amount_residual"))
            contract.paid_tenancy = contract.total_amount - contract.remain_tenancy

    def _compute_related_counts(self):
        invoice_groups = self.env["rent.invoice"]._read_group(
            [("tenancy_id", "in", self.ids)], ["tenancy_id"], ["__count"]
        ) if self.ids else []
        invoice_map = {contract.id: count for contract, count in invoice_groups}
        move_groups = self.env["account.move"]._read_group(
            [("tenancy_id", "in", self.ids)], ["tenancy_id"], ["__count"]
        ) if self.ids else []
        move_map = {contract.id: count for contract, count in move_groups}
        maintenance_groups = self.env["maintenance.request"]._read_group(
            [("tenancy_id", "in", self.ids)], ["tenancy_id"], ["__count"]
        ) if self.ids else []
        maintenance_map = {contract.id: count for contract, count in maintenance_groups}
        commission_groups = self.env["rental.commission"]._read_group(
            [("contract_id", "in", self.ids)], ["contract_id"], ["__count"]
        ) if self.ids else []
        commission_map = {contract.id: count for contract, count in commission_groups}
        renewal_groups = self.env["tenancy.details"]._read_group(
            [("previous_contract_id", "in", self.ids)], ["previous_contract_id"], ["__count"]
        ) if self.ids else []
        renewal_map = {contract.id: count for contract, count in renewal_groups}
        property_ids = self.mapped("property_id").ids
        document_groups = self.env["property.documents"]._read_group(
            [("property_id", "in", property_ids)], ["property_id"], ["__count"]
        ) if property_ids else []
        document_map = {property_record.id: count for property_record, count in document_groups}
        for contract in self:
            contract.invoice_count = invoice_map.get(contract.id, 0)
            contract.accounting_invoice_count = move_map.get(contract.id, 0)
            contract.maintenance_count = maintenance_map.get(contract.id, 0)
            contract.document_count = document_map.get(contract.property_id.id, 0)
            contract.commission_count = commission_map.get(contract.id, 0)
            contract.renewal_count = renewal_map.get(contract.id, 0)

    @api.constrains("start_date", "end_date", "duration_id", "invoice_start_date", "total_rent")
    def _check_contract_dates_and_amounts(self):
        for contract in self:
            if contract.duration_id and contract.duration_id.month <= 0:
                raise ValidationError(_("Contract duration must be greater than zero."))
            if contract.start_date and contract.end_date and contract.start_date > contract.end_date:
                raise ValidationError(_("Contract start date cannot be after its end date."))
            if contract.invoice_start_date and contract.start_date and contract.end_date:
                if not contract.start_date <= contract.invoice_start_date <= contract.end_date:
                    raise ValidationError(_("Invoice start date must fall within the contract period."))
            if contract.total_rent <= 0:
                raise ValidationError(_("Rent amount must be greater than zero."))

    @api.constrains("broker_commission_percentage", "broker_commission", "is_any_broker")
    def _check_broker_values(self):
        for contract in self:
            if contract.broker_commission < 0 or contract.broker_commission_percentage < 0:
                raise ValidationError(_("Broker commission cannot be negative."))
            if contract.broker_commission_percentage > 100:
                raise ValidationError(_("Broker commission percentage cannot exceed 100%."))

    @api.constrains("property_id", "tenancy_id", "company_id", "tax_ids")
    def _check_company_consistency(self):
        for contract in self:
            if contract.property_id and contract.property_id.company_id != contract.company_id:
                raise ValidationError(_("The property and rental contract must belong to the same company."))
            if contract.tax_ids.filtered(lambda tax: tax.company_id != contract.company_id):
                raise ValidationError(_("All contract taxes must belong to the contract company."))

    def _check_required_for_activation(self):
        self.ensure_one()
        required = {
            _("Property"): self.property_id,
            _("Tenant"): self.tenancy_id,
            _("Company"): self.company_id,
            _("Start Date"): self.start_date,
            _("Duration"): self.duration_id,
            _("End Date"): self.end_date,
            _("Rent Amount"): self.total_rent,
            _("Payment Term"): self.payment_term,
            _("Invoice Start Date"): self.invoice_start_date,
            _("Installment Product"): self.installment_item_id,
        }
        missing = [label for label, value in required.items() if not value]
        if missing:
            raise UserError(_("Complete the following fields before activation: %s") % ", ".join(missing))
        if self.is_any_deposit and not self.deposit_item_id:
            raise UserError(_("Select a deposit product before activation."))
        if self.is_maintenance_service and not self.maintenance_item_id:
            raise UserError(_("Select a separate maintenance product before activation."))
        if self.is_any_broker:
            broker_required = [self.broker_id, self.broker_item_id, self.rent_type, self.commission_type, self.commission_from]
            if not all(broker_required):
                raise UserError(_("Complete all broker and commission fields before activation."))
        self._check_contract_dates_and_amounts()
        self._check_company_consistency()

    def _get_overlap_contract(self):
        self.ensure_one()
        if not (self.property_id and self.start_date and self.end_date):
            return self.env["tenancy.details"]
        return self.search(
            [
                ("id", "!=", self.id),
                ("property_id", "=", self.property_id.id),
                ("contract_type", "in", ["running_contract", "expire_contract"]),
                ("start_date", "<=", self.end_date),
                ("end_date", ">=", self.start_date),
            ],
            limit=1,
        )

    def _check_no_overlap(self):
        self.ensure_one()
        conflict = self._get_overlap_contract()
        if conflict:
            raise ValidationError(
                _(
                    "Contract %(contract)s conflicts with property %(property)s from %(start)s to %(end)s."
                )
                % {
                    "contract": conflict.tenancy_seq,
                    "property": conflict.property_id.display_name,
                    "start": conflict.start_date,
                    "end": conflict.end_date,
                }
            )

    def action_active_contract(self):
        """Compatibility entry point used by existing views and wizards."""
        return self.action_activate_contract()

    def action_activate_contract(self):
        for contract in self:
            if contract.contract_type == "running_contract":
                contract._ensure_installment_schedule()
                contract._sync_property_stage()
                continue
            if contract.contract_type != "new_contract":
                raise UserError(_("Only draft contracts can be activated."))
            contract._check_required_for_activation()
            contract._check_no_overlap()
            with self.env.cr.savepoint():
                contract.with_context(allow_contract_structural_write=True).write(
                    {
                        "contract_type": "running_contract",
                        "activation_date": fields.Datetime.now(),
                        "activated_by_id": self.env.user.id,
                    }
                )
                contract._sync_property_stage()
                property_stage = contract.property_id.stage
                contract.tenancy_id.is_tenancy = True
                schedules = contract._ensure_installment_schedule()
                contract._ensure_commission_records()
                if contract.type == "automatic":
                    due = schedules.filtered(
                        lambda line: not line.rent_invoice_id
                        and line.due_date
                        and line.due_date <= fields.Date.context_today(contract)
                    )
                    for line in due:
                        line._create_account_move()
                contract._send_activation_email_once()
                contract._schedule_expiry_activity()
                contract.message_post(
                    body=_(
                        "Contract activated. Property status changed to %(status)s."
                    ) % {"status": _("Rented") if property_stage == "on_lease" else _("Reserved")},
                    subtype_xmlid="mail.mt_note",
                )
        return True

    def _check_manager_operation(self):
        if not self.env.user.has_group("rental_management.property_rental_manager"):
            raise AccessError(_("Only a Rental Manager can close or cancel rental contracts."))

    def action_close_contract(self):
        self._check_manager_operation()
        for contract in self:
            if contract.contract_type not in ("running_contract", "expire_contract"):
                raise UserError(_("Only running or expired contracts can be closed."))
            posted_open = contract.rent_invoice_ids.mapped("rent_invoice_id").filtered(
                lambda move: move.state == "posted" and move.amount_residual > 0
            )
            if posted_open:
                contract.message_post(
                    body=_(
                        "The contract was closed with %(count)s posted outstanding invoice(s). "
                        "The accounting documents were preserved for collection or adjustment."
                    ) % {"count": len(posted_open)}
                )
            contract.write(
                {
                    "contract_type": "close_contract",
                    "close_date": fields.Datetime.now(),
                    "closed_by_id": self.env.user.id,
                }
            )
            contract._complete_open_activities(_("Contract closed"))
            contract._release_property_if_possible()
            contract.message_post(body=_("Contract closed by %s.") % self.env.user.display_name)
        return True

    def action_open_cancel_wizard(self):
        self.ensure_one()
        self._check_manager_operation()
        return {
            "type": "ir.actions.act_window",
            "name": _("Cancel Rental Contract"),
            "res_model": "cancel.contract.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_tenancy_id": self.id},
        }

    def action_cancel_contract(self, reason=None):
        self._check_manager_operation()
        for contract in self:
            if contract.contract_type in ("close_contract", "cancel_contract"):
                raise UserError(_("The contract is already closed or cancelled."))
            posted = contract.rent_invoice_ids.mapped("rent_invoice_id").filtered(
                lambda move: move.state == "posted"
            )
            if posted:
                raise UserError(
                    _("Posted invoices exist. Create the required credit notes or accounting adjustments before cancellation.")
                )
            cancellation_reason = reason or self.env.context.get("cancel_reason")
            if not cancellation_reason:
                return contract.action_open_cancel_wizard()
            contract.write(
                {
                    "contract_type": "cancel_contract",
                    "cancel_date": fields.Datetime.now(),
                    "cancelled_by_id": self.env.user.id,
                    "cancel_reason": cancellation_reason,
                }
            )
            contract._complete_open_activities(_("Contract cancelled"))
            contract._release_property_if_possible()
            contract.message_post(
                body=_("Contract cancelled by %(user)s. Reason: %(reason)s")
                % {"user": self.env.user.display_name, "reason": cancellation_reason}
            )
        return True

    def _sync_property_stage(self):
        """Synchronize each related property from all running contracts.

        A currently effective contract takes precedence over a future reservation. This
        keeps a property shown as rented when a future renewal has already been
        activated while the previous contract is still running.
        """
        today = fields.Date.context_today(self)
        properties = self.mapped("property_id")
        if not properties:
            return
        grouped = self._read_group(
            [
                ("property_id", "in", properties.ids),
                ("contract_type", "=", "running_contract"),
                ("end_date", ">=", today),
            ],
            ["property_id", "start_date"],
            ["__count"],
        )
        current_property_ids = set()
        future_property_ids = set()
        for property_rec, start_date, _count in grouped:
            if not property_rec:
                continue
            if start_date and start_date <= today:
                current_property_ids.add(property_rec.id)
            else:
                future_property_ids.add(property_rec.id)
        for property_rec in properties:
            target_stage = (
                "on_lease"
                if property_rec.id in current_property_ids
                else "booked"
                if property_rec.id in future_property_ids
                else "available"
            )
            if property_rec.stage != target_stage:
                property_rec.stage = target_stage

    def _release_property_if_possible(self):
        """Compatibility wrapper used by close/cancel/expiry flows."""
        self._sync_property_stage()

    def _complete_open_activities(self, feedback):
        for contract in self:
            activities = contract.activity_ids.filtered(lambda activity: activity.active)
            if activities:
                activities.action_feedback(feedback=feedback)

    def _schedule_expiry_activity(self):
        activity_type = self.env.ref("mail.mail_activity_data_todo", raise_if_not_found=False)
        for contract in self.filtered(lambda rec: rec.end_date and rec.responsible_id and activity_type):
            deadline = contract.end_date - relativedelta(days=30)
            existing = contract.activity_ids.filtered(
                lambda activity: activity.activity_type_id == activity_type
                and activity.summary == _("Rental contract expiry review")
            )
            if not existing:
                contract.activity_schedule(
                    activity_type_id=activity_type.id,
                    user_id=contract.responsible_id.id,
                    date_deadline=deadline,
                    summary=_("Rental contract expiry review"),
                    note=_("Review renewal, closure, or handover before contract expiry."),
                )

    def _get_invoice_post_type(self):
        return self.env["ir.config_parameter"].sudo().get_param(
            "rental_management.invoice_post_type", "manual"
        )

    def _get_reminder_days(self):
        value = self.env["ir.config_parameter"].sudo().get_param(
            "rental_management.reminder_days", "0"
        )
        try:
            return max(int(value), 0)
        except (TypeError, ValueError):
            return 0

    def _get_contract_charge_units(self):
        self.ensure_one()
        return max(self.month, 1)

    def _get_period_delta(self):
        self.ensure_one()
        if self.payment_term == "monthly":
            return relativedelta(months=1)
        if self.payment_term == "quarterly":
            return relativedelta(months=3)
        if self.payment_term == "year":
            return relativedelta(years=1)
        return None

    def _iter_invoice_periods(self):
        self.ensure_one()
        if not self.start_date or not self.end_date:
            return
        if self.payment_term == "full_payment":
            yield self.start_date, self.end_date, self.invoice_start_date, "full_rent"
            return
        delta = self._get_period_delta()
        if not delta:
            return
        period_start = self.start_date
        due_date = self.invoice_start_date
        while period_start <= self.end_date:
            nominal_next = period_start + delta
            period_end = min(nominal_next - timedelta(days=1), self.end_date)
            yield period_start, period_end, due_date, "rent"
            period_start = nominal_next
            due_date += delta

    def _ensure_installment_schedule(self):
        self.ensure_one()
        commands = []
        existing_keys = {
            (line.period_start, line.period_end, line.invoice_type)
            for line in self.rent_invoice_ids
            if line.period_start and line.period_end
        }
        for period_start, period_end, due_date, invoice_type in self._iter_invoice_periods():
            key = (period_start, period_end, invoice_type)
            if key in existing_keys:
                continue
            amount = self._compute_period_rent_amount(period_start, period_end)
            commands.append(
                {
                    "tenancy_id": self.id,
                    "company_id": self.company_id.id,
                    "type": "full_rent" if invoice_type == "full_rent" else "rent",
                    "invoice_type": invoice_type,
                    "period_start": period_start,
                    "period_end": period_end,
                    "due_date": due_date,
                    "invoice_date": due_date,
                    "description": self._get_period_description(period_start, period_end),
                    "amount": amount,
                    "rent_amount": amount,
                    "is_yearly": self.payment_term == "year",
                }
            )
        if commands:
            self.env["rent.invoice"].create(commands)
        return self.rent_invoice_ids.sorted(lambda line: (line.due_date or fields.Date.today(), line.id))

    def _get_period_description(self, period_start, period_end):
        self.ensure_one()
        if self.payment_term == "full_payment":
            return _("Full rent for %(property)s (%(start)s - %(end)s)") % {
                "property": self.property_id.display_name,
                "start": period_start,
                "end": period_end,
            }
        return _("Rent for %(property)s (%(start)s - %(end)s)") % {
            "property": self.property_id.display_name,
            "start": period_start,
            "end": period_end,
        }

    def _compute_period_rent_amount(self, period_start, period_end):
        self.ensure_one()
        if self.payment_term == "full_payment":
            return self.total_rent * self._get_contract_charge_units()
        if self.payment_term in ("monthly", "quarterly"):
            return self.total_rent * self._count_month_equivalents(period_start, period_end)
        if self.payment_term == "year":
            nominal_end = period_start + relativedelta(years=1) - timedelta(days=1)
            nominal_days = (nominal_end - period_start).days + 1
            actual_days = (period_end - period_start).days + 1
            return self.total_rent * actual_days / nominal_days
        return self.total_rent

    @api.model
    def _count_month_equivalents(self, period_start, period_end):
        total = 0.0
        cursor = period_start
        while cursor <= period_end:
            days_in_month = calendar.monthrange(cursor.year, cursor.month)[1]
            segment_end = min(cursor.replace(day=days_in_month), period_end)
            total += ((segment_end - cursor).days + 1) / days_in_month
            cursor = segment_end + timedelta(days=1)
        return total

    def _prepare_period_invoice_lines(self, schedule):
        self.ensure_one()
        months = self._count_month_equivalents(schedule.period_start, schedule.period_end)
        rent_amount = self._compute_period_rent_amount(schedule.period_start, schedule.period_end)
        first_period = schedule.period_start == self.start_date
        lines = []
        breakdown = {"rent": rent_amount, "deposit": 0.0, "services": 0.0, "maintenance": 0.0}

        lines.append(
            Command.create(
                self._prepare_invoice_line_vals(
                    product=self.installment_item_id,
                    name=schedule.description,
                    quantity=1.0,
                    price_unit=rent_amount,
                    apply_tax=self.instalment_tax,
                )
            )
        )
        if first_period and self.is_any_deposit and self.deposit_amount:
            breakdown["deposit"] = self.deposit_amount
            lines.append(
                Command.create(
                    self._prepare_invoice_line_vals(
                        product=self.deposit_item_id,
                        name=_("Security deposit for %s") % self.property_id.display_name,
                        quantity=1.0,
                        price_unit=self.deposit_amount,
                        apply_tax=self.deposit_tax,
                    )
                )
            )

        for service in self.extra_services_ids:
            quantity = 1.0 if service.service_type == "once" else months
            if service.service_type == "once" and not first_period:
                continue
            if not quantity or not service.price:
                continue
            breakdown["services"] += quantity * service.price
            lines.append(
                Command.create(
                    self._prepare_invoice_line_vals(
                        product=service.service_id,
                        name=_("%(kind)s service: %(service)s")
                        % {
                            "kind": _("One-time") if service.service_type == "once" else _("Recurring"),
                            "service": service.service_id.display_name,
                        },
                        quantity=quantity,
                        price_unit=service.price,
                        apply_tax=self.service_tax,
                    )
                )
            )

        if self.is_maintenance_service and self.total_maintenance:
            recurring = self.maintenance_rent_type == "recurring"
            if recurring or first_period:
                quantity = months if recurring else 1.0
                breakdown["maintenance"] += quantity * self.total_maintenance
                lines.append(
                    Command.create(
                        self._prepare_invoice_line_vals(
                            product=self.maintenance_item_id,
                            name=_("Maintenance for %s") % self.property_id.display_name,
                            quantity=quantity,
                            price_unit=self.total_maintenance,
                            apply_tax=self.service_tax,
                        )
                    )
                )
        return lines, breakdown

    def _prepare_invoice_line_vals(self, product, name, quantity, price_unit, apply_tax=False):
        self.ensure_one()
        if not product:
            raise UserError(_("A required invoice product is missing on the rental contract."))
        vals = {
            "product_id": product.id,
            "name": name,
            "quantity": quantity,
            "price_unit": price_unit,
        }
        if apply_tax:
            vals["tax_ids"] = [Command.set(self.tax_ids.ids)]
        return vals

    def _prepare_rent_invoice_vals(self, schedule, invoice_lines):
        self.ensure_one()
        vals = {
            "partner_id": self.tenancy_id.id,
            "move_type": "out_invoice",
            "invoice_date": schedule.due_date or fields.Date.context_today(self),
            "company_id": self.company_id.id,
            "currency_id": self.currency_id.id,
            "invoice_origin": self.tenancy_seq,
            "ref": self.tenancy_seq,
            "tenancy_id": self.id,
            "rental_schedule_id": schedule.id,
            "invoice_line_ids": invoice_lines,
        }
        if self.invoice_payment_term_id:
            vals["invoice_payment_term_id"] = self.invoice_payment_term_id.id
        fiscal_position = self.tenancy_id.with_company(self.company_id).property_account_position_id
        if fiscal_position:
            vals["fiscal_position_id"] = fiscal_position.id
        return vals

    def action_create_rent_invoice_entry(self, amount, invoice_id):
        """Legacy-compatible helper; it never duplicates an existing move link."""
        self.ensure_one()
        existing = self.rent_invoice_ids.filtered(lambda line: line.rent_invoice_id == invoice_id)
        if existing:
            return existing
        return self.env["rent.invoice"].create(
            {
                "tenancy_id": self.id,
                "company_id": self.company_id.id,
                "type": "rent",
                "invoice_type": "rent",
                "invoice_date": invoice_id.invoice_date,
                "due_date": invoice_id.invoice_date,
                "description": _("Rental invoice"),
                "rent_invoice_id": invoice_id.id,
                "amount": amount,
            }
        )

    def action_utility_service_invoice(self):
        """Legacy helper returning first-period service line commands."""
        self.ensure_one()
        dummy = self.env["rent.invoice"].new(
            {"period_start": self.start_date, "period_end": min(self.end_date, self.start_date + (self._get_period_delta() or relativedelta(months=1)) - timedelta(days=1))}
        )
        lines, _breakdown = self._prepare_period_invoice_lines(dummy)
        return lines[1:]  # rent line is first

    def _ensure_commission_records(self):
        self.ensure_one()
        if not self.is_any_broker or not self.commission:
            return self.env["rental.commission"]
        sources = ["customer", "landlord"] if self.commission_from == "both" else [self.commission_from]
        records = self.env["rental.commission"]
        for source in filter(None, sources):
            record = self.env["rental.commission"].search(
                [("contract_id", "=", self.id), ("source", "=", source)], limit=1
            )
            if not record:
                record = self.env["rental.commission"].create(
                    {
                        "contract_id": self.id,
                        "source": source,
                        "broker_id": self.broker_id.id,
                        "amount": self.commission,
                        "company_id": self.company_id.id,
                        "currency_id": self.currency_id.id,
                    }
                )
            record.action_create_accounting_documents()
            if record.broker_bill_id and not self.broker_invoice_id:
                self.broker_invoice_id = record.broker_bill_id
            records |= record
        return records

    def action_broker_invoice(self):
        for contract in self:
            contract._check_required_for_activation()
            contract._ensure_commission_records()
        return True

    def action_invoices(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Rental Installments"),
            "res_model": "rent.invoice",
            "domain": [("tenancy_id", "=", self.id)],
            "view_mode": "list,form",
            "context": {"default_tenancy_id": self.id, "default_company_id": self.company_id.id},
        }

    def action_accounting_invoices(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Accounting Invoices"),
            "res_model": "account.move",
            "domain": [("tenancy_id", "=", self.id)],
            "view_mode": "list,form",
            "context": {"default_tenancy_id": self.id, "default_move_type": "out_invoice"},
        }


    def action_create_maintenance_request(self):
        self.ensure_one()
        if self.contract_type != "running_contract":
            raise UserError(_("Maintenance requests can only be created for a running contract."))
        return {
            "type": "ir.actions.act_window",
            "name": _("Create Maintenance Request"),
            "res_model": "maintenance.request",
            "view_mode": "form",
            "target": "current",
            "context": {
                "default_tenancy_id": self.id,
                "default_property_id": self.property_id.id,
                "default_landlord_id": self.property_landlord_id.id,
                "default_company_id": self.company_id.id,
            },
        }

    def action_register_payment(self):
        self.ensure_one()
        invoices = self.env["account.move"].search(
            [
                ("tenancy_id", "=", self.id),
                ("move_type", "=", "out_invoice"),
                ("state", "=", "posted"),
                ("payment_state", "in", ["not_paid", "partial"]),
            ]
        )
        if not invoices:
            raise UserError(_("There are no posted unpaid rental invoices to register."))
        return {
            "type": "ir.actions.act_window",
            "name": _("Register Payment"),
            "res_model": "account.payment.register",
            "view_mode": "form",
            "target": "new",
            "context": {
                "active_model": "account.move",
                "active_ids": invoices.ids,
            },
        }

    def action_documents(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Property Documents"),
            "res_model": "property.documents",
            "domain": [("property_id", "=", self.property_id.id)],
            "view_mode": "list,form",
            "context": {"default_property_id": self.property_id.id},
        }

    def action_commissions(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Broker Commissions"),
            "res_model": "rental.commission",
            "domain": [("contract_id", "=", self.id)],
            "view_mode": "list,form",
            "context": {"default_contract_id": self.id, "default_company_id": self.company_id.id},
        }

    def action_maintenance_requests(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Maintenance Requests"),
            "res_model": "maintenance.request",
            "domain": [("tenancy_id", "=", self.id)],
            "view_mode": "list,form",
            "context": {
                "default_tenancy_id": self.id,
                "default_property_id": self.property_id.id,
                "default_company_id": self.company_id.id,
            },
        }

    def action_renewals(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Contract Renewals"),
            "res_model": "tenancy.details",
            "domain": ["|", ("previous_contract_id", "=", self.id), ("id", "=", self.previous_contract_id.id)],
            "view_mode": "list,form",
        }

    def action_send_active_contract(self):
        return self._send_activation_email_once()

    def _send_activation_email_once(self):
        template = self.env.ref("rental_management.active_contract_mail_template", raise_if_not_found=False)
        for contract in self.filtered(lambda rec: not rec.activation_email_sent and template):
            if contract.tenancy_id.email:
                template.send_mail(contract.id, force_send=False)
                contract.activation_email_sent = True
        return True

    def action_send_tenancy_reminder(self):
        template = self.env.ref("rental_management.tenancy_reminder_mail_template", raise_if_not_found=False)
        for contract in self.filtered(lambda rec: template and rec.tenancy_id.email):
            template.send_mail(contract.id, force_send=False)
        return True

    def _send_invoice_reminder_once(self, schedule):
        self.ensure_one()
        if self.last_reminder_schedule_id == schedule:
            return
        self.action_send_tenancy_reminder()
        self.last_reminder_schedule_id = schedule

    @api.model
    def _cron_process_rental_lifecycle(self, batch_size=200):
        today = fields.Date.context_today(self)
        running = self.search(
            [("contract_type", "=", "running_contract")], order="end_date, id", limit=batch_size
        )
        reminder_days = self._get_reminder_days()
        reminder_limit = today + relativedelta(days=reminder_days)
        for contract in running:
            try:
                with self.env.cr.savepoint():
                    contract._ensure_installment_schedule()
                    if (
                        reminder_days > 0
                        and contract.end_date
                        and today <= contract.end_date <= reminder_limit
                        and not contract.expiry_reminder_sent
                    ):
                        contract.action_send_tenancy_reminder()
                        contract.expiry_reminder_sent = True
                        contract._schedule_expiry_activity()
                        contract.message_post(
                            body=_("Contract expiry reminder sent. End date: %s.") % contract.end_date
                        )
                    if contract.end_date and contract.end_date < today:
                        contract.write({"contract_type": "expire_contract"})
                        contract._release_property_if_possible()
                        contract._schedule_expiry_activity()
                        if not contract.expiry_email_sent:
                            contract.action_send_tenancy_reminder()
                            contract.expiry_email_sent = True
                        contract.message_post(body=_("Contract expired automatically on %s.") % contract.end_date)
            except Exception:
                _logger.exception("Rental lifecycle processing failed for contract %s", contract.display_name)
        running._sync_property_stage()
        self.env["rent.invoice"]._cron_create_due_invoices(batch_size=batch_size)
        return len(running)

    @api.model
    def tenancy_recurring_invoice(self):
        return self._cron_process_rental_lifecycle()

    @api.model
    def tenancy_recurring_quarterly_invoice(self):
        return self._cron_process_rental_lifecycle()

    @api.model
    def tenancy_yearly_invoice(self):
        return self._cron_process_rental_lifecycle()

    @api.model
    def tenancy_manual_invoice(self):
        return self._cron_process_rental_lifecycle()

    @api.model
    def tenancy_expire(self):
        return self._cron_process_rental_lifecycle()


class RentalCommission(models.Model):
    _name = "rental.commission"
    _description = "Rental Broker Commission"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "contract_id desc, source, id"
    _check_company_auto = True

    contract_id = fields.Many2one(
        "tenancy.details", required=True, ondelete="cascade", index=True, check_company=True
    )
    source = fields.Selection(
        [("customer", "Tenant"), ("landlord", "Landlord")], required=True, index=True
    )
    broker_id = fields.Many2one("res.partner", required=True, index=True)
    amount = fields.Monetary(required=True)
    company_id = fields.Many2one("res.company", required=True, index=True)
    currency_id = fields.Many2one("res.currency", required=True)
    broker_bill_id = fields.Many2one("account.move", copy=False, check_company=True)
    charge_invoice_id = fields.Many2one("account.move", copy=False, check_company=True)
    state = fields.Selection(
        [("draft", "Draft"), ("invoiced", "Invoiced"), ("cancelled", "Cancelled")],
        default="draft",
        required=True,
        tracking=True,
    )

    _commission_source_unique = models.Constraint(
        "UNIQUE(contract_id, source)", "Only one commission record per source is allowed."
    )
    _commission_amount_positive = models.Constraint(
        "CHECK(amount >= 0)", "Commission cannot be negative."
    )

    @api.constrains("contract_id", "company_id")
    def _check_company(self):
        for commission in self:
            if commission.company_id != commission.contract_id.company_id:
                raise ValidationError(_("Commission and contract must belong to the same company."))

    def action_create_accounting_documents(self):
        for commission in self:
            if commission.state == "invoiced" and commission.broker_bill_id and commission.charge_invoice_id:
                continue
            contract = commission.contract_id
            product = contract.broker_item_id
            if not product:
                raise UserError(_("Select a broker commission product on the contract."))
            source_partner = contract.tenancy_id if commission.source == "customer" else contract.property_landlord_id
            if not source_partner:
                raise UserError(_("The selected commission source has no partner configured."))
            line_name = _("Broker commission for %s") % contract.property_id.display_name
            line_vals = {
                "product_id": product.id,
                "name": line_name,
                "quantity": 1.0,
                "price_unit": commission.amount,
            }
            if not commission.broker_bill_id:
                bill = self.env["account.move"].with_company(commission.company_id).create(
                    {
                        "partner_id": commission.broker_id.id,
                        "move_type": "in_invoice",
                        "invoice_date": contract.invoice_start_date,
                        "company_id": commission.company_id.id,
                        "currency_id": commission.currency_id.id,
                        "invoice_origin": contract.tenancy_seq,
                        "tenancy_id": contract.id,
                        "invoice_line_ids": [Command.create(line_vals)],
                    }
                )
                if contract._get_invoice_post_type() == "automatically":
                    bill.action_post()
                commission.broker_bill_id = bill
            if not commission.charge_invoice_id:
                charge = self.env["account.move"].with_company(commission.company_id).create(
                    {
                        "partner_id": source_partner.id,
                        "move_type": "out_invoice",
                        "invoice_date": contract.invoice_start_date,
                        "company_id": commission.company_id.id,
                        "currency_id": commission.currency_id.id,
                        "invoice_origin": contract.tenancy_seq,
                        "tenancy_id": contract.id,
                        "invoice_line_ids": [Command.create(line_vals)],
                    }
                )
                if contract._get_invoice_post_type() == "automatically":
                    charge.action_post()
                commission.charge_invoice_id = charge
            commission.state = "invoiced"
        return True


class ContractDuration(models.Model):
    _name = "contract.duration"
    _description = "Contract Duration"
    _rec_name = "duration"
    _order = "rent_unit, month, id"

    duration = fields.Char(string="Duration", required=True, translate=True)
    month = fields.Integer(string="Unit", required=True)
    rent_unit = fields.Selection(
        [("Day", "Day"), ("Month", "Month"), ("Year", "Year")],
        default="Month",
        required=True,
        string="Rent Unit",
    )

    @api.constrains("month")
    def _check_positive_duration(self):
        for duration in self:
            if duration.month <= 0:
                raise ValidationError(_("Duration must be greater than zero."))


class TenancyExtraServiceLine(models.Model):
    _name = "tenancy.service.line"
    _description = "Tenancy Service Line"
    _check_company_auto = True

    service_id = fields.Many2one(
        "product.product",
        string="Service",
        required=True,
        domain="[('is_extra_service_product', '=', True)]",
        check_company=True,
    )
    price = fields.Float(string="Cost", required=True)
    service_type = fields.Selection(
        [("once", "Once"), ("monthly", "Recurring")], string="Type", default="once", required=True
    )
    tenancy_id = fields.Many2one(
        "tenancy.details", string="Tenancies", required=True, ondelete="cascade", check_company=True
    )
    company_id = fields.Many2one(related="tenancy_id.company_id", store=True, index=True)
    from_contract = fields.Boolean(copy=False)

    @api.constrains("price")
    def _check_non_negative_service_price(self):
        for service in self:
            if service.price < 0:
                raise ValidationError(_("Service price cannot be negative."))

    @api.onchange("service_id")
    def _onchange_service_id_price(self):
        for line in self:
            if line.service_id:
                line.price = line.service_id.lst_price

    def action_create_service_invoice(self):
        for service in self:
            contract = service.tenancy_id
            if contract.contract_type != "running_contract":
                raise UserError(_("Extra service invoices can only be created for a running contract."))
            today = fields.Date.context_today(service)
            existing = self.env["rent.invoice"].search(
                [
                    ("tenancy_id", "=", contract.id),
                    ("invoice_type", "=", "service"),
                    ("period_start", "=", today),
                    ("period_end", "=", today),
                ],
                limit=1,
            )
            if existing:
                return existing.action_create_invoice()
            schedule = self.env["rent.invoice"].create(
                {
                    "tenancy_id": contract.id,
                    "company_id": contract.company_id.id,
                    "type": "other",
                    "invoice_type": "service",
                    "period_start": today,
                    "period_end": today,
                    "due_date": today,
                    "invoice_date": today,
                    "description": _("Additional service: %s") % service.service_id.display_name,
                    "amount": service.price,
                }
            )
            line = Command.create(
                contract._prepare_invoice_line_vals(
                    product=service.service_id,
                    name=schedule.description,
                    quantity=1.0,
                    price_unit=service.price,
                    apply_tax=contract.service_tax,
                )
            )
            move = self.env["account.move"].with_company(contract.company_id).create(
                contract._prepare_rent_invoice_vals(schedule, [line])
            )
            if contract._get_invoice_post_type() == "automatically":
                move.action_post()
            schedule.write(
                {
                    "rent_invoice_id": move.id,
                    "amount": move.amount_total,
                    "service_amount": move.amount_total,
                }
            )
            service.from_contract = True
        return True


class AgreementTemplate(models.Model):
    _name = "agreement.template"
    _description = "Agreement Template"
    _check_company_auto = True

    name = fields.Char(string="Title", required=True, translate=True)
    company_id = fields.Many2one(
        "res.company", string="Company", required=True, default=lambda self: self.env.company, index=True
    )
    agreement = fields.Html(string="Agreement")
