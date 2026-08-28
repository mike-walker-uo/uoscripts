### UO Ultimate Dexxer Attack Script by Mike|Walker ##########
### https://github.com/mike-walker-uo/uoscripts/tree/main/UltimateDexxerAttackScript
### Version 1.32 last edit 28.08.2026 ###
### Try to run at least Razor Enhanced Version 0.8.2.215 with fixed Skill Names ###
### SAVE THE SCRIPT AS .py file and add to the Python Script Section in Razor Enhanced ####

### START THE ATTACK SCRIPT FIRST

import winsound
import math
import json, os
import time
from System.Collections.Generic import List
from System import Byte

# ── Save / Load settings ────────────────────────────────────────────────────
try:
    _script_dir = os.path.dirname(os.path.abspath(__file__)) or os.path.expanduser('~')
except:
    _script_dir = os.path.expanduser('~')
LEGACY_SETTINGS_FILE = os.path.join(_script_dir, "AttackScript_settings.json")
SETTINGS_FILE = os.path.join(
    _script_dir,
    "AttackScript_settings_%08X.json" % (int(Player.Serial) & 0xFFFFFFFF)
)
DEFAULT_LOOTBAG_SERIAL = 0

ignored_mob_names = set()
ignored_mob_serials = set()
ignored_summon_names = set()

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
    "use_curseweapon", "use_playingtheodds",
    "use_pot_refresh", "use_pot_cure", "use_pot_apple", "use_pot_heal_emergency",
    "stam_pot_pct", "heal_pot_pct", "quiver_low_threshold",
    "use_pet_sync", "use_smart_target", "use_smart_specials", "disable_weaponspecials",
    "use_slayer_swap", "use_slayer_talisman",
    "attackrange", "nearbyrange", "honordistance",
]

miscartis = [
    "Flute of Renewal", "blighted cotton", "gnaw's fang", "thorny briar",
    "sabrix's eye", "lissith's silk", "irk's brain", "Raptor Claw",
    "Tome of Enlightenment", "Void Infused Kilt", "Axe of Abandon",
    "Ancient Farmer's Kasa", "Totem of the Void", "Bloodwood Spirit",
    "Soul Seeker", "Fey Leggings", "Boomstick", "Talon Bite",
    "Robe of the Equinox", "Blade Dance", "Flesh Ripper", "Aegis of Grace",
    "Righteous Anger", "Bonesmasher", "Raed's Glory", "Brightsight Lenses",
    "Wildfire Bow", "Quiver of the Elements", "Quiver of Rage",
    "Helm of Swiftness", "Robe of the Eclipse", "Windsong",
    "Gauntlets of Villainous Epiphany", "Breastplate of Virtuous Epiphany",
    "Legs of Virtuous Epiphany", "Helm of Villainous Epiphany",
    "Arms of Villainous Epiphany", "Kilt of Virtuous Epiphany",
    "Tattered Remnants of an Ancient Scroll", "Helm of Virtuous Epiphany",
    "Gorget of Villainous Epiphany", "Earrings of Villainous Epiphany",
    "Gorget of Virtuous Epiphany", "Demon Bridle Ring",
    "Sword of Shattered Hopes", "Blade of Battle", "Giant Steps",
    "Demon Forks", "Peasant's Bokuto", "Pigments of Tokuno", "Exiler",
    "Pilfered Dancer Fans", "Gloves of the Pugilist", "Ancient Samurai Do",
    "Dragon Nunchaku", "Staff of Power", "Honorable Swords of Nami",
    "Honorable Swords of Ryo", "Arms of Tactical Excellence", "Hanzo's Bow",
    "Gloves of the Sun", "Legs of Stability", "Daimyo's Helm",
    "Black Lotus Hood", "Leurocian's Mempo of Fortune", "The Destroyer",
    "Brightblade", "Blight of the Tundra", "Storm Caller", "Pixie Swatter",
    "Blaze of Death", "Cavorting Club", "Enchanted Titan Leg Bone",
    "Bow of the Juka King", "Burglar's Bandana", "Night's Kiss",
    "Phillip's Wooden Steed", "Nox Ranger's Heavy Crossbow", "Iolo's Lute",
    "Wrath of the Dryad", "Alchemist's Bauble", "Orcish Visage",
    "Polar Bear Mask",
]

destardartis = [
    "Katrina's Crook", "Heart of the Lion", "a map of the known world",
    "Sollerets of Sacrifice (Virtue Armor Set)", "Sentinel's Guard",
    "Legs of Honor (Virtue Armor Set)", "Jaana's Staff",
    "Helm of Spirituality (Virtue Armor Set)", "Violet Courage",
    "Lord Blackthorn's Exemplar", "Arms of Compassion (Virtue Armor Set)",
    "Gauntlets of Valor (Virtue Armor Set)", "Shield of Invulnerability",
    "Dragon's End", "Breastplate of Justice (Virtue Armor Set)",
    "Arctic Death Dealer", "Luna Lance", "Ankh Pendant", "Gold Bricks",
    "Gwenno's Harp", "Gorget of Honesty (Virtue Armor Set)",
]

ARTIFACT_NAMES = set(name.lower() for name in miscartis + destardartis)

HEIRLOOM_CHEST_ID = 0x2811
HEIRLOOM_CHEST_HUE = 0x0000
HEIRLOOM_CHEST_NAME = "chest of heirlooms"
ENCHANTED_APPLE_ID = 0x2FD8
HEIRLOOM_DROP_OFFSETS = (
    (0, 0), (1, 0), (0, 1), (-1, 0), (0, -1),
    (1, 1), (-1, -1), (1, -1), (-1, 1),
)

def save_settings():
    try:
        data = {}
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, 'r') as f:
                loaded = json.load(f)
            if isinstance(loaded, dict):
                data.update(loaded)
        data.update({k: Misc.ReadSharedValue(k) for k in SETTINGS_KEYS})
        data.setdefault("ignored_mob_names", sorted(ignored_mob_names))
        data.setdefault("ignored_mob_serials", sorted(ignored_mob_serials))
        data.setdefault("ignored_summon_names", sorted(ignored_summon_names))
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(data, f, indent=2)
        Player.HeadMessage(68, "Character settings saved!")
    except Exception as e:
        Player.HeadMessage(30, "Save failed: %s" % str(e))

def load_settings():
    global ignored_mob_names, ignored_mob_serials, ignored_summon_names
    try:
        source_file = SETTINGS_FILE
        imported_legacy = False
        if not os.path.exists(source_file) and os.path.exists(LEGACY_SETTINGS_FILE):
            source_file = LEGACY_SETTINGS_FILE
            imported_legacy = True

        if os.path.exists(source_file):
            with open(source_file, 'r') as f:
                data = json.load(f)
            for k, v in data.items():
                if k in SETTINGS_KEYS:
                    Misc.SetSharedValue(k, v)

            ignored_mob_names.clear()
            ignored_mob_names.update(
                str(name).strip().lower()
                for name in data.get("ignored_mob_names", [])
                if str(name).strip()
            )
            ignored_mob_serials.clear()
            for serial in data.get("ignored_mob_serials", []):
                try:
                    ignored_mob_serials.add(int(serial))
                except:
                    pass
            ignored_summon_names.clear()
            ignored_summon_names.update(
                str(name).strip().lower()
                for name in data.get("ignored_summon_names", [])
                if str(name).strip()
            )

            if imported_legacy:
                character_data = dict(data)
                character_data.update(
                    {k: Misc.ReadSharedValue(k) for k in SETTINGS_KEYS})
                character_data["ignored_mob_names"] = sorted(ignored_mob_names)
                character_data["ignored_mob_serials"] = sorted(ignored_mob_serials)
                character_data["ignored_summon_names"] = sorted(ignored_summon_names)
                with open(SETTINGS_FILE, 'w') as f:
                    json.dump(character_data, f, indent=2)
                Player.HeadMessage(68, "Legacy settings imported for this character")
            else:
                Player.HeadMessage(68, "Character settings loaded!")
            return True
    except Exception as e:
        Player.HeadMessage(30, "Load failed: %s" % str(e))
    return False
# ────────────────────────────────────────────────────────────────────────────

##################################################################
###  MAKE ALL YOUR SETTINGS HERE ################################# 
##################################################################

# attack blue mobs (notoriety 1) use with care!
Misc.SetSharedValue("attack_blues",0)

# attack red humans (to avoid attacking red players)
Misc.SetSharedValue("attack_red_humans",0)
# check and attack blue changelings that imitate you
Misc.SetSharedValue("attack_blue_changelings",0)
 
# show overhead messages yes=1, no=0 (silent mode)
Misc.SetSharedValue("use_messages",0)

# Use Bag of Sending (will send gold to the bank, when almost full)
Misc.SetSharedValue("use_bagofsending",1)

# Move named artifacts from the backpack into the selected loot bag.
Misc.SetSharedValue("use_move_artis",0)
Misc.SetSharedValue("lootbag_serial",DEFAULT_LOOTBAG_SERIAL)

# Use a trapped crate (red one) to get out of Paralyze
Misc.SetSharedValue("use_trappedcrate",1)
 
# Use Town Buff. It will check if the town buff is active
Misc.SetSharedValue("use_townbuff",1)

# Checks the journal for legendary messages & astral spawns and show overhead message and annoying beep lol
Misc.SetSharedValue("use_checkforlegendaries",1)

#check for rare mobs. It will show a message and mark the rare mob.
Misc.SetSharedValue("use_checkforraremobs",1)
#stop the fight, go to peace mode and stop the script when a rare is near (can be dangerous, esp at the bears!)
Misc.SetSharedValue("use_stopwarwhenrare",0)

#shows an arrow above the mob. The color indicates the distance
# melee: 0-1 = green, 2 - 3 = orange, >3 = red
# ranged: 0-10: green, 11-12 orange, >12 = red
Misc.SetSharedValue("use_distancemarker",1)
Misc.SetSharedValue("use_bluemarkermode",0) #if you want blue arrows (3 arrows = out of range, 2 arrows = almost in range, 1 arrow = in range)

# if you use Spellweaving as dexxer! (hint: its good)
# check if you have arcane focus. Even with 0 SW you can get +6 STR for 2 hours
Misc.SetSharedValue("use_arcanefocus",0)
# if you use the SW Summon Feys
Misc.SetSharedValue("use_summonfeys",0)
#if you are below that amount of follower slots you will auto cast the feys
Misc.SetSharedValue("fey_threshold",3)
#if you use SW Immolating weapon (melee only)
Misc.SetSharedValue("use_immolatingweapon",0)
#if you use attune weapon (absorb phys dmg)
Misc.SetSharedValue("use_attuneweapon",0)
#if you use thunderstorm spellweaving spell
Misc.SetSharedValue("use_thunderstorm",0)
#if you want to adjust the delay/lag of some cast time calculation, delay in ms
serverdelay = 100 #Adjustable correction delay for lag or things going too fast and misbehaving in ms

# Dress set: if you want to make sure that you keep your clothes on, use_dresslist = 1 
# Write down the name of the dresslist 
# Go to Razor Enhanced > Agents > Dress/Arm and pick the name of the dresslist you want to use
# One hint: if you want to change the weapon, shield or talisman during the fight, remove them from the dress list
# do not set use_dresslist = 1 if you switch your different dress lists via hotkey!
 
Misc.SetSharedValue("use_dresslist",0)
Misc.SetSharedValue("dresslist_name","")

##################################################################
# Set the spells you want to use to 1 ############################
    
Misc.SetSharedValue("use_eoo",0) # Use Chiv Enemy of One - dangerous!
Misc.SetSharedValue("use_df",0) # Use Chiv Divine Fury
Misc.SetSharedValue("use_cw",0) # Use Chiv Consecrate Weapon
Misc.SetSharedValue("use_holylight",0) # Use Chiv Holy Light with 2+ mobs within 3 tiles
Misc.SetSharedValue("use_honor",1) # Use Honor.. can be used without Bushido
Misc.SetSharedValue("use_ca",0) # Use Bushido Counter Attack
Misc.SetSharedValue("use_removecurse",1) #If you want to remove curses with chiv
Misc.SetSharedValue("use_confidence",1) #Use confidence to heal
Misc.SetSharedValue("use_evasion",1) #Use evasion to defend
Misc.SetSharedValue("use_closewounds",1) #Use Close Wounds to heal (when mob is not near!)
Misc.SetSharedValue("use_removepoison",1) #Use Remove Poison (when mob is not near!)
Misc.SetSharedValue("use_momentumstrike",1) # Use Bushido Momentum Strike
Misc.SetSharedValue("use_lightningstrike",1) # Use Bushido Lightning Strike
Misc.SetSharedValue("use_onslaught",1) # Use Swordsmanship Onslaught
Misc.SetSharedValue("use_he",0) # Use Bushido Honorable Execution as finisher (violates no-Bushido build — opt-in only)
Misc.SetSharedValue("use_mirrorimage",0) # With mobs in AttackRange, cast while 3 or fewer follower slots are occupied
Misc.SetSharedValue("use_releasemirrorimage",0) # With mobs in AttackRange and exactly 4 followers, release one Mirror Image
Misc.SetSharedValue("use_whitetigerform",0) # Maintain White Tiger Form with 120 Ninjitsu and 120 Stealth
Misc.SetSharedValue("use_deathstrike",0) # Use Ninjitsu Death Strike instead of weapon/special moves
Misc.SetSharedValue("use_focusattack",0) # Use Ninjitsu Focus Attack instead of weapon/special moves
Misc.SetSharedValue("use_backstab",0) # Alternate a weapon's Shadow Strike with Ninjitsu Backstab
Misc.SetSharedValue("use_smokebombs",0) # Use Egg/Smoke Bombs as a Backstab hiding fallback
Misc.SetSharedValue("he_killshot_pct",15) # HE fires when nearest HP bar <= this % of max (e.g. 15 = 15%)
Misc.SetSharedValue("use_curseweapon",0) #Use curse weapon when 50% or lower health    
Misc.SetSharedValue("use_playingtheodds",0) #Use Archery Mastery Spell Playing the Odds

# Potion auto-quaff — non-spell so does not break swing/VE leech
Misc.SetSharedValue("use_pot_refresh",1) # Greater Refresh when low stam (archer must-have)
Misc.SetSharedValue("use_pot_cure",1) # Greater Cure when poisoned and Chiv mana low
Misc.SetSharedValue("use_pot_apple",1) # Enchanted Apple only for Blood Oath
Misc.SetSharedValue("use_pot_heal_emergency",0) # Greater Heal pot at very low HP (VE leech usually covers — opt-in)
Misc.SetSharedValue("stam_pot_pct",30) # Stam % threshold for Greater Refresh
Misc.SetSharedValue("heal_pot_pct",20) # HP % threshold for emergency Heal pot
Misc.SetSharedValue("quiver_low_threshold",20) # quiver auto-refill when count drops below this

# Pet/summon attack sync — issue "all kill" when target changes
Misc.SetSharedValue("use_pet_sync",1) # enabled for tamer / fey-summoner builds

# Smart target priority — replace 'nearest' with score-based picker
Misc.SetSharedValue("use_smart_target",0) # opt-in; locks Onslaught primary + boosts paragons / known casters / healers
Misc.SetSharedValue("use_smart_specials",0) # opt-in; context-aware weapon-special slot picker (Mortal Strike on healers/paragons, ParaBlow on casters)
Misc.SetSharedValue("disable_weaponspecials",0) # Disable primary/secondary weapon abilities only
# MobileID sets — tune per shard
SMART_TARGET_HEALER_IDS = ()    # e.g. (0x0190, 0x0191) — healer/buffer mob IDs
SMART_TARGET_CASTER_IDS = ()    # e.g. (0x0009, 0x000A) — caster mob IDs

