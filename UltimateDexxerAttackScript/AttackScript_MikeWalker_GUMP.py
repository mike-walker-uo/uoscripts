### UO Ultimate Dexxer Attack Script GUMP by Mike|Walker ##########
### https://github.com/mike-walker-uo/uoscripts/tree/main/UltimateDexxerAttackScript
### Version 1.32 last edit 28.08.2026 ###
### Try to run at least Razor Enhanced Version 0.8.2.215 with fixed Skill Names ###
### SAVE THE SCRIPT AS .py file and add to the Python Script Section in Razor Enhanced ####


### START THE ATTACK SCRIPT FIRST
### SET THIS SCRIPT TO LOOP MODE

import json, os
from System.Collections.Generic import List

setX = 100
setY = 100
GUMP_ID = 947566

TAB_SETTINGS = 900001
TAB_SLAYER = 900002
SLAYER_REFRESH = 910001
SLAYER_AUTO = 910010
SLAYER_ADD_WEAPON = 910011
SLAYER_ADD_TALISMAN = 910012
SLAYER_DELETE_MODE = 910013
SLAYER_TOGGLE_WEAPON = 910020
SLAYER_TOGGLE_TALISMAN = 910021
SLAYER_WEAPON_ROW = 911000
SLAYER_TALISMAN_ROW = 912000
DRESS_NAME_ENTRY = 920001

_active_tab = 'settings'
_slayer_delmode = False
_slayer_render_data = {'weapons': [], 'talismans': [], 'mob_overrides': {}}

# ── Save / Load settings (mirrors AttackScript_MikeWalker.py) ───────────────
try:
    _script_dir = os.path.dirname(os.path.abspath(__file__)) or os.path.expanduser('~')
except:
    _script_dir = os.path.expanduser('~')
LEGACY_SETTINGS_FILE = os.path.join(_script_dir, "AttackScript_settings.json")
SETTINGS_FILE = os.path.join(
    _script_dir,
    "AttackScript_settings_%08X.json" % (int(Player.Serial) & 0xFFFFFFFF)
)
LEGACY_SLAYER_FILE = os.path.join(_script_dir, "AttackScript_SlayerSets.json")
SLAYER_FILE = os.path.join(
    _script_dir,
    "AttackScript_SlayerSets_%08X.json" % (int(Player.Serial) & 0xFFFFFFFF)
)

SETTINGS_KEYS = [
    "attack_blues", "attack_red_humans", "attack_blue_changelings",
    "use_messages",
    "use_bagofsending", "use_move_artis", "lootbag_serial",
    "use_trappedcrate", "use_townbuff",
    "use_checkforlegendaries", "use_checkforraremobs", "use_stopwarwhenrare",
    "use_distancemarker", "use_bluemarkermode",
    "use_dresslist", "dresslist_name",
    "use_arcanefocus", "use_summonfeys", "fey_threshold",
    "use_immolatingweapon", "use_attuneweapon", "use_thunderstorm",
    "use_eoo", "use_df", "use_cw", "use_holylight", "use_honor", "use_ca",
    "use_removecurse", "use_removepoison", "use_closewounds",
    "use_confidence", "use_evasion",
    "use_momentumstrike", "use_lightningstrike", "use_onslaught", "use_he",
    "use_mirrorimage", "use_releasemirrorimage", "use_whitetigerform", "use_deathstrike", "use_focusattack", "use_backstab", "use_smokebombs",
    "he_killshot_pct",
    "use_pot_refresh", "use_pot_cure", "use_pot_apple", "use_pot_heal_emergency",
    "stam_pot_pct", "heal_pot_pct", "quiver_low_threshold",
    "use_pet_sync", "use_smart_target", "use_smart_specials", "disable_weaponspecials",
    "use_slayer_swap", "use_slayer_talisman",
    "use_curseweapon", "use_playingtheodds",
    "attackrange", "nearbyrange", "honordistance",
]

def load_character_data():
    try:
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, 'r') as f:
                data = json.load(f)
            if isinstance(data, dict):
                return data
    except:
        pass
    return {}


def save_settings(extra_data=None):
    try:
        data = load_character_data()
        data.update({k: Misc.ReadSharedValue(k) for k in SETTINGS_KEYS})
        data.setdefault("ignored_mob_names", [])
        data.setdefault("ignored_mob_serials", [])
        data.setdefault("ignored_summon_names", [])
        if extra_data:
            data.update(extra_data)
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(data, f, indent=2)
        Player.HeadMessage(68, "Character settings saved!")
    except Exception as e:
        Player.HeadMessage(30, "Save failed: %s" % str(e))


def prompt_target(message):
    Misc.SetSharedValue("attack_gump_targeting", 1)
    try:
        return Target.PromptTarget(message)
    finally:
        Misc.SetSharedValue("attack_gump_targeting", 0)


def item_is_in_backpack(item):
    if not item or item.Deleted:
        return False
    backpack_serial = Player.Backpack.Serial
    seen = set()
    current = item
    while current and current.Serial not in seen:
        seen.add(current.Serial)
        container = current.Container
        try:
            container_serial = container.Serial
        except:
            container_serial = container
        if container_serial == backpack_serial:
            return True
        if not container_serial:
            return False
        current = Items.FindBySerial(container_serial)
    return False


def select_artifact_lootbag():
    serial = prompt_target("Select the artifact loot bag")
    if serial is None or serial <= 0:
        Player.HeadMessage(30, "Loot bag selection canceled")
        return 0
    if serial == Player.Backpack.Serial:
        Player.HeadMessage(30, "Select a bag inside the backpack, not the backpack")
        return 0
    lootbag = Items.FindBySerial(serial)
    if not lootbag:
        Player.HeadMessage(30, "Loot bag not found")
        return 0
    if not item_is_in_backpack(lootbag):
        Player.HeadMessage(30, "Loot bag must be inside your backpack")
        return 0
    return serial


# ── Slayer registry / manual equip ───────────────────────────────────────────
_PROP_GROUPS = (
    ('Undead',    ("silver", "undead slay")),
    ('Repond',    ("repond", "orc slay", "troll slay", "ogre slay")),
    ('Arachnid',  ("arachnid", "spider slay", "scorpion slay", "terathan")),
    ('Reptile',   ("reptile", "dragon slay", "lizardman slay", "snake slay", "ophidian")),
    ('Demon',     ("demon", "daemon", "exorcism", "gargoyle", "balron")),
    ('Elemental', ("elemental",)),
    ('Fey',       ("fey",)),
    ('Eodon',     ("eodon", "dinosaur", "myrmidex")),
)


