# UPGRADE REPORT — rental_management 19.0.1.0.12

## Version
- Technical module: `rental_management`
- Target: Odoo 19 Enterprise
- Final audited version: `19.0.1.0.12`
- License and original author metadata preserved.

## Main upgrade areas
- Odoo 19 manifest, products, views, actions, assets and cron compatibility
- Rental/property lifecycle state machine
- Contract overlap and activation/renewal/close/cancel rules
- Unified idempotent rent invoicing and catch-up cron processing
- Broker commission accounting
- Property sale booking/installments/refund lifecycle
- Multi-company enforcement
- Rental Officer / Rental Manager security
- Portal ownership and maintenance creation security
- Dashboard grouped/batched queries
- XLSX reports
- migration/data-preservation scripts
- automated test suite

## Full-audit additions in 19.0.1.0.12
- redesigned rental-linked Maintenance creation around explicit authorization + scoped privileged Core creation;
- fixed missing Maintenance Stage access for Portal and rental-only users without granting configuration access;
- separated duration unit from rent pricing unit;
- fixed dormant scheduled-action method references for measurement/address synchronization;
- hardened property and sale state changes against direct RPC manipulation;
- restored For Sale flow and corrected booking arithmetic;
- batched project/subproject statistics and property state validation;
- corrected tax/fiscal-position handling in broker accounting;
- made manual additional-charge schedules recoverable without misclassifying them as rent;
- corrected migration function signatures for Odoo 19;
- compared custom schema and selection keys against the original uploaded module to protect upgrade data.

## Runtime status
The previous Odoo.sh build loaded the module and executed the post-install suite, reaching 39 tests with 0 assertion failures and 3 Maintenance-related runtime errors. Those three root causes are addressed here. This exact 19.0.1.0.12 build has not been executed locally because an Odoo 19 Enterprise/PostgreSQL runtime is unavailable in this workspace.
