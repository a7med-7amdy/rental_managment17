# Test Report — rental_management 19.0.1.0.9

## Actual Odoo.sh evidence
### Run dated 2026-08-05 (previous full post-test pass-through)
Odoo executed 30 post-install tests. There were 0 assertion failures and 4 runtime errors: three commission `_check_company` signature collisions and one missing maintenance-team value. Those production defects were fixed in 19.0.1.0.8.

### Run dated 2026-08-07
The module again loaded through assets successfully. Post-install tests then stopped at the shared `RentalCommon.setUpClass`: five classes hit the same ACL error while creating `maintenance.team`. The runner halted at its maximum error threshold, so later tests were skipped.

## Fix in 19.0.1.0.9
The shared fixture no longer creates maintenance-team configuration. It reuses `rental_management.maintenance_team_rental`, which is loaded by module data. Two security regression tests were added.

## Static/package verification performed here
- Python compile: PASS
- XML parse: PASS
- Duplicate XML IDs: PASS
- Manifest file references: PASS
- JavaScript syntax: PASS
- CSV structure: PASS
- Deprecated `.read_group()` calls: none
- Custom `_check_company` override collision: none
- Old `<tree>`, `view_mode=tree`, `attrs`, `states`: none
- Test fixture direct `maintenance.team.create()`: removed except the intentional negative ACL regression test

## Runtime status
This environment does not contain a runnable Odoo 19 + PostgreSQL server. Therefore 19.0.1.0.9 has not been claimed as Runtime-passed here. The next Odoo.sh test-enabled build is the authoritative runtime verification.
