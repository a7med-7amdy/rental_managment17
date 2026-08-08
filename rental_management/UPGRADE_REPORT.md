# UPGRADE REPORT — rental_management 19.0.1.0.15

Version 19.0.1.0.15 is an Odoo 19 form-architecture compatibility hotfix on top of 19.0.1.0.14.

It fixes the legacy mail chatter markup that caused Project/Subproject/Rent Invoice/Property Sale forms to render raw followers, activities and messages as one2many tables and squeeze the business form content.

The four affected forms now use the native Odoo 19 `<chatter/>` semantic component. Existing business logic, security, multi-company behavior, accounting, portal behavior, migrations, restored original dashboard, chart libraries, and technical model/field names are preserved.

A regression test was added so future upgrades cannot silently reintroduce the legacy chatter block.
