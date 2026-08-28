### UO Ultimate Mage & Summoner Attack Script GUMP by Mike|Walker ##########
### https://github.com/mike-walker-uo/uoscripts/tree/main/UltimateMageAttackScript
### Version 0.48 last edit 03.08.2026 ###
### Try to run at least Razor Enhanced Version 0.8.2.215 ###
### SAVE THE SCRIPT AS .py file and add to the Python Script Section in Razor Enhanced ###

### START THE ATTACK SCRIPT FIRST
### SET THIS SCRIPT TO LOOP MODE

from System.Collections.Generic import List
import json
import os

LEGACY_PROFILE_PATH = os.path.join(Misc.CurrentScriptDirectory(), "mage_settings.json")

def safe_profile_name(name):
    safe = "".join(ch if (ch.isalnum() or ch in "-_") else "_" for ch in str(name or "character"))
    return safe.strip("_") or "character"

PROFILE_FILENAME = "mage_settings_%s_%08X.json" % (
    safe_profile_name(Player.Name), int(Player.Serial))
PROFILE_PATH = os.path.join(Misc.CurrentScriptDirectory(), PROFILE_FILENAME)

setX = 100
setY = 100

def mark_settings_changed():
    try:
        revision = int(Misc.ReadSharedValue("mw_settings_revision"))
    except Exception:
        revision = 0
    Misc.SetSharedValue("mw_settings_revision", revision + 1)

def SetSharedValue(sharedvalue):
    if not sharedvalue:  # RefreshGUMP dummy — just re-render, touch nothing
        return
    val = Misc.ReadSharedValue(sharedvalue)
    Misc.SetSharedValue(sharedvalue, 0 if val == 1 else 1)
    mark_settings_changed()


def mySort(e):
    return e['name']


def get_all_sv_keys():
    """Collect every sharedvalue/displayvalue key from the sections dict,
    plus the per-section collapse-state keys (gump_col_N)."""
    keys = set()
    for section in sections.values():
        for action in section.values():
            if 'sharedvalue' in action:
                keys.add(action['sharedvalue'])
            if 'displayvalue' in action:
                keys.add(action['displayvalue'])
    keys.discard("")  # RefreshGUMP dummy key
    for i in range(len(sections)):
        keys.add("gump_col_%d" % i)
    return keys

def save_settings():
    data = {k: Misc.ReadSharedValue(k) for k in sorted(get_all_sv_keys())}
    try:
        with open(PROFILE_PATH, 'w') as f:
            json.dump(data, f, indent=2, sort_keys=True)
        Player.HeadMessage(68, "Settings saved: %s" % PROFILE_FILENAME)
    except Exception as e:
        Player.HeadMessage(33, "Save failed: %s" % str(e))

def load_settings():
    load_path = PROFILE_PATH
    migrate_legacy = False
    if not os.path.exists(load_path) and os.path.exists(LEGACY_PROFILE_PATH):
        load_path = LEGACY_PROFILE_PATH
        migrate_legacy = True
    if not os.path.exists(load_path):
        Player.HeadMessage(33, "No profile found!")
        return
    try:
        with open(load_path, 'r') as f:
            data = json.load(f)
        for k, v in data.items():
            Misc.SetSharedValue(k, v)
        mark_settings_changed()
        if migrate_legacy:
            with open(PROFILE_PATH, 'w') as f:
                json.dump(data, f, indent=2, sort_keys=True)
            Player.HeadMessage(68, "Legacy settings migrated: %s" % PROFILE_FILENAME)
        else:
            Player.HeadMessage(68, "Settings loaded: %s" % PROFILE_FILENAME)
    except Exception as e:
        Player.HeadMessage(33, "Load failed: %s" % str(e))


# Preset profiles — apply curated bundles of shared values for common play styles.
PRESETS = {
    'trash': {
        # Light, fast, cheap — for low-HP mob waves
        'use_evil_omen': 0, 'use_corpse_skin': 0, 'use_strangle': 0, 'use_mind_rot': 0,
        'use_explosion_combo': 0,
        'use_flamestrike': 0, 'use_energybolt': 1, 'use_mindblast': 1, 'use_lightning': 1,
        'use_chainlightning': 1, 'use_meteorswarm': 0, 'use_wither': 1,
        'use_skip_debuffs_on_trash': 1, 'use_mana_aware': 1,
        'multi_threshold': 2, 'mass_threshold': 4,
        'urgent_buff_threshold': 50,
    },
    'boss': {
        # Full burst, full debuffs, defensive shields
        'use_evil_omen': 1, 'use_corpse_skin': 1, 'use_strangle': 1, 'use_mind_rot': 1,
        'use_explosion_combo': 1,
        'use_flamestrike': 1, 'use_energybolt': 1, 'use_wordofdeath': 1,
        'use_arcaneempowerment': 1, 'use_magicreflect': 1, 'use_reactivearmor': 1,
        'use_mana_shield': 1,
        'use_nuke_cascade': 1, 'use_resist_aware': 1,
        'use_skip_debuffs_on_trash': 1,
        'urgent_buff_threshold': 70,
    },
    'solo': {
        # Self-reliant — summons, defensives, conservative
        'use_summonfey': 1, 'use_summonfiend': 1, 'use_risingcolossus': 1,
        'use_magicreflect': 1, 'use_reactivearmor': 1, 'use_protection': 0,
        'use_mana_shield': 1, 'use_vampiricembrace': 1,
        'use_energybolt': 1, 'use_flamestrike': 1,
        'use_evil_omen': 1, 'use_corpse_skin': 1,
        'urgent_buff_threshold': 70,
    },
}

def apply_preset_trash(): _apply_preset('trash')
def apply_preset_boss():  _apply_preset('boss')
def apply_preset_solo():  _apply_preset('solo')

def _apply_preset(name):
    cfg = PRESETS.get(name)
    if not cfg:
        Player.HeadMessage(33, "Preset not found: %s" % name)
        return
    for k, v in cfg.items():
        Misc.SetSharedValue(k, v)
    mark_settings_changed()
    Player.HeadMessage(68, "Preset applied: %s" % name)


# Slayer spellbook controls. Manual selections set a shared request; the attack
# script performs the actual equip only when no spell is being cast.
SPELLBOOK_IDS = [0x0EFA, 0x2253, 0x2D50, 0x2D9D]  # Magery, Necro, SW, Mysticism
SLAYER_GROUPS = ['Reptile', 'Dragon', 'Repond', 'Fey', 'Undead',
                 'Elemental', 'Demon', 'Arachnid']

def book_slayer_group(item):
    try:
        for p in item.Properties:
            ps = str(p).lower()
            if 'slayer' in ps or 'slaying' in ps or ps.strip() == 'silver':
                for group in SLAYER_GROUPS:
                    if group.lower() in ps:
                        return group
                if 'silver' in ps:
                    return 'Undead'
                return 'Other'
    except Exception:
        pass
    return None

def equipped_book_serial():
    for layer in ('LeftHand', 'RightHand'):
        item = Player.GetItemOnLayer(layer)
        if item and item.ItemID in SPELLBOOK_IDS:
            return item.Serial
    return 0

def scan_slayer_books():
    """Return slayer books plus one default Magery book from backpack/hands."""
    books = []
    default = None
    seen = set()
    candidates = []
    for item_id in SPELLBOOK_IDS:
        found = Items.FindAllByID(item_id, -1, Player.Backpack.Serial, 2)
        if found:
            candidates.extend(found)
    for layer in ('LeftHand', 'RightHand'):
        item = Player.GetItemOnLayer(layer)
        if item and item.ItemID in SPELLBOOK_IDS:
            candidates.append(item)
    for book in candidates:
        if book.Serial in seen:
            continue
        seen.add(book.Serial)
        group = book_slayer_group(book)
        if group:
            books.append((group, book.Serial, True))
        elif default is None and book.ItemID == 0x0EFA:
            default = ('Default', book.Serial, False)
    books.sort()
    if default:
        books.append(default)
    return books

