# Hotfix Report — 19.0.1.0.3

## Runtime failure addressed

Odoo 19 stopped while loading `data/property_product_data.xml` because the legacy external ID below no longer exists:

```text
product.product_category_all
```

## Changes

- Replaced the removed category reference with the Odoo 19 service category:

  ```text
  product.product_category_services
  ```

- Replaced the removed `product.template` field `detailed_type` with the Odoo 19 field `type` for all rental and maintenance service products.
- Preserved all existing rental module XML IDs, including `rental_management.product_category_property` and all product records.
- Bumped the module version from `19.0.1.0.2` to `19.0.1.0.3`.

## Data safety

No business model, field technical name, product XML ID, contract, invoice, property, or accounting record was deleted or renamed.

## Validation performed

- Python compilation.
- XML parsing.
- Manifest parsing.
- JavaScript syntax validation.
- Search for removed `product.product_category_all` references.
- Search for removed `detailed_type` XML fields.
- ZIP CRC validation after packaging.

## Runtime limitation

The local workspace does not contain an executable Odoo 19 server, so the clean-install and upgrade commands were not run locally. The changes directly address the runtime traceback and the next incompatible product field found in the same data file.

- Added `product` as an explicit manifest dependency because the module directly references product models, views, categories, and data.
