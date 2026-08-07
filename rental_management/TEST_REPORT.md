# rental_management — Test Report 19.0.1.0.8

## 1. Latest Odoo.sh runtime evidence

Environment evidenced by the supplied log:

```text
Platform: Odoo.sh
Odoo: 19 Enterprise
Module: rental_management
Post-install tests: enabled
```

The run reached and completed 30 post-tests and reported:

```text
rental_management: 50 tests
30 post-tests
0 failed
4 errors
```

The four errors were:

- 3 × `RentalCommission._check_company()` signature collision with Odoo 19 core.
- 1 × `maintenance.request.maintenance_team_id` PostgreSQL NOT NULL violation.

The same run produced 3 deprecation warnings from backend `read_group()` calls in the dashboard.

## 2. Corrections in 19.0.1.0.8

- Renamed the custom commission constraint method so it no longer overrides Odoo core `_check_company(fnames=None)`.
- Added deterministic Maintenance Team resolution for rental maintenance requests.
- Added a shared `Rental Maintenance` team as safe clean-install fallback data.
- Migrated every remaining backend `.read_group()` call to `_read_group()` with Odoo 19 tuple result handling.
- Added portal own-request coverage without explicitly supplying a Maintenance Team.
- Hardened the portal route's chatter logging after ownership validation.

## 3. Automated tests included

The module contains **34 Python test methods** across:

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

Coverage includes lifecycle, required fields, contract overlap, monthly/quarterly/yearly/full/manual invoicing, catch-up cron, duplicate prevention, partial periods, renewal, commissions, portal ownership, access rights, and multi-company isolation.

## 4. Static validation executed on 19.0.1.0.8

The following checks were executed on the working tree and are repeated on an independently extracted final ZIP:

- Python AST parse and in-memory compilation.
- XML parse.
- Duplicate explicit XML ID detection.
- CSV structural validation.
- PO parsing through Babel.
- Manifest version/dependency/data/asset path validation.
- JavaScript syntax through Node.js.
- Cron method target validation.
- `type="object"` button method target validation.
- Duplicate class member/method scan.
- Deprecated/invalid pattern scan.
- Package junk scan (`__pycache__`, `.pyc`, `.DS_Store`).

Explicit compatibility guards include:

```text
custom def _check_company(...): 0
.read_group(...):                0
<tree> architecture:             0
view_mode="tree":                0
attrs= modifiers:                0
states= modifiers:               0
```

## 5. Runtime status

The four failures in the supplied 19.0.1.0.7 Odoo.sh run are addressed in 19.0.1.0.8. A new Odoo.sh build is still required before claiming that all 19.0.1.0.8 runtime tests pass, because this workspace does not contain a runnable Odoo 19 Enterprise/PostgreSQL environment.