# Slayer auto-swap — equip the matching slayer weapon/talisman for the current
# target's group. Register slayer items on the Slayer Sets tab in
# AttackScript_MikeWalker_GUMP.py. It writes a per-character SlayerSets file,
# which this script reads. Manual picks set a HOLD that suppresses auto-swap
# until the target group changes.
Misc.SetSharedValue("use_slayer_swap",0)     # auto-swap weapons
Misc.SetSharedValue("use_slayer_talisman",0) # auto-swap talismans

# Range defaults must be set before loading settings so saved GUMP values win.
_is_ranged_build = (Player.GetSkillValue('Archery') >= 40 or
                    Player.GetSkillValue('Throwing') >= 40)
Misc.SetSharedValue("attackrange", 16 if _is_ranged_build else 10)
Misc.SetSharedValue("nearbyrange", 10 if _is_ranged_build else 1)
Misc.SetSharedValue("honordistance", 10)

# Load saved settings — overrides all defaults above with last saved values
load_settings()

# Dress list initialisation (runs after load so saved use_dresslist value is respected)
if Misc.ReadSharedValue("use_dresslist") == 1:
    dresslistname = str(Misc.ReadSharedValue("dresslist_name") or "").strip()
    if dresslistname:
        Dress.ChangeList(dresslistname)
        Dress.DressFStart()
        Timer.Create('dress', 2500)
    else:
        Misc.SetSharedValue("use_dresslist", 0)
        Player.HeadMessage(30, "Dress List disabled: no list name saved")

# Built-in summon/animal safety ignores stay in code. Character-specific mob
# names, summon names, and targeted serials load from the character settings.
DEFAULT_SUMMONS_TO_IGNORE = {"a reaper", "a rising colossus", "a nature's fury", "a blade spirit"}
summonsToIgnore = DEFAULT_SUMMONS_TO_IGNORE | ignored_summon_names #only red summons (notoriety 6) will be ignored
mobsToIgnore = ignored_mob_names
serialsToIgnore = ignored_mob_serials
for ignored_serial in serialsToIgnore:
    Misc.IgnoreObject(ignored_serial)
_ignore_revision = Misc.ReadSharedValue("attack_ignore_revision")

def refresh_persistent_ignores():
    global _ignore_revision
    revision = Misc.ReadSharedValue("attack_ignore_revision")
    if revision == _ignore_revision:
        return

    try:
        with open(SETTINGS_FILE, 'r') as f:
            data = json.load(f)
        updated = set()
        for serial in data.get("ignored_mob_serials", []):
            try:
                updated.add(int(serial))
            except:
                pass
    except:
        return

    for serial in serialsToIgnore - updated:
        Misc.UnIgnoreObject(serial)
    for serial in updated - serialsToIgnore:
        Misc.IgnoreObject(serial)
    serialsToIgnore.clear()
    serialsToIgnore.update(updated)
    _ignore_revision = revision
# List provided by BigDa
mobileIDsToIgnore = {
    0x00C9,  # cat
    0x00D0,  # chicken
    0x00D8,  # cow
    0x00E8,  # bull
    0x00E9,  # another bull
    0x0122,  # boar
    0x00CB,  # pig
    0x00CF,  # sheep
    0x00D1,  # goat

    0x00C8,  # horse
    0x00CC,  # another horse
    0x00E2,  # another horse
    0x0123,  # pack horse
    0x00DC,  # llama
    0x0124,  # pack llama

    0x00D9,  # dog
    0x00CD,  # rabbit
    0x0114,  # squirrel
    0x0117,  # ferret
  

    0x00ED,  # hind (deer)
    0x00EA,  # great hart

    0x00D2,  # desert ostard
    0x00E4,  # forest ostard
    0x00E7,  # frenzied ostard

    0x0006,  # bird
    0x0045,  # crane
    0x00FE,  # crane (ServUO)

    0x0097,  # dolphin
    0x00DF,  # walrus
    0x00E0,  # white wolf / seal
    
    0x00E1,  # grey wolf / timber wolf
    0x00D6,  # cougar / snow leopard
    0x003F,  # panther
    0x0041,   #another bloody leopard
    0x00D3,  # black bear
    0x00D4,  # brown bear

    # --- New Additions Below ---
    0x0019,  # grey wolf (variant)
    0x001B,  # white wolf (variant)
    
    0x00DD,  # walrus (alt variant)
    0x0050,  # toad (giant)
    0x0051,  # bullfrog
    
    0x00F3,  # mountain goat
    
    
    0x0119,  # crane (variant)
    0x0005,  # eagle
    0x0002,  # brown bear (variant)
    0x00A7,  # polar bear
    0x0125,  # ridge ostard
    
   
    0x0123,  # rideable pack horse
    0x02D1,  # boura (ruddy/neutral)
    0x02D0,  # boura (highland)
    0x011C,  # turkey (seasonal/neutral)
    0x0211,  # beetle (giant)
    
    0x00F2,  #a deathwatch beetle (hatchling )
    
}
   
##################################################################
# Dont touch anything below! ####################################
##################################################################

use_honor_fix = 0 #clear Honor if its still exiting without mobs around
Misc.SetSharedValue("use_bandages",0) #will be automatically actived when you have healing or vet
Misc.SetSharedValue("use_vampiricembrace",0) #will be automatically actived when you have 99+ Necro
Misc.SetSharedValue("use_arrows",0) #will be automatically activated when you have archery
Misc.SetSharedValue("use_weaponspecialprimary",1) #needed for Tactics check
Misc.SetSharedValue("use_weaponspecialsecondary",1) #needed for Tactics check
changelingrange = 1 #range of the blue changelings that will be attacked
Misc.SetSharedValue("activeattack",1)
requiredmana = 0 #used for weapon specials mana calculation
nearestonslaught = 0 #used for onslaught
_onslaught_journal_timestamp = time.time()
_legendary_journal_timestamp = time.time()
_last_pet_target_serial = 0 #throttle for "all kill" pet target sync
_victims_cache = [] #cached mobs_list result, refreshed on 'mobscan' timer (perf)
_changelings_cache = [] #cached blue changelings, refreshed with the main mob scan
_binding_journal_timestamp = time.time()
_target_cursor_seen = False
_weapon_special_was_armed = Player.HasSpecial
_backstab_target_serial = 0
_backstab_state = "SHADOW_STRIKE"
_backstab_was_armed = False
_backstab_attack_sent = False
_backstab_stealth_requested = False
_smoke_bomb_cache_serial = 0
_enchanted_apple_cache_serial = 0
_bag_of_sending_cache_serial = 0
_artifact_name_cache = {}
firsthitmob = 0 #used for onslaught
guardme = 0 #used for summon feys
weapon_set = 'default' #used for weapon check

COLOSSAL_STUN_MESSAGE = "You have been stunned by a colossal blow!"
BINDING_BRACELET_ID = 0x1086
BINDING_BRACELET_HUE = 0x0489
BINDING_BRACELET_TIMER = "binding_bracelet_use"
TARGET_CURSOR_TIMEOUT_MS = 2000
TARGET_CURSOR_TIMER = "attack_stuck_target_cursor"
MIRROR_IMAGE_FOLLOWER_THRESHOLD = 3
WEAPON_SPECIAL_ARM_DEBOUNCE_MS = 800
WEAPON_SPECIAL_REPEAT_WINDOW_MS = 3000
BACKSTAB_LOCK_MS = 5000
BACKSTAB_FINAL_NORMAL_MS = 3000
BACKSTAB_SWING_MS = 1250
BACKSTAB_STEALTH_ACK_MS = 600
BACKSTAB_STATE_SHADOW = "SHADOW_STRIKE"
BACKSTAB_STATE_STEALTH = "ENTER_STEALTH"
BACKSTAB_STATE_BACKSTAB = "BACKSTAB"
BACKSTAB_STATE_FILLER = "FILLER_SPECIALS"
BACKSTAB_STATE_FINAL = "FINAL_NORMAL_SWINGS"
BACKSTAB_STEP_DIRECTIONS = (
    ("North", 0, -1), ("South", 0, 1),
    ("East", 1, 0), ("West", -1, 0),
    ("NorthEast", 1, -1), ("NorthWest", -1, -1),
    ("SouthEast", 1, 1), ("SouthWest", -1, 1),
)

sv = {}  # shared value cache, refreshed every loop tick

def refresh_sv():
    sv['activeattack']           = Misc.ReadSharedValue("activeattack")
    sv['attackrange']            = Misc.ReadSharedValue("attackrange")
    sv['nearbyrange']            = Misc.ReadSharedValue("nearbyrange")
    sv['honordistance']          = Misc.ReadSharedValue("honordistance")
    sv['use_messages']           = Misc.ReadSharedValue("use_messages")
    sv['use_df']                 = Misc.ReadSharedValue("use_df")
    sv['use_cw']                 = Misc.ReadSharedValue("use_cw")
    sv['use_holylight']          = Misc.ReadSharedValue("use_holylight")
    sv['use_eoo']                = Misc.ReadSharedValue("use_eoo")
    sv['use_honor']              = Misc.ReadSharedValue("use_honor")
    sv['use_ca']                 = Misc.ReadSharedValue("use_ca")
    sv['use_confidence']         = Misc.ReadSharedValue("use_confidence")
    sv['use_evasion']            = Misc.ReadSharedValue("use_evasion")
    sv['use_closewounds']        = Misc.ReadSharedValue("use_closewounds")
    sv['use_removepoison']       = Misc.ReadSharedValue("use_removepoison")
    sv['use_removecurse']        = Misc.ReadSharedValue("use_removecurse")
    sv['use_momentumstrike']     = Misc.ReadSharedValue("use_momentumstrike")
    sv['use_lightningstrike']    = Misc.ReadSharedValue("use_lightningstrike")
    sv['use_onslaught']          = Misc.ReadSharedValue("use_onslaught")
    sv['use_he']                 = Misc.ReadSharedValue("use_he")
    sv['use_mirrorimage']        = Misc.ReadSharedValue("use_mirrorimage")
    sv['use_releasemirrorimage'] = Misc.ReadSharedValue("use_releasemirrorimage")
    sv['use_whitetigerform']     = Misc.ReadSharedValue("use_whitetigerform")
    sv['use_deathstrike']        = Misc.ReadSharedValue("use_deathstrike")
    sv['use_focusattack']        = Misc.ReadSharedValue("use_focusattack")
    sv['use_backstab']           = Misc.ReadSharedValue("use_backstab")
    sv['use_smokebombs']         = Misc.ReadSharedValue("use_smokebombs")
    sv['he_killshot_pct']        = Misc.ReadSharedValue("he_killshot_pct")
    sv['use_pot_refresh']        = Misc.ReadSharedValue("use_pot_refresh")
    sv['use_pot_cure']           = Misc.ReadSharedValue("use_pot_cure")
    sv['use_pot_apple']          = Misc.ReadSharedValue("use_pot_apple")
    sv['use_pot_heal_emergency'] = Misc.ReadSharedValue("use_pot_heal_emergency")
    sv['stam_pot_pct']           = Misc.ReadSharedValue("stam_pot_pct")
    sv['heal_pot_pct']           = Misc.ReadSharedValue("heal_pot_pct")
    sv['quiver_low_threshold']   = Misc.ReadSharedValue("quiver_low_threshold")
    sv['use_pet_sync']           = Misc.ReadSharedValue("use_pet_sync")
    sv['use_smart_target']       = Misc.ReadSharedValue("use_smart_target")
    sv['use_smart_specials']     = Misc.ReadSharedValue("use_smart_specials")
    sv['disable_weaponspecials'] = Misc.ReadSharedValue("disable_weaponspecials")
    sv['use_slayer_swap']        = Misc.ReadSharedValue("use_slayer_swap")
    sv['use_slayer_talisman']    = Misc.ReadSharedValue("use_slayer_talisman")
    sv['use_curseweapon']        = Misc.ReadSharedValue("use_curseweapon")
    sv['use_playingtheodds']     = Misc.ReadSharedValue("use_playingtheodds")
    sv['use_bagofsending']       = Misc.ReadSharedValue("use_bagofsending")
    sv['use_move_artis']         = Misc.ReadSharedValue("use_move_artis")
    sv['lootbag_serial']         = Misc.ReadSharedValue("lootbag_serial")
    sv['use_trappedcrate']       = Misc.ReadSharedValue("use_trappedcrate")
    sv['use_townbuff']           = Misc.ReadSharedValue("use_townbuff")
    sv['use_checkforlegendaries']= Misc.ReadSharedValue("use_checkforlegendaries")
    sv['use_checkforraremobs']   = Misc.ReadSharedValue("use_checkforraremobs")
    sv['use_stopwarwhenrare']    = Misc.ReadSharedValue("use_stopwarwhenrare")
    sv['use_distancemarker']     = Misc.ReadSharedValue("use_distancemarker")
    sv['use_bluemarkermode']     = Misc.ReadSharedValue("use_bluemarkermode")
    sv['use_arcanefocus']        = Misc.ReadSharedValue("use_arcanefocus")
    sv['use_summonfeys']         = Misc.ReadSharedValue("use_summonfeys")
    sv['fey_threshold']          = Misc.ReadSharedValue("fey_threshold")
    sv['use_immolatingweapon']   = Misc.ReadSharedValue("use_immolatingweapon")
    sv['use_attuneweapon']       = Misc.ReadSharedValue("use_attuneweapon")
    sv['use_thunderstorm']       = Misc.ReadSharedValue("use_thunderstorm")
    sv['use_dresslist']          = Misc.ReadSharedValue("use_dresslist")
    sv['dresslist_name']         = Misc.ReadSharedValue("dresslist_name")
    sv['attack_blues']           = Misc.ReadSharedValue("attack_blues")
    sv['attack_red_humans']      = Misc.ReadSharedValue("attack_red_humans")
    sv['attack_blue_changelings']= Misc.ReadSharedValue("attack_blue_changelings")
    sv['use_bandages']           = Misc.ReadSharedValue("use_bandages")
    sv['use_vampiricembrace']    = Misc.ReadSharedValue("use_vampiricembrace")
    sv['use_arrows']             = Misc.ReadSharedValue("use_arrows")
    sv['use_weaponspecialprimary']  = Misc.ReadSharedValue("use_weaponspecialprimary")
    sv['use_weaponspecialsecondary']= Misc.ReadSharedValue("use_weaponspecialsecondary")

refresh_sv()
Timer.Create("sv_refresh", 2500)

class Weapon:
    name = ''
    itemID = 0
    weaponspecial_primary = ''
    weaponspecial_secondary = ''
    singleenemyspecial = ''
    multienemyspecial = ''
    # prefer_range: ideal player-to-target distance for this weapon.
    # 1 = melee (default), 6-10 = ranged (bows / crossbows).
    # HOOK ONLY -- consumed by future kite-step logic (item #7 deferred).
    prefer_range = 1

    def __init__ ( self, name, ItemID, weaponspecial_primary, weaponspecial_secondary, singleenemyspecial, multienemyspecial, prefer_range=1):
        self.name = name
        self.ItemID = ItemID
        self.weaponspecial_primary = weaponspecial_primary
        self.weaponspecial_secondary = weaponspecial_secondary
        self.singleenemyspecial = singleenemyspecial
        self.multienemyspecial = multienemyspecial
        self.prefer_range = prefer_range
        
