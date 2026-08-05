# rental_management — Test Report

## 1. Test Scope

This report distinguishes between:

- **Executed static validation** in the supplied workspace.
- **Authored Odoo automated tests** included in the module.
- **Runtime tests not executed** because Odoo 19 was not installed in the execution environment.

No runtime success is claimed.


## 1.1 Odoo.sh Runtime Attempt and Import Hotfix

An actual Odoo.sh module load was attempted on **2026-08-05**. The initial `19.0.1.0.0` package failed before registry initialization with:

```text
ModuleNotFoundError: No module named 'odoo.addons.web_editor'
```

The failure occurred in three model files that imported video helpers from the pre-Odoo-19 addon path. Version **19.0.1.0.1** applied the following hotfix:

- `odoo.addons.web_editor.tools` → `odoo.addons.html_editor.tools`
- Adds `html_editor` to manifest dependencies.
- Re-runs Python, XML, JavaScript, manifest-reference, and package-integrity checks.

A second Odoo.sh attempt reached model reflection and exposed manifest-description and duplicate-label warnings, followed by a registry failure whose fatal traceback was not included in the supplied excerpt. Version `19.0.1.0.2` addresses every visible warning and removes strict SQL checks that could reject incomplete legacy draft/history records during upgrade. Runtime acceptance remains pending another Odoo.sh build.

## 2. Validation Environment

| Component | Version / Result |
|---|---|
| Execution date | 2026-08-05 |
| Python | 3.13.5 |
| Node.js | 22.16.0 |
| lxml | 6.1.1 |
| Babel | 2.18.0 |
| XlsxWriter | 3.2.9 |
| Odoo Python package | Not installed |
| `odoo-bin` | Not available |
| Target Odoo version | Odoo 19 Enterprise |

## 3. Executed Static Checks

### 3.1 Python syntax and compilation

Executed against every Python source file, including models, controllers, wizards, migration scripts, and tests.

Result:

```text
Python files checked: 45
Syntax/compile errors: 0
```

### 3.2 XML parsing

All manifest-loaded XML, portal templates, QWeb reports, security data, cron data, mail templates, and wizard views were parsed with `lxml`.

Result:

```text
XML files checked: 56
XML parse errors: 0
```

### 3.3 JavaScript syntax

Executed:

```bash
node --check static/src/js/rental.js
```

Result:

```text
Passed
```

### 3.4 Manifest file reference validation

Validated every path declared under:

- `data`
- `assets`
- `images`

Result:

```text
Missing manifest files: 0
```

### 3.5 Translation parsing

Parsed all PO catalogs using Babel.

Result:

```text
ar_001.po: parsed
 de.po: parsed
 es.po: parsed
 ro.po: parsed
 nl.po: parsed
 fr.po: parsed
PO parse errors: 0
```

### 3.6 Structural duplicate/reference audit

Custom static audit result:

```text
Python classes inspected: 72
Custom models detected: 52
Field declarations inspected: 858
Methods inspected: 297
Duplicate custom fields: 0
Duplicate custom methods: 0
XML records: 216
Views: 87
XML IDs: 273
Object buttons cross-checked: 71
Cron methods cross-checked: 8
Duplicate XML IDs: 0
Missing local XML references: 0
ACL rows: 110
ACL references to missing custom models: 0
```


### 3.7 Legacy/dead-code pattern scan

Scanned for:

- `<tree>`
- `view_mode` containing `tree`
- `attrs=`
- `states=`
- `print()`
- `TODO`
- bare `pass` placeholders
- eager date/datetime defaults
- legacy Python many-to-many tuple commands
- `xlwt` imports

Result:

```text
Blocking matches: 0
```

### 3.8 External dependency check

```text
xlsxwriter: available (3.2.9)
xlwt: removed from module imports
```

`xlsxwriter` is declared under `external_dependencies` in `__manifest__.py`.

### 3.9 Cross-file and package checks

Validated:

- Every Python package `__init__.py` imports its model, wizard, controller, and test modules.
- All 71 XML object buttons resolve to methods on the correct parent or One2many comodel.
- All 8 scheduled-action methods resolve to loaded model methods.
- Manifest image, data, report, template, and asset paths exist.
- No `__pycache__`, `.pyc`, `.pyo`, `.DS_Store`, or removed legacy dashboard libraries are present in the delivery tree.

Result:

```text
Cross-file/package errors: 0
```

### 3.10 Runtime availability check

Executed:

```bash
command -v odoo-bin
python -c "import odoo"
```

Result:

```text
odoo-bin: not available
Python import odoo: ModuleNotFoundError
```

## 4. Automated Odoo Tests Included

The module contains **28 automated test methods** across the following files:

