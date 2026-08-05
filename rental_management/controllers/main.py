# -*- coding: utf-8 -*-

import logging

from dateutil.relativedelta import relativedelta

from werkzeug.exceptions import BadRequest, NotFound

from odoo import _, fields, http
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager

_logger = logging.getLogger(__name__)


class RentalCustomerPortal(CustomerPortal):
    """Permission-aware rental counters on the standard portal home page."""

    def _rental_partner_domain(self, partner_field):
        partner = request.env.user.partner_id.commercial_partner_id
        return [(f"{partner_field}.commercial_partner_id", "=", partner.id)]

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        contract_model = request.env["tenancy.details"]
        contract_domain = self._rental_partner_domain("tenancy_id")
        today = fields.Date.context_today(contract_model)

        if "sell_contract_count" in counters:
            values["sell_contract_count"] = request.env["property.vendor"].search_count(
                self._rental_partner_domain("customer_id")
            )
        if "rent_contract_count" in counters:
            values["rent_contract_count"] = contract_model.search_count(contract_domain)
        if "active_rent_contract_count" in counters:
            values["active_rent_contract_count"] = contract_model.search_count(
                contract_domain + [("contract_type", "=", "running_contract")]
            )
        if "expiring_rent_contract_count" in counters:
            limit_date = today + relativedelta(days=30)
            values["expiring_rent_contract_count"] = contract_model.search_count(
                contract_domain
                + [
                    ("contract_type", "=", "running_contract"),
                    ("end_date", ">=", today),
                    ("end_date", "<=", limit_date),
                ]
            )
        if "rent_invoice_count" in counters:
            values["rent_invoice_count"] = request.env["rent.invoice"].search_count(
                self._rental_partner_domain("tenancy_id.tenancy_id")
            )
        if "maintenance_count" in counters:
            values["maintenance_count"] = request.env["maintenance.request"].search_count(
                self._rental_partner_domain("tenancy_id.tenancy_id")
            )
        return values


