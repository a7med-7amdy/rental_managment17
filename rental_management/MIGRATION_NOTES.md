# MIGRATION NOTES — rental_management 19.0.1.0.14

This revision is a frontend/dashboard restoration and does not require a database schema migration.

Upgrade the module normally so Odoo regenerates `web.assets_backend` and the client action uses the restored dashboard template/controller.

Recommended Odoo.sh procedure:

1. Deploy the complete 19.0.1.0.14 module directory.
2. Upgrade `rental_management`.
3. Allow the build to regenerate assets.
4. Hard-refresh the browser once after deployment if an old browser asset bundle remains cached.
5. Open **Properties → Statistics** and verify the restored cards, property-type chart, rent due/paid chart, top-broker chart, and property-location map.

No contract/property/accounting data transformation is performed by this revision.
