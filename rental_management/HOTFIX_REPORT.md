# HOTFIX REPORT — rental_management 19.0.1.0.12

## Scope
Full source audit of the Odoo 19 upgrade after the 19.0.1.0.11 Odoo.sh run. This pass reviewed models, wizards, controllers, security, data, cron jobs, reports, frontend assets, tests, migrations, and compatibility with the original module schema.

## Runtime errors addressed
The latest supplied Odoo.sh run reached 39 post-install tests with 0 assertion failures and 3 runtime errors, all in rental-linked Maintenance Request creation.

The root cause was not only `maintenance.request` ACLs: Odoo 19 Maintenance resolves required `maintenance.stage` / `maintenance.team` defaults and performs additional access checks that Portal and rental-only users cannot satisfy. Version 19.0.1.0.12 now:

- validates rental role / portal ownership / contract state / property / company before elevation;
- resolves required Maintenance Team and Stage through narrowly scoped read-only sudo lookups;
- executes only the already-authorized rental-linked `maintenance.request.create()` in superuser mode;
- returns the record in the caller's normal environment;
- preserves the caller as `create_uid`;
- leaves unrelated Maintenance requests on standard Odoo security;
- blocks internal users without a rental role from linking requests to rental contracts/properties.

## Additional defects found and fixed during the full audit

### Rental lifecycle and invoicing
- Separated contract duration unit from property rental pricing unit.
- Corrected day/month/year contract end-date calculation.
- Corrected partial-period and month-end anchoring behavior.
- Prevented direct creation of contracts already in Running state.
- Batched property lifecycle consistency checks; removed per-property `search_count()` queries.
- Fixed cron cursor batching so later records cannot starve behind the first batch.
- Preserved catch-up invoicing (`due_date <= today`) with row locking and idempotency.
- Manual service/deposit/maintenance/other schedules now retain source product, taxes and base amount so recovery cannot accidentally recreate full rent.
- Service schedules are unique per source service line and period, allowing multiple different services on the same date.
- Broker commissions use separate records per source and row-locked accounting creation.
- Broker supplier/customer taxes now use the Odoo tax engine and each partner's fiscal position.

### Property sale lifecycle
- Restored the For Sale business state.
- Booking amount is positive and correctly deducted from the remaining sale amount.
- Sale bookings are serialized with row locks and are synchronized at model level, not only through a wizard.
- Direct RPC sale-state manipulation is blocked; sale/refund/sold transitions use controlled workflow contexts.
- Sale history cannot be deleted.
- Quarterly installment count derives from actual duration rather than a hard-coded value.
- Remaining-payment consolidation preserves original schedules.
- Booking and installment invoice creation is idempotent.
- Sale tax display and accounting invoice taxes both apply fiscal-position mapping.

### Property / project integrity
- Added missing commercial and industrial measurement compute methods.
- Added the missing parent-property address synchronization method used by scheduled jobs.
- Added server-side property status consistency validation.
- Child documents/images/floor plans/measurements/certificates/services/connectivity use cascade cleanup where they are owned by the property.
- Parent property and landlord relations enforce company consistency.
- Project and Subproject statistics are loaded in batches instead of issuing searches for every project.
- Restored the three area total fields to their original Integer schema to avoid unnecessary upgrade type conversion.

### Multi-company and CRM
- Removed the custom redefinition of `crm.lead.company_id`; Odoo 19 Core owns this field.
- Property matching now respects the lead company.
- Added `_check_company_auto = True` to rental invoice and affected transactional wizards.
- Added `check_company=True` to relevant contract, inquiry, agreement, maintenance, product, partner and accounting relations.
- Inquiry booking validates lead, property, customer and company consistency server-side.

### Security / portal
- Portal maintenance creation verifies contract ownership and Running state.
- Portal cannot link a request to another tenant's contract/property.
- Portal routes use ownership domains before any limited sudo operation.
- Rental Manager does not receive Maintenance Team administration privileges.
- Dashboard and computed amounts do not use sudo to aggregate unauthorized companies/accounting data.

### Odoo 19 compatibility
- Corrected all migration entrypoints to `migrate(cr, version)`.
- Removed deprecated `.read_group()` backend calls in favor of `_read_group()`.
- Removed old `tree`, `attrs`, `states`, `detailed_type`, `web_editor`, obsolete cron fields and old relational-command patterns.
- Product service data uses Odoo 19 `type = service` and an existing Odoo 19 product category.
- XLS reports use `xlsxwriter`; no `xlwt` import remains.

## Known external warning
The recurring docutils warning emitted while Odoo prepares `res.partner.email_normalized` is not emitted by rental_management and does not stop the registry or tests. No Odoo Core files are modified to suppress it.
