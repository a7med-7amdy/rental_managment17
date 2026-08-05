# rental_management — Odoo 19 Upgrade Report

## 1. Executive Summary

The `rental_management` module was structurally upgraded from version **3.1.1** to **19.0.1.0.2** while retaining:

- Technical module name: `rental_management`
- Original author: `TechKhedut Inc.`
- License: `OPL-1`
- Existing model names and principal XML IDs
- Existing property, rental, sale, invoice, maintenance, portal, report, and configuration data structures where technically safe

The upgrade focused on Odoo 19 compatibility, rental lifecycle visibility, accounting-safe recurring invoicing, portal ownership security, multi-company isolation, migration safety, dashboard modernization, and automated regression coverage.

## 2. Version Information

| Item | Value |
|---|---|
| Original module version | `3.1.1` |
| Final module version | `19.0.1.0.2` |
| Target platform | Odoo 19 Enterprise |
| Technical name | `rental_management` |
| Author | TechKhedut Inc. |
| License | OPL-1 |
| External Python dependency | `xlsxwriter` (declared in the manifest) |

## 3. Main Upgrade Areas

### 3.1 Odoo 19 framework compatibility

- Replaced the removed Odoo 19 import path `odoo.addons.web_editor.tools` with `odoo.addons.html_editor.tools` for video embed and thumbnail helpers.
- Declared `html_editor` as an explicit dependency because the module imports its Python API directly.
- Corrected invalid-video validation messages to use `display_name` rather than assuming image-line records contain a `name` field.
- Replaced legacy `<tree>` architecture with Odoo 19 `<list>` architecture.
- Updated action `view_mode` values from `tree` to `list`.
- Removed legacy `attrs` and `states` usage.
- Updated relational writes to `odoo.fields.Command` in Python business logic.
- Corrected eager date defaults and retained callable defaults.
- Converted transient operational models to `models.TransientModel`.
- Replaced legacy display-name overrides with `_compute_display_name`.
- Converted SQL constraint declarations to Odoo 19 `models.Constraint` and `models.UniqueIndex` table objects.
- Updated the manifest, asset bundles, data order, and external dependency declaration.
- Rebuilt XLS reports as XLSX reports using `xlsxwriter`, removing the unavailable `xlwt` import.

### 3.2 Rental lifecycle redesign

The authoritative contract state remains the existing `contract_type` selection:

- `new_contract`
- `running_contract`
- `expire_contract`
- `close_contract`
- `cancel_contract`

The existing property state keys remain:

- `draft`
- `available`
- `booked`
- `on_lease`
- `sale`
- `sold`

The user interface now exposes the complete lifecycle through status bars, state-dependent actions, ribbons, smart buttons, filters, grouped searches, and contract/property synchronization.

Important behavior:

- A future activated contract reserves the property as `booked`.
- A currently effective contract sets the property to `on_lease`.
- A current contract takes precedence over a future renewal when both exist.
- Closing, cancelling, or expiring a contract recalculates the property from all remaining running contracts.
- The property is returned to `available` only when no current or future running contract reserves it.

### 3.3 Contract validation and overlap prevention

Implemented:

- Required activation validation for property, tenant, company, dates, duration, rent, payment policy, invoice start date, and installment product.
- Company consistency checks for property, contract, taxes, accounting documents, maintenance, schedules, and commissions.
- Positive rent and non-negative deposit/commission constraints.
- Commission percentage range validation.
- Start/end and invoice-start date validation.
- Contract overlap validation using the inclusive period rule:

```text
new_start <= existing_end
and
new_end >= existing_start
```

- Direct creation or write of a `running_contract` also invokes overlap protection.
- Existing duplicate or inconsistent legacy data is reported by migration scripts instead of being deleted automatically.

### 3.4 Activation, closure, cancellation, and expiry

#### Activation

Activation is idempotent and performs validation before changing data. It:

- Validates all required business fields.
- Validates company consistency and overlap.
- Changes the contract to `running_contract`.
- Synchronizes the property state.
- Builds the installment schedule once.
- Creates broker commission records independently from the contract.
- Creates all currently due automatic invoices.
- Sends the activation email once when a valid recipient exists.
- Schedules an expiry-review activity.
- Posts a chatter audit message.