| File | Coverage |
|---|---|
| `test_property_lifecycle.py` | Draft → available → running → rented → closed → available |
| `test_rental_contract.py` | Required activation fields, overlap, close/cancel history, posted invoice protection |
| `test_rent_invoicing.py` | Monthly, missed cron, quarterly, service amount, yearly, full payment, manual schedules |
| `test_contract_renewal.py` | Next-day renewal, old/new links, data copying, overlap behavior |
| `test_broker_commission.py` | Tenant, landlord, both sources, fixed and percentage commission |
| `test_security.py` | Officer, manager, internal user, portal/public access, server-side close/cancel restriction |
| `test_multi_company.py` | Company rules, cross-company rejection, dashboard isolation |
| `test_portal.py` | Contract ownership, maintenance ownership, unauthorized creation, authentication |
| `test_upgrade_data.py` | Existing states and accounting history preservation |

Test classes use Odoo accounting-ready test data through `AccountTestInvoicingCommon`, `Command`, tagged Odoo tests, and portal HTTP tests where appropriate.

## 5. Runtime Commands Required for Acceptance

These commands were prepared but could not be executed in this environment.

### 5.1 Clean installation

```bash
odoo-bin \
  -d rental_test_clean \
  -i rental_management \
  --stop-after-init \
  --test-enable \
  --log-level=test
```

### 5.2 Existing database upgrade

```bash
odoo-bin \
  -d rental_test_upgrade \
  -u rental_management \
  --stop-after-init \
  --test-enable \
  --log-level=test
```

Recommended Odoo.sh equivalent:

```bash
odoo-bin -d "$DB_NAME" -u rental_management --stop-after-init --test-enable --log-level=test
```

Use a duplicate/staging database, never the only production database.

## 6. Runtime Test Status

| Test category | Status |
|---|---|
| Python static syntax | Passed |
| XML static syntax | Passed |
| JavaScript static syntax | Passed |
| Manifest references | Passed |
| PO parsing | Passed |
| Duplicate/static reference audit | Passed |
| Odoo clean installation | Not executed — Odoo runtime unavailable |
| Odoo module upgrade | Not executed — Odoo runtime unavailable |
| Automated Odoo tests | Authored, not executed here |
| Browser/OWL runtime | Not executed |
| JavaScript console inspection | Not executed |
| QWeb PDF rendering | Not executed |
| Live email delivery | Not executed |
| Odoo.sh deployment | Not executed |

## 7. Acceptance Checklist for Staging

Before production deployment, verify on Odoo 19 Enterprise:

1. Install the module on a clean database.
2. Upgrade a copy of the existing production database.
3. Run all included tests.
4. Review migration warnings for incomplete or overlapping contracts.
5. Open every main menu, form, list, kanban, report, and dashboard.
6. Verify portal access using two unrelated portal users.
7. Test company switching using users with one and multiple allowed companies.
8. Create and post monthly, quarterly, yearly, full-payment, service, deposit, maintenance, and commission invoices.
9. Run the lifecycle cron twice and verify idempotency.
10. Render Arabic and English contract/property/invoice reports.
11. Confirm mail templates with valid and missing recipient emails.
12. Review browser console and server log for warnings/errors.

## 8. Conclusion

All executable static checks passed. Runtime installation, upgrade, and Odoo automated-test results remain pending because no Odoo 19 runtime was available in the workspace.


## 9. Static Validation for 19.0.1.0.2

Executed after applying the registry hotfix:

```text
Python files compiled: 45 / 45
XML files parsed: 56 / 56
JavaScript files checked: passed
Manifest data/assets missing: 0
CSV row-shape errors: 0
Duplicate explicit custom-model labels: 0
Obsolete web_editor imports: 0
Old tree/attrs/states patterns: 0
```

The Odoo 19 clean-install and upgrade commands were not executed locally because `odoo-bin`, PostgreSQL, and Odoo 19 Enterprise are not available in this workspace.

## Static verification added for 19.0.1.0.3

- Confirmed no `product.product_category_all` reference remains.
- Confirmed no `<field name="detailed_type">` remains.
- Confirmed `product.product_category_services` is used by the custom Property category.
- Confirmed all seven rental/maintenance products use `<field name="type">service</field>`.

- Confirmed `product` is declared explicitly in the manifest dependencies.

## Static verification added for 19.0.1.0.4

- Parsed all XML files successfully.
- Audited all search views: only `field`, `filter`, `separator`, `group`, and `searchpanel` are used as direct children.
- Confirmed all group-by containers inside search views are plain `<group>` elements without obsolete attributes.
- Confirmed the rental-contract **Expiring Soon** filter uses `relativedelta` rather than an unavailable `datetime` symbol.
- Python compilation passed.
- JavaScript syntax validation passed.
- Final ZIP CRC validation passed.

Odoo runtime installation and upgrade tests remain pending on an actual Odoo 19 environment.
