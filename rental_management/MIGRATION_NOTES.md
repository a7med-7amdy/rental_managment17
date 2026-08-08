# Migration Notes — 19.0.1.0.13

## Upgrade path
Upgrade normally from the previous `rental_management` build with `-u rental_management` or the Odoo.sh module upgrade flow.

## Data safety
This release does not rename/drop persistent models, fields, XML IDs, contract states, invoice links, sequences, or accounting records.

The renewal wizard changes affect only the transient wizard model. Existing rental contracts are not rewritten.

Stored related display fields keep the same technical names and remain stored; only translation metadata/UI labels were corrected.

## Before production upgrade
1. Take a database and filestore backup.
2. Run the upgrade on staging.
3. Run the full module test suite.
4. Verify one renewal, one automatic missed-invoice catch-up, one portal maintenance request, and one multi-company switch.
