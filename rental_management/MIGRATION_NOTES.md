# Migration Notes — rental_management 19.0.1.0.7

## Upgrade path

Upgrade from any earlier delivered Odoo 19 revision by replacing the module directory and running:

```bash
odoo-bin -d <staging_database> -u rental_management --stop-after-init
```

Use a recent database and filestore backup. Validate on staging before production.

## Data and schema impact

Version `19.0.1.0.7` does not:

- Rename or remove models.
- Rename or remove fields.
- Change Selection keys.
- Change XML IDs.
- Delete contracts, properties, schedules, invoices, commissions or maintenance requests.
- Add a new SQL column or database constraint.

No new migration directory is required for this hotfix. Existing migration scripts from earlier revisions remain in place.

## Functional reconciliation

Property-stage synchronization now evaluates all non-ended running contracts for each affected property:

```text
Current running contract -> on_lease
Future running contract only -> booked
No current/future running contract -> available
```

The update occurs during activation, closure, cancellation and lifecycle cron processing. It does not delete or rewrite contract history.

## Pre-upgrade checklist

1. Back up database and filestore.
2. Confirm the current custom module directory is named exactly `rental_management`.
3. Replace the complete module directory; do not merge individual files into an older copy.
4. Commit and rebuild Odoo.sh.
5. Run the focused test suite.
6. Upgrade a production-data staging copy.
7. Review properties with simultaneous current and future contracts to confirm `on_lease` precedence.
8. Review properties with only future contracts to confirm `booked` status.

## Rollback

If the upgrade fails, restore both the database and its matching filestore backup, then restore the previous module commit. Do not restore only one side of the database/filestore pair.
