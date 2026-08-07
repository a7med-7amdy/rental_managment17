# TEST REPORT — rental_management 19.0.1.0.11

## Latest target-runtime evidence

The latest Odoo.sh run supplied for version 19.0.1.0.10 reached 33 post-install tests with:

- Failed assertions: 0
- Runtime errors: 3
- Root cause of all 3 errors: missing effective `create` access on `maintenance.request`.

Those three runtime errors are addressed in 19.0.1.0.11 through explicit XML ACL records plus an upgrade migration and rental-specific server-side authorization.

## Static/package validation executed for 19.0.1.0.11

- Python AST/compile: passed
- XML parsing: passed
- Manifest file references: passed
- Asset references: passed
- ACL CSV parsing: passed
- Dedicated maintenance ACL XML validation: passed
- JavaScript syntax check: passed when Node is available
- Translation PO validation: passed when msgfmt is available
- Duplicate explicit XML ID scan: passed
- Legacy `tree`, `attrs`, `states` pattern scan: passed
- Deprecated backend `.read_group()` scan: passed
- Custom `_check_company` collision scan: passed
- Automated test methods included: 39

## Runtime status

This environment does not contain a complete Odoo 19 Enterprise + PostgreSQL runtime, so 19.0.1.0.11 has not been executed here with `odoo-bin`. The next Odoo.sh build remains the authoritative runtime verification.