weapons = {
    'default': Weapon( 'Default', None, "Primary Weapon Special", "Secondary Weapon Special", "primary", "secondary"),
    'bladedstaff': Weapon( 'Bladed Staff', 0x26BD, "Armor Ignore", None, "primary", "primary"),
    'doubleaxe': Weapon( 'Double Axe', 0x0F4B, "Double Strike", "Whirlwind", "primary", "secondary"), 
    'largebattleaxe': Weapon( 'Large Battle Axe', 0x13FB, "Whirlwind", None, "primary", "primary"),
    'longsword': Weapon( 'Longsword', 0x0F61, "Armor Ignore", None, "primary", "primary"),
    'broadsword': Weapon( 'Broadsword', 0x0F5E, None, "Armor Ignore",  "secondary", "secondary"),
    'radiantscimitar': Weapon( 'Radiant Scimitar', 0x2D33, "Whirlwind", None, "primary", "primary"),
    'bladedwhip': Weapon( 'Bladed Whip', 0xA28B, None, "Whirlwind", "secondary", "secondary"),
    'barbedwhip': Weapon( 'Barbed Whip', 0xA289, None, "Whirlwind", "secondary", "secondary"),
    'hammerpick': Weapon( 'Hammer Pick', 0x143D, "Armor Ignore", None, "primary", "primary"),
    'waraxe': Weapon( 'War Axe', 0x13B0, "Armor Ignore", None, "primary", "primary"),   
    'warhammer': Weapon( 'War Hammer', 0x1439, "Whirlwind", "Crushing Blow", "secondary", "primary"), 
    'gargishwarhammer': Weapon( 'Gargish War Hammer', 0x48C0, "Whirlwind", "Crushing Blow", "secondary", "primary"),
    'gnarledstaff': Weapon( 'Gnarled Staff', 0x13F8, None, "Force of Nature", "secondary", "secondary"),
    'gargishkryss': Weapon( 'Gargish Kryss', 0x48BC, "Armor Ignore", None, "primary", "primary"),
    'shortblade': Weapon( 'Shortblade', 0x0907, "Armor Ignore", None, "primary", "primary"),  
    'bloodblade': Weapon( 'Bloodblade', 0x08FE, None, "Paralyzing Blow", "secondary", "secondary"),
    'assassinspike': Weapon('Assassin Spike', 0x2D21, "Infectious Strike", "Shadow Strike", "primary", "primary"),
    'dagger': Weapon('Dagger', 0x0F52, "Shadow Strike", "Infectious Strike", "secondary", "secondary"),
    'shortspear': Weapon('Short Spear', 0x1403, "Shadow Strike", "Mortal Strike", "secondary", "secondary"),
    'gargishdagger': Weapon('Gargish Dagger', 0x0902, "Shadow Strike", "Infectious Strike", "secondary", "secondary"),
    'skinningknife': Weapon('Skinning Knife', 0x0EC4, "Shadow Strike", "Bleed Attack", "secondary", "secondary"),
    'cutlass': Weapon('Cutlass', 0x1441, "Bleed Attack", "Shadow Strike", "primary", "primary"),
    'compositebow': Weapon( 'Composite Bow', 0x26C2, "Armor Ignore", None, "primary", "primary", 8),
    'soulglaive': Weapon( 'Soul Glaive', 0x090A, "Armor Ignore", None, "primary", "primary", 6),
    'repeatingcrossbow': Weapon( 'Repeating Crossbow', 0x26C3, "Double Shot", None, "primary", "primary", 8),
    'yumi': Weapon( 'Yumi', 0x27A5, None, "Double Shot", "secondary", "secondary", 10),
    'elvencompositebow': Weapon( 'Elven Composite Bow', 0x2D1E, "Force Arrow", None, "primary", "primary", 8),
    'kama': Weapon('Kama', 0x27AD, "Whirlwind", None, "primary", "primary"),
    'halberd': Weapon('Halberd', 0x143E, "Whirlwind", "Concussion Blow", "secondary", "primary"),
    'blackstaff': Weapon('Black Staff', 0x0DF0, "Whirlwind", "Paralyzing Blow", "secondary", "primary"),
    'maul': Weapon('Maul', 0x143B, "Double Strike", None, "primary", "primary"),
    'boomerang': Weapon('Boomerang', 0x08FF, "Mystic Arc", "Concussion Blow", "primary", "primary"),
    'cyclone': Weapon('Cyclone', 0x0901, "Moving Shot", "Infused Throw", "secondary", "secondary"),
    'daisho': Weapon('Daisho', 0x27A9, "Feint", "Double Strike", "secondary", "secondary"),
    'magicalshortbow': Weapon('Magical Shortbow', 0x2D2B, "Lightning Arrow", "Psychic Attack", "primary", "primary"),
    'twhohandedaxe': Weapon('TwoHanded Axe', 0x1443, "Double Strike", "Shadow Strike", "primary", "primary"),
    'stonewarsword': Weapon('Stone War Sword', 0x0900, "Armor Ignore", "Paralyzing Blow", "primary", "primary"),   
    'gargishmaul': Weapon('Gargish Maul', 0x48C2, "Double Strike", "Concussion Blow", "primary", "primary"),
    'gargishbattleaxe': Weapon('Gargish Battle Axe', 0x48B0, "Bleed Attack", "Concussion Blow", "secondary", "secondary"),   
    'cutlass': Weapon('Cutlass', 0x1441, "Bleed Attack", "Shadow Strike", "secondary", "secondary") 
        
}

_weapon_key_by_item_id = {}
for _weapon_key, _weapon in weapons.items():
    if _weapon_key != 'default' and _weapon.ItemID not in _weapon_key_by_item_id:
        _weapon_key_by_item_id[_weapon.ItemID] = _weapon_key
  

    
def mobs_list (range):
    refresh_persistent_ignores()
    fil = Mobiles.Filter()
    fil.Enabled = True
    fil.RangeMax = range
    if sv['attack_blues'] == 0:
        fil.Notorieties = List[Byte](bytes([3,4,5,6]))
    elif sv['attack_blues'] == 1:
        fil.Notorieties = List[Byte](bytes([1,3,4,5,6]))
    fil.IsGhost = False
    fil.CheckIgnoreObject = True
    fil.IgnorePets = True
    #fil.CheckLineOfSight = True
    fil.Friend = False
    mobs = Mobiles.ApplyFilter(fil)
    accepted = []
    run_rare_check = (sv['use_checkforraremobs'] == 1 and
                      Timer.Check("rarecheck") == False)
    rare_reported = False
    for mob in mobs:
        mob_name = str(mob.Name or "").strip().lower()
        if run_rare_check and not rare_reported:
            if Mobiles.GetPropStringByIndex(mob,0) == "Rare" or Mobiles.GetPropStringByIndex(mob,1) == "Rare":
                Player.HeadMessage(20,"Rare {} around!".format(mob.Name))
                Mobiles.Message(mob, 20, 'Rare PET!' )
                Mobiles.Message(mob,15,"♥")
                Mobiles.Message(mob, 20, 'Rare PET!' )
                Mobiles.Message(mob,15,"♥")
                Mobiles.Message(mob, 20, 'Rare PET!' )
                Mobiles.Message(mob,15,"♥")
                if sv['use_stopwarwhenrare'] == 1:
                    if Player.WarMode:
                        Player.SetWarMode(False)
                    Player.WeaponClearSA() 
                    Misc.ScriptStopAll(False)
                rare_reported = True
        
        if mob.IsHuman and mob.Notoriety == 6 and sv['attack_red_humans'] == 0:
            if sv['use_messages'] == 1 and Timer.Check("reds") == False:
                Player.HeadMessage(40,"Ignore red: %s" % mob.Name)
                Timer.Create("reds",3000)
        elif mob_name in mobsToIgnore:
            continue
        elif mob_name in summonsToIgnore and mob.Notoriety == 6:
            continue
        elif mob.MobileID in mobileIDsToIgnore:
            continue
        elif mob.Serial in serialsToIgnore:
            continue
        else:
            accepted.append(mob)
            
    if run_rare_check:
        Timer.Create("rarecheck", 2000)
    return accepted

def changelings(range):
    fil = Mobiles.Filter()
    fil.Enabled = True
    fil.RangeMax = range
    fil.Notorieties = List[Byte](bytes([1]))
    fil.IsGhost = False
    fil.CheckIgnoreObject = False
    fil.IgnorePets = True
    fil.Friend = False    
    mobs = Mobiles.ApplyFilter(fil)
    return [mob for mob in mobs if mob.Name == Player.Name]


Player.HeadMessage(90,"Start Ultimate Attack Script by Mike|Walker") 
Player.HeadMessage(40,"Dont forget to start the GUMP script") 
equippedweapon = Player.GetItemOnLayer('FirstValid')
if not equippedweapon:
    equippedweapon = Player.GetItemOnLayer('LeftHand')

if equippedweapon:
    weapon_set = _weapon_key_by_item_id.get(equippedweapon.ItemID, 'default')
    if weapon_set != 'default':
        weapon = weapons[weapon_set]
        Player.HeadMessage(60,"%s" % weapon.name)
        if weapon.singleenemyspecial == "primary":
            Player.HeadMessage(70,"Single Target: %s" % weapon.weaponspecial_primary)
        elif weapon.singleenemyspecial == "secondary":
            Player.HeadMessage(70,"Single Target: %s" % weapon.weaponspecial_secondary)
        if weapon.multienemyspecial == "primary":
            Player.HeadMessage(70,"Muli Target: %s" % weapon.weaponspecial_primary)
        elif weapon.multienemyspecial == "secondary":
            Player.HeadMessage(70,"Multi Target: %s" % weapon.weaponspecial_secondary)
else:
    Player.HeadMessage(20,"No weapon!")
    
if equippedweapon and weapon_set == 'default':
    Player.HeadMessage(20,"Unknown Weapon, using Default!")
    weapons[ 'default' ].ItemID = equippedweapon.ItemID 
    Misc.Pause(1000)
    Player.HeadMessage(50,"Single Target: %s"% weapons[ weapon_set ].weaponspecial_primary)
    Player.HeadMessage(50,"Multi Target: %s"% weapons[ weapon_set ].weaponspecial_secondary)
    Misc.Pause(1000)
    
def checkweapon():
    # equippedweapon is global: after a slayer/manual swap the feint check in
    # fighting() must see the NEW weapon, not the one from script start.
    global weapon_set, _cached_fcr, _cached_fc, _cached_castpause, lmc, lrc, equippedweapon

    weapon_set = 'default'
    equippedweapon = Player.GetItemOnLayer('FirstValid')
    if not equippedweapon:
        equippedweapon = Player.GetItemOnLayer('LeftHand')

    if equippedweapon:
        weapon_set = _weapon_key_by_item_id.get(equippedweapon.ItemID, 'default')
        if weapon_set == 'default':
            weapons['default'].ItemID = equippedweapon.ItemID
    else:
        Player.HeadMessage(20,"No weapon!")

    # Refresh stats after weapon/gear swap
    lmc              = (min(40, Player.LowerManaCost)) / 100
    lrc              = Player.SumAttribute("Lower Reagent Cost")
    _cached_fc       = Player.FasterCasting
    _cached_fcr      = min(6, Player.FasterCastRecovery)
    _cached_castpause = max(((6 - _cached_fcr) * 250) + serverdelay, serverdelay)

# ── Slayer auto-swap (weapon + talisman) ─────────────────────────────────────
# Registry lives in a per-character AttackScript_SlayerSets_<serial>.json file
# managed by the main GUMP's Slayer Sets tab. Target group is resolved by name
# table below (JSON "mob_overrides" win). Swap fires on group change, gated by
# a cooldown so mixed spawns don't thrash the weapon.
LEGACY_SLAYER_FILE = os.path.join(_script_dir, "AttackScript_SlayerSets.json")
SLAYER_FILE = os.path.join(
    _script_dir,
    "AttackScript_SlayerSets_%08X.json" % (int(Player.Serial) & 0xFFFFFFFF)
)

# First match wins — order matters: "skeletal dragon" must hit Undead before
# Reptile, "bone daemon" is covered by a seeded mob_override instead.
SLAYER_MOB_KEYWORDS = (
    ('Undead',    ("skelet","zombie","lich","wraith","bone","mumm","ghoul",
                   "spectre","specter","shade","vampire","revenant","rotting",
                   "undead","dark father","dark wisp")),
    ('Repond',    ("orc","ratman","ettin","troll","ogre","cyclops","titan",
                   "savage","headless","meer","juka","barracoon")),
    ('Arachnid',  ("spider","scorpion","terathan","mephitis")),
    ('Reptile',   ("dragon","drake","wyvern","wyrm","serpent","lizardman",
                   "ophidian","snake","alligator","basilisk","reptalon",
                   "rikktor","slith","naga")),
    ('Demon',     ("daemon","demon","imp","gargoyle","balron","succubus",
                   "fiend","semidar","moloch")),
    ('Elemental', ("elemental","efreet")),
    ('Fey',       ("pixie","wisp","treefellow","dryad","satyr","changeling",
                   "silvani","twaulo","centaur","fey")),
    ('Eodon',     ("dimetrosaur","allosaurus","tyrannosaur","triceratops",
                   "dinosaur","myrmidex","saurosaurus","najasaurus",
                   "anchisaur","gallusaurus","archaeosaurus","infernus")),
)

_slayer_weapons   = []
_slayer_talismans = []
_slayer_overrides = {}
_slayer_overrides_normalized = ()
_slayer_weapon_by_group = {}
_slayer_talisman_by_group = {}
_slayer_group_by_name = {}
_slayer_file_signature = ()
_last_slayer_target_group = None

def _index_slayer_entries(entries):
    indexed = {}
    for entry in entries:
        group = entry.get('group')
        if group not in indexed:
            indexed[group] = entry
    return indexed

def load_slayer_sets(force=False):
    global _slayer_weapons, _slayer_talismans, _slayer_overrides
    global _slayer_overrides_normalized, _slayer_weapon_by_group
    global _slayer_talisman_by_group, _slayer_group_by_name
    global _slayer_file_signature
    try:
        if (not os.path.exists(SLAYER_FILE) and
                os.path.exists(LEGACY_SLAYER_FILE)):
            with open(LEGACY_SLAYER_FILE, 'r') as f:
                legacy_data = json.load(f)
            with open(SLAYER_FILE, 'w') as f:
                json.dump(legacy_data, f, indent=2)
            Player.HeadMessage(68, "Legacy Slayer sets imported for this character")

        exists = os.path.exists(SLAYER_FILE)
        signature = ((os.path.getmtime(SLAYER_FILE), os.path.getsize(SLAYER_FILE))
                     if exists else None)
        if not force and signature == _slayer_file_signature:
            return False

        if exists:
            with open(SLAYER_FILE, 'r') as f:
                data = json.load(f)
            _slayer_weapons   = data.get('weapons', [])
            _slayer_talismans = data.get('talismans', [])
            _slayer_overrides = data.get('mob_overrides', {})
        else:
            _slayer_weapons = []
            _slayer_talismans = []
            _slayer_overrides = {}
        _slayer_overrides_normalized = tuple(
            (pattern.lower(), group)
            for pattern, group in _slayer_overrides.items()
        )
        _slayer_weapon_by_group = _index_slayer_entries(_slayer_weapons)
        _slayer_talisman_by_group = _index_slayer_entries(_slayer_talismans)
        _slayer_group_by_name.clear()
        _slayer_file_signature = signature
        return True
    except Exception as e:
        Player.HeadMessage(30, "Slayer sets load failed: %s" % str(e))
        return False

load_slayer_sets(True)

def slayer_group_for_mob(mob):
    try:
        name = (mob.Name or "").lower()
    except:
        return 'none'
    cached = _slayer_group_by_name.get(name)
    if cached is not None:
        return cached
    for pattern, group in _slayer_overrides_normalized:
        if pattern in name:
            _slayer_group_by_name[name] = group
            return group
    for group, kws in SLAYER_MOB_KEYWORDS:
        for kw in kws:
            if kw in name:
                _slayer_group_by_name[name] = group
                return group
    _slayer_group_by_name[name] = 'none'
    return 'none'

def _slayer_pick(indexed_entries, group):
    # exact group first; otherwise fall back to a registered neutral
    # ("none") item so leaving a slayer zone re-equips your default weapon.
    entry = indexed_entries.get(group)
    if entry is not None or group == 'none':
        return entry
    return indexed_entries.get('none')

