# Changelog

## 1.32 - 2026-08-28

### Added

- Per-character settings and slayer profiles.
- Slayer weapon and talisman management in the main GUMP.
- Mirror Image, White Tiger Form, Death Strike, Focus Attack and Backstab options.
- Smoke and Egg Bomb support for the Backstab cycle.
- Artifact loot-bag handling and Chest of Heirlooms dropping.
- Permanent per-character target ignores.
- Pet target synchronization and automatic potion handling.

### Changed

- Weapon abilities can be chained on successive swings.
- Lightning Strike and Momentum Strike are now mana-aware fallbacks.
- Blood Oath combat is restricted to Whirlwind against more than two enemies.
- Artifact and heirloom scans now run every ten seconds.
- Settings, targeting and backpack scans were optimized.

### Fixed

- Enchanted Apples are detected by item ID and used only for Blood Oath.
- Weapon abilities are no longer overwritten by Bushido or Ninjitsu moves.
- Attack filters include previously missed hostile mobile bodies.
- Transient targeting and deleted-mobile errors no longer stop the script.
