# Changelog

All notable HuntTracker changes are documented here.

## 1.0.0 — 2026-08-29

### Added

- Modular, offline-testable tracking core and Razor Enhanced client adapter.
- Overview, Monsters, Loot, and Records gump pages plus compact mode.
- Live encounter duration, damage, current DPS, peak DPS, and activity state.
- Per-monster encounters, kills, escapes, damage, average damage/DPS, average/best
  kill time, and last-kill timestamp.
- Current/best kill streak and session peak DPS.
- Player, party, and pet damage modes.
- Strict, balanced, and permissive kill-confirmation policies.
- Configurable pet, human, line-of-sight, notoriety, range, and name filters.
- Pause/resume, save-without-exit, confirmed reset, and save-on-stop controls.
- Kill, gold, and duration goals with head-message and optional sound alerts.
- Weight, gold-capacity, and equipped-item durability warnings.
- Configurable item/hue loot counters with estimated values and value/hour.
- Location buckets with map, coordinates, time, kills, and damage.
- Automatic checkpoint recovery and configurable saves on death/disconnect/stop.
- Persistent session history, personal bests, and rolling seven-session comparisons.
- Full UTF-8 JSON, encounter CSV, and per-monster CSV exports.
- Eleven offline regression tests.

### Fixed

- Replaced `WaitForGump` as a timing mechanism with an explicit fixed-rate loop.
- Prevented the gump from causing unbounded mobile scans and redraws.
- Added disappearance grace time so briefly out-of-range mobiles can reappear.
- Required configured damage attribution before awarding kills.
- Stopped hiding from ending and repeatedly resetting the session.
- Stopped death from creating a new session every three seconds.
- Replaced nearby-hostile time with recent-damage-based active combat time.
- Removed completed mobiles from active dictionaries and accumulated finalized damage.
- Updated initially unknown mobile names when the client later supplies a name.
- Added deterministic monster ranking for equal kill counts.
- Exported all monsters instead of discarding everything below the top ten.
- Added correct CSV quoting for commas, quotes, and non-ASCII monster names.
- Preserved/restored DPS Meter ownership and added cleanup on exit/error.
- Replaced broad silent failures in the main path with one-time client messages.
- Added a UTF-8 source declaration and IronPython 3.4-compatible syntax.

### Changed

- Gold is documented as observed positive backpack gold rather than guaranteed loot.
- Average DPS now uses active combat time controlled by `combat_timeout_seconds`.
- The original single-file 0.1 tracker is superseded by the `HuntTracker/` release
  folder; the source file outside this folder remains untouched.