def _current_weapon():
    w = Player.GetItemOnLayer('FirstValid')
    if not w:
        w = Player.GetItemOnLayer('LeftHand')
    return w

def _slayer_equip(entry, is_weapon):
    ser = entry.get('serial', 0)
    cur = _current_weapon() if is_weapon else Player.GetItemOnLayer('Talisman')
    if cur and cur.Serial == ser:
        return False
    item = Items.FindBySerial(ser)
    if not item:
        if Timer.Check('slayermissing') == False:
            Player.HeadMessage(30, "Slayer item missing: %s" % entry.get('name','?'))
            Timer.Create('slayermissing', 10000)
        return False
    if is_weapon:
        if cur:
            r = Player.GetItemOnLayer('RightHand')
            if r and r.Serial == cur.Serial:
                Player.UnEquipItemByLayer('RightHand')
            else:
                Player.UnEquipItemByLayer('LeftHand')
            Misc.Pause(600)
    else:
        if cur:
            Player.UnEquipItemByLayer('Talisman')
            Misc.Pause(600)
    Player.EquipItem(item.Serial)
    Misc.Pause(600)
    if is_weapon:
        checkweapon()   # refresh weapon_set / cached stats / equippedweapon
        neww = _current_weapon()
        if not neww or neww.Serial != ser:
            Player.HeadMessage(30, "Slayer swap failed (shield blocking a 2H weapon?)")
            return True   # still counts as an attempt -> cooldown applies
    if sv['use_messages'] == 1:
        Player.HeadMessage(60, "Slayer swap: %s" % entry.get('name','?'))
    return True

def slayer_swap_tick(nearest):
    global _last_slayer_target_group
    if sv['use_slayer_swap'] != 1 and sv['use_slayer_talisman'] != 1:
        return
    # pick up registrations the main GUMP saved while we run
    if Timer.Check('slayerreload') == False:
        load_slayer_sets()
        Timer.Create('slayerreload', 5000)
    group = slayer_group_for_mob(nearest)
    if group != _last_slayer_target_group:
        Misc.SetSharedValue("slayer_target_group", group)
        _last_slayer_target_group = group
    # manual HOLD from the slayer gump: respect the player's pick until the
    # target group actually changes, then hand control back to auto.
    if Misc.ReadSharedValue("slayer_hold") == 1:
        if group == Misc.ReadSharedValue("slayer_hold_group"):
            return
        Misc.SetSharedValue("slayer_hold", 0)
    if Timer.Check('slayerswap') != False:
        return
    if Player.SpellIsEnabled("Onslaught"):
        return   # don't drop a readied Onslaught for a swap
    swapped = False
    if sv['use_slayer_swap'] == 1:
        e = _slayer_pick(_slayer_weapon_by_group, group)
        if e and _slayer_equip(e, True):
            swapped = True
    if sv['use_slayer_talisman'] == 1:
        e = _slayer_pick(_slayer_talisman_by_group, group)
        if e and _slayer_equip(e, False):
            swapped = True
    if swapped:
        Timer.Create('slayerswap', 3000)
# ─────────────────────────────────────────────────────────────────────────────

### Set the options if you dont have the skills
if not Player.BuffsExist("Saving Throw") or not Player.GetRealSkillValue('Swordsmanship') >= 90:
    Misc.SetSharedValue("use_onslaught",0)

# Chivalry    
if Player.GetSkillValue('Chivalry') < 5:
    Misc.SetSharedValue("use_removecurse",0)
    Misc.SetSharedValue("use_removepoison",0)
if Player.GetSkillValue('Chivalry') < 15:
    Misc.SetSharedValue("use_cw",0)
if Player.GetSkillValue('Chivalry') < 25:
    Misc.SetSharedValue("use_df",0)
if Player.GetSkillValue('Chivalry') < 45:
    Misc.SetSharedValue("use_eoo",0)
    
# Bushido    
if Player.GetSkillValue('Bushido') < 25:
    Misc.SetSharedValue("use_confidence",0)
if Player.GetSkillValue('Bushido') < 40:
    Misc.SetSharedValue("use_ca",0)
if Player.GetSkillValue('Bushido') < 50:
    Misc.SetSharedValue("use_lightningstrike",0)
if Player.GetSkillValue('Bushido') < 60:
    Misc.SetSharedValue("use_evasion",0)
if Player.GetSkillValue('Bushido') < 70:
    Misc.SetSharedValue("use_momentumstrike",0)

#Spellweaving 
if Player.GetSkillValue('Spellweaving') < 10:
    Misc.SetSharedValue("use_immolatingweapon",0)
    Misc.SetSharedValue("use_thunderstorm",0)
if Player.GetSkillValue('Spellweaving') < 38:
    Misc.SetSharedValue("use_summonfeys",0)

# Misc    
if Player.GetSkillValue('Parry') < 10:
    Misc.SetSharedValue("use_ca",0)
    
if _is_ranged_build:
    changelingrange = 10 
    
if Player.GetSkillValue('Healing') > 30 or Player.GetSkillValue('Veterinary') > 30:
    Misc.SetSharedValue("use_bandages",1)

if Player.GetSkillValue('Necromancy') >= 99:    
    Misc.SetSharedValue("use_vampiricembrace",1)
    
if Player.GetSkillValue('Archery') >= 40:   
    Misc.SetSharedValue("use_arrows",1)
    
if Player.GetRealSkillValue('Archery') < 90:    
    Misc.SetSharedValue("use_playingtheodds",0)
    
# Check for Tactics and weapon skill to execute the weapon specials
if Player.GetSkillValue('Tactics') < 30:
    Player.HeadMessage(20,"Tactics skill is too low. Disable All Weapon Specials!")
    Misc.SetSharedValue("use_weaponspecialprimary",0)
    Misc.SetSharedValue("use_weaponspecialsecondary",0)
    Misc.Pause(1000)
    
elif Player.GetSkillValue('Tactics') < 60:
    Player.HeadMessage(20,"Tactics skill is too low. Disable Secondary Weapon Special!")
    Misc.SetSharedValue("use_weaponspecialsecondary",0)
    Misc.Pause(1000)
    
if Player.GetSkillValue('Mace Fighting') < 70 and Player.GetSkillValue('Fencing') < 70 and Player.GetSkillValue('Swordsmanship') < 70 and \
    Player.GetSkillValue('Archery') < 70 and Player.GetSkillValue('Throwing') < 70:
        Player.HeadMessage(20,"Weapon skill is too low. Disable Weapon Specials!")
        Misc.SetSharedValue("use_weaponspecialprimary",0)
        Misc.Pause(1000)
        
elif Player.GetSkillValue('Mace Fighting') < 90 and Player.GetSkillValue('Fencing') < 90 and Player.GetSkillValue('Swordsmanship') < 90 and \
    Player.GetSkillValue('Archery') < 90 and Player.GetSkillValue('Throwing') < 90:
        Player.HeadMessage(20,"Weapon skill is too low. Disable Secondary Weapon Special!")
        Misc.SetSharedValue("use_weaponspecialsecondary",0)   
        Misc.Pause(1000)

####################################
    
lmc = (min(40,Player.LowerManaCost))/100
lrc = Player.SumAttribute("Lower Reagent Cost")

# Cached gear stats
_cached_fcr       = min(6, Player.FasterCastRecovery)
_cached_fc        = Player.FasterCasting          # raw, caps applied in calc functions
_cached_castpause = ((6 - _cached_fcr) * 250) + serverdelay

# Cached mana reduction from combat skills
_cached_totalskills = (
    Player.GetSkillValue('Swordsmanship') + Player.GetSkillValue('Tactics') +
    Player.GetSkillValue('Mace Fighting') + Player.GetSkillValue('Fencing') +
    Player.GetSkillValue('Archery')       + Player.GetSkillValue('Parry') +
    Player.GetSkillValue('Lumberjacking') + Player.GetSkillValue('Stealth') +
    Player.GetSkillValue('Throwing')      + Player.GetSkillValue('Poisoning') +
    Player.GetSkillValue('Bushido')       + Player.GetSkillValue('Ninjitsu')
)

if _cached_totalskills >= 300:   _cached_manareduction = 10
elif _cached_totalskills >= 200: _cached_manareduction = 5
else:                            _cached_manareduction = 0

def get_weaponabilitiesmanacost(basemana):
    manacostscalar = 1
    if Player.BuffsExist("Mind Rot"): 
        manacostscalar += .25
    manacostscalar -= lmc
    requiredmana = int((basemana - _cached_manareduction) * manacostscalar)
    # Repeated weapon specials cost double mana for three seconds after use.
    # This timer tracks only that mana window; it must never block re-arming.
    if Timer.Check("weaponspecial_mana") == True:
        requiredmana *= 2
    return requiredmana

def longalarm():
    for i in range(0,5):
        winsound.Beep(1000,300)
        winsound.Beep(1000,300)
        winsound.Beep(1000,300)
        winsound.Beep(1000,800)
        
def legendarycheck():
    global _legendary_journal_timestamp
    entries = Journal.GetJournalEntry(_legendary_journal_timestamp)
    for entry in entries:
        if entry.Timestamp > _legendary_journal_timestamp:
            _legendary_journal_timestamp = entry.Timestamp
    if sv['use_checkforlegendaries'] != 1:
        return

    texts = [(entry.Text or "").lower() for entry in entries]
    if any("you sense a legendary" in text or
           "senses a legendary" in text for text in texts):
        Player.HeadMessage(20,"Legendary pet around!")
        Player.HeadMessage(20,"Legendary pet around!")
        Player.HeadMessage(20,"Legendary pet around!")
        longalarm()
    elif any("a curious creature apparates nearby" in text
             for text in texts):
        Player.HeadMessage(40,"Astral Pet around!")
        Player.HeadMessage(40,"Astral Pet around!")
        Player.HeadMessage(40,"Astral Pet around!")
        longalarm()

def calc_castspeed(spellcasttime):
    fcmin = 250
    fc = min(2, _cached_fc)
    if Player.BuffsExist('Protection'): 
        fc = _cached_fc - 2
    castspeed = spellcasttime - (fc * 250) + serverdelay + fcmin
    if castspeed < (serverdelay + fcmin): castspeed = serverdelay + fcmin
    return castspeed

def calc_castspeed_chiv_sw(spellcasttime):
    fcmin = 250
    fc = min(4, _cached_fc)
    if Player.BuffsExist('Protection'):
        fc = _cached_fc - 2
    castspeed = spellcasttime - (fc * 250) + serverdelay + fcmin
    if castspeed < (serverdelay + fcmin): castspeed = serverdelay + fcmin
    return castspeed

def trappedcrate():
    if sv['use_trappedcrate'] == 1 and Player.BuffsExist("Paralyze"):
        crate = Items.FindByID(0x0E7E, -1, Player.Backpack.Serial, 0, False)
        if not crate:
            Player.HeadMessage(20, "No trapped crate!")
        else:
            Player.HeadMessage(50, "Use trapped crate!")
            Items.UseItem(crate)

def binding_bracelet():
    global _binding_journal_timestamp
    entries = Journal.GetJournalEntry(_binding_journal_timestamp)
    for entry in entries:
        if (entry.Text and COLOSSAL_STUN_MESSAGE in entry.Text and
                Timer.Check(BINDING_BRACELET_TIMER) == False):
            bracelet = Items.FindByID(
                BINDING_BRACELET_ID,
                BINDING_BRACELET_HUE,
                Player.Backpack.Serial,
                -1,
                True)
            if bracelet:
                Items.UseItem(bracelet)
                Timer.Create(BINDING_BRACELET_TIMER, 3000)
                Player.HeadMessage(68, "Binding bracelet activated")
            else:
                Player.HeadMessage(30, "Binding bracelet not found")
        if entry.Timestamp > _binding_journal_timestamp:
            _binding_journal_timestamp = entry.Timestamp

def clear_stuck_target_cursor():
    global _target_cursor_seen
    if Misc.ReadSharedValue("attack_gump_targeting") == 1:
        _target_cursor_seen = False
        return
    if not Target.HasTarget():
        _target_cursor_seen = False
        return
    if not _target_cursor_seen:
        Timer.Create(TARGET_CURSOR_TIMER, TARGET_CURSOR_TIMEOUT_MS)
        _target_cursor_seen = True
        return
    if Timer.Check(TARGET_CURSOR_TIMER):
        return
    Target.TargetExecute(Player.Backpack.Serial)
    _target_cursor_seen = False
    Player.HeadMessage(68, "Cleared stuck target cursor")
    
            
def dresslist(): 
    if sv['use_dresslist'] == 1:
        name = str(sv['dresslist_name'] or "").strip()
        if name:
            Dress.ChangeList(name)
            Dress.DressFStart()
        
def check_townbuff():
    if sv['use_townbuff'] ==1:
        if not Player.BuffsExist ("City Trade Deal Buff"):
            Player.HeadMessage(20,"NO Town Bonus!")

def counterattack():
    if sv['use_ca'] == 1:
        if not Player.BuffsExist('Confidence') and not Player.BuffsExist('Evasion') and Timer.Check('spells') == False:
            if not Player.BuffsExist('Counter Attack') and Player.Hits >= Player.HitsMax * 0.50 and Player.Mana >= (5 - (5 * lmc)) and not Player.Paralized:
                if sv['use_messages'] == 1:
                    Player.HeadMessage(80,"Counter Attack!") 
                Spells.CastBushido("Counter Attack")
                Timer.Create('spells',calc_castspeed_chiv_sw(250) + _cached_castpause)

def onslaught(nearest):
    # Single-target only: Onslaught on the mob currently being attacked.
    # CastMastery with no target -> server applies it to the current combatant.
    # Recast is timed to Onslaught's ~6.2s active duration, which naturally
    # yields ~4 weapon-special swings in between. blockspecials keeps a weapon
    # special from arming and cancelling the readied Onslaught.
    global nearestonslaught, _onslaught_journal_timestamp
    entries = Journal.GetJournalEntry(_onslaught_journal_timestamp)
    for entry in entries:
        if entry.Timestamp > _onslaught_journal_timestamp:
            _onslaught_journal_timestamp = entry.Timestamp
    if sv['use_onslaught'] != 1:
        return

    if any(entry.Text and "you deliver an onslaught" in entry.Text.lower()
           for entry in entries):
        nearestonslaught = nearest.Serial
        Timer.Create('onslaught',6200)
        Timer.Create('blockspecials',100)
        Misc.Pause(100)

    if Player.Hits < Player.HitsMax * 0.50 or Player.Mana < (20 - (20 * lmc)):
        return

    # Recast on target switch while the timer is still running...
    if not Player.SpellIsEnabled("Onslaught") and Timer.Check('onslaught') == True:
        if nearest.Serial != nearestonslaught:
            Spells.CastMastery('Onslaught')
            Timer.Create('onslaught',1300)
            Timer.Create('blockspecials',1300)
            Misc.Pause(100)

    # ...or when the ~6.2s Onslaught duration has lapsed.
    if not Player.SpellIsEnabled("Onslaught") and Timer.Check('onslaught') == False:
        Spells.CastMastery('Onslaught')
        Timer.Create('onslaught',1300)
        Timer.Create('blockspecials',1300)
        Misc.Pause(100)

