# HOTFIX REPORT — rental_management 19.0.1.0.15

## Odoo 19 form-layout / Chatter correction

### User-visible defect

The Property Project form was compressed into a narrow strip while three large technical one2many tables were rendered across the form. The tables exposed raw mail internals such as related model/id/partner, activities, and messages.

### Root cause

Four form views still used the legacy chatter architecture:

```xml
<div class="oe_chatter">
    <field name="message_follower_ids"/>
    <field name="activity_ids"/>
    <field name="message_ids"/>
</div>
```

Under Odoo 19 these fields are rendered as ordinary relational fields instead of the modern Chatter semantic component, which breaks the form layout and exposes technical mail records.

### Correction

Replaced the legacy block with the Odoo 19 semantic component:

```xml
<chatter/>
```

Corrected forms:

- `property.project`
- `property.sub.project`
- `rent.invoice`
- `property.vendor`

The existing `property.details` and `tenancy.details` forms were already using the Odoo 19 `<chatter/>` component and were left unchanged.

### Regression protection

Added `tests/test_view_architecture.py`. It verifies at runtime that the four corrected forms:

- contain `<chatter`;
- contain no legacy `oe_chatter` block;
- do not expose raw `message_follower_ids` or `message_ids` in the form architecture.

No database schema, technical field, XML ID, contract lifecycle, accounting flow, dashboard visual, or security rule is changed by this UI hotfix.

## Dashboard preservation

All dashboard restoration work from 19.0.1.0.14 is preserved unchanged. The original TechKhedut dashboard XML/SCSS and restored chart libraries remain in the package.
