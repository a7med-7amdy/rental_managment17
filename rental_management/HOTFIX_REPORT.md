# Hotfix Report — 19.0.1.0.4

## Runtime failure

Odoo 19 rejected the rental contract search view while loading `views/tenancy_details_view.xml`:

```text
RELAXNG_ERR_INVALIDATTR: Invalid attribute expand for element group
Invalid view tenancy.details.search.view definition
```

## Root cause

The search view used the legacy group-by container:

```xml
<group expand="0" string="Group By">
```

The Odoo 19 search-view schema accepts the `group` element as a structural container, but the legacy `expand` attribute is not valid there.

## Changes

- Replaced the legacy search group with a plain `<group>` in:
  - `views/tenancy_details_view.xml`
  - `views/property_project_view.xml`
  - `views/property_sub_project_views.xml`
- Updated the **Expiring Soon** filter to use `relativedelta(days=30)` instead of `datetime.timedelta(days=30)`, matching the search-domain evaluation context.
- Preserved all view XML IDs, filter names, domains, group-by fields, and search-panel fields.
- Bumped the module version from `19.0.1.0.3` to `19.0.1.0.4`.

## Static verification

- Parsed every XML file with `lxml`.
- Confirmed every search view contains only supported direct child elements.
- Confirmed no `<search><group ...>` element retains attributes.
- Confirmed no legacy `<tree>`, `view_mode="tree"`, `attrs`, or `states` patterns remain.
- Compiled every Python file.
- Checked JavaScript syntax with Node.js.
- Tested the final ZIP CRC and inspected the extracted delivery copy.

## Runtime status

This hotfix directly addresses the RelaxNG traceback supplied from Odoo.sh. Full Odoo 19 runtime installation was not executed locally because this workspace does not contain an Odoo 19 server and PostgreSQL test database.
