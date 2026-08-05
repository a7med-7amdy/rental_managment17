# -*- coding: utf-8 -*-
"""Pre-upgrade data preparation for rental_management 19.0.1.0.0.

The script fills only values that can be derived safely from an existing relation.
It never removes contracts, invoices, properties, or accounting entries.
"""

import logging

_logger = logging.getLogger(__name__)


def _table_exists(cr, table):
    cr.execute("SELECT to_regclass(%s)", (table,))
    return bool(cr.fetchone()[0])


def _column_exists(cr, table, column):
    cr.execute(
        """
        SELECT 1
          FROM information_schema.columns
         WHERE table_name = %s AND column_name = %s
        """,
        (table, column),
    )
    return bool(cr.fetchone())


def _count(cr, table, where="TRUE"):
    cr.execute(f'SELECT COUNT(*) FROM "{table}" WHERE {where}')
    return cr.fetchone()[0]


def migrate(cr, version):
    if not version:
        return

    cr.execute("SELECT id FROM res_company ORDER BY id LIMIT 1")
    row = cr.fetchone()
    fallback_company_id = row[0] if row else None
    _logger.info("rental_management: starting pre-migration from %s", version)

    if _table_exists(cr, "property_details"):
        if _column_exists(cr, "property_details", "stage"):
            cr.execute("UPDATE property_details SET stage = 'draft' WHERE stage IS NULL")
        if fallback_company_id and _column_exists(cr, "property_details", "company_id"):
            # Prefer the project company, then landlord company, then the oldest company.
            cr.execute(
                """
                UPDATE property_details p
                   SET company_id = COALESCE(
                       (SELECT pp.company_id
                          FROM property_project pp
                         WHERE pp.id = p.property_project_id),
                       (SELECT rp.company_id
                          FROM res_partner rp
                         WHERE rp.id = p.landlord_id),
                       %s
                   )
                 WHERE p.company_id IS NULL
                """,
                (fallback_company_id,),
            )
            cr.execute(
                "UPDATE property_details SET company_id = %s WHERE company_id IS NULL",
                (fallback_company_id,),
            )

    if _table_exists(cr, "tenancy_details"):
        if _column_exists(cr, "tenancy_details", "contract_type"):
            cr.execute(
                "UPDATE tenancy_details SET contract_type = 'new_contract' WHERE contract_type IS NULL"
            )
        if fallback_company_id and _column_exists(cr, "tenancy_details", "company_id"):
            cr.execute(
                """
                UPDATE tenancy_details t
                   SET company_id = COALESCE(
                       (SELECT p.company_id
                          FROM property_details p
                         WHERE p.id = t.property_id),
                       (SELECT rp.company_id
                          FROM res_partner rp
                         WHERE rp.id = t.tenancy_id),
                       %s
                   )
                 WHERE t.company_id IS NULL
                """,
                (fallback_company_id,),
            )
            cr.execute(
                "UPDATE tenancy_details SET company_id = %s WHERE company_id IS NULL",
                (fallback_company_id,),
            )

    if _table_exists(cr, "rent_invoice") and _column_exists(cr, "rent_invoice", "company_id"):
        cr.execute(
            """
            UPDATE rent_invoice ri
               SET company_id = t.company_id
              FROM tenancy_details t
             WHERE ri.company_id IS NULL AND t.id = ri.tenancy_id
            """
        )
        if fallback_company_id:
            cr.execute(
                "UPDATE rent_invoice SET company_id = %s WHERE company_id IS NULL",
                (fallback_company_id,),
            )

    if _table_exists(cr, "property_vendor"):
        if _column_exists(cr, "property_vendor", "stage"):
            cr.execute("UPDATE property_vendor SET stage = 'booked' WHERE stage IS NULL")
        if _column_exists(cr, "property_vendor", "company_id"):
            if _table_exists(cr, "property_details"):
                cr.execute(
                    """
                    UPDATE property_vendor pv
                       SET company_id = p.company_id
                      FROM property_details p
                     WHERE pv.company_id IS NULL AND p.id = pv.property_id
                    """
                )
            if fallback_company_id:
                cr.execute(
                    "UPDATE property_vendor SET company_id = %s WHERE company_id IS NULL",
                    (fallback_company_id,),
                )

    if _table_exists(cr, "sale_invoice") and _column_exists(cr, "sale_invoice", "company_id"):
        if _table_exists(cr, "property_vendor"):
            cr.execute(
                """
                UPDATE sale_invoice si
                   SET company_id = pv.company_id
                  FROM property_vendor pv
                 WHERE si.company_id IS NULL AND pv.id = si.property_sold_id
                """
            )
        if fallback_company_id:
            cr.execute(
                "UPDATE sale_invoice SET company_id = %s WHERE company_id IS NULL",
                (fallback_company_id,),
            )

    if _table_exists(cr, "maintenance_request") and _column_exists(cr, "maintenance_request", "company_id"):
        if _column_exists(cr, "maintenance_request", "tenancy_id"):
            cr.execute(
                """
                UPDATE maintenance_request mr
                   SET company_id = t.company_id
                  FROM tenancy_details t
                 WHERE mr.company_id IS NULL AND t.id = mr.tenancy_id
                """
            )
        if fallback_company_id:
            cr.execute(
                "UPDATE maintenance_request SET company_id = %s WHERE company_id IS NULL",
                (fallback_company_id,),
            )

    for table in ("property_details", "tenancy_details", "rent_invoice", "property_vendor", "sale_invoice"):
        if _table_exists(cr, table):
            _logger.info("rental_management: %s rows before upgrade: %s", table, _count(cr, table))

    if _table_exists(cr, "tenancy_details"):
        cr.execute(
            """
            SELECT COUNT(*)
              FROM tenancy_details
             WHERE property_id IS NULL OR tenancy_id IS NULL OR start_date IS NULL
                OR duration_id IS NULL OR total_rent IS NULL OR total_rent <= 0
            """
        )
        _logger.warning(
            "rental_management: legacy contracts requiring manual review: %s",
            cr.fetchone()[0],
        )