def auto_potion():
    # Non-spell quaff — pots do NOT break swing rhythm or VE leech.
    # Each branch is gated on its own cooldown timer.
    # One pot per tick: first match returns to avoid stacking pauses.

    # 1) Greater Refresh — stam recovery (archer swing-speed lifeline)
    if sv['use_pot_refresh'] == 1 and Timer.Check('pot_refresh') == False:
        pct = float(sv['stam_pot_pct']) / 100.0
        if Player.StamMax > 0 and Player.Stam < Player.StamMax * pct:
            pot = Items.FindByID(0x0F0B, -1, Player.Backpack.Serial, -1, True)
            if pot:
                Items.UseItem(pot)
                Timer.Create('pot_refresh', 10500)
                return

    # 2) Greater Cure — poisoned with no Chiv mana for Cleanse by Fire
    if sv['use_pot_cure'] == 1 and Timer.Check('pot_cure') == False:
        if Player.Poisoned and Player.Mana < (10 - (10 * lmc)):
            pot = Items.FindByID(0x0F07, -1, Player.Backpack.Serial, -1, True)
            if pot:
                Items.UseItem(pot)
                Timer.Create('pot_cure', 10500)
                return

    # 3) Emergency Heal pot — last-resort fallback at very low HP
    # Pots are NOT spells -> doesn't violate VE rule (no spell-heal in combat).
    if sv['use_pot_heal_emergency'] == 1 and Timer.Check('pot_heal') == False:
        pct = float(sv['heal_pot_pct']) / 100.0
        if Player.HitsMax > 0 and Player.Hits < Player.HitsMax * pct:
            pot = Items.FindByID(0x0F0C, -1, Player.Backpack.Serial, -1, True)
            if pot:
                Items.UseItem(pot)
                Timer.Create('pot_heal', 10500)
                return

def sync_pet_target(nearest):
    # Pet/summon attack sync — "all kill" issued only when target swaps.
    # Throttled by _last_pet_target_serial (no spam on same target) and a
    # short pet_sync timer (avoids back-to-back issues with target cursors).
    global _last_pet_target_serial
    if sv['use_pet_sync'] != 1:
        return
    if Player.Followers <= 0:
        return
    if nearest is None or nearest.Serial == 0:
        return
    if _last_pet_target_serial == nearest.Serial:
        return
    if Timer.Check('pet_sync') != False:
        return
    Player.ChatSay("all kill")
    Target.WaitForTarget(1500, True)
    Target.TargetExecute(nearest.Serial)
    _last_pet_target_serial = nearest.Serial
    Timer.Create('pet_sync', 2000)

def pick_target(victims_dist):
    # Score-based target picker. Higher score wins.
    # Up-rank casters/healers/paragons; closer is better otherwise.
    if not victims_dist:
        return None
    best = None
    best_score = None
    for m, d in victims_dist:
        s = -float(d)  # closer is better, by default
        try:
            if m.YellowHits:
                s += 100.0
            mid = m.MobileID
            if mid in SMART_TARGET_CASTER_IDS:
                s += 500.0
            if mid in SMART_TARGET_HEALER_IDS:
                s += 300.0
        except:
            pass
        if best_score is None or s > best_score:
            best = m
            best_score = s
    return best

def pick_weapon_special(nearest, weapon):
    # Context-aware weapon-special slot picker for single-target fights.
    # Returns "primary", "secondary", or None.
    # Priority (highest first):
    #   1) Mortal Strike on paragons (YellowHits) or known healer IDs
    #      -> lock out enemy self-heals while you grind them down.
    #   2) Paralyzing / Concussion Blow on known caster IDs
    #      -> interrupt mid-cast for a free swing window.
    #   3) Armor Ignore as finisher when nearest is the current Onslaught
    #      target AND HP bar <= 25%.
    #   4) Fall back to the weapon's configured singleenemyspecial.

    def slot_for(*names):
        for n in names:
            if weapon.weaponspecial_primary == n:
                return "primary"
            if weapon.weaponspecial_secondary == n:
                return "secondary"
        return None

    try:
        mid = nearest.MobileID
        is_paragon = nearest.YellowHits
        low_hp = (nearest.HitsMax > 0 and (nearest.Hits / float(nearest.HitsMax)) <= 0.25)
    except:
        mid = 0
        is_paragon = False
        low_hp = False

    if is_paragon or mid in SMART_TARGET_HEALER_IDS:
        slot = slot_for("Mortal Strike")
        if slot:
            return slot

    if mid in SMART_TARGET_CASTER_IDS:
        slot = slot_for("Paralyzing Blow", "Concussion Blow")
        if slot:
            return slot

    if low_hp and nearestonslaught != 0 and nearest.Serial == nearestonslaught:
        slot = slot_for("Armor Ignore")
        if slot:
            return slot

    return weapon.singleenemyspecial

def honorable_execution(nearest):
    # Bushido finisher — fire only when killshot likely.
    # On kill: -resist self-debuff suppressed, +HCI/+SSI ~20s reward buff.
    # NOTE: nearest.Hits is HP-bar value (0..HitsMax bar), not absolute HP -> use ratio.
    if sv['use_he'] != 1:
        return
    if nearest is None or nearest.HitsMax <= 0:
        return
    if Player.BuffsExist('Honorable Execution'):
        return
    if Player.HasSpecial:
        return
    if Player.Paralized:
        return
    if Timer.Check('he_cd') != False:
        return
    if Player.DistanceTo(nearest) > 1 or nearest.Hits <= 0:
        return
    # mana check — HE base cost ~25 mana, lmc-scaled
    if Player.Mana < (25 - (25 * lmc)):
        return
    # killshot window — nearest at/below configured % of max HP bar
    pct = float(sv['he_killshot_pct']) / 100.0
    if (nearest.Hits / float(nearest.HitsMax)) > pct:
        return
    if sv['use_messages'] == 1:
        Player.HeadMessage(80, "Honorable Execution!")
    Spells.CastBushido('Honorable Execution')
    Timer.Create('he_cd', 1500)
    Timer.Create('blockspecials', 1500)
    Misc.Pause(150)

def playingtheodds():
    if sv['use_playingtheodds'] == 1:
        if not Player.BuffsExist("Playing The Odds Debuff") and Player.Mana >= (25 - (25 * lmc)):        
            if Timer.Check('spells') == False and Timer.Check('odds') == False and not Player.Mount:
                Player.HeadMessage(80,"Playing The Odds") 
                Spells.CastMastery("Playing The Odds")
                Timer.Create('spells',calc_castspeed(2250) + _cached_castpause)
                Timer.Create('odds',95000)           
            
            
def curseweapon(): 
    if sv['use_curseweapon'] == 1 and Player.Hits < Player.HitsMax * 0.50 and Player.Mana >= (7 - (7 * lmc)) and Timer.Check('spells') == False and not Player.Paralized:
        has_reagent = lrc > 90
        if not has_reagent:
            pigiron = Items.FindByID(0x0F8A,0x0000,Player.Backpack.Serial,-1,True)
            has_reagent = pigiron is not None and pigiron.Amount > 0
        if has_reagent and not Player.BuffsExist("Curse Weapon"):
            if sv['use_messages'] == 1:
                Player.HeadMessage(90,"Curse Weapon")
            Spells.CastNecro("Curse Weapon")
            Timer.Create('spells',calc_castspeed(1000) + _cached_castpause)

def checkbloodoath():
    if Player.BuffsExist('Bload Oath (curse)'):
        Player.HeadMessage(40,"Blood Oath! RUN!")
        Player.HeadMessage(40,"Blood Oath! RUN!")
        Player.HeadMessage(40,"Blood Oath! RUN!")
        if Player.WarMode:
            Player.SetWarMode(False)

        if sv['use_pot_apple'] != 1:
            blood_oath_apple_warning("Enchanted Apples disabled")
        elif Timer.Check('pot_apple') != False:
            blood_oath_apple_warning("Enchanted Apple cooldown")
        else:
            apple = find_enchanted_apple()
            if apple:
                if sv['use_messages'] == 1:
                    Player.HeadMessage(80,"Enchanted Apple!")
                Items.UseItem(apple)
                Timer.Create('pot_apple', 60000)
                Misc.Pause(1000)
                if not Player.BuffsExist('Bload Oath (curse)'):
                    return
            else:
                blood_oath_apple_warning("No Enchanted Apples")

        # Missing, disabled, cooling down, or attempted without clearing Blood
        # Oath: immediately fall back to Remove Curse.
        if sv['use_removecurse'] == 1 and Timer.Check('spells') == False and not Player.Paralized:
            if sv['use_messages'] == 1:
                Player.HeadMessage(80,"Remove Curse!")
            Spells.CastChivalry('Remove Curse',Player.Serial,True)
            Timer.Create('spells',calc_castspeed_chiv_sw(1500) + _cached_castpause)


def blood_oath_apple_warning(message):
    if Timer.Check('blood_oath_apple_warning') != False:
        return
    Player.HeadMessage(30, message)
    Timer.Create('blood_oath_apple_warning', 5000)
            
def checkweight():
    if sv['use_bagofsending'] == 1 and Timer.Check("bagcheck") == False:
        bagofsending = find_bag_of_sending()
        Timer.Create("bagcheck", 3000)
        if not bagofsending:
            if Timer.Check("bagofsending") == False:
                Player.HeadMessage(20, "NO Bag of Sending!")
                Timer.Create("bagofsending", 10000)
        else:
            if Player.Weight >= Player.MaxWeight * 0.95:
                gold = Items.FindByID(0x0EED, 0, Player.Backpack.Serial, 1, False)
                if gold:
                    Items.UseItem(bagofsending)
                    Target.WaitForTarget(4000,True)
                    Target.TargetExecute(gold) 
                    
            if Timer.Check("bagofsending") == False:
                charges = Items.GetPropValue(bagofsending, "Charges")
                if charges < 4:
                    Player.HeadMessage(30, "Bag of Sending %i charges left!" % charges)
                Timer.Create("bagofsending", 10000)


def find_bag_of_sending():
    global _bag_of_sending_cache_serial

    if _bag_of_sending_cache_serial != 0:
        cached = Items.FindBySerial(_bag_of_sending_cache_serial)
        if cached and not cached.Deleted:
            container = cached.Container
            try:
                container = container.Serial
            except:
                pass
            if container == Player.Backpack.Serial:
                return cached
        _bag_of_sending_cache_serial = 0

    bag = Items.FindByName("a bag of sending", -1, Player.Backpack.Serial, 0, False)
    if bag:
        _bag_of_sending_cache_serial = bag.Serial
    return bag


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


def select_lootbag(prompt):
    serial = Target.PromptTarget(prompt)
    if serial is None or serial <= 0:
        Player.HeadMessage(30, "Loot bag selection canceled")
        return None
    if serial == Player.Backpack.Serial:
        Player.HeadMessage(30, "Select a bag inside the backpack, not the backpack")
        return None
    lootbag = Items.FindBySerial(serial)
    if not lootbag:
        Player.HeadMessage(30, "Loot bag not found")
        return None
    if not item_is_in_backpack(lootbag):
        Player.HeadMessage(30, "Loot bag must be inside your backpack")
        return None
    Misc.SetSharedValue("lootbag_serial", serial)
    sv['lootbag_serial'] = serial
    save_settings()
    Player.HeadMessage(68, "Artifact loot bag saved")
    return lootbag


def backpack_items_except(container, excluded_serial, seen=None):
    if seen is None:
        seen = set()
    if not container or container.Serial in seen:
        return []
    seen.add(container.Serial)
    try:
        contents = list(container.Contains)
    except:
        return []

    found = []
    for item in contents:
        if item is None or item.Deleted or item.Serial == excluded_serial:
            continue
        found.append(item)
        found.extend(backpack_items_except(item, excluded_serial, seen))
    return found


def cached_item_name(item, cache):
    cached = cache.get(item.Serial)
    if cached is not None:
        return cached

    name = item.Name
    if not name:
        Items.WaitForProps(item.Serial, 500)
        refreshed = Items.FindBySerial(item.Serial)
        name = refreshed.Name if refreshed else None
    if not name:
        return None

    normalized = str(name).strip().lower()
    cache[item.Serial] = normalized
    return normalized


def find_enchanted_apple():
    global _enchanted_apple_cache_serial

    if Timer.Check('enchanted_apple_scan') != False:
        if _enchanted_apple_cache_serial == 0:
            return None
        cached = Items.FindBySerial(_enchanted_apple_cache_serial)
        if (cached and not cached.Deleted and
                cached.ItemID == ENCHANTED_APPLE_ID and cached.Amount > 0):
            return cached
        _enchanted_apple_cache_serial = 0

    apple = Items.FindByID(
        ENCHANTED_APPLE_ID,
        -1,
        Player.Backpack.Serial,
        True,
        False
    )
    if apple:
        _enchanted_apple_cache_serial = apple.Serial
        Timer.Create('enchanted_apple_scan', 1000)
        return apple
    Timer.Create('enchanted_apple_scan', 1000)
    return None


def drop_heirloom_chests():
    if Timer.Check("heirloomdrop") != False:
        return
    Timer.Create("heirloomdrop", 10000)

    # Filter natively by graphic/hue instead of walking every backpack item.
    checked = set()
    while True:
        item = Items.FindByID(
            HEIRLOOM_CHEST_ID,
            HEIRLOOM_CHEST_HUE,
            Player.Backpack.Serial,
            True,
            False
        )
        if not item or item.Serial in checked:
            return
        checked.add(item.Serial)

        name = item.Name
        if not name:
            Items.WaitForProps(item.Serial, 500)
            refreshed = Items.FindBySerial(item.Serial)
            name = refreshed.Name if refreshed else None
        if not name or str(name).strip().lower() != HEIRLOOM_CHEST_NAME:
            return

        serial = item.Serial
        for dx, dy in HEIRLOOM_DROP_OFFSETS:
            Items.MoveOnGround(
                item, 0,
                Player.Position.X + dx,
                Player.Position.Y + dy,
                Player.Position.Z
            )
            Misc.Pause(600)
            moved = Items.FindBySerial(serial)
            if moved is None or moved.Container is None or moved.Container == 0:
                if sv['use_messages'] == 1:
                    Player.HeadMessage(68, "Dropped Chest of Heirlooms")
                break
        else:
            Player.HeadMessage(30, "Could not drop Chest of Heirlooms")
            return


def move_artifacts_to_lootbag():
    if sv['use_move_artis'] != 1 or Timer.Check("artifactmove") != False:
        return
    Timer.Create("artifactmove", 10000)

    lootbag = Items.FindBySerial(sv['lootbag_serial'])
    if lootbag and not item_is_in_backpack(lootbag):
        lootbag = None
    if not lootbag:
        if Timer.Check("lootbagprompt") != False:
            return
        Timer.Create("lootbagprompt", 10000)
        lootbag = select_lootbag("Loot bag not found - select the artifact loot bag")
        if not lootbag:
            return

    items = backpack_items_except(Player.Backpack, lootbag.Serial)
    live_serials = {item.Serial for item in items}
    for serial in list(_artifact_name_cache):
        if serial not in live_serials:
            del _artifact_name_cache[serial]

    for item in items:
        name = cached_item_name(item, _artifact_name_cache)
        if name in ARTIFACT_NAMES:
            Items.Move(item, lootbag.Serial, -1)
            if sv['use_messages'] == 1:
                Player.HeadMessage(68, "Move artifact: %s" % name)
            Misc.Pause(600)


def check_vamp():
    if sv['use_vampiricembrace'] == 1:
        if not Player.BuffsExist ("Vampiric Embrace"):
            #Spells.CastNecro ("Vampiric Embrace")
            Player.HeadMessage(20,"NO VAMPIRIC EMBRACE!")
                
def check_bandages():
    if sv['use_bandages'] == 1:
        bandagesamount = Items.ContainerCount(Player.Backpack.Serial,0x0E21,-1,False)
        firstaidbelt = Items.FindByName("First Aid Belt", -1, Player.Backpack.Serial, -1, False)
        if firstaidbelt:
            bandagesamount += Items.ContainerCount(firstaidbelt.Serial, 0x0E21, -1, False)
        waist_item = Player.GetItemOnLayer("Waist")
        if waist_item and waist_item.Name == "First Aid Belt":
            #Items.UseItem(waist_item)
            bandagesamount += Items.ContainerCount(waist_item.Serial, 0x0E21, -1, False)
        #Player.HeadMessage(50,"%s Bandages left" % bandagesamount)  
        if bandagesamount < 100:
            Player.HeadMessage(30,"Warning: %s Bandages left" % bandagesamount)

