# store

Compatibility adapter layer.

## Files

- `state.js`: exposes the historical `useAppState()` interface while delegating to the new Pinia store and API service layer

## Notes

- Transport-layer connection state is still separate from backend snapshot source state in `snapshot.meta`.
- New code should prefer `src/stores/app.js` for snapshot lifecycle and `src/services/api.js` for write requests.
