# UO Ultimate Mage Attack Script

By Mike|Walker

An all-in-one Razor Enhanced combat script for Mage, Mystic, Necromancer, Spellweaver, Bard, Tamer and summoner templates. It was mainly developed and tested on UOAlive, so shard rules, journal text and spell behavior may differ elsewhere.

## Requirements

- Razor Enhanced 0.8.2.215 or newer.
- ClassicUO with the Razor Enhanced plugin.
- Windows for the legendary/astral spawn sound alarm (`winsound`).
- `MageAttackScript_MikeWalker.py` and `MageAttackScript_MikeWalker_GUMP.py` stored in the same script folder.
- Required skills, mana, spellbooks, masteries, expansions and items for the options you enable.

## Setup

1. Add both Python files to the Razor Enhanced Scripts list.
2. Start `MageAttackScript_MikeWalker.py` first.
3. Set `MageAttackScript_MikeWalker_GUMP.py` to Loop mode and start it.
4. Configure options in the GUMP and press `SaveSettings`.

The attack script loads the current character's saved settings when it starts. GUMP changes reach the running attack script immediately. `Attack Off` pauses offensive targeting while healing and safety handling remain available.

The GUMP includes three starting presets:

- `Trash`: fast and mana-efficient attacks with expensive debuffs reduced.
- `Boss`: stronger nukes, debuffs and defensive buffs.
- `Solo`: summons and defensive options for unsupported play.

Presets are starting points. Review enabled spells before entering combat.

## Character profiles

Settings are stored beside the scripts in a separate file for each character:

```text
mage_settings_<character>_<serial>.json
```

The character serial prevents characters with the same name from sharing settings. An old `mage_settings.json` file is imported and migrated automatically when no character profile exists.

These local files contain the character name, serial and personal preferences. Keep `mage_settings.json` and `mage_settings_*.json` out of Git.

## Combat priority and recovery

The main loop gives survival and cast-state recovery priority over offense:

1. Detect server cast failures, fizzles and interruptions.
2. Resolve an existing target cursor before starting another spell.
3. Handle Paralyze and Blood Oath safety.
4. Heal or cure the player, then care for pets.
5. Run maintenance and legendary/astral checks.
6. Manage required summons.
7. Select a fresh visible hostile and cast buffs, debuffs or attacks.

Damage and the journal's disturbed-cast message release healing quickly after an interrupted spell. Busy messages such as `You are already casting a spell` and `You must wait to perform another action` are tracked so the script can recover without repeatedly stacking casts. Target waits account for cast speed and can tolerate temporary lag.

Only the newest running attack-script instance owns combat. Starting a new copy makes an older copy stop instead of letting both copies compete for target cursors.

## Targeting and line of sight

- `AttackRange` controls the maximum target distance.
- `MultiThreshold` and `MassThreshold` control when the script switches to multi-target or mass-area spells.
- `HonorRange` controls the maximum Honor distance.
- The nearest current visible hostile is selected; a previously selected or low-health distant target is not retained when a nearer mob appears.
- Target lists are rebuilt during the combat cycle and again immediately before the offensive spell.
- Harmful targeted spells use a line-of-sight check. A mobile rejected for line of sight is reconsidered after it moves.
- Blue mobiles, red humans and blue changelings are excluded by default unless their options are enabled.
- Distance markers and the optional status overlay show current combat state without changing target selection.

Enabling blue or red-human attacks can target players or unintended mobiles. Use those options carefully.

## Spell selection

The GUMP separates spells into single-target, multi-target, mass-target, debuff, buff, summon and mastery groups. Options are available for Magery, Mysticism, Necromancy and Spellweaving.

Single-target selection can use MOBSLIST resistance data, prioritize enabled spells matching the target's weakest resistance and avoid expensive nukes on low-HP trash. Low-mana mode reserves resources, while the optional nuke cascade favors a strong follow-up after Evil Omen or Corpse Skin.

Available attacks include Magery circles, Word of Death, Eagle Strike, Bombard, Nether Cyclone, Hail Storm, Spell Plague, Wither, Poison Strike, Thunderstorm, Wildfire, Earthquake and an Explosion follow-up combo. The script falls back to another enabled spell when the preferred category is unavailable.

Debuff options include Evil Omen, Curse, Corpse Skin, Strangle, Mind Rot, Poison, Sleep, Mass Sleep, Paralyze and Mana Vampire. Expensive debuffs can be skipped on trash targets.

