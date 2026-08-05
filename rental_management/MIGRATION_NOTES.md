# rental_management — Migration Notes for Odoo 19

## 1. Purpose

These notes apply when upgrading an existing database containing `rental_management` data to module version `19.0.1.0.0`.

The migration is conservative: it preserves historical records and reports anomalies rather than deleting or silently rewriting business history.

## 2. Mandatory Backup

Before any upgrade:

1. Stop user activity or place the database in a maintenance window.
2. Create a complete PostgreSQL backup.
3. Create a filestore backup.
4. Record the installed module version and latest contract/invoice sequences.
5. Test restoration of the backup.
6. Perform the first upgrade on a cloned staging database.

Example PostgreSQL backup:

```bash
pg_dump -Fc -d production_database -f production_database_before_rental_odoo19.dump
```

Example filestore archive:

```bash
tar -czf production_filestore_before_rental_odoo19.tar.gz \
  /path/to/odoo/filestore/production_database
```

Odoo.sh users should create a staging branch/build and a database duplicate before upgrading production.

## 3. Migration Scripts

```text
migrations/
└── 19.0.1.0.0/
    ├── pre-migration.py
    └── post-migration.py
```

### 3.1 Pre-migration

The pre-migration script:

- Detects tables and columns before operating on them.
- Fills null property status with `draft`.
- Fills missing company values using safely related records, then a fallback company when required.
- Fills null contract status with `new_contract`.
- Fills null property-sale status with `booked` so the new required selection can be applied safely.
- Propagates company values to rental schedules, property-sale schedules, property-sale records, and maintenance requests.
- Logs row counts.
- Logs the number of incomplete legacy contracts.

It does not delete:

- Properties.
- Contracts.
- Rental schedules.
- Customer invoices.
- Vendor bills.
- Posted accounting entries.

### 3.2 Post-migration

The post-migration script:

- Marks running contracts whose end date is in the past as expired.
- Determines currently rented properties.
- Determines properties reserved by future running contracts.
- Releases stale `on_lease`/`booked` properties when no running contract reserves them.
- Rebuilds missing installment schedules for running contracts.
- Backfills `account.move.rental_schedule_id` and `account.move.sale_schedule_id` from existing schedule-to-invoice links, preserving old invoices while enabling the new unique indexes.
- Logs overlapping contracts.
- Logs incomplete contracts requiring manual review.

The script intentionally does not auto-resolve overlapping historical contracts.

## 4. Data Preserved

The upgrade retains existing:

- Model names.
- Main field technical names.
- State selection keys.
- Main XML IDs.
- Property records.
- Rental contracts.
- Sale contracts.
- Rental schedules.
- Accounting invoices and bills.
- Posted entries.
- Maintenance records.
- Sequences.
- Portal relationships.
- Attachments and documents.

## 5. Schema Additions

The upgrade may add fields and database objects for:

- Activation/closing/cancellation audit data.
- Previous/new renewal links.
- Invoice period start/end/type.
- Rental schedule company/currency data.
- Account-move-to-schedule link.
- Reminder/idempotency flags.
- Broker commission records.
- Stored company-aware relations.
- SQL constraints and a partial unique invoice index.

## 6. Pre-upgrade Data Review Queries

Run equivalent ORM checks or SQL on the staging copy.

### Running contract ended in the past

```sql
SELECT id, tenancy_seq, property_id, start_date, end_date
FROM tenancy_details
WHERE contract_type = 'running_contract'
  AND end_date < CURRENT_DATE;
```

### Available property with a current running contract

```sql
SELECT p.id, p.name, p.stage, t.tenancy_seq
FROM property_details p
JOIN tenancy_details t ON t.property_id = p.id
WHERE p.stage = 'available'
  AND t.contract_type = 'running_contract'
  AND t.start_date <= CURRENT_DATE
  AND t.end_date >= CURRENT_DATE;
```

### On-rent property without a current running contract

```sql
SELECT p.id, p.name
FROM property_details p
WHERE p.stage = 'on_lease'
  AND NOT EXISTS (
      SELECT 1
      FROM tenancy_details t
      WHERE t.property_id = p.id
        AND t.contract_type = 'running_contract'
        AND t.start_date <= CURRENT_DATE
        AND t.end_date >= CURRENT_DATE
  );
```

### Incomplete contracts

```sql
SELECT id, tenancy_seq, property_id, tenancy_id, company_id,
       start_date, duration_id, payment_term, total_rent
FROM tenancy_details
WHERE property_id IS NULL
   OR tenancy_id IS NULL
   OR company_id IS NULL
   OR start_date IS NULL
   OR duration_id IS NULL
   OR payment_term IS NULL
   OR total_rent IS NULL
   OR total_rent <= 0;
```

## 7. Upgrade Procedure

1. Copy the final `rental_management` directory to the custom addons path.
2. Ensure the addons path contains all manifest dependencies.
3. Ensure Python package `xlsxwriter` is available.
4. Restart Odoo to load the new Python code.
5. Upgrade a staging database:

```bash
odoo-bin \
  -d rental_test_upgrade \
  -u rental_management \
  --stop-after-init \
  --test-enable \
  --log-level=test
```

6. Review the full server log for entries beginning with:

```text
rental_management:
```

7. Resolve business-data anomalies in staging.
8. Repeat the upgrade from a fresh production clone after any data cleanup.
9. Complete functional, accounting, portal, and company-isolation tests.
10. Schedule the production upgrade only after staging acceptance.

## 8. Required Post-upgrade Review

Review:

- Contracts reported as overlapping.
- Contracts missing tenant, property, company, duration, dates, payment policy, or rent.
- Properties whose state changed to available/reserved/rented.
- Running contracts converted to expired.
- Newly rebuilt schedules.
- Existing duplicate invoices by business period.
- Posted invoices related to cancelled or closed legacy contracts.
- Portal users with shared commercial partners.
- Users assigned to Rental Officer or Rental Manager.
- Company ownership of properties, contracts, taxes, and invoices.

## 9. Rollback

If the upgrade fails:

1. Stop Odoo.
2. Preserve the failed-upgrade log and database for diagnosis.
3. Restore the PostgreSQL backup.
4. Restore the matching filestore backup.
5. Restore the previous module source.
6. Restart Odoo.
7. Verify sequence values and latest accounting entries.

Do not attempt to partially reverse schema/data changes manually on the only production database.

## 10. Important Operational Notes

- Do not execute the first upgrade directly on production.
- Do not remove posted invoices to resolve contract inconsistencies.
- Do not manually change selection keys in SQL.
- Do not delete conflicting contracts before business approval.
- Do not disable global company rules to bypass access errors; correct the company ownership data instead.
- Run the lifecycle cron twice in staging and confirm no duplicate invoice is produced.