#### Closure

Closure:

- Is restricted server-side to Rental Managers.
- Preserves all accounting invoices and installment history.
- Records the closing user and timestamp.
- Completes open activities.
- Logs outstanding posted invoices in chatter.
- Recalculates the property state safely.

#### Cancellation

Cancellation:

- Is restricted server-side to Rental Managers.
- Requires a cancellation reason through a dedicated wizard.
- Refuses cancellation while posted invoices remain, requiring an explicit credit-note/accounting policy.
- Preserves accounting history.
- Records the user, date, and reason.
- Recalculates the property state.

#### Expiry

The unified daily lifecycle cron:

- Sends one pre-expiry reminder according to settings.
- Schedules an activity for the responsible user.
- Marks contracts expired after the end date.
- Does not release the property before the contractual end date.
- Recalculates property availability from all current and future running contracts.
- Uses savepoints so a single failed contract does not stop the full batch.

### 3.5 Renewal

The renewal wizard now:

- Defaults the new start date to old end date plus one day.
- Creates one linked new contract.
- Keeps the old and new contract references in both directions.
- Copies the tenant, property, company, currency, payment configuration, products, taxes, deposit settings, services, maintenance settings, broker settings, agreement, and terms where appropriate.
- Does not copy historical invoices, activities, emails, closing/cancellation metadata, or accounting links.
- Does not close the old contract before the new record is created successfully.
- Prevents overlapping activation.

### 3.6 Recurring invoicing redesign

A centralized schedule-and-invoice engine replaced duplicated monthly, quarterly, yearly, and full-payment blocks.

Implemented capabilities:

- Monthly billing.
- Quarterly billing.
- Yearly billing.
- Full payment.
- Manual installment schedules.
- Automatic installment schedules.
- Partial final periods.
- Security deposits.
- Extra services.
- Recurring maintenance.
- Tax-engine-based calculation.
- Company, currency, partner, payment-term, fiscal-position, and product consistency.

Idempotency controls:

- Unique schedule key: contract, period start, period end, invoice type.
- One accounting invoice per rental schedule through a partial unique index.
- Catch-up logic uses `due_date <= today`.
- Re-running the cron does not create a second invoice for the same period.
- Closed or cancelled contracts cannot create new rental invoices.

Property-sale billing was also hardened without changing the existing sale model names:

- Booking invoices are company/currency aware and idempotent.
- Sale installments now carry a unique accounting-side schedule link.
- Re-running the sale scheduler cannot create a second accounting invoice for the same linked schedule.
- Remaining-payment consolidation returns the existing consolidation record instead of duplicating it.
- Negative or out-of-range broker commissions are rejected.

Specific known defects corrected:

- Undefined annual-invoice variable.
- Use of `self.total_rent` inside record loops.
- Quarterly service double multiplication.
- Exact-date-only cron behavior.
- Duplicate schedule/invoice generation.
- Inconsistent period handling.
- Manual tax percentage calculations.

### 3.7 Broker commissions

The contract wizard now creates exactly one rental contract per transaction.

Commission processing is independent and supports:

- Tenant source.
- Landlord source.
- Both sources.
- Fixed commission.
- Percentage commission.
- One-rent-period commission.
- Entire-contract commission.

When both parties pay, two `rental.commission` records are created against one contract. Each record can hold its broker bill and customer/landlord charge invoice independently.

### 3.8 Security and multi-company

#### Groups

- Added the Odoo 19 `res.groups.privilege` structure.
- Rental Manager implies Rental Officer.
- No users are automatically added to the manager group.
- No base administrator record is modified.

#### Server-side authorization

- Rental Officers cannot delete active contracts.
- Rental Officers cannot close or cancel contracts, including through direct RPC calls.
- Rental Managers retain close/cancel and configuration responsibilities.

#### Record rules

Global allowed-company isolation was added for:

