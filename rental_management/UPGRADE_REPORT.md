# UPGRADE REPORT — rental_management 19.0.1.0.14

Version 19.0.1.0.14 restores the visual dashboard from the original TechKhedut `rental_management` 3.1.1 source while keeping the Odoo 19 backend, security, multi-company, invoicing, portal, maintenance, and lifecycle fixes delivered in the previous revisions.

The dashboard XML and SCSS are restored from the original package. The legacy JavaScript controller itself is not copied unchanged because it relied on older OWL globals/imports; it is ported to the Odoo 19 frontend APIs while preserving the original UI behavior.

The original local graph libraries are restored and loaded dynamically through Odoo's frontend asset loader. Existing Odoo 19 dashboard statistics remain permission-aware and company-scoped.