def check_arrows():
    # Threshold-based refill for arrows AND bolts (crossbow support).
    # Tops up quiver from pack stock whenever quiver count dips below
    # sv['quiver_low_threshold'] — no need to wait for empty.
    if sv['use_arrows'] != 1:
        return
    quiver = Player.GetItemOnLayer('Cloak')
    has_quiver = quiver and quiver.ItemID == 0x2B02
    threshold = sv['quiver_low_threshold']

    for ammo_id, ammo_name in ((0x0F3F, "arrows"), (0x1BFB, "bolts")):
        pack_count = Items.ContainerCount(Player.Backpack.Serial, ammo_id, 0, True)
        quiver_count = 0
        if has_quiver:
            quiver_count = Items.ContainerCount(quiver, ammo_id, 0, False)
            if quiver_count < threshold and pack_count > 0:
                ammo = Items.FindByID(ammo_id, -1, Player.Backpack.Serial, -1, False)
                if ammo:
                    if sv['use_messages'] == 1:
                        Player.HeadMessage(50, "Refill %s -> quiver" % ammo_name)
                    Items.Move(ammo, quiver, 500)
                    Misc.Pause(500)
                    pack_count = Items.ContainerCount(Player.Backpack.Serial, ammo_id, 0, True)
                    quiver_count = Items.ContainerCount(quiver, ammo_id, 0, False)
        total = pack_count + quiver_count
        # only warn for the ammo type the player actually carries (>0)
        if total > 0 and total < 100:
            Player.HeadMessage(30, "Warning: %s %s left" % (total, ammo_name))
        
def removepoison():
    if sv['use_removepoison'] == 1:
        if Player.Poisoned and not Player.BuffsExist("Bleed") and Timer.Check('spells') == False and not Player.Paralized:
            if sv['use_messages'] == 1:
                Player.HeadMessage(80,"Remove Poison!")
            Spells.CastChivalry("Cleanse by fire",Player.Serial,True)
            Timer.Create('spells',calc_castspeed_chiv_sw(1000) + _cached_castpause)

def removecurse():          
    if sv['use_removecurse'] == 1 and not Player.Poisoned and not Player.BuffsExist("Bleed") and not Player.BuffsExist("Strangle")and Timer.Check('spells') == False and not Player.Paralized:
        if Player.BuffsExist("Curse") or Player.BuffsExist("Clumsy") or Player.BuffsExist("Weaken") or Player.BuffsExist("Blood Oath"):
            if sv['use_messages'] == 1:
                Player.HeadMessage(80,"Remove Curse!")
            Spells.CastChivalry('Remove Curse',Player.Serial,True)
            Timer.Create('spells',calc_castspeed_chiv_sw(1500) + _cached_castpause)
                    
def checkhits():
        if Player.Hits <= Player.HitsMax * 0.85 and sv['use_confidence'] == 1:
            if not Player.BuffsExist('Evasion') and Timer.Check('confidence') == False and not Player.BuffsExist('Confidence') and not Player.Paralized and Timer.Check('spells') == False:
                if sv['use_messages'] == 1:
                    Player.HeadMessage(80,"Confidence!")
                Spells.CastBushido("Confidence",True)
                Timer.Create('spells',calc_castspeed_chiv_sw(250) + _cached_castpause)
                Timer.Create('confidence',4000)
            if not Player.BuffsExist('Evasion') and Timer.Check('confidence') == True and not Player.BuffsExist('Confidence'):
                Timer.Create('confidence',3000)
                    
def evasion():
    if Player.Hits <= Player.HitsMax * 0.60 and sv['use_evasion'] == 1 and Timer.Check('evasion') == False and Player.Mana >= (10 - (10 * lmc)) and not Player.Paralized and Timer.Check('spells') == False:
        if not Player.BuffsExist('Confidence'):
            if sv['use_messages'] == 1:
                Player.HeadMessage(80,"Evasion!")
            Spells.CastBushido("Evasion",True)
            Timer.Create('spells',calc_castspeed_chiv_sw(250) + _cached_castpause)
            Timer.Create('evasion',20000)               
                
_DF_STAM_THRESHOLD = 180

def divinefury_lowstam():
    # Auto Divine Fury whenever stamina is low, even when not cursed.
    if Player.BuffsExist('Divine Fury'):
        return
    if Timer.Check('spells') != False or Player.Paralized:
        return
    if Player.Mana < (15 - (15 * lmc)):
        return
    if Player.Stam < _DF_STAM_THRESHOLD:
        if sv.get('use_messages') == 1:
            Player.HeadMessage(80,"Divine Fury!")
        Spells.CastChivalry('Divine Fury')
        Timer.Create('spells',calc_castspeed_chiv_sw(1000) + _cached_castpause)

def closewounds():
    if Player.Hits <= Player.HitsMax * 0.70 and sv['use_closewounds'] == 1 and Timer.Check('spells') == False and not Player.Paralized and Player.Mana >= (10 - (10 * lmc)):
        if sv['use_messages'] == 1:
            Player.HeadMessage(80,"Close Wounds!")
        Spells.CastChivalry("Close Wounds",Player.Serial,True)
        Timer.Create('spells',calc_castspeed_chiv_sw(1500) + _cached_castpause)

def check_arcanefocus():
    if sv['use_arcanefocus'] == 1:
        arcanefocus = Items.BackpackCount(0x3155, 0)
        if not arcanefocus:
            Player.HeadMessage(40,"NO ARCANE FOCUS!")
                
def immolatingweapon():
    if sv['use_immolatingweapon'] == 1:
        if Timer.Check('spells') == False and not Player.Paralized and Player.Mana >= (32 - (32 * lmc)):
            if Timer.Check('immolating') == False:
                Player.HeadMessage(80,"Immolating Weapon")
                Spells.CastSpellweaving("Immolating Weapon")
                Timer.Create('immolating',20000)
                Timer.Create('spells',calc_castspeed_chiv_sw(1000) + _cached_castpause)

def attuneweapon():
    if sv['use_attuneweapon'] == 1:
        if Timer.Check('spells') == False and not Player.Paralized and Player.Mana >= (24 - (24 * lmc)): 
            if Timer.Check('attuneweapon') == False and not Player.BuffsExist("Attunement",True):
                Player.HeadMessage(80,"Attune Weapon")
                Spells.CastSpellweaving("Attune Weapon")
                Timer.Create('attuneweapon',120000)
                Timer.Create('spells',calc_castspeed_chiv_sw(1000) + _cached_castpause)

def castsummonfey():
    global guardme
    if sv['use_summonfeys'] == 1:
        if Timer.Check('spells') == False and not Player.Paralized:
            if Player.Followers >= sv['fey_threshold']:   
                if guardme == 1:
                    Player.ChatSay("all guard me")
                    guardme = 0
            elif Player.Followers < sv['fey_threshold'] and Player.Mana >= (10 - (10 * lmc)):
                Player.HeadMessage(80,"Summon Fey")
                Spells.CastSpellweaving("Summon Fey")
                guardme = 1
                Timer.Create('spells',calc_castspeed_chiv_sw(1500) + _cached_castpause)

def castmirrorimage(has_nearby_mobs):
    if sv['use_mirrorimage'] != 1:
        return
    if not has_nearby_mobs:
        return
    if Player.Followers >= MIRROR_IMAGE_FOLLOWER_THRESHOLD or Player.Mount or Player.Paralized:
        return
    if Player.GetSkillValue('Ninjitsu') < 20 or Player.Mana < (10 - (10 * lmc)):
        return
    if Timer.Check('spells') != False:
        return
    if sv['use_messages'] == 1:
        Player.HeadMessage(80,"Mirror Image")
    Spells.CastNinjitsu("Mirror Image")
    Timer.Create('spells',calc_castspeed(1500) + _cached_castpause)

def release_one_mirror_image(has_nearby_mobs):
    if sv['use_releasemirrorimage'] != 1:
        return
    # Releasing without a nearby mob causes the player to take bleed damage.
    if not has_nearby_mobs:
        return
    if Player.Followers != 4 or Timer.Check('mirror_release') != False:
        return

    Timer.Create('mirror_release', 3000)
    fil = Mobiles.Filter()
    fil.Enabled = True
    # Images can follow outside a melee character's short AttackRange.
    fil.RangeMax = max(12, sv['attackrange'])
    fil.CheckIgnoreObject = False
    fil.IgnorePets = False
    copies = Mobiles.ApplyFilter(fil)

    for mob in copies:
        if mob is None or mob.Deleted or mob.Serial == Player.Serial:
            continue
        if mob.Name != Player.Name or mob.MobileID != Player.MobileID:
            continue

        contexts = Misc.WaitForContext(mob.Serial, 750) or []
        for context in contexts:
            if str(context.Entry).strip().lower() == "release":
                Misc.ContextReply(mob.Serial, context.Response)
                if sv['use_messages'] == 1:
                    Player.HeadMessage(68, "Released one Mirror Image")
                return

def checkwhitetigerform():
    if sv['use_whitetigerform'] != 1:
        return
    if Player.GetSkillValue('Ninjitsu') < 120 or Player.GetSkillValue('Stealth') < 120:
        return
    if Player.BuffsExist("White Tiger Form") or Player.BuffsExist('Bload Oath (curse)'):
        return
    if Player.Paralized or Player.Mana < (10 - (10 * lmc)):
        return
    if Timer.Check('spells') != False or Timer.Check('white_tiger_form') != False:
        return
    if sv['use_messages'] == 1:
        Player.HeadMessage(80,"White Tiger Form")
    Spells.CastMastery("White Tiger Form")
    Timer.Create('white_tiger_form',5000)
    Timer.Create('spells',calc_castspeed(2250) + _cached_castpause)

def holylight(victims_3):
    if sv['use_holylight'] != 1 or len(victims_3) < 3:
        return
    if (sv['use_mirrorimage'] == 1 and
            Player.Followers < MIRROR_IMAGE_FOLLOWER_THRESHOLD):
        return
    if Player.BuffsExist('Bload Oath (curse)'):
        return
    if Timer.Check('spells') != False or Player.Paralized:
        return
    if Player.Mana < (10 - (10 * lmc)):
        return
    if sv['use_messages'] == 1:
        Player.HeadMessage(80,"Holy Light")
    Spells.CastChivalry('Holy Light')
    Timer.Create('spells',calc_castspeed_chiv_sw(1750) + _cached_castpause)
                
def thunderstorm():
    if Timer.Check('spells') == False and not Player.Paralized and Player.Mana >= (32 - (32 * lmc)):
        Player.HeadMessage(80,'Thunderstorm') 
        Spells.CastSpellweaving('Thunderstorm')
        Timer.Create('spells',calc_castspeed_chiv_sw(1500) + _cached_castpause) 
            
def selected_ninjitsu_attack():
    # Death Strike and Focus Attack are mutually exclusive. Backstab is handled
    # by its own Shadow Strike -> hidden Backstab state loop below.
    if sv['use_deathstrike'] == 1:
        return ("Death Strike", 30)
    if sv['use_focusattack'] == 1:
        return ("Focus Attack", 10)
    return None

def ninjitsu_move_mana_cost(base_mana):
    mana_scalar = 1.25 if Player.BuffsExist("Mind Rot") else 1.0
    return int(base_mana * (mana_scalar - lmc))

def shadow_strike_slot():
    weapon = weapons.get(weapon_set)
    if weapon is None:
        return None
    if weapon.weaponspecial_primary == "Shadow Strike":
        return "primary"
    if weapon.weaponspecial_secondary == "Shadow Strike":
        return "secondary"
    return None

SMOKE_BOMB_IDS = (0x2808, 0x2809)
SMOKE_BOMB_MANA = 10
SMOKE_BOMB_RETRY_MS = 10000

def find_smoke_bomb():
    global _smoke_bomb_cache_serial

    if sv.get('use_smokebombs') != 1:
        return None

    if Timer.Check('smokebomb_scan') != False:
        if _smoke_bomb_cache_serial == 0:
            return None
        cached = Items.FindBySerial(_smoke_bomb_cache_serial)
        if (cached and not cached.Deleted and
                cached.ItemID in SMOKE_BOMB_IDS and cached.Amount > 0):
            return cached
        _smoke_bomb_cache_serial = 0
        return None

    _smoke_bomb_cache_serial = 0
    for item_id in SMOKE_BOMB_IDS:
        bomb = Items.FindByID(item_id, -1, Player.Backpack.Serial, -1, True)
        if bomb:
            _smoke_bomb_cache_serial = bomb.Serial
            Timer.Create('smokebomb_scan', 1000)
            return bomb
    Timer.Create('smokebomb_scan', 1000)
    return None

def smoke_bomb_available():
    if sv['use_smokebombs'] != 1:
        return False
    if Player.GetSkillValue('Ninjitsu') < 50:
        return False
    return find_smoke_bomb() is not None

def use_smoke_bomb():
    if (sv['use_smokebombs'] != 1 or
            Player.GetSkillValue('Ninjitsu') < 50 or not Player.Visible or
            Player.Paralized or Timer.Check('smokebomb_retry') != False or
            Player.Mana < SMOKE_BOMB_MANA):
        return False

    bomb = find_smoke_bomb()
    if bomb is None:
        return False

    if sv['use_messages'] == 1:
        Player.HeadMessage(80,"Egg/Smoke Bomb")
    Items.UseItem(bomb)
    Timer.Create('smokebomb_retry', SMOKE_BOMB_RETRY_MS)
    Misc.Pause(250)
    return not Player.Visible

def backstab_loop_enabled():
    if sv['use_backstab'] != 1:
        return False
    if selected_ninjitsu_attack() is not None:
        return False
    if (Player.GetSkillValue('Ninjitsu') < 40 or
            Player.GetSkillValue('Stealth') < 80 or
            Player.GetRealSkillValue('Hiding') < 30 or
            Player.BuffsExist('Bload Oath (curse)')):
        return False

    shadow_available = (shadow_strike_slot() is not None and
                        sv['disable_weaponspecials'] != 1)
    return shadow_available or smoke_bomb_available()

def reset_backstab_cycle(clear_target=True):
    global _backstab_state, _backstab_target_serial
    global _backstab_was_armed, _backstab_attack_sent
    global _backstab_stealth_requested

    _backstab_state = BACKSTAB_STATE_SHADOW
    _backstab_was_armed = False
    _backstab_attack_sent = False
    _backstab_stealth_requested = False
    if clear_target:
        _backstab_target_serial = 0

def start_backstab_filler():
    global _backstab_state, _backstab_was_armed, _backstab_attack_sent

    _backstab_state = BACKSTAB_STATE_FILLER
    _backstab_was_armed = False
    _backstab_attack_sent = False
    Timer.Create('backstab_lock', BACKSTAB_LOCK_MS)
    if sv['use_messages'] == 1:
        Player.HeadMessage(68,"Backstab confirmed: filler combat")

def track_backstab_execution():
    global _backstab_was_armed

    if not backstab_loop_enabled():
        reset_backstab_cycle()
        return

    armed = Player.SpellIsEnabled("Backstab")
    consumed = (_backstab_state == BACKSTAB_STATE_BACKSTAB and
                _backstab_was_armed and not armed)
    attempted = (_backstab_state == BACKSTAB_STATE_BACKSTAB and
                 _backstab_attack_sent and Player.Visible)

    if consumed or attempted:
        start_backstab_filler()
        return
    _backstab_was_armed = armed

def backstab_reserved_mana():
    if (shadow_strike_slot() is not None and
            sv['disable_weaponspecials'] != 1):
        hide_mana = get_weaponabilitiesmanacost(20)
    else:
        hide_mana = SMOKE_BOMB_MANA
    return hide_mana + ninjitsu_move_mana_cost(30)