- Properties.
- Property documents.
- Parent properties.
- Rental contracts.
- Property sale contracts.
- Rental schedules.
- Sale schedules.
- Contract services.
- Sale inquiries.
- Broker commissions.
- Agreement templates.
- Maintenance requests.
- Property projects.
- Property subprojects.

The dashboard uses the active company for monetary KPIs. This prevents invalid aggregation of different company currencies and naturally respects company switching.

### 3.9 Portal security and usability

Portal routes now search through ownership domains before returning records.

A portal user can access only records linked to the commercial partner of the signed-in user:

- Rental contracts.
- Property sale contracts.
- Contract properties.
- Rental installment records.
- Maintenance requests.
- Authorized property documents.

Maintenance creation requires:

- An owned contract.
- `running_contract` state.
- A valid maintenance product for the contract company.
- A property inherited from the owned contract.
- CSRF-protected POST submission.

The limited `sudo()` use in the maintenance form is restricted to reading maintenance product configuration only, after ownership validation. Contract, property, invoice, maintenance, and document records are not elevated before ownership checks.

Portal UI additions:

- My Rental Contracts.
- Active Contracts.
- Rent Invoices.
- Maintenance Requests.
- Contracts Expiring Soon.
- Contract state timeline.
- Invoice/payment information.
- Renewal links.
- Controlled maintenance request creation.

### 3.10 Dashboard and frontend

- Rebuilt the backend dashboard as an Odoo 19 OWL client action.
- Removed bundled legacy global chart/map libraries.
- Added loading, empty, error, and retry states.
- Removed unrestricted `sudo()` aggregation.
- Replaced repeated per-record counters with grouped ORM queries.
- Scoped all monetary KPIs to the active company.
- Added responsive layout and state-aware navigation.

KPIs include:

- Total properties.
- Available, reserved, rented, for-sale, and sold properties.
- Active, expiring, expired, closed, and cancelled contracts.
- Monthly rent.
- Collected, outstanding, and overdue amounts.
- Pending invoices.
- Maintenance requests.
- Occupancy rate.

### 3.11 Email, reports, and translation

- Updated email sender fallbacks and recipient guards.
- Corrected malformed template markup.
- Preserved existing template XML IDs.
- Updated report/view list architecture.
- Added safer portal links and ownership rules.
- Rebuilt legacy XLS output as XLSX.
- Parsed and normalized Arabic PO encoding/header data.
- Added/updated key Arabic rental workflow terminology.

## 4. Modified Files

The following existing files were materially modified:

```text
__manifest__.py
controllers/main.py
data/active_contract_mail_template.xml
data/ir_cron.xml
data/property_book_mail_template.xml
data/property_sold_mail_template.xml
data/sale_invoice_mail_template.xml
data/tenancy_reminder_mail_template.xml
i18n/ar_001.po
models/crm_lead.py
models/maintenance.py
models/property_details.py
models/property_project.py
models/property_sub_project.py
models/rent_contract.py
models/rent_invoice.py
models/res_partner.py
models/sale_contract.py
security/groups.xml
security/ir.model.access.csv
security/security.xml
static/src/js/rental.js
static/src/scss/style.scss
static/src/xml/template.xml
views/agreement_template_view.xml
views/certificate_type_view.xml
views/configuration_views.xml
views/contract_duration_view.xml
views/nearby_connectivity_view.xml
views/parent_property_view.xml
views/product_product_inherit_view.xml
views/property_amenities_view.xml
views/property_crm_lead_inherit_view.xml
views/property_details_view.xml
views/property_document_view.xml
views/property_maintenance_view.xml
views/property_project_view.xml
views/property_region_views.xml
views/property_res_city.xml
views/property_specification_view.xml
views/property_sub_project_views.xml
views/property_tag_view.xml
views/property_vendor_view.xml
views/rent_invoice_view.xml
views/templates/property_web_template.xml
views/tenancy_details_view.xml
views/user_type_view.xml
wizard/__init__.py
wizard/active_contract.py
wizard/active_contract_view.xml
wizard/booking_wizard.py
wizard/contract_wizard_view.xml
wizard/contract_wizrd.py
wizard/extend_contract_wizard.py
wizard/extend_contract_wizard_view.xml
wizard/landlord_tenancy_sold_xls.py
wizard/property_payment_wizard.py
wizard/property_sale_tenancy_xls_report.py
wizard/property_vedor_wizard.py
wizard/subproject_creation.py
wizard/unit_creation.py
```

