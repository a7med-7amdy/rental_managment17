# Test Report — rental_management 19.0.1.0.13

## Last real Odoo.sh runtime result
Version `19.0.1.0.12`:
- Tests executed: 45
- Failed assertions: 0
- Runtime errors: 2

Both runtime errors are addressed in 19.0.1.0.13.

## Regression suite in 19.0.1.0.13
- Test methods: 46
- Added/strengthened coverage:
  - renewal wizard does not mutate active source contract
  - renewed draft receives its own changed payment/invoice mode
  - running-contract financial fields remain locked
  - missed cron starts with automatic mode before activation

## Static/package verification executed for 19.0.1.0.13
- Python parse/compile: PASS
- XML parse: PASS
- Manifest file references: PASS
- CSV parse: PASS
- JavaScript syntax: PASS
- PO parsing: PASS
- Duplicate XML IDs: 0
- Stored translated related-field warning patterns: 0
- Duplicate explicit field-label warning patterns: 0
- Legacy `<tree>`: 0
- Legacy `attrs=`: 0
- Legacy `states=`: 0
- Deprecated `.read_group()`: 0
- Eager Date/Datetime defaults: 0
- Migration signatures: PASS
- Custom models with ACL coverage: 52 / 52

## Runtime status
The 19.0.1.0.13 package itself could not be executed with `odoo-bin` in this workspace because an Odoo 19 Enterprise + PostgreSQL runtime is not installed here. Therefore this report does not claim 46/46 runtime success before the package is run on Odoo.sh.
