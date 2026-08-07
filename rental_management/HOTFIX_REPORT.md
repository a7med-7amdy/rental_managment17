# Hotfix Report — rental_management 19.0.1.0.9

## Runtime evidence reviewed
The Odoo.sh run dated 2026-08-07 reached post-install test setup after the module, views, security, data and assets loaded successfully. Five test classes stopped in the same shared fixture because `tests/common.py` attempted to create `maintenance.team` with a Rental Manager test user. In Odoo 19, normal internal users have read-only access to maintenance teams; creation is restricted to Maintenance / Equipment Manager.

## Root fix
- Removed per-test-class creation of `maintenance.team`.
- Reused the stable module-owned XML record `rental_management.maintenance_team_rental`.
- Did **not** grant Rental Manager the Maintenance/Equipment Manager group.
- Kept rental maintenance requests creatable by ordinary internal rental users through Odoo's normal `maintenance.request` ACL.
- Hardened `_get_rental_maintenance_team()` to prefer a company-specific active team, then the stable shared rental team, then any legacy shared team.
- The team lookup uses `sudo()` only to resolve configuration; the request itself continues through the caller's normal ACLs and record rules.

## Regression coverage added
- Rental Manager cannot create Maintenance Team configuration.
- Rental Manager can create a rental Maintenance Request without passing a team explicitly.
- Existing portal regression continues to verify a portal tenant can create a request only for their own running rental contract and receives a default team.

## Why this is safer
The test suite now matches production security instead of making production security weaker merely to satisfy test setup.
