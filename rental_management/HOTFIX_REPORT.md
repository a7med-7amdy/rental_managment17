# Hotfix Report — 19.0.1.0.6

## Runtime trigger

Odoo.sh successfully completed module loading, XML validation, asset generation, and entered the post-install test suite for version `19.0.1.0.5`.

The test suite then stopped after five identical setup errors:

```text
odoo.exceptions.AccessError: You are not allowed to create
'Contract Duration' (contract.duration) records.

Allowed group:
- Rental Management / Rental Manager
```

The failure was in the shared test fixture `tests/common.py`. The accounting test user had the required accounting permissions but did not have the Rental Manager group required to create rental configuration records.

## Corrections in 19.0.1.0.6

### 1. Shared test-user authorization

The shared accounting-ready test user is explicitly linked to:

```text
rental_management.property_rental_manager
```

before any rental configuration, duration, property, contract, schedule, or commission fixture is created.

This preserves the production ACL design: Contract Duration remains manager-maintained; the test does not weaken or bypass the ACL.

### 2. Odoo 19 test-user creation

Security, portal, and multi-company test users are now created with Odoo's official `new_test_user()` helper instead of direct `res.users.create()` calls. This correctly prepares group membership, required email/password values, and allowed-company fields.

Affected files:

```text
tests/test_security.py
tests/test_multi_company.py
tests/test_portal.py
```

### 3. Test defects found proactively

The complete suite was reviewed instead of changing only the failing line. The following latent test defects were corrected:

- Tests no longer treat `action_create_invoice()`'s Boolean return value as an `account.move` record.
- Posted-invoice cancellation tests now retrieve the real invoice from the rental schedule.
- The close-contract test now verifies that an uninvoiced schedule cannot create a new invoice after closure, while preserving the already-created invoice.
- The missed-cron test changes the contract to automatic installments and verifies the stored related installment mode before running the cron.
- Dashboard multi-company comparison now uses an explicit allowed-company context.
- Manager close/cancel tests use users without Accounting privilege to verify server-side separation of duties.

### 4. Contract-period calculation correction

Invoice periods are now anchored to the original contract start date. This prevents month-end drift such as:

```text
31 January → 28 February → 28 March
```

from creating a wrong period count or distorted rent amount.

Implemented behavior:

- Monthly and quarterly boundaries are recomputed from the original start date.
- Yearly boundaries are recomputed from the original start date.
- Every complete contractual month is charged as one full month.
- Only the final incomplete contractual month is prorated.
- A four-month contract beginning on 31 January produces exactly four monthly schedules.

### 5. Rental Manager and Accounting separation

A Rental Manager without Accounting access can now close or cancel a contract safely.

Only the minimum linked invoice state inspection uses elevated read access, and only after the Rental Manager server-side authorization check. Accounting records are never deleted or modified by this operation.

Dashboard and computed accounting totals now return safe zero values when the current user lacks `account.move` read access instead of raising an unexpected AccessError.

### 6. Amount validation

- Draft contracts may temporarily contain zero rent while being prepared.
- Negative rent is always rejected.
- Activation or any non-draft state requires positive rent.
- Negative security deposits are rejected.

## Files changed

```text
__manifest__.py
models/rent_contract.py
models/property_details.py
tests/common.py
tests/test_rent_invoicing.py
tests/test_rental_contract.py
tests/test_upgrade_data.py
tests/test_security.py
tests/test_multi_company.py
tests/test_portal.py
HOTFIX_REPORT.md
TEST_REPORT.md
UPGRADE_REPORT.md
MIGRATION_NOTES.md
```

## Test inventory

The module now contains **31 automated test methods** across property lifecycle, rental contracts, invoicing, renewal, commissions, security, portal ownership, multi-company isolation, and upgrade-data preservation.

## Runtime status

Version `19.0.1.0.5` was executed on Odoo.sh and reached the module post-install tests. The five recorded setup errors are addressed in `19.0.1.0.6`.

Version `19.0.1.0.6` could not be executed inside this workspace because a live Odoo 19 Enterprise server and PostgreSQL database are not available here. Static checks and package-integrity checks are documented in `TEST_REPORT.md`; the next Odoo.sh build remains the runtime source of truth.

## Separate reStructuredText warning

The recurring warning:

```text
Unexpected indentation
Block quote ends without a blank line
```

is non-fatal in the supplied runtime log: registry loading continued through module installation, asset generation, and test execution. This module has an explicit plain-text manifest description and contains no README/RST file, so the supplied evidence does not attribute that warning to `rental_management`. It should be traced against the other installed addons' manifest descriptions or README files if a clean repository-wide log is required.
