# rental_management Odoo 19 Registry Hotfix

## Package

- Previous package: `19.0.1.0.1`
- Corrected package: `19.0.1.0.2`
- Date: `2026-08-05`

## Runtime Evidence Received

The second Odoo.sh attempt passed the previous `web_editor` import failure and reached model registration. The supplied log then showed:

- reStructuredText parser warnings (`Unexpected indentation`).
- six duplicate field-label warnings.
- `Failed to load registry` without the subsequent exception traceback.

The duplicate-label messages are warnings; the supplied excerpt does not include the fatal exception that followed registry failure. This hotfix therefore addresses every visible issue and also removes a schema constraint that could reject valid legacy draft/history data during upgrade.

## Changes

### Manifest description

Replaced the indented bullet-list manifest description with a plain valid description and summary. This avoids module-description parser warnings without changing functionality.

### Duplicate field labels

Changed display labels only; technical field names and stored data are unchanged:

- `res.partner.properties_ids`: `Rental Properties`.
- `tenancy.details.commission`: `Calculated Broker Commission`.
- `tenancy.details.broker_commission`: `Fixed Broker Commission`.
- `crm.lead.sale_lease`: `Selected Property For`.
- `crm.lead.domain_sale_lease`: `Requested Property For`.
- `crm.lead.price`: `Selected Property Price`.
- `crm.lead.property_price`: `Requested Property Price`.
- `contract.wizard.is_extra_service`: `Has Utility Services`.
- `contract.wizard.services`: `Utility Service Summary`.
- `contract.wizard.duration_ids`: `Allowed Durations`.

### Upgrade-safe SQL validation

Removed strict SQL `CHECK` declarations from legacy business tables where pre-existing draft/history records can legitimately contain incomplete values. Equivalent business validation remains in Python when records are edited and when a contract is activated.

Added:

```text
migrations/19.0.1.0.2/pre-migration.py
migrations/19.0.1.0.2/post-migration.py
```

The pre-migration drops only the obsolete named constraints if present. It does not delete or rewrite any property, contract, invoice, payment, or accounting entry. The post-migration logs incomplete legacy contracts for manual review.

## Validation Executed

- Python compilation: passed for 45 files.
- XML parsing: passed for 56 files.
- JavaScript syntax: passed.
- Manifest data and asset references: passed.
- CSV shape validation: passed.
- Duplicate explicit labels within custom models: none detected.
- Obsolete `web_editor` imports: none detected.
- Old `<tree>`, `attrs=`, and `states=` architecture: none detected.

## Runtime Limitation

No Odoo 19 runtime exists in this workspace. The corrected package must be rebuilt on Odoo.sh. If the registry still fails, the complete traceback immediately after `Failed to load registry` is required; warnings alone do not identify the fatal exception.
