# HOTFIX REPORT — Odoo 19.0.1.0.10

## Runtime issue addressed
Odoo.sh completed 32 rental_management tests with 0 assertion failures and 2 runtime errors. Both errors were AccessError exceptions while creating `maintenance.request` records.

## Root cause
The rental lifecycle intentionally allows Rental Officer and Rental Manager users to create maintenance requests, but the module relied on access rights inherited from Odoo Maintenance instead of declaring that capability explicitly. The target Odoo.sh database did not grant create access to those rental users, so both the portal ownership fixture (whose shared test user is elevated to Rental Manager) and the explicit manager security test failed.

## Permanent fix
- Added explicit ACL for `rental_management.property_rental_officer` on `maintenance.request`: read/write/create, no unlink.
- Added explicit ACL for `rental_management.property_rental_manager` on `maintenance.request`: read/write/create, no unlink.
- Kept the existing Portal ACL limited to read/create and protected by the portal ownership record rule.
- Kept the global allowed-company record rule for `maintenance.request`.
- Did not grant Maintenance Team administration to rental users.
- Did not use `sudo()` to create maintenance requests.
- Added regression coverage proving a Rental Officer can create a rental maintenance request with the default team.

## Why this is safer
ACLs are now owned by the rental module instead of depending on implementation details of another module. The user can create/update operational maintenance requests but cannot delete them, preserving history. Team configuration remains restricted to Maintenance administrators.

## Unrelated log warning
The repeated docutils warning around `res.partner.email_normalized` is not sourced by this module: its manifest description is a single plain string and there are no multiline RST/help strings in `res_partner.py`. It is non-fatal and Odoo continues through module loading and tests after it.
