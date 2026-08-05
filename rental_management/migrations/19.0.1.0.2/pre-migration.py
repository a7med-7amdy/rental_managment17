# -*- coding: utf-8 -*-
"""Remove strict SQL checks that can reject valid legacy draft/history rows.

Business validation remains enforced in Python when records are edited or contracts
are activated. No business record is deleted or rewritten by this migration.
"""

import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    constraints = (
        ("tenancy_details", "tenancy_details_rent_positive"),
        ("tenancy_details", "tenancy_details_deposit_non_negative"),
        ("tenancy_details", "tenancy_details_broker_values_non_negative"),
        ("contract_duration", "contract_duration_duration_positive"),
        ("tenancy_service_line", "tenancy_service_line_service_price_non_negative"),
    )
    for table, constraint in constraints:
        cr.execute("SELECT to_regclass(%s)", (table,))
        if not cr.fetchone()[0]:
            continue
        cr.execute(
            "SELECT 1 FROM pg_constraint WHERE conname = %s",
            (constraint,),
        )
        if cr.fetchone():
            cr.execute(f'ALTER TABLE "{table}" DROP CONSTRAINT "{constraint}"')
            _logger.info("rental_management: dropped legacy-hostile constraint %s", constraint)
