# components

Reusable Vue components live here.

## Structure

- `app/`: application shell pieces such as navigation and top status UI
- `common/`: view-agnostic building blocks shared by multiple workflows
- `datasets/`: dataset-specific drawers, tables, dialogs, and config
- `pools/`: pool-specific drawers, topology UI, dialogs, and config

## Layering

- `common/` should stay free of pool- or dataset-specific field names.
- `datasets/` and `pools/` can depend on `common/`, but should keep backend calls in the routed views.
- Routed views should assemble these components and own page-level state.
