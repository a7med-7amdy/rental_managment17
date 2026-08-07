# TEST REPORT — Odoo 19.0.1.0.10

## Last real Odoo.sh runtime result supplied by the user
- Runtime: Odoo 19 Enterprise / Odoo.sh
- Tests reached: 32
- Assertion failures: 0
- Runtime errors: 2
- Both runtime errors: missing `create` access on `maintenance.request`

## Fix in 19.0.1.0.10
Explicit rental ACLs now grant read/write/create and deny unlink for both Rental Officer and Rental Manager on `maintenance.request`.

## Static/package verification performed after the fix
- Python files compiled: 45
- XML files parsed: 57
- Explicit XML IDs checked: 274
- CSV access files parsed and duplicate IDs checked
- Manifest data/assets references checked
- JavaScript syntax checked
- Deprecated `.read_group()` backend calls: 0
- Custom `_check_company` collision: 0
- Shared fixture `maintenance.team.create()`: 0
- Automated test methods included: 37
- New regression: Rental Officer creates maintenance request with default team

## Runtime status for this exact package
Not executed locally because an Odoo 19 Enterprise + PostgreSQL runtime is not available in this workspace. The next Odoo.sh build is the authoritative runtime verification for version 19.0.1.0.10.
