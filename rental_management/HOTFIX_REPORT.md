# Hotfix Report — rental_management 19.0.1.0.7

## Trigger

The supplied Odoo.sh Odoo 19 Enterprise run completed module loading, generated the CSS asset bundles, and entered the `rental_management` post-install suite. The runner stopped after five errors with two underlying causes:

1. `tenancy.details._sync_property_stage()` grouped by the Date field `start_date` without a date granularity:

   ```text
   ValueError: Granularity not set on a date(time) field: 'start_date'
   ```

2. `test_cross_company_contract_is_rejected` passed a tuple to Odoo's overridden `assertRaises()`:

   ```text
   TypeError: issubclass() arg 1 must be a class
   ```

The first root cause affected broker commission and renewal tests because every activation synchronizes the property stage. The second root cause was isolated to the multi-company test implementation.

## Production fix

### Property-stage synchronization

`models/rent_contract.py::_sync_property_stage()` no longer groups by `start_date`.

The method now performs two batched `_read_group()` queries, both grouped only by the Many2one field `property_id`:

- Current contracts: `start_date <= today` and `end_date >= today`.
- Future reservations: `start_date > today` and `end_date >= today`.

Stage precedence is deterministic:

```text
Current running contract exists  -> on_lease
No current contract, future exists -> booked
No current or future contract      -> available
```

This retains batched performance and avoids one search per property.

### Manager activity completion

Closing or cancelling a contract is already restricted server-side to Rental Managers. Activity completion now uses narrowly scoped elevated access only for the related `mail.activity` records, allowing a manager to complete an activity assigned to another responsible user without granting broad Accounting permissions.

## Test-suite fix

Odoo 19's test case override calls `issubclass(exception, AccessError)`, so a tuple cannot be supplied to `assertRaises()`.

The multi-company test now executes the create operation directly, accepts the two legitimate rejection classes (`UserError` or `ValidationError`), and explicitly fails if the cross-company contract is created.

## Regression coverage added

Two lifecycle tests were added:

1. A future running contract marks its property as `booked`.
2. When a current contract and a future renewal coexist, `on_lease` takes precedence; closing the current contract changes the property to `booked` while preserving the future contract.

The suite now contains 33 test methods.

## Other cleanup

- Removed a duplicate `target` key from the Register Payment action dictionary.
- Audited every `_read_group()` call for Date/Datetime group-by fields.
- Audited every test for tuple-based `assertRaises()` usage.
- No schema, field, XML ID, or business-data migration is required for this hotfix.

## Runtime status

The supplied 19.0.1.0.6 Odoo.sh run is the runtime evidence for this report. Version 19.0.1.0.7 has not been executed in this workspace because Odoo 19, PostgreSQL, and `odoo-bin` are not installed here. A new Odoo.sh build is required to execute the remaining tests that were skipped after the five-error threshold.
