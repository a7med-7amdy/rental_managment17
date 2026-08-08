# -*- coding: utf-8 -*-
"""Post-upgrade consistency logging for rental schedules."""

import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    if not version:
        return
    env = api.Environment(cr, SUPERUSER_ID, {})
    duplicates = env["rent.invoice"].sudo().search_count([("legacy_duplicate", "=", True)])
    if duplicates:
        _logger.warning(
            "%s legacy duplicate rental schedule(s) remain preserved after upgrade.",
            duplicates,
        )
