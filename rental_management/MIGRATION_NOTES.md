# MIGRATION NOTES — rental_management 19.0.1.0.12

## Before upgrading
1. Create a database backup and filestore backup.
2. Upgrade first on a staging clone.
3. Keep the original `rental_management` technical name.
4. Do not delete historical rental, sale or accounting records to satisfy new constraints.

## Migration scripts
All migration entrypoints use the Odoo 19 signature `migrate(cr, version)`.

### 19.0.1.0.0
Normalizes missing company/status data where a safe deterministic value exists and reports inconsistent historical rows instead of deleting them.

### 19.0.1.0.2
Removes legacy-hostile strict database checks that could prevent loading an existing database containing incomplete Draft/history records. Business validation remains in Python and activation workflows.

### 19.0.1.0.11
Verifies/repairs the compatibility access records used for rental-linked Maintenance Requests.

### 19.0.1.0.12
- normalizes the historical Property `used_for` key `" retail_stores"` to `"retail_stores"`;
- marks historical duplicate rental schedules with `legacy_duplicate` rather than deleting them;
- marks historical duplicate broker commission rows rather than deleting them;
- allows the new partial unique indexes to protect future data without destroying old history.

## Data compatibility findings
- No original custom model was removed.
- No original technical field was intentionally removed from its owning custom model, except the module no longer redefines `crm.lead.company_id` because that is an Odoo Core field in Odoo 19; the database column remains part of CRM.
- Existing rental and sale state keys are preserved.
- The malformed original selection key `" retail_stores"` is migrated explicitly.
- Existing XML IDs are retained except unsafe legacy modifications of Odoo base security records; those are intentionally not recreated.
- Historical duplicate invoices/commissions are preserved and flagged, never silently deleted.

## Post-upgrade review
Review migration logs for:
- incomplete historical contracts;
- overlapping historical contracts;
- properties whose stored state disagrees with active contracts/sales;
- historical duplicate rental schedules or commission records.