def load_slayer_sets():
    data = {'weapons': [], 'talismans': [], 'mob_overrides': {}}
    try:
        if (not os.path.exists(SLAYER_FILE) and
                os.path.exists(LEGACY_SLAYER_FILE)):
            with open(LEGACY_SLAYER_FILE, 'r') as f:
                legacy_data = json.load(f)
            with open(SLAYER_FILE, 'w') as f:
                json.dump(legacy_data, f, indent=2)
            Player.HeadMessage(68, "Legacy Slayer sets imported for this character")
        if os.path.exists(SLAYER_FILE):
            with open(SLAYER_FILE, 'r') as f:
                loaded = json.load(f)
            for k in data:
                if k in loaded:
                    data[k] = loaded[k]
    except Exception as e:
        Player.HeadMessage(30, "Slayer sets load failed: %s" % str(e))
    return data


def save_slayer_sets(data):
    try:
        with open(SLAYER_FILE, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        Player.HeadMessage(30, "Slayer sets save failed: %s" % str(e))


def detect_slayer_group(serial):
    Items.WaitForProps(serial, 1000)
    props = [str(p).lower() for p in Items.GetPropStringList(serial)]
    for group, keywords in _PROP_GROUPS:
        for prop in props:
            for keyword in keywords:
                if keyword in prop:
                    return group
    return 'none'


def register_slayer_item(kind_key, kind_label):
    serial = prompt_target("Select the %s to register" % kind_label)
    if serial is None or serial <= 0:
        Player.HeadMessage(30, "Registration canceled")
        return
    item = Items.FindBySerial(serial)
    if not item:
        Player.HeadMessage(30, "Item not found")
        return
    group = detect_slayer_group(serial)
    name = item.Name or ("0x%X" % serial)
    data = load_slayer_sets()
    data[kind_key] = [e for e in data[kind_key] if e.get('serial') != serial]
    data[kind_key].append({'serial': serial, 'name': name, 'group': group})
    save_slayer_sets(data)
    Player.HeadMessage(68, "Registered %s: %s [%s]" % (kind_label, name, group))
    if group == 'none':
        Player.HeadMessage(50, "No slayer property found -> neutral/default item")


def current_weapon_serial():
    weapon = Player.GetItemOnLayer('FirstValid')
    if not weapon:
        weapon = Player.GetItemOnLayer('LeftHand')
    return weapon.Serial if weapon else 0


def current_talisman_serial():
    talisman = Player.GetItemOnLayer('Talisman')
    return talisman.Serial if talisman else 0


def manual_slayer_equip(entry, is_weapon):
    serial = entry.get('serial', 0)
    item = Items.FindBySerial(serial)
    if not item:
        Player.HeadMessage(30, "Item missing: %s" % entry.get('name', '?'))
        return

    if is_weapon:
        if current_weapon_serial() == serial:
            Player.HeadMessage(50, "Already equipped")
        else:
            current = Player.GetItemOnLayer('FirstValid')
            if not current:
                current = Player.GetItemOnLayer('LeftHand')
            if current:
                right = Player.GetItemOnLayer('RightHand')
                if right and right.Serial == current.Serial:
                    Player.UnEquipItemByLayer('RightHand')
                else:
                    Player.UnEquipItemByLayer('LeftHand')
                Misc.Pause(600)
            Player.EquipItem(serial)
            Misc.Pause(600)
    else:
        if current_talisman_serial() == serial:
            Player.HeadMessage(50, "Already equipped")
        else:
            if Player.GetItemOnLayer('Talisman'):
                Player.UnEquipItemByLayer('Talisman')
                Misc.Pause(600)
            Player.EquipItem(serial)
            Misc.Pause(600)

    equipped_serial = current_weapon_serial() if is_weapon else current_talisman_serial()
    if equipped_serial != serial:
        Player.HeadMessage(30, "Equip failed: %s" % entry.get('name', '?'))
        return

    group = Misc.ReadSharedValue("slayer_target_group") or 'none'
    Misc.SetSharedValue("slayer_hold", 1)
    Misc.SetSharedValue("slayer_hold_group", group)
    Player.HeadMessage(68, "Manual: %s [HOLD until group change]" % entry.get('name', '?'))


def delete_slayer_entry(data, kind_key, entry):
    data[kind_key] = [e for e in data[kind_key]
                      if e.get('serial') != entry.get('serial')]
    save_slayer_sets(data)
    Player.HeadMessage(30, "Removed: %s" % entry.get('name', '?'))
# ────────────────────────────────────────────────────────────────────────────

class Sharedvalue:
    name = ''
    defaultvalue = 0
 
    def __init__ ( self, name, defaultvalue):
        self.name = name
        self.defaultvalue = defaultvalue
    
def SetSharedValue(sharedvalue):
    val = Misc.ReadSharedValue(sharedvalue)
    Misc.SetSharedValue(sharedvalue, 0 if val == 1 else 1)

def SetNinjitsuAttack(sharedvalue):
    val = Misc.ReadSharedValue(sharedvalue)
    new_value = 0 if val == 1 else 1
    Misc.SetSharedValue(sharedvalue, new_value)
    if new_value == 1:
        for other in ("use_deathstrike", "use_focusattack", "use_backstab"):
            if other != sharedvalue:
                Misc.SetSharedValue(other, 0)
        Player.WeaponClearSA()


def gump_dresslist_name(gump_data):
    try:
        return str(Gumps.GetTextByID(gump_data, DRESS_NAME_ENTRY) or "").strip()
    except:
        return str(Misc.ReadSharedValue("dresslist_name") or "").strip()


def save_dresslist_name(gump_data):
    name = gump_dresslist_name(gump_data)
    Misc.SetSharedValue("dresslist_name", name)
    if not name and Misc.ReadSharedValue("use_dresslist") == 1:
        Misc.SetSharedValue("use_dresslist", 0)
        Player.HeadMessage(30, "Dress List disabled: no list name saved")
    elif name and Misc.ReadSharedValue("use_dresslist") == 1:
        Dress.ChangeList(name)
        Dress.DressFStart()
    save_settings()
    Player.HeadMessage(68, "Dress List name saved: %s" % (name or "<empty>"))


def toggle_dresslist(gump_data):
    if Misc.ReadSharedValue("use_dresslist") == 1:
        Misc.SetSharedValue("use_dresslist", 0)
        save_settings()
        Player.HeadMessage(50, "Dress List: OFF")
        return

    name = gump_dresslist_name(gump_data)
    if not name:
        Player.HeadMessage(30, "Enter and save a Dress List name first")
        return
    Misc.SetSharedValue("dresslist_name", name)
    Misc.SetSharedValue("use_dresslist", 1)
    Dress.ChangeList(name)
    Dress.DressFStart()
    save_settings()
    Player.HeadMessage(68, "Dress List: ON [%s]" % name)


def normalized_serials(values):
    serials = set()
    for value in values or []:
        try:
            serials.add(int(value))
        except:
            pass
    return serials


def bump_ignore_revision():
    try:
        revision = int(Misc.ReadSharedValue("attack_ignore_revision") or 0)
    except:
        revision = 0
    Misc.SetSharedValue("attack_ignore_revision", revision + 1)


def set_target_ignored(ignore):
    prompt = "Select the specific mobile to ignore" if ignore else "Select the specific mobile to unignore"
    serial = prompt_target(prompt)
    if serial is None or serial <= 0:
        Player.HeadMessage(30, "Mob selection canceled")
        return
    mob = Mobiles.FindBySerial(serial)
    if not mob or mob.Serial == Player.Serial:
        Player.HeadMessage(30, "Select a mobile other than yourself")
        return

    data = load_character_data()
    serials = normalized_serials(data.get("ignored_mob_serials", []))
    labels = data.get("ignored_mob_labels", {})
    if not isinstance(labels, dict):
        labels = {}
    name = mob.Name or ("0x%X" % serial)

    if ignore:
        serials.add(int(serial))
        labels[str(int(serial))] = name
        Misc.IgnoreObject(mob)
        message = "Permanently ignored: %s [0x%X]" % (name, serial)
    else:
        serials.discard(int(serial))
        labels.pop(str(int(serial)), None)
        Misc.UnIgnoreObject(mob)
        message = "Removed permanent ignore: %s [0x%X]" % (name, serial)

    save_settings({
        "ignored_mob_serials": sorted(serials),
        "ignored_mob_labels": labels,
    })
    bump_ignore_revision()
    Player.HeadMessage(68, message)
 

def mySort(e):
  return e['name']
    
    
sections = {

        '1: Status & Ranges': 
        {
            'Attack Off':
                {
                'buttontype':"setsharedvalue",
                'sharedvalue':"activeattack",
                'task':SetSharedValue,
                'tooltip':"you can pause the attack here, even if there are mobs around",
                },
            'RefreshGUMP':
                {
                'buttontype':"setsharedvalue",
                'sharedvalue':"",
                'task':SetSharedValue,
                'tooltip':"refresh this gump without changing an setting",
                },
            'AttackRange':
                {
                'buttontype':"setvalue",
                'displayvalue':"attackrange",
                'minValue':1,
                'maxValue':25,
                'tooltip':"Range of mobs you will attack. (Default: 10 for melee, 16 for ranged)",
                },
            'HonorRange':
                {
                'buttontype':"setvalue",
                'displayvalue':"honordistance",
                'minValue':1,
                'maxValue':25,
                'tooltip':"Range to honor mobs (Default == Max: 10 tiles)",
                },
            'NearbyRange':
                {
                'buttontype':"setvalue",
                'displayvalue':"nearbyrange",
                'minValue':1,
                'maxValue':25,
                'tooltip':"Range that determines weapon specials and distance markers (Default: 1 for melee, 10 for ranged)",
                },
            'SaveSettings':
                {
                'buttontype':"savesettings",
                'tooltip':"Save all current settings to file so they reload automatically on next script start",
                },
        },
        '2: Global': 
        {
            'Messages':
                {
                'buttontype':"setsharedvalue",
                'sharedvalue':"use_messages",
                'task':SetSharedValue,
                'tooltip':"if you want to see overhead messages for most actions",
                },
            'AttackBlue':
                {
                'buttontype':"setsharedvalue",
                'sharedvalue':"attack_blues",
                'task':SetSharedValue,
                'tooltip':"if you want attack blue mobs",
                },
            'AttackRedHumans':
                {
                'buttontype':"setsharedvalue",
                'sharedvalue':"attack_red_humans",
                'task':SetSharedValue,
                'tooltip':"if you want attack red humans. If there are any red players around and you dont want to attack them disable this feature",
                },
            'AttackBlueChangeling':
                {
                'buttontype':"setsharedvalue",
                'sharedvalue':"attack_blue_changelings",
                'task':SetSharedValue,
                'tooltip':"sometimes changelings will mimic you and get blue. If you hunt them in the Twisted Weald activate this feature",
                },
            'BagOfSending':
                {
                'buttontype':"setsharedvalue",
                'sharedvalue':"use_bagofsending",
                'task':SetSharedValue,
                'tooltip':"if you have a Bag of Sending the script will automatically send Gold to the bank if you are almost overweight",
                },
            'MoveArtisToLootBag':
                {
                'buttontype':"lootbagtoggle",
                'sharedvalue':"use_move_artis",
                'tooltip':"Move named artifacts from anywhere in your backpack to a selected loot bag. Enabling asks you to target the bag and saves it to the current profile.",
                },
            'TrappedCrate':
                {
                'buttontype':"setsharedvalue",
                'sharedvalue':"use_trappedcrate",
                'task':SetSharedValue,
                'tooltip':"if you use a Trapped Crate (really useful when paralyzed)",
                },
            'TownBuff':
                {
                'buttontype':"setsharedvalue",
                'sharedvalue':"use_townbuff",
                'task':SetSharedValue,
                'tooltip':"if you use the Town Buff (City Trade Deal) it will check if its active",
                },
            'CheckforLegendaries':
                {
                'buttontype':"setsharedvalue",
                'sharedvalue':"use_checkforlegendaries",
                'task':SetSharedValue,
                'tooltip':"if you have 120 Lore & Tame (real skills not necessary) you have a chance of spawning a legendary pet in certain areas. This feature will make an annoying sound and overhead text when a legendary spawns",
                },
            'CheckforRare':
                {
                'buttontype':"setsharedvalue",
                'sharedvalue':"use_checkforraremobs",
                'task':SetSharedValue,
                'tooltip':"this will show an overhead message if there is an rare mob (with purple Rare tag) nearby)",
                },
            'StopWhenRare':
                {
                'buttontype':"setsharedvalue",
                'sharedvalue':"use_stopwarwhenrare",
                'task':SetSharedValue,
                'tooltip':"this will stop the attack script if there is an rare mob nearby",
                },
            'DistanceMarker':
                {
                'buttontype':"setsharedvalue",
                'sharedvalue':"use_distancemarker",
                'task':SetSharedValue,
                'tooltip':"if you want to use Distance Markers. It will show colored triangles over the mobs if you are in attack range or not",
                },
            'BlueDistanceMarker':
                {
                'buttontype':"setsharedvalue",
                'sharedvalue':"use_bluemarkermode",
                'task':SetSharedValue,
                'tooltip':"if use Distance Markers and want to use blue triangles (1-3) instead of colored ones. Better vision for visually impaired players.",
                },
            'Dress List':
                {
                'buttontype':"dresslisttoggle",
                'sharedvalue':"use_dresslist",
                'tooltip':"Maintain the per-character Razor Enhanced Dress List named below. Enter and save its exact name before enabling.",
                },
            'Dress List Name':
                {
                'buttontype':"dresslistname",
                'entryid':DRESS_NAME_ENTRY,
                'tooltip':"Exact Razor Enhanced Dress/Arm list name for this character.",
                },
            'Ignore Target':
                {
                'buttontype':"ignoretarget",
                'tooltip':"Target one specific mobile. Its serial is ignored immediately and saved for this character.",
                },
            'Unignore Target':
                {
                'buttontype':"unignoretarget",
                'tooltip':"Target a previously ignored mobile to remove its permanent per-character ignore.",
                },
          
        },
        '4: Spells': 
        {
                'CheckArcaneFocus':
                {
                'buttontype':"setsharedvalue",
                'skillCheck':'Spellweaving',
                'skillValue':0,
                'sharedvalue':"use_arcanefocus",
                'task':SetSharedValue,
                'tooltip':"Even with 0 SW you can use Arcane Focus to get +6 STR for 2 hours. This will check if you have Arcane Focus",
                },
                'SummonFeys':
                {
                'buttontype':"setsharedvalue",
                'skillCheck':'Spellweaving',
                'skillValue':38,
                'sharedvalue':"use_summonfeys",
                'task':SetSharedValue,
                'tooltip':"If you use the feys as tanks (really funny) use this feature. It will automatically cast them when they have died",
                },
                'ImmolatingWeapon':
                {
                'buttontype':"setsharedvalue",
                'skillCheck':'Spellweaving',
                'skillValue':0,
                'sharedvalue':"use_immolatingweapon",
                'task':SetSharedValue,
                'tooltip':"this feature will cast Immolating Weapon regularly(adding some fire dmg to your weapon)",
                },
                'AttuneWeapon':
                {
                'buttontype':"setsharedvalue",
                'skillCheck':'Spellweaving',
                'skillValue':0,
                'sharedvalue':"use_attuneweapon",
                'task':SetSharedValue,
                'tooltip':"this feature will cast Attunement to have a (depleting) shield against physical damage",
                },
                'Thunderstorm':
                {
                'buttontype':"setsharedvalue",
                'skillCheck':'Spellweaving',
                'skillValue':0,
                'sharedvalue':"use_thunderstorm",
                'task':SetSharedValue,
                'tooltip':"this feature will cast Thunderstorm if there are more than 3 mobs in Thunderstorm range, but not in melee range",
                },
        },
        '3: Attacks': 
        {
                'EnemyOfOne':
                {
                'buttontype':"setsharedvalue",
                'skillCheck':'Chivalry',
                'skillValue':45,
                'sharedvalue':"use_eoo",
                'task':SetSharedValue,
                'tooltip':"this feature will cast Enemy Of One, when there is only one mob or only one type of mobs in range. It will auto deactivate EoO when there are mob groups to avoid increased damage taken.",
                },
                'DivineFury':
                {
                'buttontype':"setsharedvalue",
                'skillCheck':'Chivalry',
                'skillValue':25,
                'sharedvalue':"use_df",
                'task':SetSharedValue,
                'tooltip':"this feature will cast / check for Divine Fury before you attack mobs",
                },
                'ConsWeap':
                {
                'buttontype':"setsharedvalue",
                'skillCheck':'Chivalry',
                'skillValue':15,
                'sharedvalue':"use_cw",
                'task':SetSharedValue,
                'tooltip':"this feature will cast / check for Consecrated Weapon before you attack mobs",
                },
                'Holy Light':
                {
                'buttontype':"setsharedvalue",
                'skillCheck':'Chivalry',
                'skillValue':55,
                'sharedvalue':"use_holylight",
                'task':SetSharedValue,
                'tooltip':"Cast Holy Light when at least 3 mobs are within its 3-tile radius. If Mirror Image is enabled, waits for 3 occupied follower slots. Suppressed during Blood Oath.",
                },
                'Honor':
                {
                'buttontype':"setsharedvalue",
                'skillCheck':'Bushido',
                'skillValue':0,
                'sharedvalue':"use_honor",
                'task':SetSharedValue,
                'tooltip':"if you want to honor your mobs (either for Honor Taming or Bushido Perfection system)",
                },
                'CounterAttack':
                {
                'buttontype':"setsharedvalue",
                'skillCheck':'Parry',
                'skillValue':10,
                'sharedvalue':"use_ca",
                'task':SetSharedValue,
                'tooltip':"if you want to use Counter Attack (needs Bushido & Parry)",
                },
                'RemoveCurse':
                {
                'buttontype':"setsharedvalue",
                'skillCheck':'Chivalry',
                'skillValue':5,
                'sharedvalue':"use_removecurse",
                'task':SetSharedValue,
                'tooltip':"this feature will cast Chiv Remove Curse if there are no mobs in range (6) or if you are cursed with Blood Oath",
                },
                'RemovePoison':
                {
                'buttontype':"setsharedvalue",
                'skillCheck':'Chivalry',
                'skillValue':5,
                'sharedvalue':"use_removepoison",
                'task':SetSharedValue,
                'tooltip':"this feature will cast Chiv Remove Poison if there are no mobs in range (6)",
                },
                'Confidence':
                {
                'buttontype':"setsharedvalue",
                'skillCheck':'Bushido',
                'skillValue':25,
                'sharedvalue':"use_confidence",
                'task':SetSharedValue,
                'tooltip':"this feature will cast Confidence if you are hit",
                },
                'Evasion':
                {
                'buttontype':"setsharedvalue",
                'skillCheck':'Bushido',
                'skillValue':60,
                'sharedvalue':"use_evasion",
                'task':SetSharedValue,
                'tooltip':"this feature will cast Evasion if you are hit",
                },
                'CloseWounds':
                {
                'buttontype':"setsharedvalue",
                'skillCheck':'Chivalry',
                'skillValue':0,
                'sharedvalue':"use_closewounds",
                'task':SetSharedValue,
                'tooltip':"this feature will cast Chiv Close Wounds if there are no mobs in range (6)",
                },
                'MomentumStrike':
                {
                'buttontype':"setsharedvalue",
                'skillCheck':'Bushido',
                'skillValue':70,
                'sharedvalue':"use_momentumstrike",
                'task':SetSharedValue,
                'tooltip':"Low-mana fallback for multiple mobs. Weapon specials always have priority; never replaces an active or pending weapon special.",
                },
                'LightningStrike':
                {
                'buttontype':"setsharedvalue",
                'skillCheck':'Bushido',
                'skillValue':50,
                'sharedvalue':"use_lightningstrike",
                'task':SetSharedValue,
                'tooltip':"With one mob, use Lightning Strike whenever it is enabled if Weapon Specials Off is active. With weapon specials enabled, use it only as the low-mana fallback. Never replaces an active or pending combat move.",
                },
                'Weapon Specials Off':
                {
                'buttontype':"setsharedvalue",
                'sharedvalue':"disable_weaponspecials",
                'task':SetSharedValue,
                'tooltip':"Disable automatic primary and secondary weapon abilities, including Feint and Whirlwind. Enabled Lightning Strike becomes the normal single-target attack instead of a low-mana fallback. Focus Attack, Death Strike, Momentum Strike, Onslaught, and other spell-based attacks remain available.",
                },
                'Onslaught':
                {
                'buttontype':"setsharedvalue",
                'skillCheck':'Swordsmanship',
                'skillValue':90,
                'sharedvalue':"use_onslaught",
                'task':SetSharedValue,
                'tooltip':"this feature will use the Swords Mastery Onslaught on mobs, but only if you not one/two-hit them",
                },
                'HonorableExec':
                {
                'buttontype':"setsharedvalue",
                'skillCheck':'Bushido',
                'skillValue':25,
                'sharedvalue':"use_he",
                'task':SetSharedValue,
                'tooltip':"Bushido Honorable Execution as finisher — fires only when nearest is at killshot HP (default <=15% bar). On kill: -resist self-debuff suppressed, +HCI/SSI buff ~20s for next mob.",
                },
                'Mirror Image':
                {
                'buttontype':"setsharedvalue",
                'skillCheck':'Ninjitsu',
                'skillValue':20,
                'sharedvalue':"use_mirrorimage",
                'task':SetSharedValue,
                'tooltip':"Cast Mirror Image only while a mob is within AttackRange and fewer than 3 follower slots are occupied. Stops at 3 occupied slots; cannot cast while mounted.",
                },
                'Release Mirror':
                {
                'buttontype':"setsharedvalue",
                'skillCheck':'Ninjitsu',
                'skillValue':20,
                'sharedvalue':"use_releasemirrorimage",
                'task':SetSharedValue,
                'tooltip':"At exactly 4 occupied follower slots, release one verified Mirror Image only while an attackable mob is within AttackRange. Never releases without a nearby mob, preventing accidental bleed damage.",
                },
                'White Tiger Form':
                {
                'buttontype':"setsharedvalue",
                'skillCheck':'Ninjitsu',
                'skillValue':120,
                'skillCheck2':'Stealth',
                'skillValue2':120,
                'sharedvalue':"use_whitetigerform",
                'task':SetSharedValue,
                'tooltip':"Maintain Ninjitsu Mastery White Tiger Form with 120 Ninjitsu and 120 Stealth. Requires the Ninjitsu mastery path and dismounts you.",
                },
                'Death Strike':
                {
                'buttontype':"setsharedvalue",
                'skillCheck':'Ninjitsu',
                'skillValue':85,
                'sharedvalue':"use_deathstrike",
                'task':SetNinjitsuAttack,
                'tooltip':"Use Death Strike instead of weapon abilities and other combat special moves. Enabling it disables Focus Attack and Backstab Loop.",
                },
                'Focus Attack':
                {
                'buttontype':"setsharedvalue",
                'skillCheck':'Ninjitsu',
                'skillValue':30,
                'sharedvalue':"use_focusattack",
                'task':SetNinjitsuAttack,
                'tooltip':"Use Focus Attack instead of weapon abilities and other combat special moves. Melee weapon only; no shield. Enabling it disables Death Strike and Backstab Loop.",
                },
                'Backstab Loop':
                {
                'buttontype':"setsharedvalue",
                'skillCheck':'Ninjitsu',
                'skillValue':40,
                'skillCheck2':'Stealth',
                'skillValue2':80,
                'sharedvalue':"use_backstab",
                'task':SetNinjitsuAttack,
                'tooltip':"Cycle Shadow Strike, take one walking Stealth step while staying beside the locked target, Backstab, then five seconds of visible filler combat. With Smoke/Egg Bombs enabled, a backpack bomb can hide you after Shadow Strike is unavailable or misses, and can run the cycle without a Shadow Strike weapon. Requires 30 real Hiding. Enabling this disables Death Strike and Focus Attack.",
                },
                'Smoke/Egg Bombs':
                {
                'buttontype':"setsharedvalue",
                'skillCheck':'Ninjitsu',
                'skillValue':50,
                'sharedvalue':"use_smokebombs",
                'task':SetSharedValue,
                'tooltip':"Use an Egg Bomb or Smoke Bomb (item 0x2808/0x2809) from the backpack as a Backstab hiding fallback. Shadow Strike remains preferred. Bombs are only used with Backstab Loop and a locked nearby target; if no bomb is found, the normal combat loop continues.",
                },
                'CurseWeapon':
                {
                'buttontype':"setsharedvalue",
                'skillCheck':'Necromancy',
                'skillValue':0,
                'sharedvalue':"use_curseweapon",
                'task':SetSharedValue,
                'tooltip':"this feature will use Necromancy Cursed Weapon to gain addional 50% Life Leech when you are low on HP",
                },
                'PlayingTheOdds':
                {
                'buttontype':"setsharedvalue",
                'skillCheck':'Archery',
                'skillValue':90,
                'sharedvalue':"use_playingtheodds",
                'task':SetSharedValue,
                'tooltip':"this feature will use the Archery Mastery Playing the Odds to buff your allies and pets, but lower the attack range",
                },
                'CheckBandages':
                {
                'buttontype':"setsharedvalue",
                'sharedvalue':"use_bandages",
                'task':SetSharedValue,
                'tooltip':"this feature will check if you have enough bandages with you",
                },
                'CheckArrows':
                {
                'buttontype':"setsharedvalue",
                'skillCheck':'Archery',
                'skillValue':40,
                'sharedvalue':"use_arrows",
                'task':SetSharedValue,
                'tooltip':"this feature will check if you have enough arrows with you",
                },
                'VampiricEmbrace':
                {
                'buttontype':"setsharedvalue",
                'skillCheck':'Necromancy',
                'skillValue':99,
                'sharedvalue':"use_vampiricembrace",
                'task':SetSharedValue,
                'tooltip':"this feature will check if you have Vampiric Embrace",
                },
        },

        '5: Potions & Convenience':
        {
                'PotRefresh':
                {
                'buttontype':"setsharedvalue",
                'sharedvalue':"use_pot_refresh",
                'task':SetSharedValue,
                'tooltip':"Auto-quaff Greater Refresh when stam below threshold (critical for archer swing speed). 10s pot cooldown respected.",
                },
                'PotCure':
                {
                'buttontype':"setsharedvalue",
                'sharedvalue':"use_pot_cure",
                'task':SetSharedValue,
                'tooltip':"Auto-quaff Greater Cure when poisoned AND not enough mana for Chiv Cleanse by Fire. 10s cooldown.",
                },
                'PotApple':
                {
                'buttontype':"setsharedvalue",
                'sharedvalue':"use_pot_apple",
                'task':SetSharedValue,
                'tooltip':"Use Enchanted Apple (item 0x2FD8) only for Blood Oath (60s cooldown), then immediately use Remove Curse if the apple is disabled, missing, cooling down, or unsuccessful. Never consumes apples for other curses.",
                },
                'PotHealEmergency':
                {
                'buttontype':"setsharedvalue",
                'sharedvalue':"use_pot_heal_emergency",
                'task':SetSharedValue,
                'tooltip':"Auto-quaff Greater Heal pot at very low HP as VE-leech fallback. Opt-in: VE usually covers. 10s cooldown.",
                },
                'PetSync':
                {
                'buttontype':"setsharedvalue",
                'sharedvalue':"use_pet_sync",
                'task':SetSharedValue,
                'tooltip':"Issue 'all kill' to pets/summons whenever the player target changes. Throttled (no spam on same target). For tamers and fey/EV builds.",
                },
                'SmartTarget':
                {
                'buttontype':"setsharedvalue",
                'sharedvalue':"use_smart_target",
                'task':SetSharedValue,
                'tooltip':"Score-based target picker: locks Onslaught primary (prevents stack waste), prioritizes paragons + caster/healer mob IDs. Opt-in: changes core targeting. Tune SMART_TARGET_CASTER_IDS / HEALER_IDS in script.",
                },
                'SmartSpecials':
                {
                'buttontype':"setsharedvalue",
                'sharedvalue':"use_smart_specials",
                'task':SetSharedValue,
                'tooltip':"Context-aware single-target weapon special slot: Mortal Strike on paragons/healers, Paralyzing/Concussion Blow on casters, Armor Ignore as Onslaught finisher. Falls back to weapon's configured singleenemyspecial. Tune mob ID sets in script.",
                },
                'SlayerWeapSwap':
                {
                'buttontype':"setsharedvalue",
                'sharedvalue':"use_slayer_swap",
                'task':SetSharedValue,
                'tooltip':"Auto-equip the matching slayer WEAPON for the current target group (Undead/Repond/Arachnid/Reptile/Demon/Elemental/Fey/Eodon). Register and manually equip weapons on the Slayer tab.",
                },
                'SlayerTalisman':
                {
                'buttontype':"setsharedvalue",
                'sharedvalue':"use_slayer_talisman",
                'task':SetSharedValue,
                'tooltip':"Auto-equip the matching slayer TALISMAN for the current target group. Register and manually equip talismans on the Slayer tab.",
                },
        },

    }

# Precompute section indices once — avoids O(n) list(sections).index(title) on every render
_section_indices = {title: i for i, title in enumerate(sections)}

def action_skills_met(action):
    if ('skillCheck' in action and
            Player.GetSkillValue(action['skillCheck']) < action['skillValue']):
        return False
    if ('skillCheck2' in action and
            Player.GetSkillValue(action['skillCheck2']) < action['skillValue2']):
        return False
    return True

def calc_section_height(title, actions):
    """Mirror buildSection() row logic to compute height without rendering."""
    sectionIndex_raw = _section_indices[title]
    collapsed = Misc.ReadSharedValue("gump_col_%d" % sectionIndex_raw) == 1
    if collapsed:
        return 20  # header only

    validActions = []
    for action_key in actions:
        a = actions[action_key]
        name = action_key
        if 'displayvalue' in a:
            name = action_key + ": " + str(Misc.ReadSharedValue(a['displayvalue']))
        if action_skills_met(a):
            validActions.append({'name': name, 'buttontype': a.get('buttontype', ''),
                                  'displayvalue': 'displayvalue' in a})

    if len(validActions) == 0:
        return 20

    validActions.sort(key=lambda x: x['name'])

    increments = 0
    first_item = True
    col = 0
    for action in validActions:
        is_fullrow = (action['displayvalue'] or
                      action['buttontype'] in ('savesettings', 'dresslistname'))
        if is_fullrow:
            if not first_item:
                increments += 20
            col = 0
            first_item = False
        else:
            if col == 0 and not first_item:
                increments += 20
            first_item = False
            col = (col + 1) % 2

    return 20 + increments + 20  # header + row increments + final row

def buildSection(gd, title, sy, actions, sectionhue, titleX=0):
    if gd is None or title is None:
        return sy

    # Button-ID scheme (sectionIndex_raw = insertion-order index):
    #   regular toggle : sectionIndex_raw * 1000 + i + 1         (0 – 3 999)
    #   increment  (+) : (sectionIndex_raw + 100) * 1000 + i + 1 (100 001 – 103 999)
    #   decrement  (−) : (sectionIndex_raw + 200) * 1000 + i + 1 (200 001 – 203 999)
    #   collapse       : (sectionIndex_raw + 300) * 1000          (300 000 – 303 000)
    sectionIndex_raw = _section_indices[title]
    col_key          = "gump_col_%d" % sectionIndex_raw
    collapsed        = Misc.ReadSharedValue(col_key) == 1
    collapse_id      = (sectionIndex_raw + 300) * 1000

    # Section header with collapse toggle
    arrow = "► " if collapsed else "▼ "
    Gumps.AddButton(gd, titleX, sy, 9762, 9763, collapse_id, 1, 0)
    Gumps.AddLabel(gd, titleX + 15, sy, 52, arrow + title)
    sy += 20

    if collapsed:
        return sy

    # Build valid-action list (enumerate over raw dict to keep index stable)
    validActions = []
    for i, action_key in enumerate(actions):
        a = dict(actions[action_key])           # copy — do NOT mutate global sections
        a['_key']        = action_key
        a['name']        = action_key
        a['hue']         = 900
        a['actionId']    = sectionIndex_raw * 1000 + i + 1
        a['incActionId'] = (sectionIndex_raw + 100) * 1000 + i + 1
        a['decActionId'] = (sectionIndex_raw + 200) * 1000 + i + 1

        if 'sharedvalue' in a:
            val = Misc.ReadSharedValue(a['sharedvalue'])
            if val == 1:
                a['hue'] = 68
                if a['sharedvalue'] == "activeattack":
                    a['name'] = "Attack On"
                    a['hue']  = 32

        if 'displayvalue' in a:
            val = Misc.ReadSharedValue(a['displayvalue'])
            a['hue']  = 88
            a['name'] = action_key + ": " + str(val)

        if action_skills_met(a):
            validActions.append(a)

    if len(validActions) == 0:
        return sy

    validActions.sort(key=lambda x: x['name'])

    actionY    = sy
    first_item = True
    col        = 0                              # column tracker for 2-col toggle rows

    for action in validActions:
        btype      = action.get('buttontype', '')
        is_fullrow = ('displayvalue' in action or
                      btype in ('savesettings', 'dresslistname'))

        if is_fullrow:
            if not first_item:
                actionY += 20
            col        = 0
            first_item = False

            if 'displayvalue' in action:
                val = Misc.ReadSharedValue(action['displayvalue'])
                Gumps.AddLabel(gd, 5, actionY, action['hue'],
                               action['_key'] + ": " + str(val))
                if 'tooltip' in action:
                    Gumps.AddTooltip(gd, str(action['tooltip']))
                # − button
                Gumps.AddButton(gd, 185, actionY, 9762, 9763, action['decActionId'], 1, 0)
                Gumps.AddLabel(gd, 205, actionY, 900, "-")
                # + button
                Gumps.AddButton(gd, 225, actionY, 9762, 9763, action['incActionId'], 1, 0)
                Gumps.AddLabel(gd, 245, actionY, 900, "+")

            elif btype == 'savesettings':
                Gumps.AddButton(gd, 5, actionY, 9762, 9763, action['actionId'], 1, 0)
                Gumps.AddLabel(gd, 25, actionY, 68, action['_key'])
                if 'tooltip' in action:
                    Gumps.AddTooltip(gd, str(action['tooltip']))

            else:   # dresslistname
                current_name = str(Misc.ReadSharedValue("dresslist_name") or "")
                Gumps.AddLabel(gd, 5, actionY, 900, "Dress List:")
                Gumps.AddTextEntry(gd, 75, actionY, 135, 20, 88,
                                   action['entryid'], current_name)
                if 'tooltip' in action:
                    Gumps.AddTooltip(gd, str(action['tooltip']))
                Gumps.AddButton(gd, 220, actionY, 9762, 9763,
                                action['actionId'], 1, 0)
                Gumps.AddLabel(gd, 240, actionY, 68, "Save")

        else:
            # Two-column toggle row
            if col == 0:
                if not first_item:
                    actionY += 20
                actionX = 5
            else:
                actionX = 135
            first_item = False

            Gumps.AddButton(gd, actionX, actionY, 9762, 9763, action['actionId'], 1, 0)
            actionX += 20
            Gumps.AddLabel(gd, actionX, actionY, action['hue'], action['name'])
            if 'tooltip' in action:
                Gumps.AddTooltip(gd, str(action['tooltip']))
            col = (col + 1) % 2

    return actionY + 20

def add_gump_shell(gd, height, active_tab):
    Gumps.AddBackground(gd, 0, 0, 300, height, 30546)
    Gumps.AddAlphaRegion(gd, 0, 0, 300, height)
    Gumps.AddLabel(gd, 2, 3, 68, " UO Ultimate Attack Script by Mike|Walker")
    Gumps.AddImageTiled(gd, 2, 22, 288, 2, 30547)

    settings_hue = 68 if active_tab == 'settings' else 900
    slayer_hue = 68 if active_tab == 'slayer' else 900
    Gumps.AddButton(gd, 5, 27, 9762, 9763, TAB_SETTINGS, 1, 0)
    Gumps.AddLabel(gd, 25, 27, settings_hue, "Settings")
    Gumps.AddButton(gd, 115, 27, 9762, 9763, TAB_SLAYER, 1, 0)
    Gumps.AddLabel(gd, 135, 27, slayer_hue, "Slayer Sets")
    Gumps.AddImageTiled(gd, 2, 47, 288, 2, 30547)


def build_settings_gump():
    sectionssorted = sorted(sections)
    gump_height = 52
    for section in sectionssorted:
        gump_height += calc_section_height(section, sections[section])
    gump_height += 10

    gd = Gumps.CreateGump(movable=True)
    Gumps.AddPage(gd, 0)
    add_gump_shell(gd, gump_height, 'settings')

    section_y = 52
    for section in sectionssorted:
        section_y = buildSection(gd, section, section_y, sections[section], 20, 5)
    return gd


def build_slayer_gump():
    global _slayer_render_data
    _slayer_render_data = load_slayer_sets()
    weapons = _slayer_render_data['weapons']
    talismans = _slayer_render_data['talismans']
    height = 175 + (len(weapons) + len(talismans)) * 20

    gd = Gumps.CreateGump(movable=True)
    Gumps.AddPage(gd, 0)
    add_gump_shell(gd, height, 'slayer')

    group = Misc.ReadSharedValue("slayer_target_group") or '-'
    hold = Misc.ReadSharedValue("slayer_hold") == 1
    Gumps.AddLabel(gd, 5, 55, 88, "Target group: %s" % group)
    Gumps.AddButton(gd, 175, 55, 9762, 9763, SLAYER_AUTO, 1, 0)
    Gumps.AddLabel(gd, 195, 55, 32 if hold else 68, "HOLD" if hold else "AUTO")
    Gumps.AddTooltip(gd, "Clear manual HOLD and return slayer swapping to AUTO")
    Gumps.AddButton(gd, 250, 55, 9762, 9763, SLAYER_REFRESH, 1, 0)
    Gumps.AddLabel(gd, 270, 55, 900, "R")
    Gumps.AddTooltip(gd, "Refresh target group and equipped-item highlighting")

    weapon_auto = Misc.ReadSharedValue("use_slayer_swap") == 1
    talisman_auto = Misc.ReadSharedValue("use_slayer_talisman") == 1
    Gumps.AddButton(gd, 5, 80, 9762, 9763, SLAYER_TOGGLE_WEAPON, 1, 0)
    Gumps.AddLabel(gd, 25, 80, 68 if weapon_auto else 900, "Auto Weapon")
    Gumps.AddButton(gd, 145, 80, 9762, 9763, SLAYER_TOGGLE_TALISMAN, 1, 0)
    Gumps.AddLabel(gd, 165, 80, 68 if talisman_auto else 900, "Auto Talisman")

    y = 105
    equipped_weapon = current_weapon_serial()
    Gumps.AddLabel(gd, 5, y, 52, "Weapons")
    y += 20
    for i, entry in enumerate(weapons):
        hue = 900
        if entry.get('serial') == equipped_weapon:
            hue = 32
        elif entry.get('group') == group:
            hue = 68
        Gumps.AddButton(gd, 5, y, 9762, 9763, SLAYER_WEAPON_ROW + i, 1, 0)
        Gumps.AddLabel(gd, 25, y, hue, "%s [%s]" % (
            entry.get('name', '?'), entry.get('group', '?')))
        y += 20

    equipped_talisman = current_talisman_serial()
    Gumps.AddLabel(gd, 5, y, 52, "Talismans")
    y += 20
    for i, entry in enumerate(talismans):
        hue = 900
        if entry.get('serial') == equipped_talisman:
            hue = 32
        elif entry.get('group') == group:
            hue = 68
        Gumps.AddButton(gd, 5, y, 9762, 9763, SLAYER_TALISMAN_ROW + i, 1, 0)
        Gumps.AddLabel(gd, 25, y, hue, "%s [%s]" % (
            entry.get('name', '?'), entry.get('group', '?')))
        y += 20

    y += 4
    Gumps.AddButton(gd, 5, y, 9762, 9763, SLAYER_ADD_WEAPON, 1, 0)
    Gumps.AddLabel(gd, 25, y, 900, "+Weapon")
    Gumps.AddTooltip(gd, "Register a weapon by targeting it in your pack")
    Gumps.AddButton(gd, 105, y, 9762, 9763, SLAYER_ADD_TALISMAN, 1, 0)
    Gumps.AddLabel(gd, 125, y, 900, "+Talisman")
    Gumps.AddTooltip(gd, "Register a talisman by targeting it")
    Gumps.AddButton(gd, 215, y, 9762, 9763, SLAYER_DELETE_MODE, 1, 0)
    Gumps.AddLabel(gd, 235, y, 32 if _slayer_delmode else 900, "Delete")
    Gumps.AddTooltip(gd, "Delete mode: the next registered-item click removes it")
    return gd


def sendgump():
    gd = build_slayer_gump() if _active_tab == 'slayer' else build_settings_gump()
    Gumps.SendGump(GUMP_ID, Player.Serial, setX, setY,
                   gd.gumpDefinition, gd.gumpStrings)
    return GUMP_ID


def handle_slayer_button(button_id):
    global _slayer_delmode
    data = _slayer_render_data

    if button_id == SLAYER_REFRESH:
        return
    elif button_id == SLAYER_AUTO:
        Misc.SetSharedValue("slayer_hold", 0)
        Player.HeadMessage(68, "Slayer swap: AUTO")
    elif button_id == SLAYER_ADD_WEAPON:
        register_slayer_item('weapons', 'weapon')
    elif button_id == SLAYER_ADD_TALISMAN:
        register_slayer_item('talismans', 'talisman')
    elif button_id == SLAYER_DELETE_MODE:
        _slayer_delmode = not _slayer_delmode
        Player.HeadMessage(50, "Delete mode %s" % (
            "ON — click a row to remove" if _slayer_delmode else "off"))
    elif button_id == SLAYER_TOGGLE_WEAPON:
        SetSharedValue("use_slayer_swap")
        Player.HeadMessage(50, "Slayer weapon auto-swap: %i" %
                           Misc.ReadSharedValue("use_slayer_swap"))
    elif button_id == SLAYER_TOGGLE_TALISMAN:
        SetSharedValue("use_slayer_talisman")
        Player.HeadMessage(50, "Slayer talisman auto-swap: %i" %
                           Misc.ReadSharedValue("use_slayer_talisman"))
    elif SLAYER_WEAPON_ROW <= button_id < SLAYER_WEAPON_ROW + len(data['weapons']):
        index = button_id - SLAYER_WEAPON_ROW
        entry = data['weapons'][index]
        if _slayer_delmode:
            delete_slayer_entry(data, 'weapons', entry)
            _slayer_delmode = False
        else:
            manual_slayer_equip(entry, True)
    elif SLAYER_TALISMAN_ROW <= button_id < SLAYER_TALISMAN_ROW + len(data['talismans']):
        index = button_id - SLAYER_TALISMAN_ROW
        entry = data['talismans'][index]
        if _slayer_delmode:
            delete_slayer_entry(data, 'talismans', entry)
            _slayer_delmode = False
        else:
            manual_slayer_equip(entry, False)


def buttoncheck(gumpId):
    global _active_tab
    Gumps.WaitForGump(gumpId, 9999999)
    Gumps.CloseGump(gumpId)
    gd = Gumps.GetGumpData(gumpId)

    bid = gd.buttonid
    if not bid:
        return

    if bid == TAB_SETTINGS:
        _active_tab = 'settings'
        return
    elif bid == TAB_SLAYER:
        _active_tab = 'slayer'
        return

    if _active_tab == 'slayer':
        handle_slayer_button(bid)
        return

    raw_section   = bid // 1000
    button_offset = bid % 1000

    # ── Collapse toggle ──────────────────────────────────────────────────────
    if raw_section >= 300:
        actual_section = raw_section - 300
        key = "gump_col_%d" % actual_section
        Misc.SetSharedValue(key, 0 if Misc.ReadSharedValue(key) == 1 else 1)
        return

    # ── Decode increment / decrement ─────────────────────────────────────────
    is_increment = False
    is_decrement = False
    if raw_section >= 200:
        actual_section = raw_section - 200
        is_decrement   = True
    elif raw_section >= 100:
        actual_section = raw_section - 100
        is_increment   = True
    else:
        actual_section = raw_section

    # ── Look up the action ───────────────────────────────────────────────────
    all_sections = list(sections.values())
    if button_offset == 0 or actual_section >= len(all_sections):
        return
    section_actions = all_sections[actual_section]
    section_values  = list(section_actions.values())
    if button_offset > len(section_values):
        return
    action = section_values[button_offset - 1]
    if not action:
        return

    btype = action.get('buttontype', '')

    # ── Save settings ────────────────────────────────────────────────────────
    if btype == 'savesettings':
        save_settings()

    # ── Select artifact loot bag, toggle mover, and persist immediately ────────
    elif btype == 'lootbagtoggle':
        if Misc.ReadSharedValue("use_move_artis") == 1:
            Misc.SetSharedValue("use_move_artis", 0)
            save_settings()
            Player.HeadMessage(50, "Move artifacts to loot bag: OFF")
        else:
            serial = select_artifact_lootbag()
            if serial:
                Misc.SetSharedValue("lootbag_serial", serial)
                Misc.SetSharedValue("use_move_artis", 1)
                save_settings()
                Player.HeadMessage(68, "Move artifacts to loot bag: ON")

    # ── Save/toggle this character's Razor Enhanced Dress List ──────────────
    elif btype == 'dresslistname':
        save_dresslist_name(gd)

    elif btype == 'dresslisttoggle':
        toggle_dresslist(gd)

    # ── Persist one specific targeted mobile serial per character ───────────
    elif btype == 'ignoretarget':
        set_target_ignored(True)

    elif btype == 'unignoretarget':
        set_target_ignored(False)

    # ── Toggle shared value ──────────────────────────────────────────────────
    elif btype == 'setsharedvalue':
        action['task'](action['sharedvalue'])
        Player.HeadMessage(50, "Set %s to %i" % (
            action['sharedvalue'], Misc.ReadSharedValue(action['sharedvalue'])))

    # ── Increment / decrement range value ────────────────────────────────────
    elif btype == 'setvalue':
        current = Misc.ReadSharedValue(action['displayvalue'])
        min_val = action.get('minValue', 1)
        max_val = action.get('maxValue', 99)
        if is_increment:
            new_val = min(max_val, current + 1)
        elif is_decrement:
            new_val = max(min_val, current - 1)
        else:
            return
        Misc.SetSharedValue(action['displayvalue'], new_val)
        Player.HeadMessage(50, "Set %s to %i" % (action['displayvalue'], new_val))
    
 
Player.HeadMessage(50,"Please set the Gump Script to LOOP MODE") 
        
while True:
    try:
        buttoncheck(sendgump())
    except Exception as e:
        Player.HeadMessage(30, "GUMP error: %s" % str(e))
    Misc.Pause(300)