## Nether Blast

Nether Blast has dedicated placement and recovery logic:

- Cooldown is 5100 ms from cast start to cast start.
- Directional alignment is checked before casting against a single target.
- Optional green client-side markers show valid casting tiles.
- Optional auto-move selects a valid tile only when HP and safety checks allow movement.
- The target's coordinates are saved before casting. If the mobile dies while the cursor is opening, the field is placed at its last known `(x, y, z)` position instead of being cancelled.
- Failed, interrupted or delayed casts release their synthetic state and retry without requiring a script restart.

Ground markers use client-only packets through Razor Enhanced's `PacketLogger`; disable `NBShowTiles` if a different client/plugin build does not support them.

## Summons

Supported summons include Rising Colossus, Summon Creature, elemental summons, Summon Daemon, Blade Spirits, Energy Vortex, Summon Fey, Summon Fiend and Summon Reaper.

- While safe, regular summons wait for Arcane Empowerment.
- When hostile mobiles are nearby, summons bypass that wait so defense is not delayed.
- Rising Colossus requires three free follower slots on UOAlive.
- Colossus placement cycles through nearby tiles when a location is blocked.
- A failed required summon blocks offense for that cycle instead of attacking without the requested summon.
- Follower updates receive confirmation time before another summon is attempted.
- `all guard me` is delayed until a successful summon has had time to appear.

Follower thresholds are configurable per summon type.

## Slayer spellbooks

The Slayer Books section scans equipped items and the backpack for Magery, Necromancy, Spellweaving and Mysticism books. No personal item serials are stored in the script.

- Manual buttons request a safe book swap between casts.
- Auto-Swap equips a matching book for Reptile, Dragon, Repond, Fey, Undead, Elemental, Demon or Arachnid targets.
- A non-slayer Magery book can be restored when no slayer group matches.
- The target list is rebuilt after a swap before an offensive spell is chosen.

## Healing, curing and buffs

- Player healing starts as soon as cast interruption is confirmed after damage.
- Emergency poison handling uses Magery Cure first, then Arch Cure, then Cleansing Winds when available.
- Cleansing Winds can also remove configured harmful debuffs.
- Optional defensive maintenance includes Magic Reflect, Reactive Armor, Protection, Bless, Attune Weapon, Gift of Life, Gift of Renewal, Arcane Empowerment and mastery buffs.
- Supported forms include Reaper Form, Wraith Form, Lich Form, Vampiric Embrace and Stone Form.
- Gift of Renewal uses a 180-second retry interval for both player and pet handling.
- Pet support includes bandages, Magery healing, Cleansing Winds, Bless, Gift of Life and Gift of Renewal.
- Razor Enhanced's Bandage Agent and currently selected Dress list can be maintained from GUMP options.

## Bard and Tamer support

Bard options include Discordance, Peacemaking, Area Peacemaking, Provocation and the Resilience, Perseverance, Inspire, Invigorate, Tribulation and Despair masteries. Instrument checks warn when no usable instrument is found.

Tamer options support player Bandage Agent control, configurable pet-heal thresholds, pet cure, Bless and Spellweaving gifts. Pet target cursors are owned and resolved before another spell can begin.

## Safety and supplies

- Legendary and astral spawn journal alerts show repeated warnings and run a blocking alarm. Combat remains blocked during the alert to reduce the risk of killing a spawned pet.
- Rare mobiles can be marked, and an optional setting stops combat when one appears.
- Blood Oath handling warns the player and leaves War mode.
- A trapped crate can break Paralyze.
- Bag of Sending support sends gold when the character approaches the weight limit.
- Bandage, instrument, town-buff and Arcane Focus checks run on throttled maintenance timers.
- Player, pet, summon and common harmless-mobile filters reduce accidental targeting.

## UOAlive and client-specific behavior

This release is designed for UOAlive and English spell, buff, item and journal names. Important shard/client assumptions include:

- Rising Colossus consumes three follower slots.
- Razor Enhanced exposes some buff names with its own spelling, which the script handles internally.
- MOBSLIST health, resistance and slayer data may differ on another shard.
- Journal-based recovery and alerts require matching English server messages.
- Sound alarms require Windows `winsound`.

If using another shard, begin with offensive options disabled and verify spell names, follower costs, journal text and target rules before enabling automatic combat.
