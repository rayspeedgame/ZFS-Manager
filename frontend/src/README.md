# src

> [中文版本](./README.zh-CN.md)

`src/` contains Vue frontend source code.

## Structure

- `App.vue`: Root application shell and login gate toggle
- `main.js`: Application entry point
- `i18n/`: Locale initialization and translation resources
- `styles.css`: Global shared styles
- `components/`: Reusable UI components
- `lib/`: Formatting helpers
- `router/`: Router creation and metadata
- `services/`: REST API calls
- `store/`: Compatibility adapter layer
- `stores/`: Pinia stores
- `views/`: Route-level page containers

## Current Notes

- `PoolsView.vue` and `DatasetsView.vue` continue as page containers, responsible for API calls, live snapshot rebinding, and draft protection
- `SettingsView.vue` is responsible for settings read, save, SSH test, and login configuration editing
- `App.vue` is responsible for showing login interface or main application based on auth status
- `i18n/messages.js` is now just an aggregation entry point; real translation resources are located in `i18n/messages/<locale>/<module>.js`
- Route definitions continue to expose translation keys so sidebar and titles update immediately when switching languages
