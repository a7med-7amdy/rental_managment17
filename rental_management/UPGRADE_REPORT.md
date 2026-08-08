# Upgrade Report — rental_management 19.0.1.0.13

## Scope
This release is a targeted stability and warning-cleanup release on top of the full Odoo 19 upgrade.

## Modified files
- `__manifest__.py`
- `wizard/extend_contract_wizard.py`
- `models/rent_contract.py`
- `models/maintenance.py`
- `models/sale_contract.py`
- `wizard/booking_wizard.py`
- `tests/test_contract_renewal.py`
- `tests/test_rent_invoicing.py`
- `tests/test_rental_contract.py`
- `i18n/ar_001.po`
- release documentation files

## Compatibility
- No model renamed.
- No persistent technical field renamed.
- No Selection key changed.
- No XML ID changed.
- No database column intentionally dropped.
- No Odoo Core modification.

## Behavioral changes
- Renewal wizard financial choices are independent wizard state, not inverse writes to the old contract.
- Active-contract financial protection remains strict.
- Runtime warning labels are unique and clearer.
- Stored related display-name fields explicitly disable translation storage inheritance to avoid Odoo multi-language computation warnings.

## Migration
No data migration script is required for 19.0.1.0.13. Registry upgrade is sufficient for the field metadata/string changes.
