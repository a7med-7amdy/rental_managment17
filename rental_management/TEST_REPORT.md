# TEST REPORT — rental_management 19.0.1.0.12

## Latest real Odoo.sh evidence supplied
The latest supplied Odoo.sh run for the previous build reached 39 post-install tests and reported:

- assertion failures: 0
- runtime errors: 3
- all three errors: rental-linked Maintenance Request creation / Maintenance Stage access

Those errors are the primary runtime target of 19.0.1.0.12 and are addressed by explicit authorization followed by narrowly-scoped privileged creation for rental-linked requests.

## Automated tests included in 19.0.1.0.12
45 test methods are included across the test suite. Coverage includes:

- property rental lifecycle;
- required activation fields;
- overlap prevention;
- monthly, quarterly, yearly and full-payment invoicing;
- missed cron catch-up and idempotency;
- contract month-end anchoring;
- duration-unit vs pricing-unit separation;
- manual service schedule recovery;
- renewal links and next-day dates;
- close / cancel protections;
- broker commissions from tenant, landlord and both;
- Rental Officer / Rental Manager / internal / public permissions;
- maintenance creation including default Team/Stage and caller `create_uid`;
- multi-company visibility and dashboard isolation;
- portal ownership and maintenance ownership;
- upgrade-data preservation;
- property sale booking / refund lifecycle and direct-state protection.

## Static checks executed in this environment
- Python compilation / AST parsing
- XML parsing
- manifest file-reference validation
- CSV / ACL validation
- duplicate XML ID check
- custom-model ACL coverage check
- custom compute/inverse/search method existence check
- custom Cron / action target checks
- local `env.ref()` check
- JavaScript syntax (`node --check`)
- migration signature check
- original-vs-upgraded custom model/field/selection comparison
- deprecated-pattern scan
- compiled/cache-file cleanup check
- ZIP CRC and independent extraction validation

## Runtime limitation
This environment does not contain a complete Odoo 19 Enterprise server and PostgreSQL database, therefore 19.0.1.0.12 itself has not been executed locally with `odoo-bin`. The next Odoo.sh build is the authoritative runtime verification. No report claims runtime success that was not actually observed.