## 5. New Files

The delivery documentation is included both inside the module package and as separate files.

```text
UPGRADE_REPORT.md
TEST_REPORT.md
RENTAL_WORKFLOW.md
MIGRATION_NOTES.md
migrations/19.0.1.0.0/pre-migration.py
migrations/19.0.1.0.0/post-migration.py
tests/__init__.py
tests/common.py
tests/test_broker_commission.py
tests/test_contract_renewal.py
tests/test_multi_company.py
tests/test_portal.py
tests/test_property_lifecycle.py
tests/test_rent_invoicing.py
tests/test_rental_contract.py
tests/test_security.py
tests/test_upgrade_data.py
wizard/cancel_contract_wizard.py
wizard/cancel_contract_wizard_view.xml
```

## 6. Removed Files

The following obsolete bundled JavaScript libraries were removed because the dashboard no longer relies on global legacy APIs:

```text
static/src/js/lib/Animated.js
static/src/js/lib/Material.js
static/src/js/lib/apexcharts.js
static/src/js/lib/index.js
static/src/js/lib/map.js
static/src/js/lib/worldLow.js
static/src/js/lib/xy.js
```

Generated `__pycache__`, `.pyc`, and temporary files are excluded from the final package.

## 7. Migration Behavior

The migration scripts:

- Fill safely derivable company/state values.
- Preserve all contracts, properties, invoices, and accounting entries.
- Mark past running contracts as expired.
- Synchronize rented/reserved/available property states.
- Rebuild missing schedules for running contracts and backfill accounting-side rental/sale schedule links.
- Log overlapping contracts and incomplete legacy records for manual review.
- Do not auto-delete or silently rewrite conflicting historical records.

See `MIGRATION_NOTES.md` for the operational procedure.

## 8. Known Limitations

1. An Odoo 19 runtime was not installed in the provided execution environment. Clean-install, upgrade, browser, PDF-rendering, mail-delivery, and JavaScript runtime tests were therefore not executed here.
2. The QWeb reports were XML-parsed but not rendered by an Odoo 19 report engine.
3. Migration anomaly repair is intentionally conservative. Overlapping or incomplete historical records are logged for business review rather than automatically deleted or altered.
4. XLS output is now XLSX. This is intentional because the previous `xlwt` dependency was unavailable and obsolete for modern deployments.
5. Dashboard monetary totals are deliberately scoped to the active company to avoid summing unrelated currencies across companies.

## 9. Final Status

Static validation completed successfully for:

- Python syntax and compilation.
- XML syntax.
- JavaScript syntax.
- Manifest file references.
- Translation PO parsing.
- Duplicate custom fields.
- Duplicate custom methods.
- Duplicate XML IDs.
- Local XML references.
- ACL custom model references.
- Legacy view architecture patterns.
- Debug/TODO/pass placeholders.
- Compiled/temporary file cleanup.

Runtime acceptance remains subject to executing the clean-install and upgrade commands documented in `TEST_REPORT.md` on an actual Odoo 19 Enterprise environment.


## Registry Hotfix 19.0.1.0.2

- Normalized the manifest description to avoid reStructuredText parser warnings.
- Removed duplicate display labels reported during Odoo model reflection.
- Replaced legacy-hostile SQL checks with Python validation and an upgrade-safe migration.
- Added `migrations/19.0.1.0.2/` without changing technical fields or business data.

## Hotfix 19.0.1.0.3 — Odoo 19 product data compatibility

- Replaced removed external ID `product.product_category_all` with `product.product_category_services`.
- Replaced removed product field `detailed_type` with `type` in `data/property_product_data.xml`.
- Kept all module-owned XML IDs unchanged for safe installation and upgrade behavior.

- Added `product` as an explicit dependency instead of relying on transitive dependencies.
