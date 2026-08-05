# rental_management — Test Report 19.0.1.0.7

## 1. Runtime evidence supplied

Environment evidenced by the uploaded log:

```text
Platform: Odoo.sh
Odoo: 19 Enterprise
Module: rental_management
Post-install tests: enabled
```

The run completed registry/module loading and CSS asset generation, then started rental module tests. Six tests were reached before the runner stopped at its five-error threshold.

Reported result:

```text
0 failed, 5 errors
remaining tests skipped after max failed tests
```

The five errors represented two root causes:

- Four activations failed in `_sync_property_stage()` because a Date field was passed to `_read_group()` without granularity.
- One multi-company test failed before executing its assertion because Odoo's `assertRaises()` override does not accept a tuple.

## 2. Corrections in 19.0.1.0.7

- Removed `start_date` from `_read_group()` group-by specifications.
- Split current and future contract detection into two property-grouped batch queries.
- Replaced tuple-based `assertRaises()` with explicit multi-exception handling and a failure assertion.
- Added current/future property-stage precedence tests.
- Added a future-reservation stage test.
- Added narrow manager-only activity completion elevation.

## 3. Automated tests included

The module now contains **33 test methods** across:

```text
tests/test_property_lifecycle.py
tests/test_rental_contract.py
tests/test_rent_invoicing.py
tests/test_contract_renewal.py
tests/test_broker_commission.py
tests/test_security.py
tests/test_multi_company.py
tests/test_portal.py
tests/test_upgrade_data.py
```

Coverage includes:

- Property lifecycle and future reservations.
- Current-contract precedence over a future renewal.
- Required activation data and overlap rejection.
- Monthly, quarterly, yearly, full-payment and manual schedules.
- Catch-up cron and invoice idempotency.
- Month-end period anchors and partial final periods.
- Extra services, deposits and maintenance.
- Renewal dates and old/new links.
- Tenant, landlord and dual-source broker commissions.
- Officer/Manager/Internal/Public permissions.
- Portal ownership isolation.
- Multi-company record rules, consistency and dashboard scope.
- Preservation of historical invoice schedules and accounting moves.

## 4. Static validation executed

The workspace source was checked for:

- Python AST parsing and in-memory compilation.
- Duplicate class methods/field assignments and duplicate dictionary keys.
- Every `_read_group()` group-by list, specifically bare Date/Datetime fields.
- Every `assertRaises()` call, specifically tuple exceptions.
- Manifest syntax, version, dependencies and referenced files.
- XML parsing and duplicate explicit XML IDs.
- CSV row structure.
- PO translation parsing.
- JavaScript syntax using `node --check`.
- Cron method targets.
- Object-button method targets.
- Package-relative import targets.
- Deprecated Odoo patterns and obsolete product references.
- Cache, compiled and temporary files.

Workspace result:

```text
Python files: 45 passed
XML files: 56 passed
Explicit XML IDs: 273, no duplicates
CSV files: 1 passed
PO files: 6 passed
JavaScript files: 1 passed
Cron targets: 8 passed
Object buttons: 71 passed
Automated test methods: 33
Bare Date/Datetime _read_group group-bys: 0
Tuple assertRaises patterns: 0
Static errors: 0
```

## 5. Runtime qualification

Version 19.0.1.0.7 was not executed locally because the workspace does not contain Odoo 19, PostgreSQL, or `odoo-bin`. Static success is not presented as runtime success.

Required acceptance commands on Odoo.sh/staging:

```bash
odoo-bin \
  -d rental_test_clean \
  -i rental_management \
  --stop-after-init \
  --test-enable \
  --test-tags /rental_management \
  --log-level=test
```

```bash
odoo-bin \
  -d rental_test_upgrade \
  -u rental_management \
  --stop-after-init \
  --test-enable \
  --test-tags /rental_management \
  --log-level=test
```

The next run must be reviewed because the previous test process skipped the suite remainder after reaching five errors.
