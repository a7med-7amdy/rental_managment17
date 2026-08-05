# rental_management — Test Report

## 1. Scope and honesty statement

This report separates:

1. Odoo.sh runtime results actually supplied from Odoo 19 Enterprise.
2. Static checks executed in the workspace.
3. Automated Odoo tests included in the module but not yet rerun for version `19.0.1.0.6`.

No runtime success is claimed for `19.0.1.0.6` until the next Odoo.sh build completes.

## 2. Runtime environment evidenced by supplied logs

```text
Platform: Odoo.sh
Odoo major version: 19 Enterprise
Module: rental_management
Test mode: enabled by Odoo.sh module build/force-demo process
```

The supplied Odoo.sh runs demonstrated progressive runtime coverage:

- Python package import reached and exposed the removed `web_editor` import.
- XML data loading reached and exposed the removed product category XML ID and product field.
- View validation reached and exposed invalid Search View `group expand` architecture.
- Asset bundles were generated successfully.
- The post-install test suite started.

Therefore, the current module has passed the runtime stages before post-install tests in the latest supplied run.

## 3. Latest Odoo.sh runtime result — version 19.0.1.0.5

Odoo.sh completed registry/module loading and asset generation, then entered module tests. Five test classes stopped in `RentalCommon.setUpClass()` while creating `contract.duration`:

```text
odoo.exceptions.AccessError:
You are not allowed to create 'Contract Duration' records.
Allowed group: Rental Management / Rental Manager
```

Reported result:

```text
0 failed, 5 errors
Test suite halted after reaching max failed tests
```

This is a test-fixture authorization error, not an XML/view/import failure and not evidence of five different production defects.

## 4. Corrections prepared in version 19.0.1.0.6

### 4.1 Shared fixture authorization

The shared accounting-ready test user receives the Rental Manager group before creating rental configuration records. Production ACLs are not weakened.

### 4.2 Official Odoo 19 user fixtures

`new_test_user()` is used for:

- Rental Officer.
- Rental Manager.
- Internal user without rental access.
- Company-restricted rental user.
- Portal User A.
- Portal User B.

### 4.3 Additional test-source corrections

The suite was reviewed beyond the immediate AccessError:

- Real invoices are retrieved from `rent.invoice._create_account_move()`.
- Boolean action returns are no longer treated as `account.move` records.
- Closed contracts are tested against uninvoiced schedules.
- Automatic installment mode is verified before missed-cron processing.
- Multi-company dashboard comparison uses explicit allowed companies.
- Manager close/cancel is tested without Accounting privilege.
- A month-end contract regression verifies exactly four schedules from a four-month contract starting on 31 January.

### 4.4 Production logic corrections covered by tests

- Contract-start-anchored monthly, quarterly, and yearly boundaries.
- Full-month charging and final-partial-period proration.
- Access-aware accounting totals/dashboard data.
- Narrow invoice-state read elevation after Rental Manager authorization.
- Draft/non-draft rent validation and negative-deposit rejection.

## 5. Automated Odoo tests included

The module contains **31 test methods** in:

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

- Property Draft → Available → Rented → Available lifecycle.
- Required activation data.
- Contract overlap prevention.
- Monthly invoice idempotency.
- Missed-cron catch-up.
- Month-end billing anchors.
- Quarterly billing and final period.
- Service amount calculation.
- Yearly billing.
- Full payment and manual schedules.
- Renewal links and next-day start.
- Tenant, landlord, and dual-source commissions.
- Officer/Manager/Internal/Public access.
- Rental Manager operations without Accounting group.
- Portal ownership isolation.
- Multi-company isolation and dashboard scope.
- Upgrade-state/accounting-history preservation.

## 6. Static validation executed for 19.0.1.0.6

The final workspace and independently extracted ZIP are checked for:

- Python AST parsing and in-memory compilation.
- Manifest syntax, required keys, version, dependencies, and referenced files.
- XML well-formedness and duplicate explicit XML IDs.
- CSV structure.
- PO translation parsing.
- JavaScript syntax with `node --check`.
- Package import targets.
- Cron method existence.
- Object-button method existence.
- Deprecated Odoo patterns used by the previous version.
- Invalid product test-copy patterns.
- Direct test-user creation patterns.
- Compiled/cache/debug files.
- ZIP CRC integrity.

Final counts are recorded in the external versioned test report and verification output after package creation.

## 7. Runtime commands for acceptance

### 7.1 Clean installation

```bash
odoo-bin \
  -d rental_test_clean \
  -i rental_management \
  --stop-after-init \
  --test-enable \
  --log-level=test
```

### 7.2 Existing database upgrade

```bash
odoo-bin \
  -d rental_test_upgrade \
  -u rental_management \
  --stop-after-init \
  --test-enable \
  --log-level=test
```

### 7.3 Recommended focused rerun

```bash
odoo-bin \
  -d rental_test_clean \
  -u rental_management \
  --stop-after-init \
  --test-enable \
  --test-tags /rental_management \
  --log-level=test
```

## 8. Separate docutils warning

The supplied log also contains:

```text
Unexpected indentation
Block quote ends without a blank line
```

It did not stop registry loading: Odoo continued into asset generation and module tests. The `rental_management` manifest has an explicit plain-text description and the module contains no README/RST file. The available evidence therefore does not identify this module as the source. A repository-wide manifest/README audit is required to remove that separate warning.

## 9. Current conclusion

- Runtime module load before tests: **passed in the supplied latest Odoo.sh run**.
- Version `19.0.1.0.5` post-install tests: **stopped by shared fixture ACL error**.
- Version `19.0.1.0.6` source correction: **completed**.
- Version `19.0.1.0.6` static validation: **executed**.
- Version `19.0.1.0.6` Odoo runtime tests: **not executed in this workspace**.
- Final acceptance: requires the next clean Odoo.sh test run and, separately, an upgrade run on a staging copy of production data.


## 10. Final static result for the packaged source

The completed `19.0.1.0.6` workspace passed the following checks before ZIP creation:

```text
Python AST/in-memory compilation: 45 files passed
Manifest version: 19.0.1.0.6
XML parsing: 56 files passed
Explicit XML IDs: 273, no duplicates
CSV structure: 1 file passed
PO parsing: 6 files passed
JavaScript syntax: 1 file passed
Cron method targets: 8 records passed
Object-button method targets: 71 buttons passed
Automated test methods included: 31
Package import targets: passed
Deprecated/prohibited code scan: passed
Cache/temp cleanup: passed
```

An independent extraction and revalidation of the final ZIP is performed after packaging. Its ZIP CRC and SHA-256 are reported with the delivery artifact.
