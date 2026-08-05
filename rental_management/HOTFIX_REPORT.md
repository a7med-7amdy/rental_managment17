# rental_management Odoo 19 Import Hotfix

## Package

- Previous version: `19.0.1.0.0`
- Corrected version: `19.0.1.0.1`
- Date: `2026-08-05`

## Runtime Failure

The Odoo.sh registry stopped while importing `models/property_details.py`:

```text
ModuleNotFoundError: No module named 'odoo.addons.web_editor'
```

## Root Cause

Odoo 19 no longer provides the Python package `odoo.addons.web_editor`. The video helper functions used by the module are available from `odoo.addons.html_editor.tools`.

## Files Corrected

- `__manifest__.py`
- `models/property_details.py`
- `models/property_project.py`
- `models/property_sub_project.py`
- `UPGRADE_REPORT.md`
- `TEST_REPORT.md`

## Technical Changes

1. Replaced all three obsolete imports with:

```python
from odoo.addons.html_editor.tools import get_video_embed_code, get_video_thumbnail
```

2. Added `html_editor` as an explicit manifest dependency.
3. Bumped the module version to `19.0.1.0.1`.
4. Corrected invalid-video errors to use `display_name` instead of an undefined `name` field on image-line models.

## Validation Status

The corrected package passed the static checks documented in `TEST_REPORT.md`. It still requires a new Odoo.sh staging build to confirm the next runtime load stage.
