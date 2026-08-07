# MIGRATION NOTES — 19.0.1.0.11

## Backup

Take a full database and filestore backup before upgrading a production database.

## New migration

`migrations/19.0.1.0.11/post-migration.py` verifies that `maintenance.request` has effective ACL records for:

- `base.group_user`: read/write/create
- `base.group_portal`: read/create

The migration does not delete contracts, properties, invoices, maintenance requests, or accounting entries.

## Security behavior

A base internal user can retain standard non-rental Maintenance behavior. A request linked to `tenancy_id` is additionally protected by Python authorization: only Rental Officer/Manager may link internal requests, and Portal users may link only their own active contract.

## No core modification

The Odoo `mail` manifest RST warning is intentionally not patched because modifying Odoo Core is outside this module's upgrade policy.
