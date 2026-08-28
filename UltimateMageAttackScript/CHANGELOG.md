# Changelog

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
