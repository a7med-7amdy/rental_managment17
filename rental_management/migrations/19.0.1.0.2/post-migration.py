# -*- coding: utf-8 -*-
"""Log legacy rows that remain intentionally reviewable after upgrade."""

import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    cr.execute("SELECT to_regclass('tenancy_details')")
    if not cr.fetchone()[0]:
        return
    cr.execute(
        """
        SELECT COUNT(*)
          FROM tenancy_details
         WHERE total_rent IS NULL OR total_rent <= 0
            OR start_date IS NULL OR property_id IS NULL OR tenancy_id IS NULL
        """
    )
    count = cr.fetchone()[0]
    if count:
        _logger.warning(
            "rental_management: %s legacy contracts remain available for manual review",
            count,
        )