def refresh_slayer_section():
    """Rebuild dynamic book buttons before each GUMP render."""
    equipped = equipped_book_serial()
    actions = {
        'Auto-Swap': {
            'buttontype': 'setsharedvalue',
            'sharedvalue': 'use_slayer_autoswap',
            'task': SetSharedValue,
            'tooltip': 'Auto-equip the slayer book matching the current target. OFF = manual only.',
        },
    }
    label_counts = {}
    for label, serial, is_slayer in scan_slayer_books():
        label_counts[label] = label_counts.get(label, 0) + 1
        count = label_counts[label]
        name = label if count == 1 else "%s #%d" % (label, count)
        if serial == equipped:
            name += " <"
        actions[name] = {
            'buttontype': 'slayerbook',
            'serial': serial,
            'label': label,
            'is_slayer': is_slayer,
            'equipped': serial == equipped,
            'tooltip': 'Request this book; the attack script equips it safely between casts.',
        }
    sections['2: Slayer Books'] = actions


sections = {

    '0: Presets':
    {
        'Trash':
            {
            'buttontype': "action",
            'task': apply_preset_trash,
            'tooltip': "Apply Trash preset — cheap fast spells, debuffs off, mana-aware.",
            },
        'Boss':
            {
            'buttontype': "action",
            'task': apply_preset_boss,
            'tooltip': "Apply Boss preset — full debuff stack, top-tier nukes, defensive shields.",
            },
        'Solo':
            {
            'buttontype': "action",
            'task': apply_preset_solo,
            'tooltip': "Apply Solo preset — summons + defensives + Vampiric Embrace.",
            },
    },

    '1: Status & Ranges':
    {
        'Attack Off':
            {
            'buttontype': "setsharedvalue",
            'sharedvalue': "activeattack",
            'task': SetSharedValue,
            'tooltip': "Pause the attack script without stopping it. Toggle back on when ready.",
            },
        'RefreshGUMP':
            {
            'buttontype': "setsharedvalue",
            'sharedvalue': "",
            'task': SetSharedValue,
            'tooltip': "Refresh this GUMP without changing any setting.",
            },
        'AttackRange':
            {
            'buttontype': "setvalue",
            'displayvalue': "attackrange",
            'id': 0,
            'tooltip': "Range at which mobs are targeted. Mage default is 12. (Max useful: 14)",
            },
        'MultiThreshold':
            {
            'buttontype': "setvalue",
            'displayvalue': "multi_threshold",
            'id': 3,
            'tooltip': "Minimum nearby mobs to switch from single-target to multi-target spells. (Default: 2)",
            },
        'MassThreshold':
            {
            'buttontype': "setvalue",
            'displayvalue': "mass_threshold",
            'id': 2,
            'tooltip': "Minimum nearby mobs to switch to mass AoE spells like Earthquake/Wildfire. (Default: 4)",
            },
        'HonorRange':
            {
            'buttontype': "setvalue",
            'displayvalue': "honordistance",
            'id': 1,
            'tooltip': "Range to honor mobs. (Default == Max: 10 tiles)",
            },
    },

    '2: Global':
    {
        'Messages':
            {
            'buttontype': "setsharedvalue",
            'sharedvalue': "use_messages",
            'task': SetSharedValue,
            'tooltip': "Show overhead messages for most script actions.",
            },
        'AttackBlue':
            {
            'buttontype': "setsharedvalue",
            'sharedvalue': "attack_blues",
            'task': SetSharedValue,
            'tooltip': "Attack blue (innocent) mobs. Use with care to avoid criminal flags.",
            },
        'AttackRedHumans':
            {
            'buttontype': "setsharedvalue",
            'sharedvalue': "attack_red_humans",
            'task': SetSharedValue,
            'tooltip': "Attack red human mobiles. Disable if red players are nearby.",
            },
        'AttackBlueChangeling':
            {
            'buttontype': "setsharedvalue",
            'sharedvalue': "attack_blue_changelings",
            'task': SetSharedValue,
            'tooltip': "Attack blue changelings that have mimicked you. Useful in Twisted Weald.",
            },
        'BagOfSending':
            {
            'buttontype': "setsharedvalue",
            'sharedvalue': "use_bagofsending",
            'task': SetSharedValue,
            'tooltip': "Automatically send gold to bank with Bag of Sending when almost overweight.",
            },
        'TrappedCrate':
            {
            'buttontype': "setsharedvalue",
            'sharedvalue': "use_trappedcrate",
            'task': SetSharedValue,
            'tooltip': "Use a Trapped Crate to escape paralysis.",
            },
        'TownBuff':
            {
            'buttontype': "setsharedvalue",
            'sharedvalue': "use_townbuff",
            'task': SetSharedValue,
            'tooltip': "Check if the City Trade Deal town buff is active.",
            },
        'CheckforLegendaries':
            {
            'buttontype': "setsharedvalue",
            'sharedvalue': "use_checkforlegendaries",
            'task': SetSharedValue,
            'tooltip': "Play a sound and show overhead text when a legendary spawn appears nearby.",
            },
        'CheckforRare':
            {
            'buttontype': "setsharedvalue",
            'sharedvalue': "use_checkforraremobs",
            'task': SetSharedValue,
            'tooltip': "Show overhead message when a rare mob (purple Rare tag) is nearby.",
            },
        'StopWhenRare':
            {
            'buttontype': "setsharedvalue",
            'sharedvalue': "use_stopwarwhenrare",
            'task': SetSharedValue,
            'tooltip': "Stop the attack script and leave war mode when a rare mob is nearby.",
            },
        'DistanceMarker':
            {
            'buttontype': "setsharedvalue",
            'sharedvalue': "use_distancemarker",
            'task': SetSharedValue,
            'tooltip': "Show colored triangles over mobs indicating whether they are in attack range.",
            },
        'Honor':
            {
            'buttontype': "setsharedvalue",
            'sharedvalue': "use_honor",
            'task': SetSharedValue,
            'tooltip': "Invoke Honor virtue on each new target for bonus damage.",
            },
        'LoadSettings':
            {
            'buttontype': "action",
            'task': load_settings,
            'tooltip': "Load settings from %s" % PROFILE_PATH,
            },
        'SaveSettings':
            {
            'buttontype': "action",
            'task': save_settings,
            'tooltip': "Save current settings to %s" % PROFILE_PATH,
            },
        'BlueDistanceMarker':
            {
            'buttontype': "setsharedvalue",
            'sharedvalue': "use_bluemarkermode",
            'task': SetSharedValue,
            'tooltip': "Use blue triangles (1-3) instead of colored ones for the distance markers.",
            },
        'ShowMobInfo':
            {
            'buttontype': "setsharedvalue",
            'sharedvalue': "use_mobinfo",
            'task': SetSharedValue,
            'tooltip': "Show mob info overhead (HP, weakest resist, karma).",
            },
        'Dresslist':
            {
            'buttontype': "setsharedvalue",
            'sharedvalue': "use_dresslist",
            'task': SetSharedValue,
            'tooltip': "Periodically check and restore your equipped gear using a Razor Enhanced Dresslist.",
            },
    },

    '3: Heal Cure & Buff':
    {
        'AutoHeal':
            {
            'buttontype': "setsharedvalue",
            'skillCheck': 'Magery',
            'skillValue': 0,
            'sharedvalue': "use_heal",
            'task': SetSharedValue,
            'tooltip': "Auto-cast Greater Heal or Heal when HP drops below the heal threshold.",
            },
        'HealThreshold':
            {
            'buttontype': "setvalue",
            'displayvalue': "heal_threshold",
            'id': 4,
            'tooltip': "HP percentage below which the script will cast a heal spell. (Default: 70)",
            },
        'AutoCure':
            {
            'buttontype': "setsharedvalue",
            'skillCheck': 'Magery',
            'skillValue': 0,
            'sharedvalue': "use_cure",
            'task': SetSharedValue,
            'tooltip': "Auto-cast Cure (or Arch Cure) when poisoned.",
            },
        'MagicReflect':
            {
            'buttontype': "setsharedvalue",
            'skillCheck': 'Magery',
            'skillValue': 0,
            'sharedvalue': "use_magicreflect",
            'task': SetSharedValue,
            'tooltip': "Keep Magic Reflect active — reflects the next harmful spell back at the attacker.",
            },
        'ReactiveArmor':
            {
            'buttontype': "setsharedvalue",
            'skillCheck': 'Magery',
            'skillValue': 0,
            'sharedvalue': "use_reactivearmor",
            'task': SetSharedValue,
            'tooltip': "Keep Reactive Armor active — increases physical resistance.",
            },
        'Protection':
            {
            'buttontype': "setsharedvalue",
            'skillCheck': 'Magery',
            'skillValue': 0,
            'sharedvalue': "use_protection",
            'task': SetSharedValue,
            'tooltip': "Keep Protection active — prevents spell interruption. WARNING: -2 FC penalty while active.",
            },
        'Bless':
            {
            'buttontype': "setsharedvalue",
            'skillCheck': 'Magery',
            'skillValue': 22,
            'sharedvalue': "use_bless",
            'task': SetSharedValue,
            'tooltip': "Magery C3: Bless self — +10 to all stats. 5 mana. Refreshed on expiry.",
            },
        'AttuneWeapon':
            {
            'buttontype': "setsharedvalue",
            'skillCheck': 'Spellweaving',
            'skillValue': 0,
            'sharedvalue': "use_attuneweapon",
            'task': SetSharedValue,
            'tooltip': "Keep SW Attune Weapon active — absorbs physical damage like a mana shield.",
            },
        'GiftOfLife':
            {
            'buttontype': "setsharedvalue",
            'skillCheck': 'Spellweaving',
            'skillValue': 0,
            'sharedvalue': "use_giftoflife",
            'task': SetSharedValue,
            'tooltip': "Keep SW Gift of Life active — automatically resurrects you on death. Needs Arcane Focus.",
            },
        'GiftOfRenewal':
            {
            'buttontype': "setsharedvalue",
            'skillCheck': 'Spellweaving',
            'skillValue': 0,
            'sharedvalue': "use_giftofrenewal",
            'task': SetSharedValue,
            'tooltip': "SW: Gift of Renewal — healing over time buff on self. 180s cooldown.",
            },
        'ArcaneFocus':
            {
            'buttontype': "setsharedvalue",
            'skillCheck': 'Spellweaving',
            'skillValue': 0,
            'sharedvalue': "use_arcanefocus",
            'task': SetSharedValue,
            'tooltip': "Check and renew Arcane Focus. Even at 0 SW it grants +6 STR for 2 hours.",
            },
        'CleansingWinds':
            {
            'buttontype': "setsharedvalue",
            'skillCheck': 'Mysticism',
            'skillValue': 51,
            'sharedvalue': "use_cleansingwinds",
            'task': SetSharedValue,
            'tooltip': "Mysticism C6: Cleansing Winds — cures poison AND removes debuffs (Curse, Corpse Skin, etc). Prioritized over regular Cure. (req. 51 Mysticism)",
            },
        'ArcaneEmpowerment':
            {
            'buttontype': "setsharedvalue",
            'skillCheck': 'Spellweaving',
            'skillValue': 24,
            'sharedvalue': "use_arcaneempowerment",
            'task': SetSharedValue,
            'tooltip': "SW: Arcane Empowerment — boosts spell damage and healing. Keep active. 3s cast, 50 mana. (req. 24 SW)",
            },
        'ReaperForm':
            {
            'buttontype': "setsharedvalue",
            'skillCheck': 'Spellweaving',
            'skillValue': 0,
            'sharedvalue': "use_reaperform",
            'task': SetSharedValue,
            'tooltip': "SW: Reaper Form — transform into a reaper, boosting spellweaving spell damage. 3s cast, 34 mana.",
            },
        'WraithForm':
            {
            'buttontype': "setsharedvalue",
            'skillCheck': 'Necromancy',
            'skillValue': 15,
            'sharedvalue': "use_wraithform",
            'task': SetSharedValue,
            'tooltip': "Necro: Wraith Form — drains mana from enemies on melee hit. Mutually exclusive with Lich Form and Vampiric Embrace. (req. 15 Necro)",
            },
        'LichForm':
            {
            'buttontype': "setsharedvalue",
            'skillCheck': 'Necromancy',
            'skillValue': 70,
            'sharedvalue': "use_lichform",
            'task': SetSharedValue,
            'tooltip': "Necro: Lich Form — mana regenerates from INT, immune to poison. Mutually exclusive with Wraith Form and Vampiric Embrace. (req. 70 Necro)",
            },
        'VampiricEmbrace':
            {
            'buttontype': "setsharedvalue",
            'skillCheck': 'Necromancy',
            'skillValue': 99,
            'sharedvalue': "use_vampiricembrace",
            'task': SetSharedValue,
            'tooltip': "Necro: Vampiric Embrace — life drain on melee hit. Mutually exclusive with Wraith Form and Lich Form. (req. 99 Necro)",
            },
        'StoneForm':
            {
            'buttontype': "setsharedvalue",
            'skillCheck': 'Mysticism',
            'skillValue': 33,
            'sharedvalue': "use_stoneform",
            'task': SetSharedValue,
            'tooltip': "Mysticism: Stone Form — increases physical resistance significantly. 1.75s cast, 11 mana. (req. 33 Mysticism)",
            },
    },

    '4: Mob Debuffs':
    {
        'EvilOmen':
            {
            'buttontype': "setsharedvalue",
            'sharedvalue': "use_evil_omen",
            'skillCheck': 'Necromancy',
            'skillValue': 20,
            'task': SetSharedValue,
            'tooltip': "Necro: Evil Omen — next harmful spell against the target does increased damage. 6s cooldown. (req. 20 Necro)",
            },
        'Curse':
            {
            'buttontype': "setsharedvalue",
            'skillCheck': 'Magery',
            'skillValue': 20,
            'sharedvalue': "use_curse",
            'task': SetSharedValue,
            'tooltip': "Magery C4: Curse — reduces all mob stats. 55s duration, cast once per target. (req. 20 Magery)",
            },
        'CorpseSkin':
            {
            'buttontype': "setsharedvalue",
            'skillCheck': 'Necromancy',
            'skillValue': 20,
            'sharedvalue': "use_corpse_skin",
            'task': SetSharedValue,
            'tooltip': "Necro: Corpse Skin — lowers mob fire and poison resistance. 25s cooldown. (req. 20 Necro)",
            },
        'Strangle':
            {
            'buttontype': "setsharedvalue",
            'skillCheck': 'Necromancy',
            'skillValue': 65,
            'sharedvalue': "use_strangle",
            'task': SetSharedValue,
            'tooltip': "Necro: Strangle — damage over time. 15s cooldown. Strong vs high-HP mobs. (req. 65 Necro)",
            },
        'MindRot':
            {
            'buttontype': "setsharedvalue",
            'skillCheck': 'Necromancy',
            'skillValue': 30,
            'sharedvalue': "use_mind_rot",
            'task': SetSharedValue,
            'tooltip': "Necro: Mind Rot — increases mana cost for the target. Excellent vs caster mobs. 25s cooldown. (req. 30 Necro)",
            },
        'Poison':
            {
            'buttontype': "setsharedvalue",
            'skillCheck': 'Magery',
            'skillValue': 0,
            'sharedvalue': "use_poison",
            'task': SetSharedValue,
            'tooltip': "Magery C3: Poison — poisons the target for damage over time. 20s cooldown.",
            },
        'Wither':
            {
            'buttontype': "setsharedvalue",
            'skillCheck': 'Necromancy',
            'skillValue': 60,
            'sharedvalue': "use_wither",
            'task': SetSharedValue,
            'tooltip': "Necro: Wither — self-centered cold AoE, also slows mobs. (req. 60 Necro)",
            },
        'ManaVampire':
            {
            'buttontype': "setsharedvalue",
            'skillCheck': 'Magery',
            'skillValue': 60,
            'sharedvalue': "use_mana_vampire",
            'task': SetSharedValue,
            'tooltip': "Magery C7: Mana Vampire — drains mana from the target and transfers it to you. 40 mana. (req. 60 Magery)",
            },
        'MassSleep':
            {
            'buttontype': "setsharedvalue",
            'skillCheck': 'Mysticism',
            'skillValue': 50,
            'sharedvalue': "use_mass_sleep",
            'task': SetSharedValue,
            'tooltip': "Mysticism C5: Mass Sleep — puts all nearby mobs to sleep (broken by damage). 20 mana. (req. 50 Mysticism)",
            },
        'Paralyze':
            {
            'buttontype': "setsharedvalue",
            'skillCheck': 'Magery',
            'skillValue': 50,
            'sharedvalue': "use_paralyze",
            'task': SetSharedValue,
            'tooltip': "Magery C6: Paralyze — freezes the target in place. 20 mana, 8s cooldown. (req. 50 Magery)",
            },
        'Sleep':
            {
            'buttontype': "setsharedvalue",
            'skillCheck': 'Mysticism',
            'skillValue': 0,
            'sharedvalue': "use_sleep",
            'task': SetSharedValue,
            'tooltip': "Mysticism C2: Sleep — puts a single target to sleep (broken by damage). 9 mana.",
            },
        'SpellPlague':
            {
            'buttontype': "setsharedvalue",
            'skillCheck': 'Mysticism',
            'skillValue': 66,
            'sharedvalue': "use_spellplague",
            'task': SetSharedValue,
            'tooltip': "Mysticism C7: Spell Plague — 40 mana. Chains explosions between nearby targets on contact with a spell.",
            },
    },

    '5: Single Target':
    {
        'WordOfDeath':
            {
            'buttontype': "setsharedvalue",
            'skillCheck': 'Spellweaving',
            'skillValue': 83,
            'sharedvalue': "use_wordofdeath",
            'task': SetSharedValue,
            'tooltip': "SW: Word of Death — instantly kills mob below 10% HP. 50 mana, 3.5s cast.",
            },
        'FlameStrike':
            {
            'buttontype': "setsharedvalue",
            'skillCheck': 'Magery',
            'skillValue': 60,
            'sharedvalue': "use_flamestrike",
            'task': SetSharedValue,
            'tooltip': "Magery C7: Flame Strike — 40 mana, 2.75s cast. Strong fire damage.",
            },
        'EnergyBolt':
            {
            'buttontype': "setsharedvalue",
            'skillCheck': 'Magery',
            'skillValue': 50,
            'sharedvalue': "use_energybolt",
            'task': SetSharedValue,
            'tooltip': "Magery C6: Energy Bolt — 20 mana, 2.5s cast. Good energy damage.",
            },
        'MindBlast':
            {
            'buttontype': "setsharedvalue",
            'skillCheck': 'Magery',
            'skillValue': 40,
            'sharedvalue': "use_mindblast",
            'task': SetSharedValue,
            'tooltip': "Magery C5: Mind Blast — 14 mana, 2.25s cast. Damage based on highest vs lowest stat diff.",
            },
        'Lightning':
            {
            'buttontype': "setsharedvalue",
            'skillCheck': 'Magery',
            'skillValue': 0,
            'sharedvalue': "use_lightning",
            'task': SetSharedValue,
            'tooltip': "Magery C4: Lightning — 11 mana, 2s cast. Reliable energy damage.",
            },
        'Fireball':
            {
            'buttontype': "setsharedvalue",
            'skillCheck': 'Magery',
            'skillValue': 0,
            'sharedvalue': "use_fireball",
            'task': SetSharedValue,
            'tooltip': "Magery C3: Fireball — 9 mana, 1.75s cast. Low-mana fire damage.",
            },
        'Harm':
            {
            'buttontype': "setsharedvalue",
            'skillCheck': 'Magery',
            'skillValue': 0,
            'sharedvalue': "use_harm",
            'task': SetSharedValue,
            'tooltip': "Magery C2: Harm — 6 mana, 1.5s cast. Close range only (2 tiles)!",
            },
        'MagicArrow':
            {
            'buttontype': "setsharedvalue",
            'skillCheck': 'Magery',
            'skillValue': 0,
            'sharedvalue': "use_magicarrow",
            'task': SetSharedValue,
            'tooltip': "Magery C1: Magic Arrow — 4 mana, 1.25s cast. Last-resort low-mana spell.",
            },
        'EagleStrike':
            {
            'buttontype': "setsharedvalue",
            'skillCheck': 'Mysticism',
            'skillValue': 9,
            'sharedvalue': "use_eaglestrike",
            'task': SetSharedValue,
            'tooltip': "Mysticism C3: Eagle Strike — 9 mana. Physical damage, bypasses magic resistance.",
            },
        'Bombard':
            {
            'buttontype': "setsharedvalue",
            'skillCheck': 'Mysticism',
            'skillValue': 51,
            'sharedvalue': "use_bombard",
            'task': SetSharedValue,
            'tooltip': "Mysticism C6: Bombard — physical damage, paralyzes target briefly. 2.25s cast, 20 mana. (req. 51 Mysticism)",
            },
        'NetherBolt':
            {
            'buttontype': "setsharedvalue",
            'skillCheck': 'Mysticism',
            'skillValue': 0,
            'sharedvalue': "use_nether_bolt",
            'task': SetSharedValue,
            'tooltip': "Mysticism C1: Nether Bolt — 4 mana. Low-mana fallback for Mysticism builds.",
            },
        'ExplosionCombo':
            {
            'buttontype': "setsharedvalue",
            'skillCheck': 'Magery',
            'skillValue': 40,
            'sharedvalue': "use_explosion_combo",
            'task': SetSharedValue,
            'tooltip': "Magery v0.5: Explosion + immediate follow-up burst — both land ~3s after cast.",
            },
        'ComboFollowup':
            {
            'buttontype': "cyclevalue",
            'skillCheck': 'Magery',
            'skillValue': 40,
            'displayvalue': "combo_followup",
            'options': ["energybolt", "flamestrike", "mindblast", "lightning"],
            'tooltip': "Spell paired with Explosion in the combo. Click to cycle: EB / FS / MB / Lit.",
            },
    },

    '6: Multi Target':
    {
        'ChainLightning':
            {
            'buttontype': "setsharedvalue",
            'skillCheck': 'Magery',
            'skillValue': 60,
            'sharedvalue': "use_chainlightning",
            'task': SetSharedValue,
            'tooltip': "Magery C7: Chain Lightning — 40 mana. Hits main target and jumps to nearby mobs.",
            },
        'MeteorSwarm':
            {
            'buttontype': "setsharedvalue",
            'skillCheck': 'Magery',
            'skillValue': 60,
            'sharedvalue': "use_meteorswarm",
            'task': SetSharedValue,
            'tooltip': "Magery C7: Meteor Swarm — 40 mana. Fire AoE around target.",
            },
        'EssenceOfWind':
            {
            'buttontype': "setsharedvalue",
            'skillCheck': 'Spellweaving',
            'skillValue': 52,
            'sharedvalue': "use_essenceofwind",
            'task': SetSharedValue,
            'tooltip': "SW: Essence of Wind — 40 mana. Air AoE around target. Also lowers mob FCR.",
            },
        'HailStorm':
            {
            'buttontype': "setsharedvalue",
            'skillCheck': 'Mysticism',
            'skillValue': 66,
            'sharedvalue': "use_hailstorm",
            'task': SetSharedValue,
            'tooltip': "Mysticism C7: Hail Storm — 50 mana. Cold AoE around target. (req. 66 Mysticism)",
            },
        'NetherCyclone':
            {
            'buttontype': "setsharedvalue",
            'skillCheck': 'Mysticism',
            'skillValue': 80,
            'sharedvalue': "use_nethercyclone",
            'task': SetSharedValue,
            'tooltip': "Mysticism C8: Nether Cyclone — 50 mana. Strong chaos AoE around target. Needs 80 Mysticism.",
            },
        'PoisonStrike':
            {
            'buttontype': "setsharedvalue",
            'skillCheck': 'Necromancy',
            'skillValue': 65,
            'sharedvalue': "use_poison_strike",
            'task': SetSharedValue,
            'tooltip': "Necro: Poison Strike — targeted AoE poison damage. 17 mana. Closer mobs take more dmg. (req. 65 Necro)",
            },
    },

    '7: Mass Target':
    {
        'Earthquake':
            {
            'buttontype': "setsharedvalue",
            'skillCheck': 'Magery',
            'skillValue': 70,
            'sharedvalue': "use_earthquake",
            'task': SetSharedValue,
            'tooltip': "Magery C8: Earthquake — 50 mana. Self-centered AoE, hits all nearby mobs. Best mass spell.",
            },
        'Thunderstorm':
            {
            'buttontype': "setsharedvalue",
            'skillCheck': 'Spellweaving',
            'skillValue': 10,
            'sharedvalue': "use_thunderstorm",
            'task': SetSharedValue,
            'tooltip': "SW: Thunderstorm — 32 mana. Self-centered lightning AoE. Great for grouped mobs. (req. 10 SW)",
            },
        'Wildfire':
            {
            'buttontype': "setsharedvalue",
            'skillCheck': 'Spellweaving',
            'skillValue': 66,
            'sharedvalue': "use_wildfire",
            'task': SetSharedValue,
            'tooltip': "SW: Wildfire — 50 mana. Targeted large fire AoE. Excellent for tight mob clusters. (req. 66 SW)",
            },
    },

    '8: Summons':
    {
        'SummonFey':
            {
            'buttontype': "setsharedvalue",
            'skillCheck': 'Spellweaving',
            'skillValue': 38,
            'sharedvalue': "use_summonfey",
            'task': SetSharedValue,
            'tooltip': "SW: Summon Fey — summon pixies to assist in combat. Re-summons when followers drop below threshold.",
            },
        'SummonFiend':
            {
            'buttontype': "setsharedvalue",
            'skillCheck': 'Spellweaving',
            'skillValue': 38,
            'sharedvalue': "use_summonfiend",
            'task': SetSharedValue,
            'tooltip': "SW: Summon Fiend — summon imps to assist in combat. Re-summons when followers drop below threshold.",
            },
        'RisingColossus':
            {
            'buttontype': "setsharedvalue",
            'skillCheck': 'Mysticism',
            'skillValue': 80,
            'sharedvalue': "use_risingcolossus",
            'task': SetSharedValue,
            'tooltip': "Mysticism: Rising Colossus — summon a powerful elemental colossus. Needs 80+ Mysticism.",
            },
        'SummonElemental':
            {
            'buttontype': "setsharedvalue",
            'skillCheck': 'Magery',
            'skillValue': 70,
            'sharedvalue': "use_summonelemental",
            'task': SetSharedValue,
            'tooltip': "Magery C8: Summon Elemental — summon an elemental of the chosen type. Set ElementalType below.",
            },
        'SummonDaemon':
            {
            'buttontype': "setsharedvalue",
            'skillCheck': 'Magery',
            'skillValue': 70,
            'sharedvalue': "use_summon_daemon",
            'task': SetSharedValue,
            'tooltip': "Magery C8: Summon Daemon — summon a daemon. Re-summons when followers drop below threshold. (req. 70 Magery)",
            },
        'DaemonThreshold':
            {
            'buttontype': "setvalue",
            'displayvalue': "daemon_threshold",
            'id': 8,
            'tooltip': "Re-summon Daemon when follower count drops below this value. (Default: 1)",
            },
        'EnergyVortex':
            {
            'buttontype': "setsharedvalue",
            'skillCheck': 'Magery',
            'skillValue': 60,
            'sharedvalue': "use_energy_vortex",
            'task': SetSharedValue,
            'tooltip': "Magery C7: Energy Vortex — summon an energy vortex near player. Re-summons when followers drop below threshold. (req. 60 Magery)",
            },
        'EnergyVortexThreshold':
            {
            'buttontype': "setvalue",
            'displayvalue': "energy_vortex_threshold",
            'id': 11,
            'tooltip': "Re-summon Energy Vortex when follower count drops below this value. (Default: 1)",
            },
        'BladeSpirit':
            {
            'buttontype': "setsharedvalue",
            'skillCheck': 'Magery',
            'skillValue': 50,
            'sharedvalue': "use_blade_spirit",
            'task': SetSharedValue,
            'tooltip': "Magery C6: Blade Spirits — summon blade spirits near player. Re-summons when followers drop below threshold. (req. 50 Magery)",
            },
        'BladeSpiritThreshold':
            {
            'buttontype': "setvalue",
            'displayvalue': "blade_spirit_threshold",
            'id': 5,
            'tooltip': "Re-summon Blade Spirits when follower count drops below this value. (Default: 1)",
            },
        'SummonCreature':
            {
            'buttontype': "setsharedvalue",
            'skillCheck': 'Magery',
            'skillValue': 0,
            'sharedvalue': "use_summon_creature",
            'task': SetSharedValue,
            'tooltip': "Magery C5: Summon Creature — summons a random creature to assist. Re-summons when followers drop below threshold.",
            },
        'ElementalType':
            {
            'buttontype': "setvalue",
            'displayvalue': "elemental_type",
            'id': 10,
            'tooltip': "Elemental type: 0=Air  1=Earth  2=Fire  3=Water",
            },
        'FeyThreshold':
            {
            'buttontype': "setvalue",
            'displayvalue': "fey_threshold",
            'id': 12,
            'tooltip': "Re-summon Fey/Fiend when follower count drops below this value. (Default: 3)",
            },
        'ElementalThreshold':
            {
            'buttontype': "setvalue",
            'displayvalue': "elemental_threshold",
            'id': 9,
            'tooltip': "Re-summon Elemental when follower count drops below this value. (Default: 2)",
            },
        'CreatureThreshold':
            {
            'buttontype': "setvalue",
            'displayvalue': "creature_threshold",
            'id': 7,
            'tooltip': "Re-summon Creature when follower count drops below this value. (Default: 1)",
            },
    },

    '9: Skill Masteries':
    {
        'CommandUndead':
            {
            'buttontype': "setsharedvalue",
            'skillCheck': 'Necromancy',
            'skillValue': 90,
            'useRealSkill': True,
            'sharedvalue': "use_command_undead",
            'task': SetSharedValue,
            'tooltip': "Necromancy Mastery: Command Undead — seizes control of a nearby undead. 3s cast. (req. 90 real Necromancy)",
            },
        'Conduit':
            {
            'buttontype': "setsharedvalue",
            'skillCheck': 'Necromancy',
            'skillValue': 90,
            'useRealSkill': True,
            'sharedvalue': "use_conduit",
            'task': SetSharedValue,
            'tooltip': "Necromancy Mastery: Conduit — channels necromantic energy around you. 2.25s cast. (req. 90 real Necromancy)",
            },
        'DeathRay':
            {
            'buttontype': "setsharedvalue",
            'skillCheck': 'Magery',
            'skillValue': 90,
            'useRealSkill': True,
            'sharedvalue': "use_death_ray",
            'task': SetSharedValue,
            'tooltip': "Magery Mastery: Death Ray — fires a powerful targeted beam. 2.25s cast. (req. 90 real Magery)",
            },
        'EtherealBlast':
            {
            'buttontype': "setsharedvalue",
            'skillCheck': 'Magery',
            'skillValue': 90,
            'useRealSkill': True,
            'sharedvalue': "use_ethereal_blast",
            'task': SetSharedValue,
            'tooltip': "Magery Mastery: Ethereal Blast — self-centered AoE explosion. 2.25s cast. (req. 90 real Magery)",
            },
        'ManaShield':
            {
            'buttontype': "setsharedvalue",
            'skillCheck': 'Spellweaving',
            'skillValue': 90,
            'useRealSkill': True,
            'sharedvalue': "use_mana_shield",
            'task': SetSharedValue,
            'tooltip': "Spellweaving Mastery: Mana Shield — converts damage received into mana loss. Keep active. (req. 90 real Spellweaving)",
            },
        'MysticWeapon':
            {
            'buttontype': "setsharedvalue",
            'skillCheck': 'Mysticism',
            'skillValue': 90,
            'useRealSkill': True,
            'sharedvalue': "use_mystic_weapon",
            'task': SetSharedValue,
            'tooltip': "Mysticism Mastery: Mystic Weapon — imbues your weapon with mystical energy. Keep active. (req. 90 real Mysticism)",
            },
        'NetherBlast':
            {
            'buttontype': "setsharedvalue",
            'skillCheck': 'Mysticism',
            'skillValue': 90,
            'useRealSkill': True,
            'sharedvalue': "use_nether_blast",
            'task': SetSharedValue,
            'tooltip': "Mysticism Mastery: Nether Blast — directional ground field. 2s cast, 40 base mana. (req. 90 real Mysticism)",
            },
        'NBShowTiles':
            {
            'buttontype': "setsharedvalue",
            'skillCheck': 'Mysticism',
            'skillValue': 90,
            'useRealSkill': True,
            'sharedvalue': "use_nb_show_tiles",
            'task': SetSharedValue,
            'tooltip': "Mark valid Nether Blast casting tiles on the ground (green runes, client-side only).",
            },
        'NBAutoMove':
            {
            'buttontype': "setsharedvalue",
            'skillCheck': 'Mysticism',
            'skillValue': 90,
            'useRealSkill': True,
            'sharedvalue': "use_nb_auto_move",
            'task': SetSharedValue,
            'tooltip': "Auto-walk to the nearest valid NB tile when misaligned. Blocked while poisoned, bleeding, casting, or below the HP threshold.",
            },
        'NBMoveHP':
            {
            'buttontype': "setvalue",
            'skillCheck': 'Mysticism',
            'skillValue': 90,
            'useRealSkill': True,
            'displayvalue': "nb_move_hp_min",
            'minValue': 20,
            'maxValue': 95,
            'step': 5,
            'tooltip': "Minimum HP %% required for NB auto-move. Default 50.",
            },
        'ReaperThreshold':
            {
            'buttontype': "setvalue",
            'skillCheck': 'Spellweaving',
            'skillValue': 90,
            'useRealSkill': True,
            'displayvalue': "reaper_threshold",
            'id': 13,
            'tooltip': "Re-summon Reaper when follower count drops below this value. (Default: 4)",
            },
        'SummonReaper':
            {
            'buttontype': "setsharedvalue",
            'skillCheck': 'Spellweaving',
            'skillValue': 90,
            'useRealSkill': True,
            'sharedvalue': "use_summon_reaper",
            'task': SetSharedValue,
            'tooltip': "Spellweaving Mastery: Summon Reaper — summon a reaper to assist in combat. Re-summons when followers drop below threshold. (req. 90 real Spellweaving)",
            },
    },

    'A: Bard':
    {
        'AreaPeace':
            {
            'buttontype': "setsharedvalue",
            'sharedvalue': "use_area_peace",
            'skillCheck': 'Peacemaking',
            'skillValue': 0,
            'task': SetSharedValue,
            'tooltip': "Bard: Area Peacemaking — peaces all nearby mobs, centered on self.",
            },
        'CheckInstrument':
            {
            'buttontype': "setsharedvalue",
            'sharedvalue': "use_check_instrument",
            'task': SetSharedValue,
            'tooltip': "Warn if no instrument is found in your backpack.",
            },
        'Despair':
            {
            'buttontype': "setsharedvalue",
            'sharedvalue': "use_despair",
            'skillCheck': 'Musicianship',
            'skillValue': 90,
            'task': SetSharedValue,
            'useRealSkill': True,
            'tooltip': "Bard Mastery: Despair — reduces the target's stats and skills. (req. 90 real Musicianship)",
            },
        'Discordance':
            {
            'buttontype': "setsharedvalue",
            'sharedvalue': "use_discordance",
            'skillCheck': 'Discordance',
            'skillValue': 0,
            'task': SetSharedValue,
            'tooltip': "Bard: Discordance — reduces the nearest mob's skills and stats.",
            },
        'Inspire':
            {
            'buttontype': "setsharedvalue",
            'sharedvalue': "use_inspire",
            'skillCheck': 'Musicianship',
            'skillValue': 90,
            'task': SetSharedValue,
            'useRealSkill': True,
            'tooltip': "Bard Mastery: Inspire — boosts damage for you and nearby allies. (req. 90 real Musicianship)",
            },
        'Invigorate':
            {
            'buttontype': "setsharedvalue",
            'sharedvalue': "use_invigorate",
            'skillCheck': 'Musicianship',
            'skillValue': 90,
            'task': SetSharedValue,
            'useRealSkill': True,
            'tooltip': "Bard Mastery: Invigorate — regenerates stamina for you and nearby allies. (req. 90 real Musicianship)",
            },
        'Peace':
            {
            'buttontype': "setsharedvalue",
            'sharedvalue': "use_peace",
            'skillCheck': 'Peacemaking',
            'skillValue': 0,
            'task': SetSharedValue,
            'tooltip': "Bard: Peacemaking — peaces the nearest mob.",
            },
        'Perseverance':
            {
            'buttontype': "setsharedvalue",
            'sharedvalue': "use_perseverance",
            'skillCheck': 'Musicianship',
            'skillValue': 90,
            'task': SetSharedValue,
            'useRealSkill': True,
            'tooltip': "Bard Mastery: Perseverance — reduces damage taken for you and nearby allies. (req. 90 real Musicianship)",
            },
        'Provocation':
            {
            'buttontype': "setsharedvalue",
            'sharedvalue': "use_provocation",
            'skillCheck': 'Provocation',
            'skillValue': 0,
            'task': SetSharedValue,
            'tooltip': "Bard: Provocation — provokes two mobs to fight each other. Requires 2+ mobs in range.",
            },
        'Resilience':
            {
            'buttontype': "setsharedvalue",
            'sharedvalue': "use_resilience",
            'skillCheck': 'Musicianship',
            'skillValue': 90,
            'task': SetSharedValue,
            'useRealSkill': True,
            'tooltip': "Bard Mastery: Resilience — increases HP regeneration for you and nearby allies. (req. 90 real Musicianship)",
            },
        'Tribulation':
            {
            'buttontype': "setsharedvalue",
            'sharedvalue': "use_tribulation",
            'skillCheck': 'Musicianship',
            'skillValue': 90,
            'task': SetSharedValue,
            'useRealSkill': True,
            'tooltip': "Bard Mastery: Tribulation — target takes extra damage from all sources. (req. 90 real Musicianship)",
            },
    },

    'B: Tamer':
    {
        'AutoCurePet':
            {
            'buttontype': "setsharedvalue",
            'sharedvalue': "use_auto_cure_pet",
            'task': SetSharedValue,
            'tooltip': "Automatically cure poisoned pets using the selected heal method.",
            },
        'BlessPets':
            {
            'buttontype': "setsharedvalue",
            'skillCheck': 'Magery',
            'skillValue': 22,
            'sharedvalue': "use_bless_pets",
            'task': SetSharedValue,
            'tooltip': "Magery C3: Bless each pet — +10 to all stats. Re-cast every ~90s per pet.",
            },
        'AutoHealPet':
            {
            'buttontype': "setsharedvalue",
            'sharedvalue': "use_auto_heal_pet",
            'task': SetSharedValue,
            'tooltip': "Automatically heal pets when their HP drops below the threshold.",
            },
        'BandageAgent':
            {
            'buttontype': "setsharedvalue",
            'sharedvalue': "use_bandage_agent",
            'task': SetSharedValue,
            'tooltip': "Start/stop the Razor Enhanced Bandage Agent for automatic self-healing.",
            },
        'PetGiftOfLife':
            {
            'buttontype': "setsharedvalue",
            'sharedvalue': "use_pet_giftoflife",
            'skillCheck': 'Spellweaving',
            'skillValue': 80,
            'task': SetSharedValue,
            'tooltip': "Cast Gift of Life on all pets — auto-resurrects on death. Refreshed every 90s. (req. 80 SW)",
            },
        'PetGiftOfRenewal':
            {
            'buttontype': "setsharedvalue",
            'sharedvalue': "use_pet_giftofrenewal",
            'skillCheck': 'Spellweaving',
            'skillValue': 0,
            'task': SetSharedValue,
            'tooltip': "Cast Gift of Renewal on the closest pet for healing over time. 180s cooldown.",
            },
        'PetHealOption':
            {
            'buttontype': "setvalue",
            'displayvalue': "pet_heal_option",
            'task': SetSharedValue,
            'minValue': 1,
            'maxValue': 4,
            'valueLabels': {1: "Bandages", 2: "Magery", 3: "Mysticism", 4: "Bdg+Mag"},
            'tooltip': "Heal method: 1=Bandages  2=Magery (Greater Heal/Arch Cure)  3=Mysticism (Cleansing Winds)  4=Bandages + Magery",
            },
        'PetHPThreshold':
            {
            'buttontype': "setvalue",
            'displayvalue': "pet_hp_threshold",
            'task': SetSharedValue,
            'minValue': 1,
            'maxValue': 100,
            'tooltip': "Pet HP percentage below which healing is triggered (default: 90).",
            },
    },

    'C: Advanced':
    {
        'ResistAware':
            {
            'buttontype': "setsharedvalue",
            'sharedvalue': "use_resist_aware",
            'task': SetSharedValue,
            'tooltip': "Re-rank the single-target cascade by mob.weakres (MOBSLIST). Prefers the strongest enabled spell that matches the mob's elemental weakness.",
            },
        'NukeCascade':
            {
            'buttontype': "setsharedvalue",
            'sharedvalue': "use_nuke_cascade",
            'task': SetSharedValue,
            'tooltip': "After Evil Omen or Corpse Skin lands, bias the next cast toward the strongest enabled nuke for ~1.5s.",
            },
        'ComboCooldown':
            {
            'buttontype': "setvalue",
            'displayvalue': "combo_cooldown_ms",
            'minValue': 500,
            'maxValue': 5000,
            'step': 250,
            'tooltip': "Min delay between Explosion-combo repeats (ms). Default 1500.",
            },
        'UrgentBuffHP':
            {
            'buttontype': "setvalue",
            'displayvalue': "urgent_buff_threshold",
            'minValue': 30,
            'maxValue': 95,
            'step': 5,
            'tooltip': "HP%% below which protective keep_* buffs get priority. Default 60.",
            },
        'StatusOverlay':
            {
            'buttontype': "setsharedvalue",
            'sharedvalue': "use_status_overlay",
            'task': SetSharedValue,
            'tooltip': "Periodic overhead status line: HP%/MP%/Followers/active-buff badges/target HP.",
            },
        'OverlayMs':
            {
            'buttontype': "setvalue",
            'displayvalue': "status_overlay_ms",
            'minValue': 2000,
            'maxValue': 30000,
            'step': 1000,
            'tooltip': "Throttle for the status overlay (ms). Default 8000.",
            },
        'SummonCounter':
            {
            'buttontype': "setsharedvalue",
            'sharedvalue': "use_summon_counter",
            'task': SetSharedValue,
            'tooltip': "Head-message follower count after each successful summon.",
            },
        'SkipDebuffsOnTrash':
            {
            'buttontype': "setsharedvalue",
            'sharedvalue': "use_skip_debuffs_on_trash",
            'task': SetSharedValue,
            'tooltip': "Skip expensive debuffs (Evil Omen, Strangle, Corpse Skin etc.) on trash mobs — they die before payoff lands.",
            },
        'ManaAware':
            {
            'buttontype': "setsharedvalue",
            'sharedvalue': "use_mana_aware",
            'task': SetSharedValue,
            'tooltip': "Skip top-tier nukes (Flame Strike) on trash mobs when mana is below 70%.",
            },
        'SlayerAnnounce':
            {
            'buttontype': "setsharedvalue",
            'sharedvalue': "use_slayer_announce",
            'task': SetSharedValue,
            'tooltip': "Head-message when an equipped slayer matches a mob in MOBSLIST.",
            },
        'TrashHpCap':
            {
            'buttontype': "setvalue",
            'displayvalue': "trash_hp_cap",
            'minValue': 50,
            'maxValue': 1000,
            'step': 25,
            'tooltip': "Real HP threshold below which a mob counts as 'trash'. Default 250.",
            },
        'BossHpMin':
            {
            'buttontype': "setvalue",
            'displayvalue': "boss_hp_min",
            'minValue': 1000,
            'maxValue': 50000,
            'step': 500,
            'tooltip': "Real HP threshold at/above which a mob counts as 'boss'. Default 3000.",
            },
        'LowManaMode':
            {
            'buttontype': "setsharedvalue",
            'sharedvalue': "use_low_mana_mode",
            'task': SetSharedValue,
            'tooltip': "Below the mana threshold: skip debuffs and expensive nukes until mana recovers.",
            },
        'LowManaPct':
            {
            'buttontype': "setvalue",
            'displayvalue': "low_mana_threshold",
            'minValue': 10,
            'maxValue': 60,
            'step': 5,
            'tooltip': "Mana %% below which low-mana mode activates. Default 25.",
            },
    },

}


