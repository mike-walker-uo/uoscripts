# Changelog

## 0.52 - 2026-10-22

### Added

- Saved, opt-in `Attack Lighthouses` button under `5: Single Target`. Attacks Plunder Beacons and Blackthorn lighthouses within `AttackRange`, including intact and damaged graphics (`0x4724`, `0x9983`, `0x9984`). Hostile mobiles keep priority.
- Lighthouse attacks use enabled Magery/Mysticism direct-damage spells, respecting mana, skills, low-mana mode, spell recovery and Blood Oath. Item targets are revalidated when the cursor arrives; mobile-only spells, Honor and debuffs are excluded.
- Offline regression tests for mage reliability, shared action ownership, lighthouse settings and item-targeted casts.

### Changed

This release also publishes the local 0.49–0.51 reliability updates:

- Targeted spells retain ownership of late cursors and verify successful target consumption. Each cast has a bounded recovery watchdog; routine buffs defer during combat.
- Word of Death and Nether Blast follow-up attacks take priority over another mastery cast. Failed Nether Blast attempts release their pending state without extending the 5100 ms limit.
- Debuff cooldowns are tracked per mobile. Server line-of-sight rejections are retried after player or target movement.
- Mage casts and item/equipment actions coordinate through shared inventory/combat timers. Compatible helper scripts can yield; the mage script and GUMP still work standalone.
- Character profiles save atomically. GUMP changes use a revision signal, with a fallback refresh for external settings changes.

### Fixed

- Generic action-wait messages no longer renew spell locks indefinitely or falsely report an interrupted cast.
- Rejected, interrupted and delayed casts release or retain their cooldowns and cursor ownership according to the actual server response.
- Routine buffs, repeated book swaps and failed summons no longer crowd out offensive spells in the same loop.

## 0.48 - 2026-08-28

Initial public GitHub release.

### Added

- Per-character settings with automatic migration from the legacy shared profile.
- Integrated GUMP controls for Mage, Mystic, Necromancer, Spellweaver, Bard, Tamer and summoner templates.
- Trash, Boss and Solo configuration presets.
- Manual and automatic slayer spellbook swapping.
- Rising Colossus, Summon Creature, elemental, daemon, vortex, fey, fiend and mastery summon management.
- Nether Blast alignment hints, optional tile markers and optional safe auto-movement.
- Player and pet healing, curing, buffs and Spellweaving gifts.

### Changed

- Combat now rebuilds and line-of-sight checks targets before offensive casts.
- The nearest current visible hostile replaces stale or distant cached targets.
- Summons wait for Arcane Empowerment while safe but bypass that wait when hostiles are nearby.
- Settings refreshes, skill lookups and mobile scans were optimized without caching combat targets.
- Spell and target waits account for Faster Casting, Faster Cast Recovery and temporary lag.

### Fixed

- Interrupted, fizzled, busy and stuck cast states recover without restarting the script.
- Healing begins quickly after damage interrupts the active spell.
- Emergency cure priority is Magery Cure, Arch Cure, then Cleansing Winds.
- Rising Colossus requires three free follower slots and retries blocked placement tiles safely.
- Nether Blast uses a 5100 ms cast-start cooldown and targets the saved tile if the mobile dies during casting.
- Gift of Renewal uses a 180-second retry interval and resolves its pet target cursor before another spell starts.
- Offensive spells do not target mobiles without line of sight.
- Legendary and astral spawn alerts block combat to protect spawned pets.
