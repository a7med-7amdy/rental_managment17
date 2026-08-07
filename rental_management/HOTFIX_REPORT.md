# HOTFIX REPORT — rental_management 19.0.1.0.11

## Runtime issue addressed

The Odoo.sh run on 2026-08-07 reached the post-install test suite with 0 failed assertions and 3 runtime errors. All three errors had the same root cause: `maintenance.request` create access was not effective for the users used by the rental tests, including Rental Officer and Rental Manager.

## Root-cause correction

1. Removed `maintenance.request` ACL rows from the generic CSV security file to avoid relying on an inherited-core-model ACL definition that was demonstrably ineffective on the target database.
2. Added `security/maintenance_access.xml` with fresh, updateable XML IDs:
   - Internal users: read/write/create, no unlink granted by this module.
   - Portal users: read/create, no write/unlink granted by this module.
3. Added `migrations/19.0.1.0.11/post-migration.py` to verify/repair these ACL records on upgraded databases.
4. Added server-side rental authorization in `models/maintenance.py`:
   - Portal may create only against its own active rental contract.
   - Internal users may link a maintenance request to a rental contract only when they are Rental Officer or Rental Manager.
   - Company and property must match the selected rental contract.
   - Missing property/company/landlord values are safely derived from the contract.
5. Kept Maintenance Team administration separate; Rental Manager does not receive Equipment Manager rights.
6. Portal ownership fixture creation now uses sudo only for fixture preparation; actual portal create behavior remains tested without sudo.

## Odoo upstream warning

The recurring docutils messages around `res.partner.email_normalized` (`Unexpected indentation` / `Block quote ends without a blank line`) match a known Odoo 19 `mail` manifest RST formatting issue. They are not raised by `rental_management` and do not stop registry loading or the test suite. The module does not patch Odoo Core.

## Version

- Previous: 19.0.1.0.10
- Current: 19.0.1.0.11