def buildSection(gd, title, sy, actions, sectionhue, titleX=0, values=None, skills=None):
    """Build (or dry-run) one section. Pass gd=None to calculate height only."""

    if title is None:
        return sy
    validActions = []
    sectionIndex_raw = list(sections).index(title)
    sectionIndex = sectionIndex_raw * 1000
    for i, action in enumerate(actions):
        a = actions[action]
        a['name'] = action
        a['actionId'] = sectionIndex + i + 1
        # Increment button uses section offset +100 to distinguish from regular in buttoncheck
        a['incActionId'] = (sectionIndex_raw + 100) * 1000 + i + 1
        a['hue'] = 900

        if 'sharedvalue' in a:
            key = a['sharedvalue']
            if not key:  # RefreshGUMP dummy action
                val = 0
            elif values is not None and key in values:
                val = values[key]
            else:
                val = Misc.ReadSharedValue(key)
            if val == 1:
                a['hue'] = 68
                if a['sharedvalue'] == "activeattack":
                    a['name'] = "Attack On"
                    a['hue'] = 32
        if 'displayvalue' in a:
            key = a['displayvalue']
            val = values[key] if values is not None and key in values else Misc.ReadSharedValue(key)
            a['hue'] = 88
            if a.get('buttontype') == 'cyclevalue':
                a['name'] = action + ": " + str(val)
            else:
                labels = a.get('valueLabels', {})
                val_str = labels.get(val, str(val))
                a['name'] = action + ": " + val_str
        if a.get('buttontype') == 'action':
            a['hue'] = 53  # gold — visually distinct from toggles
        elif a.get('buttontype') == 'slayerbook':
            a['hue'] = 32 if a['equipped'] else (53 if a['is_slayer'] else 88)

        if 'skillCheck' not in a:
            validActions.append(a)
            continue
        skill_key = (a.get('useRealSkill', False), a['skillCheck'])
        if skills is not None and skill_key in skills:
            skill_val = skills[skill_key]
        elif a.get('useRealSkill'):
            skill_val = Player.GetRealSkillValue(a['skillCheck'])
            if skills is not None:
                skills[skill_key] = skill_val
        else:
            skill_val = Player.GetSkillValue(a['skillCheck'])
            if skills is not None:
                skills[skill_key] = skill_val
        if skill_val >= a['skillValue']:
            validActions.append(a)

    if len(validActions) == 0:
        return sy

    validActions.sort(key=mySort)
    sectionhue = 52

    # Collapse toggle — section offset +200 keeps it clear of regular (+0) and increment (+100) ranges
    collapse_key = "gump_col_%d" % sectionIndex_raw
    collapse_actionId = (sectionIndex_raw + 200) * 1000
    collapse_value = (values[collapse_key]
                      if values is not None and collapse_key in values
                      else Misc.ReadSharedValue(collapse_key))
    is_collapsed = collapse_value == 1

    if gd is not None:
        Gumps.AddButton(gd, titleX, sy, 9762, 9763, collapse_actionId, 1, 0)
        indicator = "[+]" if is_collapsed else "[-]"
        Gumps.AddLabel(gd, titleX + 22, sy, sectionhue, indicator + " " + title)

    if is_collapsed:
        return sy + 20  # only header row consumed — gump shrinks automatically

    actionX = 5
    actionY = sy + 20
    col = 0
    last_was_displayvalue = False
    for x in range(len(validActions)):
        action = validActions[x]
        if 'displayvalue' in action:
            # Full-width row: [−] Name: N                              [+]
            actionX = 5
            if x > 0:
                actionY += 20
            col = 0
            last_was_displayvalue = True
            if gd is not None:
                is_cycle = action.get('buttontype') == 'cyclevalue'
                Gumps.AddButton(gd, 5, actionY, 9762, 9763, action['actionId'], 1, 0)
                Gumps.AddLabel(gd, 10, actionY, 900, "»" if is_cycle else "-")
                Gumps.AddLabel(gd, 30, actionY, action['hue'], action['name'])
                if 'tooltip' in action:
                    Gumps.AddTooltip(gd, str(action['tooltip']))
                if not is_cycle:
                    Gumps.AddButton(gd, 355, actionY, 9762, 9763, action['incActionId'], 1, 0)
                    Gumps.AddLabel(gd, 360, actionY, 900, "+")
        else:
            # Regular toggle button — 3 per row
            if col == 0 or last_was_displayvalue:
                actionX = 5
                if x > 0:
                    actionY += 20
                col = 0
            last_was_displayvalue = False
            col = (col + 1) % 3
            if gd is not None:
                Gumps.AddButton(gd, actionX, actionY, 9762, 9763, action['actionId'], 1, 0)
            actionX += 20
            if gd is not None:
                Gumps.AddLabel(gd, actionX, actionY, action['hue'], action['name'])
                if 'tooltip' in action:
                    Gumps.AddTooltip(gd, str(action['tooltip']))
            actionX += 100

    return actionY + 20


