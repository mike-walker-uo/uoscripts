# HuntTracker

HuntTracker is a real-time Ultima Online hunt tracker for Razor Enhanced-compatible
clients exposing the custom `Gumps.CreateGump` / `Gumps.GetGumpData` API. It tracks
kills, encounters, damage, active combat time, gold, configured loot, hunting
locations, goals, equipment warnings, session history, and personal records.

Version: **1.0.0**

## Highlights

- Fixed-rate 250 ms tracking loop and independent one-second gump refresh.
- Player, party, and pet tracking modes.
- Grace-period kill detection: a mobile leaving range is not immediately a kill.
- Strict, balanced, and permissive kill-confirmation policies.
- Active mob state is removed after each encounter; completed damage is accumulated.
- Combat time follows recent damage activity instead of nearby idle monsters.
- Live encounter name, duration, damage, DPS, peak DPS, and activity state.
- Per-monster kills, encounters, escapes, damage, average damage/DPS, average/best
  kill time, and last-kill time.
- Gold/hour, kills/hour, kills/minute, streaks, active/peak DPS, and estimated loot
  value/hour.
- Configurable item/hue loot counters and unit values.
- Map/coordinate buckets for comparing hunting locations.
- Four-page gump: Overview, Monsters, Loot, and Records, plus compact mode.
- Pause/resume, confirmed reset, save without exit, and stop controls.
- Configurable kill, gold, and duration goals with messages and optional sounds.
- Weight, gold-capacity, and equipped-item durability warnings.
- Automatic checkpoint recovery and saves on death, disconnect, error, or stop.
- JSON session archive plus correctly quoted UTF-8 encounter and monster CSV files.
- Persistent personal bests and rolling seven-session comparisons.

## Files

| File | Purpose |
| --- | --- |
| `HuntTracker.py` | Razor Enhanced entry point and gump. Run this file. |
| `hunttracker_core.py` | Client-independent tracking, persistence, and export logic. |
| `hunttracker_config.json` | Tracking, UI, goal, alert, loot, and save settings. |
| `test_hunttracker_core.py` | Offline regression tests. |
| `CHANGELOG.md` | Release history. |

At runtime HuntTracker creates ignored `data/` and `logs/` directories beside the
script.

## Installation

1. Copy the complete `HuntTracker` folder into your Razor Enhanced/NeoUO script
   directory.
2. Add `HuntTracker/HuntTracker.py` to the client script list.
3. Ensure the client's DPS Meter feature is available. HuntTracker starts it when
   required and pauses it again if HuntTracker was responsible for starting it.
4. Run `HuntTracker.py`.

Keep `HuntTracker.py`, `hunttracker_core.py`, and `hunttracker_config.json` in the
same directory.

## Gump controls

| Control | Action |
| --- | --- |
| Overview | Session totals, current encounter, and five recent kills. |
| Monsters | Top monsters with kills, average kill time, and damage. |
| Loot | Configured item counts, value, and value/hour. |
| Records | Personal bests, current-vs-seven-session averages, best hunt. |
| Pause | Stops time, combat, kill, gold, and loot accumulation until resumed. |
| Save | Writes/updates the current session without ending it. |
| Compact | Switches to a small live summary. |
| Reset | Requires a second click within three seconds. |
| Stop | Ends and saves the session, then closes HuntTracker. |

The last detected gump position is written to the config when the client exposes
position fields through `GetGumpData`. Some client builds do not provide those
fields; `ui.x` and `ui.y` remain the fallback.

## Tracking configuration

Edit `hunttracker_config.json` before starting the script.

| Setting | Meaning |
| --- | --- |
| `tick_ms` | World/DPS sampling interval. Minimum 50 ms; 250 is recommended. |
| `gump_refresh_ms` | UI redraw interval. Minimum 250 ms. |
| `mobile_range` | Maximum hostile tracking range in tiles. |
| `notorieties` | Razor notoriety codes: 3 gray, 4 criminal, 5 orange, 6 red. |
| `ignore_pets` | Uses the client filter to exclude your pets when supported. |
| `check_line_of_sight` | Excludes mobiles outside line of sight. |
| `exclude_humans` | Excludes human-bodied mobiles, including humanoid NPCs. |
| `ignored_names` | Case-insensitive name fragments to exclude. |
| `damage_mode` | `player`, `party`, or `pet`; described below. |
| `missing_grace_seconds` | Time a disappeared mobile may reappear before resolution. |
| `kill_confirmation` | `strict`, `balanced`, or `permissive`; described below. |
| `recent_damage_seconds` | Balanced-mode window for treating disappearance as death. |
| `combat_timeout_seconds` | Combat stays active this long after positive damage. |
| `location_grid_size` | Coordinate bucket size used for location comparisons. |

### Damage modes

