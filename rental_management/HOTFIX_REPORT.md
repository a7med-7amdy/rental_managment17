# Hotfix Report — rental_management 19.0.1.0.8

## Runtime trigger

The supplied Odoo.sh Odoo 19 Enterprise run completed module loading, asset generation, and the post-install suite. It executed 30 post-tests before shutdown and reported:

```text
0 failed, 4 errors
```

Those four runtime errors had two root causes:

1. Three broker commission tests failed because `RentalCommission` defined a custom method named `_check_company(self)`. Odoo 19 core calls `self._check_company(list(vals))` during `write()`, so the custom method unintentionally overrode the ORM API and raised:

   ```text
   TypeError: RentalCommission._check_company() takes 1 positional argument but 2 were given
   ```

2. Portal ownership setup failed while creating `maintenance.request` because Odoo 19 requires `maintenance_team_id`, but no readable/default Maintenance Team was available in the test/database context:

   ```text
   psycopg2.errors.NotNullViolation: null value in column "maintenance_team_id"
   ```

The same run also emitted three Odoo 19 deprecation warnings for backend calls to `read_group()` in the rental dashboard.

## Fix 1 — restore Odoo 19 core `_check_company()` behavior

The rental commission constraint method was renamed from the reserved/core name:

```text
_check_company
```

to:

```text
_check_commission_company
```

The `@api.constrains("contract_id", "company_id")` behavior is preserved, but Odoo's native `_check_company(fnames=None)` method is no longer shadowed. This allows writes to `broker_bill_id`, `charge_invoice_id`, and any other `check_company=True` relational field to use the standard ORM consistency check.

A full source scan confirms that the module contains no custom `def _check_company(...)` override.

## Fix 2 — Maintenance Team fallback for rental/portal requests

Odoo 19 defines `maintenance.request.maintenance_team_id` as required. The rental extension now guarantees a company-compatible team before delegating to core `create()`:

- Prefer an active team belonging to the request company.
- Otherwise use an active shared team (`company_id = False`).
- If neither exists, raise a clear `UserError` instead of reaching a PostgreSQL NOT NULL error.

A shared `Rental Maintenance` team is installed as module data with `noupdate="1"` so clean databases have a safe fallback without forcing a company-specific configuration.

The lookup uses narrowly scoped `sudo()` only to resolve the internal Maintenance Team configuration. Creation of the maintenance request itself remains under the caller's ACLs and record rules.

The portal test fixture also creates a normal company Maintenance Team, and a positive regression test verifies that an owning portal tenant can create a request without manually passing `maintenance_team_id`.

## Fix 3 — Odoo 19 backend aggregation API

All remaining backend `read_group()` calls in `models/property_details.py` were migrated to `_read_group()` and their tuple result handling was updated for Odoo 19.

Updated areas include:

- Property stage/type counters.
- Contract and sale status counters.
- Rent invoice totals and residual balances.
- Sold property totals.
- Top broker statistics.
- Due/Paid dashboard series.

A full module scan now reports zero `.read_group(` calls.

## Fix 4 — Portal chatter access

The maintenance POST route already verifies contract ownership before creation. Portal users intentionally have read-only access to rental contracts, while `mail.thread.message_post()` requires write access by default.

After successful ownership validation and request creation, only the chatter log operation is elevated with `contract.sudo().message_post(...)`. This prevents a legitimate portal maintenance request from failing after the maintenance record has already been created, without widening portal write rights on the contract.

## Files modified in this revision

```text
__manifest__.py
models/rent_contract.py
models/maintenance.py
models/property_details.py
controllers/main.py
tests/common.py
tests/test_portal.py
data/maintenance_data.xml   (new)
HOTFIX_REPORT.md
TEST_REPORT.md
UPGRADE_REPORT.md
MIGRATION_NOTES.md
```

## Migration impact

No model, field, selection key, or existing XML ID was renamed. No destructive migration is required for 19.0.1.0.8.

The new Maintenance Team data record is additive and `noupdate="1"`.

## Runtime qualification

The Odoo.sh run supplied for 19.0.1.0.7 is the runtime evidence for the four defects above. Version 19.0.1.0.8 cannot be executed against Odoo 19/PostgreSQL in this workspace, so a new Odoo.sh build remains required to confirm the complete runtime suite after these fixes.
