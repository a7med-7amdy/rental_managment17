# -*- coding: utf-8 -*-
"""Prepare Odoo 19.0.1.0.12 schema changes without deleting historical data."""

import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    cr.execute("SELECT to_regclass('property_details')")
    if cr.fetchone()[0]:
        cr.execute(
            "UPDATE property_details SET used_for = 'retail_stores' "
            "WHERE used_for = ' retail_stores'"
        )

    cr.execute("SELECT to_regclass('rent_invoice')")
    if cr.fetchone()[0]:
        cr.execute("ALTER TABLE rent_invoice DROP CONSTRAINT IF EXISTS rent_invoice_rental_period_unique")
        cr.execute("ALTER TABLE rent_invoice DROP CONSTRAINT IF EXISTS rent_invoice_rental_period_dates_valid")
        cr.execute(
            "ALTER TABLE rent_invoice "
            "ADD COLUMN IF NOT EXISTS legacy_duplicate boolean DEFAULT false"
        )
        cr.execute(
            """
            WITH ranked AS (
                SELECT id,
                       row_number() OVER (
                           PARTITION BY tenancy_id, period_start, period_end, invoice_type
                           ORDER BY id
                       ) AS rn
                  FROM rent_invoice
                 WHERE invoice_type IN ('rent', 'full_rent')
                   AND period_start IS NOT NULL
                   AND period_end IS NOT NULL
            )
            UPDATE rent_invoice AS ri
               SET legacy_duplicate = true
              FROM ranked
             WHERE ri.id = ranked.id
               AND ranked.rn > 1
            """
        )
        cr.execute("SELECT count(*) FROM rent_invoice WHERE legacy_duplicate = true")
        duplicate_count = cr.fetchone()[0]
        if duplicate_count:
            _logger.warning(
                "Preserved %s historical duplicate rental schedule(s) and marked "
                "them for manual review; no rows were deleted.", duplicate_count,
            )

    cr.execute("SELECT to_regclass('rental_commission')")
    if cr.fetchone()[0]:
        cr.execute("ALTER TABLE rental_commission DROP CONSTRAINT IF EXISTS rental_commission_commission_source_unique")
        cr.execute("ALTER TABLE rental_commission DROP CONSTRAINT IF EXISTS rental_commission_commission_amount_positive")
        cr.execute(
            "ALTER TABLE rental_commission "
            "ADD COLUMN IF NOT EXISTS legacy_duplicate boolean DEFAULT false"
        )
        cr.execute(
            """
            WITH ranked AS (
                SELECT id,
                       row_number() OVER (
                           PARTITION BY contract_id, source
                           ORDER BY id
                       ) AS rn
                  FROM rental_commission
                 WHERE contract_id IS NOT NULL AND source IS NOT NULL
            )
            UPDATE rental_commission AS rc
               SET legacy_duplicate = true
              FROM ranked
             WHERE rc.id = ranked.id
               AND ranked.rn > 1
            """
        )
        cr.execute("SELECT count(*) FROM rental_commission WHERE legacy_duplicate = true")
        duplicate_count = cr.fetchone()[0]
        if duplicate_count:
            _logger.warning(
                "Preserved %s historical duplicate broker commission record(s); "
                "new duplicates remain blocked.", duplicate_count,
            )
