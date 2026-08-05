# Hotfix Report — 19.0.1.0.5

## Trigger

The Odoo 19 Enterprise post-install test suite reached the module tests but stopped during `RentalCommon.setUpClass()` with five identical errors:

```text
ValueError: Invalid field 'lst_price' in 'product.template'
```

The failing fixture used:

```python
cls.product_a.copy({"name": "Rent Product", "lst_price": 1000.0})
```

In Odoo 19, copying a `product.product` copies its underlying `product.template`. The copy defaults are forwarded to the template create operation, where `lst_price` is not a valid field. The variant field remains `lst_price`, while the template field is `list_price`.

## Fix

Updated `tests/common.py` to create dedicated test products through the Odoo 19 test helper inherited from `AccountTestInvoicingCommon`:

```python
cls._create_product(name="Rent Product", lst_price=1000.0, type="service")
```

The change covers all five shared products:

- Rent Product
- Deposit Product
- Broker Product
- Recurring Service
- Maintenance

The recurring-service flag is now supplied during creation, and the maintenance template flag is set immediately after creation.

## Scope

- Test fixture only.
- No production model, field, view, XML ID, security rule, accounting logic, or business data changed.
- No migration script is required.
- Module version bumped from `19.0.1.0.4` to `19.0.1.0.5`.

## Verification

- No `product_a.copy(... lst_price ...)` pattern remains.
- Python compilation passed.
- XML parsing passed.
- JavaScript syntax validation passed.
- Manifest references passed.
- ZIP CRC validation passed.

The complete Odoo test suite must be rerun on Odoo.sh. The previous suite stopped at the configured five-error threshold, so later runtime assertions were not executed.
