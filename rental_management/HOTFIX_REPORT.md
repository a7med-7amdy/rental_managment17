# Rental Management Odoo 19 — Hotfix Report

## Release
- Module: `rental_management`
- Version: `19.0.1.0.13`
- Date: 2026-08-08

## Runtime baseline
The previous `19.0.1.0.12` Odoo.sh run executed all 45 module tests and ended with 0 assertion failures and 2 runtime errors:
1. Renewal wizard creation inverse-wrote `payment_term` / installment mode onto an already active source contract.
2. The missed-cron test changed installment mode after activation, correctly triggering the production contract lock.

## Root-cause fixes
### Renewal wizard
`payment_term` and `installment_mode` were writable related fields. On a TransientModel, assigning them caused Odoo's related-field inverse to write to the active `tenancy.details` record during wizard creation.

They are now independent Selection fields on the wizard. `default_get()` and the tenancy onchange populate them from the source contract. The new contract receives the selected values, while the source contract is never modified.

No generic context bypass was added to `tenancy.details.write()`; the post-activation financial lock remains enforced.

### Missed cron test
The test now creates the contract with `type='automatic'` before activation. It no longer mutates protected financial configuration on a running contract.

### Warning cleanup
All module-origin warnings shown in the last Odoo.sh log were addressed:
- Stored related translated Char fields now explicitly use `translate=False` while retaining their stored schema and technical field names.
- Duplicate UI labels were disambiguated without changing technical field names:
  - Project Name / Subproject Name
  - Region Name
  - Maintenance Type Name / Maintenance Stage Name
  - Tax Names
  - CRM Enquiry / Sale Enquiry
- Arabic translations were added for the new labels.

## Regression coverage
- Renewal test now proves wizard values do not mutate the active source contract.
- Renewal can select a different payment term/installment mode for the new draft.
- A new test proves protected financial terms still cannot be edited after activation.
- Total automated test methods included: 46.

## External warning
The recurring `res.partner.email_normalized` reStructuredText warning is produced by Odoo's official `mail` module manifest, not by `rental_management`. No Odoo Core file is modified by this release.
