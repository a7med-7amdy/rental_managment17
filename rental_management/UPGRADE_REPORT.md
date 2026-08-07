# UPGRADE REPORT — rental_management 19.0.1.0.10

This revision continues the Odoo 19 Enterprise migration and addresses the latest Odoo.sh runtime security failure.

## Changed files
- `__manifest__.py` — version bumped to 19.0.1.0.10
- `security/ir.model.access.csv` — explicit Rental Officer/Manager access to `maintenance.request`
- `tests/test_security.py` — added officer maintenance-request regression test
- Reports updated for this hotfix

## Security behavior
### Rental Officer
- Maintenance Request: read/create/write allowed
- Maintenance Request: delete denied
- Maintenance Team administration: denied

### Rental Manager
- Includes Rental Officer privileges
- Maintenance Request: read/create/write allowed
- Maintenance Request: delete denied
- Maintenance Team administration: denied

### Portal
- Maintenance Request: read/create only
- Ownership rule restricts records to the signed-in tenant's contracts

### Multi-company
The existing global company rule continues to limit maintenance requests to `allowed_company_ids`.