def sendgump():
    refresh_slayer_section()
    sectionssorted = sorted(sections)
    values = {k: Misc.ReadSharedValue(k) for k in get_all_sv_keys()}
    skills = {}

    # First pass (dry run): calculate exact height based on visible entries
    sY_calc = 30
    for section in sectionssorted:
        sY_calc = buildSection(None, section, sY_calc, sections[section], 20, 5, values, skills)
    gump_height = sY_calc + 10

    # Second pass: render with correct height
    gd = Gumps.CreateGump(movable=True)
    Gumps.AddPage(gd, 0)
    Gumps.AddBackground(gd, 0, 0, 380, gump_height, 30546)
    Gumps.AddAlphaRegion(gd, 0, 0, 380, gump_height)
    Gumps.AddLabel(gd, 2, 3, 68, " UO Mage Attack Script by Mike|Walker")
    Gumps.AddImageTiled(gd, 2, 25, 368, 2, 30547)

    sY = 30
    for section in sectionssorted:
        sY = buildSection(gd, section, sY, sections[section], 20, 5, values, skills)

    Gumps.SendGump(947567, Player.Serial, setX, setY, gd.gumpDefinition, gd.gumpStrings)
    return 947567


def buttoncheck(gumpId):

    Gumps.WaitForGump(gumpId, 9999999)
    Gumps.CloseGump(gumpId)
    gd = Gumps.GetGumpData(gumpId)

    # buttonid 0 = gump closed (right-click) — no action pressed
    if gd.buttonid <= 0:
        return

    raw_section = int(gd.buttonid / 1000)

    # Collapse toggle buttons use section offset +200
    if raw_section >= 200:
        actual_section = raw_section - 200
        key = "gump_col_%d" % actual_section
        Misc.SetSharedValue(key, 0 if Misc.ReadSharedValue(key) == 1 else 1)
        return

    # Increment buttons use section offset +100 (set in buildSection via incActionId)
    is_increment = raw_section >= 100
    actual_section = raw_section - 100 if is_increment else raw_section

    actions = list(sections.values())[actual_section]
    action = list(actions.values())[(gd.buttonid % 1000) - 1]
    if action is None:
        return

    if action['buttontype'] == "setsharedvalue":
        action['task'](action['sharedvalue'])
        Player.HeadMessage(50, "Set %s to %i" % (action['sharedvalue'], Misc.ReadSharedValue(action['sharedvalue'])))
    elif action['buttontype'] == "setvalue":
        current = Misc.ReadSharedValue(action['displayvalue'])
        min_val = action.get('minValue', 0)
        max_val = action.get('maxValue', 9999)
        step = action.get('step', 1)
        delta = step if is_increment else -step
        new_val = max(min_val, min(max_val, current + delta))
        Misc.SetSharedValue(action['displayvalue'], new_val)
        mark_settings_changed()
        labels = action.get('valueLabels', {})
        val_str = labels.get(new_val, str(new_val))
        Player.HeadMessage(50, "Set %s to %s" % (action['displayvalue'], val_str))
    elif action['buttontype'] == "cyclevalue":
        opts = action.get('options', [])
        if opts:
            current = Misc.ReadSharedValue(action['displayvalue'])
            try:
                idx = opts.index(current)
            except ValueError:
                idx = 0
            new_idx = (idx + 1) % len(opts)
            Misc.SetSharedValue(action['displayvalue'], opts[new_idx])
            mark_settings_changed()
            Player.HeadMessage(50, "Set %s to %s" % (action['displayvalue'], opts[new_idx]))
    elif action['buttontype'] == "slayerbook":
        Misc.SetSharedValue("slayer_swap_request", action['serial'])
        Player.HeadMessage(53, "Requested: %s" % action['label'])
    elif action['buttontype'] == "action":
        action['task']()


Player.HeadMessage(50, "Please set the Gump Script to LOOP MODE")

while True:
    try:
        buttoncheck(sendgump())
    except Exception as e:
        Player.HeadMessage(30, "GUMP error: %s" % str(e))
    Misc.Pause(300)
