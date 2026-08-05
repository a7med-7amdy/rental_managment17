# rental_management — Upgrade Report 19.0.1.0.7

## Version

```text
Previous delivered version: 19.0.1.0.6
Current version: 19.0.1.0.7
Technical module name: rental_management
License: OPL-1
Author retained: TechKhedut Inc.
```

## Files modified in this revision

```text
__manifest__.py
models/rent_contract.py
tests/test_multi_company.py
tests/test_property_lifecycle.py
HOTFIX_REPORT.md
TEST_REPORT.md
UPGRADE_REPORT.md
MIGRATION_NOTES.md
```

## Runtime defects corrected

### Odoo 19 `_read_group()` date granularity

The previous property-stage query grouped by `start_date` to distinguish current and future contracts. Odoo 19 requires an explicit granularity for Date/Datetime group-by fields and raised:

```text
ValueError: Granularity not set on a date(time) field: 'start_date'
```

The new implementation does not group by the date. Dates are used only in Domains, while results are grouped by `property_id`.

### Odoo test `assertRaises()` tuple incompatibility

Odoo 19 overrides the standard context manager and invokes `issubclass()` on the supplied exception argument. A tuple therefore raised a `TypeError` before the multi-company operation was tested.

The test now explicitly accepts either legitimate business rejection exception and fails if no rejection occurs.

## Rental workflow behavior

- A property with a currently effective running contract is `on_lease`.
- A property with no current contract but at least one future running contract is `booked`.
- Current occupancy takes precedence over a future reservation.
- After closing the current contract, a future contract keeps the property reserved instead of releasing it to `available`.
- A property becomes `available` only when no current or future running contract remains.

## Security behavior

- Close/cancel remains restricted to Rental Manager at the server method level.
- Only related activity completion uses narrow elevated access after that authorization check.
- Accounting permissions are not implied or broadened.
- Multi-company record rules and company consistency checks remain unchanged.

## Test changes

- Added future reservation lifecycle coverage.
- Added current-plus-future precedence coverage.
- Hardened the cross-company rejection test against Odoo's single-exception `assertRaises()` implementation.
- Total included test methods: 33.

## Validation status

Static verification of the source and the independently extracted ZIP is recorded in `TEST_REPORT.md` and the external `VERIFICATION_v19.0.1.0.7.txt`.

The Odoo.sh runtime suite must be rerun. The previous run stopped after five errors and did not execute the remaining tests.