class RentalPortalWebsite(http.Controller):
    """Rental portal routes with explicit ownership checks before any elevated read."""

    @staticmethod
    def _commercial_partner():
        return request.env.user.partner_id.commercial_partner_id

    def _own_contract_domain(self):
        return [
            (
                "tenancy_id.commercial_partner_id",
                "=",
                self._commercial_partner().id,
            )
        ]

    def _get_owned_contract(self, contract_id):
        contract = request.env["tenancy.details"].search(
            [("id", "=", contract_id)] + self._own_contract_domain(), limit=1
        )
        if not contract:
            raise NotFound()
        return contract

    def _get_owned_maintenance(self, request_id):
        maintenance = request.env["maintenance.request"].search(
            [
                ("id", "=", request_id),
                (
                    "tenancy_id.tenancy_id.commercial_partner_id",
                    "=",
                    self._commercial_partner().id,
                ),
            ],
            limit=1,
        )
        if not maintenance:
            raise NotFound()
        return maintenance

    @http.route(["/my/sell-contract/"], type="http", auth="user", website=True)
    def rental_user_sell_contract(self, page=1, sortby="date", **kwargs):
        domain = [
            ("customer_id.commercial_partner_id", "=", self._commercial_partner().id)
        ]
        sortings = {
            "date": {"label": _("Newest"), "order": "date desc, id desc"},
            "status": {"label": _("Status"), "order": "stage, date desc"},
        }
        sortby = sortby if sortby in sortings else "date"
        model = request.env["property.vendor"]
        pager = portal_pager(
            url="/my/sell-contract/",
            total=model.search_count(domain),
            page=int(page),
            step=20,
            url_args={"sortby": sortby},
        )
        contracts = model.search(
            domain, order=sortings[sortby]["order"], limit=20, offset=pager["offset"]
        )
        return request.render(
            "rental_management.rental_user_sell_contract_info",
            {"contract": contracts, "pager": pager, "sortings": sortings, "sortby": sortby},
        )

    @http.route(
        ["/my/sell-contract/information/<model(\"property.vendor\"):sale_contract>"],
        type="http",
        auth="user",
        website=True,
    )
    def rental_user_sell_contract_detail(self, sale_contract, **kwargs):
        owned = request.env["property.vendor"].search(
            [
                ("id", "=", sale_contract.id),
                ("customer_id.commercial_partner_id", "=", self._commercial_partner().id),
            ],
            limit=1,
        )
        if not owned:
            raise NotFound()
        return request.render(
            "rental_management.rental_user_sell_contract_details",
            {"sell_contract": owned},
        )

    @http.route(["/my/rent-contract/"], type="http", auth="user", website=True)
    def rental_user_rent_contract(self, page=1, sortby="date", filterby="all", **kwargs):
        filters = {
            "all": {"label": _("All"), "domain": []},
            "active": {"label": _("Active"), "domain": [("contract_type", "=", "running_contract")]},
            "expired": {"label": _("Expired"), "domain": [("contract_type", "=", "expire_contract")]},
            "closed": {"label": _("Closed"), "domain": [("contract_type", "=", "close_contract")]},
        }
        sortings = {
            "date": {"label": _("Newest"), "order": "start_date desc, id desc"},
            "expiry": {"label": _("Expiry"), "order": "end_date, id"},
            "status": {"label": _("Status"), "order": "contract_type, start_date desc"},
        }
        sortby = sortby if sortby in sortings else "date"
        filterby = filterby if filterby in filters else "all"
        domain = self._own_contract_domain() + filters[filterby]["domain"]
        model = request.env["tenancy.details"]
        pager = portal_pager(
            url="/my/rent-contract/",
            total=model.search_count(domain),
            page=int(page),
            step=20,
            url_args={"sortby": sortby, "filterby": filterby},
        )
        contracts = model.search(
            domain, order=sortings[sortby]["order"], limit=20, offset=pager["offset"]
        )
        return request.render(
            "rental_management.rental_user_rent_contract_info",
            {
                "contract": contracts,
                "pager": pager,
                "sortings": sortings,
                "sortby": sortby,
                "filters": filters,
                "filterby": filterby,
            },
        )

    @http.route(
        ["/my/rent-contract/information/<model(\"tenancy.details\"):contract>"],
        type="http",
        auth="user",
        website=True,
    )
    def rental_user_rent_contract_detail(self, contract, **kwargs):
        owned = self._get_owned_contract(contract.id)
        maintenance_types = request.env["product.template"].sudo().search(
            [("is_maintenance", "=", True), "|", ("company_id", "=", False), ("company_id", "=", owned.company_id.id)]
        )
        return request.render(
            "rental_management.rental_user_rent_contract_details",
            {
                "rent": owned,
                "maintenance_type": maintenance_types,
                "portal_today": fields.Date.context_today(owned),
            },
        )

    @http.route(
        ["/my/rent-contract/information/maintenance-request"],
        type="http",
        auth="user",
        website=True,
        methods=["POST"],
        csrf=True,
    )
    def rental_rent_maintenance_request(self, **post):
        try:
            contract_id = int(post.get("rent", 0))
            maintenance_type_id = int(post.get("maintenance_type_id", 0))
        except (TypeError, ValueError) as exc:
            raise BadRequest(_("Invalid maintenance request data.")) from exc
        contract = self._get_owned_contract(contract_id)
        if contract.contract_type != "running_contract":
            raise BadRequest(_("Maintenance requests can only be created for an active rental contract."))
        maintenance_type = request.env["product.template"].sudo().search(
            [
                ("id", "=", maintenance_type_id),
                ("is_maintenance", "=", True),
                "|",
                ("company_id", "=", False),
                ("company_id", "=", contract.company_id.id),
            ],
            limit=1,
        )
        if not maintenance_type:
            raise BadRequest(_("Select a valid maintenance type."))
        name = (post.get("request") or "").strip() or _("%s Maintenance Request") % contract.tenancy_seq
        description = (post.get("desc") or "").strip()
        maintenance = request.env["maintenance.request"].create(
            {
                "maintenance_type_id": maintenance_type.id,
                "name": name,
                "landlord_id": contract.property_landlord_id.id,
                "property_id": contract.property_id.id,
                "tenancy_id": contract.id,
                "company_id": contract.company_id.id,
                "description": description,
            }
        )
        contract.message_post(body=_("Portal maintenance request %s created.") % maintenance.display_name)
        return request.redirect("/my/maintenance-request/?created=1")

    @http.route(["/my/rent-invoices/"], type="http", auth="user", website=True)
    def rental_user_rent_invoices(self, page=1, sortby="date", **kwargs):
        domain = [
            (
                "tenancy_id.tenancy_id.commercial_partner_id",
                "=",
                self._commercial_partner().id,
            )
        ]
        sortings = {
            "date": {"label": _("Due Date"), "order": "due_date desc, id desc"},
            "status": {"label": _("Payment Status"), "order": "payment_state, due_date desc"},
        }
        sortby = sortby if sortby in sortings else "date"
        model = request.env["rent.invoice"]
        pager = portal_pager(
            url="/my/rent-invoices/",
            total=model.search_count(domain),
            page=int(page),
            step=20,
            url_args={"sortby": sortby},
        )
        records = model.search(
            domain,
            order=sortings[sortby]["order"],
            limit=20,
            offset=pager["offset"],
        )
        return request.render(
            "rental_management.rental_user_rent_invoice_info",
            {"rent_invoices": records, "pager": pager, "sortings": sortings, "sortby": sortby},
        )

    @http.route(["/my/maintenance-request/"], type="http", auth="user", website=True)
    def rental_user_maintenance_request(self, page=1, **kwargs):
        domain = [
            (
                "tenancy_id.tenancy_id.commercial_partner_id",
                "=",
                self._commercial_partner().id,
            )
        ]
        model = request.env["maintenance.request"]
        pager = portal_pager(
            url="/my/maintenance-request/",
            total=model.search_count(domain),
            page=int(page),
            step=20,
        )
        records = model.search(domain, order="create_date desc, id desc", limit=20, offset=pager["offset"])
        return request.render(
            "rental_management.rental_user_maintenance_info",
            {"maintenance_rec": records, "pager": pager, "created": kwargs.get("created")},
        )

    @http.route(
        ["/my/maintenance-request/information/<model(\"maintenance.request\"):maintenance>"],
        type="http",
        auth="user",
        website=True,
    )
    def rental_user_maintenance_request_details(self, maintenance, **kwargs):
        owned = self._get_owned_maintenance(maintenance.id)
        return request.render(
            "rental_management.rental_user_maintenance_details", {"mr": owned}
        )
