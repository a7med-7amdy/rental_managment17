# HOTFIX REPORT — rental_management 19.0.1.0.14

## Dashboard restoration

The Odoo 19 upgrade had replaced the original TechKhedut dashboard with a simplified custom dashboard. This revision restores the dashboard shipped in the original `rental_management` 3.1.1 source package.

### Root cause

The upgraded dashboard assets were not a compatibility port of the original source:

- original `static/src/js/rental.js`: ~627 lines;
- upgraded simplified `rental.js`: ~88 lines;
- original `style.scss`: 123 lines;
- upgraded simplified `style.scss`: 39 lines;
- original chart libraries had been removed.

This was a redesign, not an Odoo 19 compatibility requirement.

### Correction

- Restored `static/src/xml/template.xml` exactly from the original 3.1.1 package.
- Restored `static/src/scss/style.scss` exactly from the original 3.1.1 package.
- Restored the original locally bundled chart libraries:
  - `index.js`
  - `xy.js`
  - `map.js`
  - `worldLow.js`
  - `Animated.js`
  - `Material.js`
  - `apexcharts.js`
- Reimplemented only the dashboard controller `rental.js` for Odoo 19 / OWL:
  - imports `Component`, lifecycle hooks, `useRef`, and `useState` from `@odoo/owl`;
  - uses Odoo services through `useService`;
  - uses Odoo 19 `loadJS` from `@web/core/assets`;
  - preserves the original client-action tag `property_dashboard`;
  - restores the original property type chart, broker chart, due/paid chart, property map, cards, and navigation actions;
  - disposes amCharts roots and ApexCharts instances on navigation/unmount to prevent browser memory leaks;
  - keeps all dashboard RPC data company-scoped and permission-aware through the already hardened server-side `get_property_stats()` implementation.

No business model, field, XML ID, state key, invoice, contract, or migration data is removed by this dashboard hotfix.