def other_weapon_special():
    weapon = weapons.get(weapon_set)
    shadow_slot = shadow_strike_slot()
    if weapon is None or shadow_slot is None:
        return (None, None)

    if shadow_slot == "primary":
        return ("secondary", weapon.weaponspecial_secondary)
    return ("primary", weapon.weaponspecial_primary)

def weapon_special_base_mana(name):
    if name == "Whirlwind":
        return 15
    if name == "Shadow Strike":
        return 20
    return 30

def arm_shadow_strike():
    slot = shadow_strike_slot()
    if slot is None:
        return False
    if Player.HasSpecial:
        return True
    if Timer.Check('weaponspecial_arm') != False or Player.Paralized:
        return False
    if Player.Mana < get_weaponabilitiesmanacost(20):
        return False

    if sv['use_messages'] == 1:
        Player.HeadMessage(70,"Shadow Strike")
    if slot == "primary":
        Player.WeaponPrimarySA()
    else:
        Player.WeaponSecondarySA()
    Timer.Create('weaponspecial_arm', WEAPON_SPECIAL_ARM_DEBOUNCE_MS)
    Misc.Pause(200)
    return Player.HasSpecial

def arm_backstab():
    global _backstab_was_armed

    if Player.SpellIsEnabled("Backstab"):
        _backstab_was_armed = True
        return True
    if Timer.Check('ninjitsu_move') != False or Player.Paralized:
        return False
    if Player.Mana < ninjitsu_move_mana_cost(30):
        return False

    if sv['use_messages'] == 1:
        Player.HeadMessage(80,"Backstab")
    Spells.CastNinjitsu("Backstab")
    Timer.Create('ninjitsu_move',800)
    Misc.Pause(200)
    if Player.SpellIsEnabled("Backstab"):
        _backstab_was_armed = True
        return True
    return False

def arm_filler_special(nearby_enemies):
    if sv['disable_weaponspecials'] == 1:
        return False
    slot, name = other_weapon_special()
    if slot is None or name is None:
        return False
    if name == "Whirlwind" and len(nearby_enemies) < 2:
        return False

    remaining = Timer.Remaining('backstab_lock')
    if remaining < (BACKSTAB_FINAL_NORMAL_MS + BACKSTAB_SWING_MS + 200):
        return False
    if Player.HasSpecial or Timer.Check('weaponspecial_arm') != False:
        return Player.HasSpecial

    required = get_weaponabilitiesmanacost(weapon_special_base_mana(name))
    if Player.Mana < (backstab_reserved_mana() + required):
        return False

    if sv['use_messages'] == 1:
        Player.HeadMessage(70,name)
    if slot == "primary" and sv['use_weaponspecialprimary'] != 0:
        Player.WeaponPrimarySA()
    elif slot == "secondary" and sv['use_weaponspecialsecondary'] != 0:
        Player.WeaponSecondarySA()
    else:
        return False
    Timer.Create('weaponspecial_arm', WEAPON_SPECIAL_ARM_DEBOUNCE_MS)
    Misc.Pause(200)
    return Player.HasSpecial

def take_backstab_stealth_step(nearest):
    try:
        px = Player.Position.X
        py = Player.Position.Y
        tx = nearest.Position.X
        ty = nearest.Position.Y
    except:
        return False

    for direction, dx, dy in BACKSTAB_STEP_DIRECTIONS:
        nx = px + dx
        ny = py + dy
        if nx == tx and ny == ty:
            continue
        if max(abs(nx - tx), abs(ny - ty)) > 1:
            continue
        if Player.Walk(direction):
            Misc.Pause(250)
            return True
    return False

def backstab_cycle_attack(nearest, nearby_enemies):
    global _backstab_state, _backstab_target_serial
    global _backstab_attack_sent, _backstab_stealth_requested

    if not backstab_loop_enabled() or nearest is None or nearest.Deleted:
        return False

    if _backstab_target_serial == 0:
        _backstab_target_serial = nearest.Serial

    if _backstab_state == BACKSTAB_STATE_SHADOW:
        if not Player.Visible:
            _backstab_state = BACKSTAB_STATE_STEALTH
            _backstab_stealth_requested = False
        elif (shadow_strike_slot() is not None and
                sv['disable_weaponspecials'] != 1 and
                Timer.Check('weaponspecial_mana') == False and
                Player.Mana >= backstab_reserved_mana()):
            arm_shadow_strike()
            if Player.HasSpecial:
                if not Player.WarMode:
                    Player.SetWarMode(True)
                Player.Attack(nearest)
                sync_pet_target(nearest)
            return True
        elif (smoke_bomb_available() and
                Timer.Check('smokebomb_retry') == False and
                Player.Mana >= (SMOKE_BOMB_MANA + ninjitsu_move_mana_cost(30))):
            if use_smoke_bomb():
                _backstab_state = BACKSTAB_STATE_STEALTH
                _backstab_stealth_requested = False
            return True
        else:
            Player.Attack(nearest)
            sync_pet_target(nearest)
            return True

    if _backstab_state == BACKSTAB_STATE_STEALTH:
        if Player.Visible:
            reset_backstab_cycle(clear_target=False)
            return True
        if not _backstab_stealth_requested:
            if take_backstab_stealth_step(nearest):
                _backstab_stealth_requested = True
                Timer.Create('backstab_stealth_ack', BACKSTAB_STEALTH_ACK_MS)
            return True
        if Timer.Check('backstab_stealth_ack') != False:
            return True
        _backstab_state = BACKSTAB_STATE_BACKSTAB

    if _backstab_state == BACKSTAB_STATE_BACKSTAB:
        if Player.Visible:
            reset_backstab_cycle(clear_target=False)
            return True
        if Player.HasSpecial:
            Player.WeaponClearSA()
        arm_backstab()
        if Player.SpellIsEnabled("Backstab"):
            if not Player.WarMode:
                Player.SetWarMode(True)
            Player.Attack(nearest)
            sync_pet_target(nearest)
            _backstab_attack_sent = True
        return True

    if _backstab_state == BACKSTAB_STATE_FILLER:
        if Timer.Check('backstab_lock') == False:
            _backstab_state = BACKSTAB_STATE_FINAL
        elif Timer.Remaining('backstab_lock') <= BACKSTAB_FINAL_NORMAL_MS:
            _backstab_state = BACKSTAB_STATE_FINAL
        else:
            arm_filler_special(nearby_enemies)

    if _backstab_state == BACKSTAB_STATE_FINAL:
        if Player.HasSpecial:
            Player.WeaponClearSA()
        if (Timer.Check('backstab_lock') == False and
                Timer.Check('weaponspecial_mana') == False):
            reset_backstab_cycle(clear_target=False)

    if not Player.WarMode:
        Player.SetWarMode(True)
    Player.Attack(nearest)
    sync_pet_target(nearest)
    return True

def backstab_locked_target(victims):
    if not backstab_loop_enabled() or _backstab_target_serial == 0:
        return None
    for mob in victims:
        if mob.Serial == _backstab_target_serial and not mob.Deleted:
            return mob
    reset_backstab_cycle()
    return None

def continue_hidden_backstab():
    if (not backstab_loop_enabled() or Player.Visible or
            _backstab_target_serial == 0):
        return False

    target = Mobiles.FindBySerial(_backstab_target_serial)
    if (target is None or target.Deleted or
            Player.DistanceTo(target) > sv['attackrange']):
        return False
    return backstab_cycle_attack(target, [])

def arm_ninjitsu_attack(move=None):
    if move is None:
        move = selected_ninjitsu_attack()
    if move is None:
        return False

    move_name, base_mana = move
    if Player.HasSpecial:
        Player.WeaponClearSA()
    if Player.SpellIsEnabled(move_name):
        return True
    if Timer.Check('ninjitsu_move') != False or Player.Paralized:
        return True

    required_mana = ninjitsu_move_mana_cost(base_mana)
    if Player.Mana < required_mana:
        return True

    if sv['use_messages'] == 1:
        Player.HeadMessage(80,move_name)
    Spells.CastNinjitsu(move_name)
    Timer.Create('ninjitsu_move',800)
    Misc.Pause(200)
    return True

def weapon_special_active_or_pending():
    if sv['disable_weaponspecials'] == 1:
        return (Player.SpellIsEnabled("Onslaught") or
                Timer.Check('blockspecials') != False)
    return (Player.HasSpecial or
            Player.SpellIsEnabled("Onslaught") or
            Timer.Check('weaponspecial_arm') != False or
            Timer.Check('blockspecials') != False)

def track_weapon_special_state():
    global _weapon_special_was_armed

    has_special = Player.HasSpecial
    if _weapon_special_was_armed and not has_special:
        Timer.Create('weaponspecial_mana', WEAPON_SPECIAL_REPEAT_WINDOW_MS)
    _weapon_special_was_armed = has_special

def prearm_weaponspecial():
    # Pre-arm the single-target weapon special so the FIRST swing on the next mob
    # lands a special (e.g. Double Strike / Armor Ignore) instead of a bare hit.
    # Safe with no mob around — the queued special persists until you swing.
    # Self-gates so it never fights the in-melee rotation or a readied Onslaught.
    if sv['activeattack'] != 1:
        return
    if selected_ninjitsu_attack() is not None:
        arm_ninjitsu_attack()
        return
    if backstab_loop_enabled():
        if (_backstab_state == BACKSTAB_STATE_SHADOW and
                Timer.Check('backstab_lock') == False and
                Timer.Check('weaponspecial_mana') == False and
                Player.Mana >= backstab_reserved_mana()):
            arm_shadow_strike()
        return
    if sv['disable_weaponspecials'] == 1:
        if Player.HasSpecial:
            Player.WeaponClearSA()
        return
    if Player.HasSpecial:
        return
    if Player.SpellIsEnabled("Onslaught") or Timer.Check('blockspecials') != False:
        return
    # WeaponPrimarySA/SecondarySA are TOGGLES — bound re-arm attempts so a lagged
    # HasSpecial can't make us flip the ability on/off every tick.
    if Timer.Check('weaponspecial_arm') != False:
        return
    if Player.Mana < get_weaponabilitiesmanacost(30):
        return
    w = weapons.get(weapon_set)
    if w is None:
        return
    if w.singleenemyspecial == "primary" and sv['use_weaponspecialprimary'] != 0:
        Player.WeaponPrimarySA()
        Timer.Create('weaponspecial_arm', WEAPON_SPECIAL_ARM_DEBOUNCE_MS)
    elif w.singleenemyspecial == "secondary" and sv['use_weaponspecialsecondary'] != 0:
        Player.WeaponSecondarySA()
        Timer.Create('weaponspecial_arm', WEAPON_SPECIAL_ARM_DEBOUNCE_MS)

