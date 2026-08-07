# -*- coding: utf-8 -*-
"""Guarantee maintenance ACL compatibility on upgraded Odoo 19 databases."""

import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def _ensure_access(env, name, group, *, read=True, write=False, create=False, unlink=False):
    model = env["ir.model"]._get("maintenance.request")
    Access = env["ir.model.access"].sudo()
    access = Access.search(
        [("model_id", "=", model.id), ("group_id", "=", group.id), ("name", "=", name)],
        limit=1,
    )
    vals = {
        "name": name,
        "model_id": model.id,
        "group_id": group.id,
        "perm_read": read,
        "perm_write": write,
        "perm_create": create,
        "perm_unlink": unlink,
    }
    if access:
        access.write(vals)
    else:
        access = Access.create(vals)
    return access


def migrate(cr, version):
    if not version:
        return
    env = api.Environment(cr, SUPERUSER_ID, {})
    internal = _ensure_access(
        env,
        "maintenance.request internal rental compatibility",
        env.ref("base.group_user"),
        read=True,
        write=True,
        create=True,
        unlink=False,
    )
    portal = _ensure_access(
        env,
        "maintenance.request portal rental",
        env.ref("base.group_portal"),
        read=True,
        write=False,
        create=True,
        unlink=False,
    )
    _logger.info(
        "rental_management: verified maintenance.request ACLs (internal=%s, portal=%s)",
        internal.id,
        portal.id,
    )
