# rental_management — Upgrade Report 19.0.1.0.8

## Version

```text
Previous delivered version: 19.0.1.0.7
Current version: 19.0.1.0.8
Technical module name: rental_management
License: OPL-1
Author retained: TechKhedut Inc.
```

## Runtime defects corrected in this revision

### 1. Rental commission / ORM multi-company collision

`RentalCommission` had a business constraint named `_check_company`. In Odoo 19, `_check_company(fnames=None)` is an ORM method invoked automatically during create/write for company-consistent relational fields.

The business constraint has been renamed to `_check_commission_company` while preserving its validation. Core multi-company validation now executes normally when commission accounting documents are linked.

### 2. Required Maintenance Team

Odoo 19 requires a Maintenance Team on every `maintenance.request`. The rental extension now selects an active company team or a shared fallback before calling the core create method. A shared `Rental Maintenance` team is installed for clean databases.

This fixes both backend/test creation and the portal maintenance flow without making the Maintenance Team field optional or changing Odoo core.

### 3. Deprecated Dashboard aggregation

All legacy backend `read_group()` calls in the rental dashboard were replaced with `_read_group()` and adapted to its tuple-based return values.

The three deprecation warnings seen in the supplied Odoo.sh run are therefore removed from the module source.

### 4. Portal maintenance chatter

Portal rental contract ownership is checked first. After a valid maintenance request is created, the audit/chatter message is posted with narrowly scoped elevated access because portal users intentionally do not have contract write access.

## Security and multi-company behavior

- Core `_check_company()` is restored and no longer shadowed.
- Commission-to-contract company validation remains active.
- Maintenance Team selection prefers the request company and only falls back to a shared team.
- Portal maintenance record creation still runs using the portal user's ACLs and record rules.
- No portal write access was added to rental contracts.
- No cross-company dashboard scope was widened.

## Files changed

```text
__manifest__.py
models/rent_contract.py
models/maintenance.py
models/property_details.py
controllers/main.py
tests/common.py
tests/test_portal.py
data/maintenance_data.xml
HOTFIX_REPORT.md
TEST_REPORT.md
UPGRADE_REPORT.md
MIGRATION_NOTES.md
```

## Data preservation

No existing database column, model technical name, selection key, invoice, property, tenancy, sequence, or existing XML ID is removed or renamed by this revision.

## Validation status

Static package validation is recorded in `TEST_REPORT.md` and `VERIFICATION_v19.0.1.0.8.txt`. Runtime acceptance still requires the next Odoo.sh build.
