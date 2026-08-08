# -*- coding: utf-8 -*-
"""Post-upgrade lifecycle synchronization and anomaly reporting."""

import logging

from odoo import SUPERUSER_ID, api, fields

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    if not version:
        return
    env = api.Environment(cr, SUPERUSER_ID, {})
    Contract = env["tenancy.details"].with_context(active_test=False)
    Property = env["property.details"].with_context(active_test=False)
    today = fields.Date.today()

    expired = Contract.search(
        [("contract_type", "=", "running_contract"), ("end_date", "<", today)]
    )
    if expired:
        expired.with_context(allow_contract_state_write=True).write({"contract_type": "expire_contract"})
        _logger.info("rental_management: marked %s past contracts as expired", len(expired))

    all_running = Contract.search(
        [("contract_type", "=", "running_contract"), ("property_id", "!=", False)]
    )
    running = all_running.filtered(
        lambda contract: contract.start_date
        and contract.end_date
        and contract.start_date <= today <= contract.end_date
    )
    properties_on_rent = running.mapped("property_id")
    properties_on_rent.filtered(lambda record: record.stage != "on_lease").write(
        {"stage": "on_lease"}
    )
    future = all_running.filtered(
        lambda contract: contract.start_date and contract.start_date > today
    )
    future_properties = future.mapped("property_id") - properties_on_rent
    future_properties.filtered(lambda record: record.stage != "booked").write(
        {"stage": "booked"}
    )

    occupied_ids = (properties_on_rent | future_properties).ids
    stale_rented = Property.search(
        [("stage", "in", ["on_lease", "booked"]), ("id", "not in", occupied_ids)]
    )
    if stale_rented:
        stale_rented.write({"stage": "available"})
        _logger.info(
            "rental_management: released %s properties without a current active contract",
            len(stale_rented),
        )

    for contract in all_running:
        try:
            with cr.savepoint():
                contract._ensure_installment_schedule()
        except Exception:
            _logger.exception(
                "rental_management: could not rebuild installment schedule for %s",
                contract.display_name,
            )

    # Backfill the new accounting-side schedule links used by unique idempotency indexes.
    for schedule in env["rent.invoice"].search([("rent_invoice_id", "!=", False)]):
        move = schedule.rent_invoice_id
        if not move.rental_schedule_id:
            move.rental_schedule_id = schedule
        elif move.rental_schedule_id != schedule:
            _logger.warning(
                "rental_management: account move %s is referenced by multiple rental schedules",
                move.id,
            )

    for schedule in env["sale.invoice"].search([("invoice_id", "!=", False)]):
        move = schedule.invoice_id
        if not move.sale_schedule_id:
            move.sale_schedule_id = schedule
        elif move.sale_schedule_id != schedule:
            _logger.warning(
                "rental_management: account move %s is referenced by multiple sale schedules",
                move.id,
            )

    # Report overlaps in memory after one ordered query; do not close or delete history.
    overlap_ids = set()
    active_by_property = {}
    contracts_to_check = Contract.search(
        [
            ("contract_type", "in", ["running_contract", "expire_contract"]),
            ("property_id", "!=", False),
            ("start_date", "!=", False),
            ("end_date", "!=", False),
        ],
        order="property_id, start_date, end_date, id",
    )
    for contract in contracts_to_check:
        active = active_by_property.setdefault(contract.property_id.id, [])
        active[:] = [item for item in active if item.end_date >= contract.start_date]
        if active:
            overlap_ids.add(contract.id)
            overlap_ids.update(item.id for item in active)
        active.append(contract)
    overlap_count = len(overlap_ids)
    if overlap_count:
        _logger.warning(
            "rental_management: %s contracts participate in overlapping periods and require review",
            overlap_count,
        )

    incomplete = Contract.search_count(
        [
            "|", "|", "|", "|", "|",
            ("property_id", "=", False),
            ("tenancy_id", "=", False),
            ("duration_id", "=", False),
            ("start_date", "=", False),
            ("payment_term", "=", False),
            ("total_rent", "<=", 0),
        ]
    )
    if incomplete:
        _logger.warning(
            "rental_management: %s incomplete legacy draft/history contracts need manual review",
            incomplete,
        )
