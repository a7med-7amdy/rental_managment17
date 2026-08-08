# MIGRATION NOTES — rental_management 19.0.1.0.15

No database migration is required for this revision.

This revision changes only form-view XML and adds a regression test. Upgrade the module normally so Odoo reloads the corrected `ir.ui.view` architectures.

Recommended Odoo.sh procedure:

1. Deploy the complete 19.0.1.0.15 module directory.
2. Upgrade `rental_management` (do not only restart the service).
3. After the successful upgrade, reopen a Project record.
4. Confirm the business form uses the normal full width and the native Chatter appears in its standard Odoo position instead of three technical one2many tables.
5. Check Subprojects, Rent Invoices, and Property Sale records as the same legacy chatter markup was corrected there too.

No property, project, contract, invoice, maintenance, sale, portal, or accounting record is transformed by this revision.
