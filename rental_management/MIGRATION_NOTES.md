# MIGRATION NOTES — 19.0.1.0.10

No schema or data migration is required for this hotfix.

The change is an ACL update plus test coverage. Run a normal module upgrade so Odoo reloads `security/ir.model.access.csv`.

Recommended procedure:
1. Back up the database before upgrade.
2. Deploy version 19.0.1.0.10.
3. Upgrade `rental_management`.
4. Run post-install tests.
5. Confirm Rental Officer and Rental Manager can create maintenance requests but cannot delete them.
6. Confirm Portal users can create requests only for their own running rental contracts.