- `player` uses only the positive change from `DPSMeter.GetDamage`. This is the
  recommended solo mode and avoids crediting damage done solely by other players.
- `party` uses the larger of DPS Meter damage and observed HP loss. It can count
  party damage the player meter did not attribute.
- `pet` currently uses the same observed-damage fallback as party mode. Use this
  when the client/shard does not attribute pet damage to the player's DPS Meter.

Observed `Mobile.Hits` can be a percentage rather than true hit points on some
servers. Consequently, party/pet damage and DPS may be relative values rather than
literal damage. Kill counts remain useful.

### Kill confirmation

- `strict`: requires zero last-known HP or the mobile's deleted flag. Lowest false
  positives, but it can miss kills when the server removes a mobile before a zero-HP
  sample arrives.
- `balanced`: requires tracked damage and either strict confirmation or recent
  damage immediately before disappearance. Recommended default.
- `permissive`: every damaged mobile still absent after the grace period is a kill.
  This can count fleeing or teleported mobiles.

No generic Razor Enhanced event distinguishes every death from every mobile leaving
client range. The configurable policies make that unavoidable shard/client tradeoff
explicit.

## Loot tracking

Add entries under `loot`:

```json
{
  "name": "Event Tokens",
  "item_id": 12345,
  "hue": -1,
  "unit_value": 500,
  "use_player_gold": false
}
```

- `item_id`: decimal UO item ID.
- `hue`: exact hue or `-1` for any hue.
- `unit_value`: estimated value per item; used only for totals and value/hour.
- `use_player_gold`: reads `Player.Gold` instead of counting an item ID. Normally
  only the built-in Gold entry should enable it.

HuntTracker records positive inventory deltas. Transfers into the backpack count as
gains. Items received and removed between two samples can be missed. Accurate
packet- or autoloot-event accounting would require a client/shard-specific adapter.

## Goals and warnings

Set any goal to `0` to disable it:

```json
"goals": {
  "kills": 100,
  "gold": 250000,
  "duration_minutes": 60
}
```

Alerts can use head messages and sound. `weight_percent`, `gold_capacity`, and
`durability_minimum` accept `0` to disable their respective warning.
`gold_capacity_warning_percent` controls how early the capacity warning appears.
Durability is
read from equipped-item property text such as `Durability 42 / 50`; custom wording
may not be recognized.

## Persistence and output

`data/HuntTracker_checkpoint.json` is refreshed during an active hunt. An interrupted
session is restored at startup when it is younger than `maximum_resume_age_hours`.

Each save writes these files under `logs/`:

- `HuntSession_<timestamp>.json`: complete summary, loot, monsters, locations, and
  encounters.
- `HuntSession_<timestamp>_encounters.csv`: one row per completed encounter.
- `HuntSession_<timestamp>_monsters.csv`: full per-monster breakdown, not only top 10.

Repeated manual saves update the same session files and history record. Personal
records are stored in `data/HuntTracker_history.json`.

## Offline tests

The core has no Razor Enhanced dependency:

```bash
python3 -m unittest -v test_hunttracker_core.py
```

Tests cover kill confirmation, disappearance/reappearance, solo/party attribution,
pause behavior, goals, checkpoint recovery, UTF-8 CSV quoting, and history records.

## Troubleshooting

### The gump never appears

Your client build may not expose the custom gump API used by the original script.
Confirm `Gumps.CreateGump`, `Gumps.SendGump`, and `Gumps.GetGumpData` are available.

### Kills are missing

Use `balanced` confirmation, increase `recent_damage_seconds`, or use `permissive`.
For pets/party play, change `damage_mode` from `player` to `pet` or `party`.

### Kills are too high

Use `balanced` or `strict`, increase `missing_grace_seconds`, enable line-of-sight,
reduce tracking range, exclude humans, or add problem names to `ignored_names`.

### Damage is always zero

Open the client's DPS Meter once and confirm it records damage. HuntTracker attempts
to start it automatically, but availability depends on the client build.

### A config error stops startup

Validate the JSON and compare the edited field with the supplied defaults. The
tracker deliberately reports invalid modes and unsafe refresh values instead of
silently choosing alternatives.

## Compatibility notes

The code avoids f-strings, dataclasses, type annotations, `pathlib`, and other newer
CPython-only syntax so it remains suitable for embedded IronPython 3.4 environments.
Client integration still depends on the APIs listed above and should be tested on
the target shard before relying on session totals.

Razor Enhanced references:

- [DPSMeter API](https://razorenhanced.readthedocs.io/api/DPSMeter.html)
- [Gumps API](https://razorenhanced.readthedocs.io/api/Gumps.html)
- [Mobiles.Filter API](https://razorenhanced.readthedocs.io/api/Mobiles_Filter.html)
- [Mobile properties](https://razorenhanced.readthedocs.io/api/Mobile.html)