def fighting(nearest, victims_6, victims_10, nearby_enemies, attackrange_enemy_count):

    global firsthitmob
    #Misc.SendMessage ('Attack: {}'.format(nearest.Name))

    if sv['disable_weaponspecials'] == 1 and Player.HasSpecial:
        Player.WeaponClearSA()
    
    if Player.BuffsExist('Bload Oath (curse)'):
    
        if Player.WarMode:
            Player.SetWarMode(False)
        if attackrange_enemy_count <= 2 or sv['disable_weaponspecials'] == 1:
            return

        whirlwind_slot = None
        if weapons[ weapon_set ].weaponspecial_primary == "Whirlwind" and sv['use_weaponspecialprimary'] != 0:
            whirlwind_slot = "primary"
        elif weapons[ weapon_set ].weaponspecial_secondary == "Whirlwind" and sv['use_weaponspecialsecondary'] != 0:
            whirlwind_slot = "secondary"

        # Never allow a previously armed non-Whirlwind special to land.
        if whirlwind_slot is None or Player.Mana < get_weaponabilitiesmanacost(15):
            Player.WeaponClearSA()
            return

        Player.WeaponClearSA()
        if whirlwind_slot == "primary":
            if sv['use_messages'] == 1:
                Player.HeadMessage(70,"%s"% weapons[ weapon_set ].weaponspecial_primary)
            Player.WeaponPrimarySA()
        else:
            if sv['use_messages'] == 1:
                Player.HeadMessage(70,"%s"% weapons[ weapon_set ].weaponspecial_secondary)
            Player.WeaponSecondarySA()

        Misc.Pause(200)
        if Player.HasSpecial:
            Player.Attack(nearest)
          
    else:

        ninjitsu_move = selected_ninjitsu_attack()
        ninjitsu_mode = ninjitsu_move is not None

        if not ninjitsu_mode and backstab_cycle_attack(nearest, nearby_enemies):
            return
    
        if not ninjitsu_mode and sv['use_onslaught'] == 1 and Player.DistanceTo(nearest) <= 1:
            if firsthitmob != nearest.Serial or firsthitmob == 0:
                firsthitmob = nearest.Serial
                Timer.Create("hit",2000)

        # Swing FIRST — every landed hit leeches HP (Vampiric Embrace).
        # Attacking before arming specials re-locks the swing on the current mob
        # immediately (esp. after a target switch) and lets specials ride it.
        # Ensure war mode so swings actually happen if it dropped.
        if not Player.WarMode:
            Player.SetWarMode(True)
        Player.Attack(nearest)
        reaffirm_attack = False

        if (not ninjitsu_mode and sv['disable_weaponspecials'] != 1 and
                Timer.Check("feint") == False):
            if equippedweapon and equippedweapon.ItemID == 0x27A9:
                Player.HeadMessage(70,"Activate Feint!")
                Player.WeaponPrimarySA()
                reaffirm_attack = True
                Misc.Pause(500)
                Timer.Create("feint",6000)
                Timer.Create('blockspecials',1500)                
            
                
        if sv['use_eoo'] == 1 and Timer.Check("eoo") == False:
            mob_ids = {mob.MobileID for mob in victims_10}
            #Player.HeadMessage(50, "Enemy types: %i" % len(mob_ids))
            if len(victims_6) == 1 or len(mob_ids) <= 1:
                if not Player.BuffsExist('Enemy Of One') and Timer.Check('spells') == False and Player.Mana >= (20 - (20 * lmc)) and not Player.Paralized:
                    if sv['use_messages'] == 1:
                        Player.HeadMessage(80,"Enemy Of One!")
                    Spells.CastChivalry('Enemy Of One')
                    Timer.Create("eoo",2500)
                    Timer.Create('spells',calc_castspeed_chiv_sw(500) + _cached_castpause)
                elif Player.BuffsExist('Enemy Of One') and Timer.Check('spells') == False and not Player.Paralized:
                    if nearest.Notoriety != 5 and nearest.Hits > 15:
                        if sv['use_messages'] == 1:
                            Player.HeadMessage(80,"Enemy Of One!")
                        Spells.CastChivalry('Enemy Of One')
                        Timer.Create('spells',calc_castspeed_chiv_sw(500) + _cached_castpause)
                        
            elif len(mob_ids) > 1:
                if Player.BuffsExist('Enemy Of One') and Timer.Check('spells') == False and not Player.Paralized:
                    if sv['use_messages'] == 1:
                        Player.HeadMessage(80,"Enemy Of One!")
                    Spells.CastChivalry('Enemy Of One')
                    Timer.Create('spells',calc_castspeed_chiv_sw(500) + _cached_castpause)                
    
        # Onslaught is single-target only and fires in the len==1 branch below.
        # In crowds (2+ melee) Whirlwind owns the swing.

        # HE finisher — arm before weapon-special branches so it lands on next swing.
        # Gated internally on killshot % + cooldown; safe to call every tick.
        if ninjitsu_mode:
            move_name = ninjitsu_move[0]
            move_was_enabled = Player.SpellIsEnabled(move_name)
            arm_ninjitsu_attack(ninjitsu_move)
            if not move_was_enabled and Player.SpellIsEnabled(move_name):
                reaffirm_attack = True
        else:
            he_was_enabled = Player.SpellIsEnabled("Honorable Execution")
            honorable_execution(nearest)
            if (not he_was_enabled and
                    Player.SpellIsEnabled("Honorable Execution")):
                reaffirm_attack = True

        if len(nearby_enemies) == 1:

            single_special_mana = get_weaponabilitiesmanacost(30)

            if not ninjitsu_mode and sv['use_onslaught'] == 1:
                if Timer.Check("hit") == False and firsthitmob == nearest.Serial and not Player.Paralized:
                    onslaught_was_enabled = Player.SpellIsEnabled("Onslaught")
                    onslaught(nearest)
                    if (not onslaught_was_enabled and
                            Player.SpellIsEnabled("Onslaught")):
                        reaffirm_attack = True
            
            # Block weapon specials while Onslaught is readied OR still inside the
            # blockspecials window — arming a special cancels the readied Onslaught.
            # Needs AND: only fire specials when Onslaught is not pending AND the
            # block timer has expired. (An OR here lets a special fire the instant
            # the timer lapses even though Onslaught is still readied -> cancel loop.)
            if Player.SpellIsEnabled( "Onslaught" ) == False and Timer.Check('blockspecials') == False:

                if (not ninjitsu_mode and
                        sv['disable_weaponspecials'] != 1 and
                        not weapon_special_active_or_pending() and
                        Player.Mana >= single_special_mana):
                    # Smart picker resolves slot from target context when enabled.
                    if sv['use_smart_specials'] == 1:
                        _resolved_slot = pick_weapon_special(nearest, weapons[ weapon_set ])
                    else:
                        _resolved_slot = weapons[ weapon_set ].singleenemyspecial

                    if _resolved_slot == "primary" and sv['use_weaponspecialprimary'] != 0:
                        if sv['use_messages'] == 1:
                            Player.HeadMessage(70,"%s"% weapons[ weapon_set ].weaponspecial_primary)
                        Player.WeaponPrimarySA()
                        reaffirm_attack = True
                        Timer.Create('weaponspecial_arm', WEAPON_SPECIAL_ARM_DEBOUNCE_MS)
                    elif _resolved_slot == "secondary" and sv['use_weaponspecialsecondary'] != 0:
                        if sv['use_messages'] == 1:
                            Player.HeadMessage(70,"%s"% weapons[ weapon_set ].weaponspecial_secondary)
                        Player.WeaponSecondarySA()
                        reaffirm_attack = True
                        Timer.Create('weaponspecial_arm', WEAPON_SPECIAL_ARM_DEBOUNCE_MS)

                    else:
                        if sv['use_weaponspecialprimary'] != 0:
                            if sv['use_messages'] == 1:
                                Player.HeadMessage(80,"Primary Attack!")    
                            Player.WeaponPrimarySA()
                            reaffirm_attack = True
                            Timer.Create('weaponspecial_arm', WEAPON_SPECIAL_ARM_DEBOUNCE_MS)

                    Misc.Pause(200)
                                        
                if (not ninjitsu_mode and
                        not weapon_special_active_or_pending() and
                        (sv['disable_weaponspecials'] == 1 or
                         Player.Mana < single_special_mana) and
                        sv['use_lightningstrike'] == 1 and
                        not Player.BuffsExist('Lightning Strike') and
                        Player.Mana >= (10 - (10 * lmc))):
                    if sv['use_messages'] == 1:
                        Player.HeadMessage(80,"Lightning Strike")
                    Spells.CastBushido('Lightning Strike')
                    reaffirm_attack = True
                    Misc.Pause(200)  
                    
        elif len(nearby_enemies) >= 2:
            
            if weapons[ weapon_set ].weaponspecial_primary == "Whirlwind" or weapons[ weapon_set ].weaponspecial_secondary == "Whirlwind":
                requiredmana = 15 
            else:
                requiredmana = 30 
            required_special_mana = get_weaponabilitiesmanacost(requiredmana)
        
            # The short arm timer covers the server round-trip that flips
            # HasSpecial true. The separate three-second mana timer never blocks
            # re-arming, allowing specials on every 1.25-second swing.
            if (not ninjitsu_mode and
                    sv['disable_weaponspecials'] != 1 and
                    not weapon_special_active_or_pending() and
                    Player.Mana >= required_special_mana):

                if weapons[ weapon_set ].multienemyspecial == "primary" and sv['use_weaponspecialprimary'] != 0:
                    if sv['use_messages'] == 1:
                        Player.HeadMessage(70,"%s"% weapons[ weapon_set ].weaponspecial_primary)
                    Player.WeaponPrimarySA()
                    reaffirm_attack = True
                    Timer.Create('weaponspecial_arm', WEAPON_SPECIAL_ARM_DEBOUNCE_MS)
                elif weapons[ weapon_set ].multienemyspecial == "secondary" and sv['use_weaponspecialsecondary'] != 0:
                    if sv['use_messages'] == 1:
                        Player.HeadMessage(70,"%s"% weapons[ weapon_set ].weaponspecial_secondary)
                    Player.WeaponSecondarySA()
                    reaffirm_attack = True
                    Timer.Create('weaponspecial_arm', WEAPON_SPECIAL_ARM_DEBOUNCE_MS)

                else:
                    if sv['use_weaponspecialsecondary'] != 0:
                        if sv['use_messages'] == 1:
                            Player.HeadMessage(80,"Secondary Attack!")
                        Player.WeaponSecondarySA()
                        reaffirm_attack = True
                        Timer.Create('weaponspecial_arm', WEAPON_SPECIAL_ARM_DEBOUNCE_MS)

                Misc.Pause(200)
 
            elif (not ninjitsu_mode and
                    not weapon_special_active_or_pending() and
                    Player.Mana < required_special_mana and
                    sv['use_momentumstrike'] == 1 and
                    not Player.BuffsExist('Momentum Strike') and
                    Player.Mana >= (10 - (10 * lmc))):
                if sv['use_messages'] == 1:
                    Player.HeadMessage(80,"Momentum Strike")
                Spells.CastBushido('Momentum Strike')
                reaffirm_attack = True
                Misc.Pause(200)

        # Ability setup can briefly disturb combat targeting; normal ticks do
        # not need a duplicate attack request.
        if reaffirm_attack:
            Player.Attack(nearest)
        sync_pet_target(nearest)
                
            
# Extra pause (ms) when no mobs are in range — throttles idle CPU between
# spawns. Combat pacing is unaffected. Raise to save more CPU, lower for
# faster re-engage when a new mob appears. Detection lags at most this long.
_IDLE_PAUSE_EXTRA = 250

def run_tick():
    global use_honor_fix, _victims_cache, _changelings_cache

    # Attack Off is a safety control: do not wait for the 2.5s settings refresh.
    sv['activeattack'] = Misc.ReadSharedValue("activeattack")

    track_weapon_special_state()
    track_backstab_execution()
    clear_stuck_target_cursor()
    if sv['activeattack'] == 1 and continue_hidden_backstab():
        Misc.Pause(100)
        return
    binding_bracelet()
    trappedcrate()
    checkbloodoath()
    auto_potion()
    checkhits()
    evasion()
    curseweapon()
    divinefury_lowstam()
    checkweight()
    castsummonfey()
    checkwhitetigerform()
    
    if Timer.Check("sv_refresh") == False:
        refresh_sv()
        dresslist()
        legendarycheck()
        Timer.Create("sv_refresh", 2500)

    drop_heirloom_chests()
    move_artifacts_to_lootbag()
        
    # Cache the mob scan (~200ms) — mobs_list runs a full Mobiles.ApplyFilter,
    # the loop's single most expensive call. Targeting stays responsive.
    if Timer.Check("mobscan") == False:
        _victims_cache = mobs_list(sv['attackrange'])
        if sv['attack_blue_changelings'] == 1:
            _changelings_cache = changelings(changelingrange)
        else:
            _changelings_cache = []
        Timer.Create("mobscan", 200)
    # Drop dead/stale refs — cached list can hold mobs that died within the
    # 200ms window; otherwise DistanceTo/Select on them can crash the script.
    victims = [m for m in _victims_cache if m is not None and not m.Deleted]
    changeling_victims = []
    if _changelings_cache:
        changeling_victims = [m for m in _changelings_cache
                              if m is not None and not m.Deleted]
        if changeling_victims:
            victim_serials = {m.Serial for m in victims}
            victims.extend(m for m in changeling_victims
                           if m.Serial not in victim_serials)

    has_nearby_mobs = len(victims) > 0
    release_one_mirror_image(has_nearby_mobs)
    castmirrorimage(has_nearby_mobs)

    if len(victims) > 0 and sv['activeattack'] == 1:
    
        if Timer.Check("weaponcheck") == False:
            checkweapon()
            Timer.Create("weaponcheck", 1500)
    
        if not Player.BuffsExist('Divine Fury') and sv['use_df'] == 1 and Timer.Check('spells') == False and Player.Mana >= (15 - (15 * lmc)) and not Player.Paralized:
            if sv['use_messages'] == 1:
                Player.HeadMessage(80,"Divine Fury!")
            Spells.CastChivalry('Divine Fury')
            Timer.Create('spells',calc_castspeed_chiv_sw(1000) + _cached_castpause)
            
        if not Player.BuffsExist('Consecrate Weapon') and sv['use_cw'] == 1 and Timer.Check('spells') == False and Player.Mana >= (10 - (10 * lmc)) and not Player.Paralized:
            if sv['use_messages'] == 1:
                Player.HeadMessage(80,"Consecrate Weapon!")
            Spells.CastChivalry('Consecrate Weapon')
            Timer.Create('spells',calc_castspeed_chiv_sw(500) + _cached_castpause)    
            
        attuneweapon()
        immolatingweapon()        
        counterattack()
    
        victims_dist = []
        victims_1 = []
        victims_3 = []
        victims_6 = []
        victims_9 = []
        victims_10 = []
        nearby_enemies = []
        for mob in victims:
            distance = Player.DistanceTo(mob)
            victims_dist.append((mob, distance))
            if distance <= 1:
                victims_1.append(mob)
            if distance <= 3:
                victims_3.append(mob)
            if distance <= 6:
                victims_6.append(mob)
            if distance <= 9:
                victims_9.append(mob)
            if distance <= 10:
                victims_10.append(mob)
            if distance <= sv['nearbyrange']:
                nearby_enemies.append(mob)

        holylight(victims_3)
        
        if len(victims_6) == 0:
            removepoison()        
            removecurse()
            closewounds()
        
        if sv['use_thunderstorm'] == 1:
            if len(victims_9) - len(victims_1) > 3:
                thunderstorm()
                
        # Resolve the final target once, before any target-dependent action.
        nearest_by_dist = min(victims_dist, key=lambda md: md[1])[0]
        changeling_serials = {m.Serial for m in changeling_victims}
        changelings_dist = [(m, d) for m, d in victims_dist
                            if m.Serial in changeling_serials]
        if changelings_dist:
            nearest = min(changelings_dist, key=lambda md: md[1])[0]
        elif sv['use_smart_target'] == 1:
            nearest = pick_target(victims_dist) or nearest_by_dist
        elif len(victims_1) > 1:
            nearest = min(victims_1, key=lambda m: m.Hits)
        else:
            nearest = nearest_by_dist

        locked_backstab_target = backstab_locked_target(victims)
        if locked_backstab_target is not None:
            nearest = locked_backstab_target

        # Select can return None if every candidate just died — skip this tick
        # rather than crash on Player.DistanceTo(None) / nearest.Hits below.
        if nearest is None:
            Misc.Pause(100)
            return

        # Slayer swap BEFORE engaging — the matching slayer must be in hand
        # when the swings land. Gated internally (group change + cooldown).
        slayer_swap_tick(nearest)

        if sv['use_distancemarker'] == 1 and Timer.Check('distancemarker') == False:
            nearest_distance = Player.DistanceTo(nearest)
            if nearest_distance <= sv['nearbyrange']:
                if sv['use_bluemarkermode'] == 1:
                    Mobiles.Message(nearest,90,"▼")
                else:
                    Mobiles.Message(nearest,70,"▼")
            elif nearest_distance <= sv['nearbyrange'] + 3:
                if sv['use_bluemarkermode'] == 1:
                    Mobiles.Message(nearest,100,"▼▼")
                else:
                    Mobiles.Message(nearest,45,"▼")
            elif nearest_distance >= sv['nearbyrange'] + 4:
                if sv['use_bluemarkermode'] == 1:
                    Mobiles.Message(nearest,110,"▼▼▼")
                else:
                    Mobiles.Message(nearest,28,"▼")
            Timer.Create('distancemarker', 300)
            
        if sv['use_honor'] == 1:
            if ((Player.BuffsExist('Honored') == False or use_honor_fix == 1) and
                    Timer.Check('honorattempt') == False):
                #Mobiles.WaitForStats(nearest,300)
                if nearest.Hits == nearest.HitsMax and Player.DistanceTo(nearest) <= sv['honordistance']:
                    #Target.ClearQueue()
                    #Target.Cancel()
                    Player.InvokeVirtue("Honor")
                    Target.WaitForTarget(300, True)
                    Target.TargetExecute(nearest)
                    use_honor_fix = 0
                    Timer.Create('honorattempt', 1000)
                    
                    if Timer.Check('spamhonor') == False and sv['use_messages'] == 1:  
                        Player.HeadMessage(55,"Honor mob: {}".format(nearest.Name))
                        Timer.Create('spamhonor',1500)
                        
        # Approaching (not yet in melee) — pre-arm so the FIRST swing is a special.
        # In melee, fighting() owns the rotation.
        if Player.DistanceTo(nearest) > 1:
            prearm_weaponspecial()

        fighting(nearest, victims_6, victims_10, nearby_enemies, len(victims))
        playingtheodds()
        Misc.Pause(100)
            
    else:
        
        removepoison() 
        closewounds()
        removecurse() 
        
        if Timer.Check("checks") == False:
            check_bandages()
            check_arrows()
            check_vamp()
            check_townbuff()
            check_arcanefocus()
            Timer.Create("checks", 4000)
        
        if sv['use_honor'] == 1:
            if Player.BuffsExist('Honored') == True:
                use_honor_fix = 1

        # Keep weapon_set current while idle so pre-arm toggles the RIGHT slot
        # (checkweapon otherwise only runs in the combat branch).
        if Timer.Check("weaponcheck") == False:
            checkweapon()
            Timer.Create("weaponcheck", 1500)

        # No mob around — pre-arm the single-target special so the first swing on
        # the next mob you engage lands a special instead of a bare hit.
        prearm_weaponspecial()

        # No mobs in range — throttle harder to cut idle CPU between spawns.
        # Combat branch pacing is untouched.
        Misc.Pause(_IDLE_PAUSE_EXTRA)

    Misc.Pause(100)

# Self-recovering driver: a transient API error (mob vanishing between filter
# and access, target cursor race, etc.) no longer hard-kills the script.
# A one-off fluke is shrugged off. But many failures IN A ROW = a real bug,
# not a fluke — so escalate with an alarm instead of silently retrying forever.
_tick_errors = 0          # consecutive failed ticks
_TICK_ERROR_ALARM = 10    # beep/alert after this many in a row
while not Player.IsGhost:
    try:
        run_tick()
        _tick_errors = 0          # a clean tick clears the streak
    except Exception as e:
        _tick_errors += 1
        Player.HeadMessage(30, "tick error (%i): %s" % (_tick_errors, str(e)))
        if _tick_errors == _TICK_ERROR_ALARM:
            # Not a transient hiccup — surface it loudly so it gets noticed/fixed.
            longalarm()
            Player.HeadMessage(38, "SCRIPT STUCK — %i errors in a row!" % _tick_errors)
        Misc.Pause(250)
        
