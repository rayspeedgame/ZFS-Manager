# Target

## Current Product Goal

Build ZFS Manager into a practical web UI for a single host or small home-lab deployment, so an operator can complete common pool and dataset workflows without dropping to the shell for every task.

## Shipped Capabilities

### Pool workflows

- Pool status and health overview
- Editable pool properties
- Topology visualization
- Add devices to `log`, `cache`, `special`, `dedup`, and `spare`
- Create a new pool with:
  - pool properties
  - root dataset properties
  - staged data vdev planning
  - staged auxiliary vdev planning
- Destroy a pool
- Remove supported topology targets
- Prefer stable by-id presentation when available

### Dataset workflows

- Dataset and zvol inventory
- Expandable dataset tree
- Optional snapshot display
- Create dataset and zvol children
- Edit dataset properties
- Destroy dataset and zvol entries

### UI capabilities

- English and Simplified Chinese locale switching
- Browser-language based first-load locale detection
- Persisted locale preference in the frontend
- Translated shell navigation, dashboard, pool workflows, dataset workflows, dialogs, and command-result panels

## Frontend Direction

- `PoolsView` and `DatasetsView` are now page containers instead of giant all-in-one templates.
- Shared property editors, command results, and command logs are centralized under `frontend/src/components/common/`.
- Pool-specific and dataset-specific workflow UIs live under their own component folders.
- Live snapshot refreshes should update visible data without wiping in-progress edits.
- User-visible frontend copy should be sourced from translation keys so new locales can be added without refactoring the shell or views.

## Next Steps

- Add more topology actions such as `replace`, `detach`, and `offline/online`
- Expand SMART and disk-health integration
- Add finer-grained permission handling
- Continue splitting large workflow logic into smaller composable units where it improves clarity
- Expand locale coverage for any future frontend additions as they are introduced
