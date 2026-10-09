# Changelog

## 1.36 - 2026-10-10

### Fixed

- Removed the eagle body ignore `0x0005`, which Pyre also uses on this shard. Pyre and other mobiles sharing this body are now eligible under the existing targeting rules.

## 1.35 - 2026-10-10

### Fixed

- Corrected the squirrel body ignore from `0x0114` to `0x0116`, allowing Rend and other reptalons to be targeted.
- Removed the incorrectly labeled crane body ignore `0x0119`, allowing minotaur scouts to be targeted.

## 1.34 - 2026-10-08

### Fixed

- Disabled the default mobile-body ignore for `0x02D0` (highland boura), which is also used by lava elementals. Hostile lava elementals are now eligible targets; highland boura sharing this body are also eligible under the existing targeting rules.

## 1.33 - 2026-10-05

### Added

- Opt-in `DF Low Stam` button under `3: Attacks`, disabled by default. Low-stamina Divine Fury no longer runs unconditionally.
- `DF Stam <:` text field and Save button for an absolute stamina threshold, defaulting to 180. Only positive whole numbers are accepted; casting occurs strictly below the saved value. Toggle and threshold are saved per character, independently of the existing pre-attack `DivineFury` option.
- Automatic recovery of the last equipped weapon after disarm, with one-second retries and tracking of the weapon hand and other equipped hand item.
- Regression tests for Blood Oath, disarm recovery, Honor targeting, pet commands, potion consumption, loot handling, Mirror Image release, Momentum Strike, and stamina settings/GUMP persistence.

### Changed

- Honor now selects the closest full-health eligible mobile within `HonorRange`, even when the current attack target is damaged. Combat runs before the Honor attempt; the target cursor is completed on later ticks without blocking for it. Existing Honored-buff gating remains in place.
- Refresh, Cure and emergency Heal potion cooldowns now start after consumption is confirmed. Rejected uses can retry after three seconds; missing-potion backpack lookups are throttled to once per second.
- Artifact discovery and moves are queued across ticks, with at most one property lookup per tick and moves paced 600 ms apart. Ten-second scans wait for pending queues to drain so large backpacks do not repeatedly restart unfinished scans.
- Chest of Heirlooms discovery and ground-drop attempts are queued across ticks, with 600 ms between actions and confirmation of the drop before advancing.
- Mirror Image release candidates are checked one per tick. Follower count is rechecked after the context-menu wait; the release cooldown starts only when a release is issued.
- Shared settings refresh runs before hidden Backstab continuation. Dress-list upkeep uses its own timer.
- Pet Sync avoids an existing target cursor, waits at most 300 ms for its command cursor, and retries the same target if no cursor arrives.

### Fixed

- Blood Oath prevents weapon-special pre-arming and clears readied abilities when combat is blocked.
- Enchanted Apple cooldown starts only after confirmed consumption. Rejected apple uses retry after three seconds and show a warning, without the previous one-second pause.
- Momentum Strike can be used against multiple targets when `Weapon Specials Off` is enabled. With weapon specials enabled, it remains a low-mana fallback; the GUMP tooltip now explains both modes.
- Same-graphic decoy items no longer prevent real Chests of Heirlooms from being found and dropped.
- Removed a duplicate Cutlass registration that overwrote the existing weapon configuration.

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
