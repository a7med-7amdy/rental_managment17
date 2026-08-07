# Migration Notes — rental_management 19.0.1.0.8

## Upgrade path

Upgrade from 19.0.1.0.7 to 19.0.1.0.8 using the normal module upgrade process.

## Database impact

This revision has no destructive schema migration.

It does not rename or delete:

- Models.
- Existing fields/columns.
- Selection keys.
- Existing XML IDs.
- Contracts.
- Properties.
- Accounting invoices/bills.
- Rental invoice periods.
- Sequences.

## Additive data

A single shared Maintenance Team is added as module data:

```text
XML ID: rental_management.maintenance_team_rental
Name: Rental Maintenance
Company: Shared / False
noupdate: True
```

It is a fallback only. When an active company-specific Maintenance Team exists, rental maintenance requests use the company-specific team first.

## Existing migration scripts

The earlier migration scripts under `migrations/19.0.1.0.0/` and `migrations/19.0.1.0.2/` remain unchanged. No `19.0.1.0.8` migration script is required because this hotfix does not rename schema objects or transform existing business data.

## Recommended production procedure

1. Take a full database and filestore backup.
2. Deploy 19.0.1.0.8 to a staging branch/database copied from production.
3. Upgrade `rental_management` with tests enabled.
4. Confirm the complete rental test suite has zero failures/errors.
5. Verify an internal user and a portal tenant can create a maintenance request.
6. Verify tenant/landlord/both broker commission activation creates one rental contract and the expected accounting documents.
7. Verify dashboard load has no `read_group` deprecation warnings.
8. Promote the same commit to production only after staging acceptance.
