### UO Ultimate Mage Attack Script by Mike|Walker ##########
### https://github.com/mike-walker-uo/uoscripts/tree/main/UltimateMageAttackScript
### Version 0.48 last edit 03.08.2026 ###
### Try to run at least Razor Enhanced Version 0.8.2.215 ###
### SAVE THE SCRIPT AS .py file and add to Python Script Section in Razor Enhanced ###
### START THE ATTACK SCRIPT FIRST — then start the GUMP script ###

import winsound
import time
import json
import os
from System.Collections.Generic import List
from System import Byte

LEGACY_PROFILE_PATH = os.path.join(Misc.CurrentScriptDirectory(), "mage_settings.json")

def safe_profile_name(name):
    safe = "".join(ch if (ch.isalnum() or ch in "-_") else "_"
                   for ch in str(name or "character"))
    return safe.strip("_") or "character"

PROFILE_FILENAME = "mage_settings_%s_%08X.json" % (
    safe_profile_name(Player.Name), int(Player.Serial))
PROFILE_PATH = os.path.join(Misc.CurrentScriptDirectory(), PROFILE_FILENAME)

Journal.Clear()

##################################################################
###  MAKE ALL YOUR SETTINGS HERE #################################
##################################################################

# attack blue mobs (notoriety 1) — use with care!
Misc.SetSharedValue("attack_blues", 0)
# attack red humans (to avoid attacking red players)
Misc.SetSharedValue("attack_red_humans", 0)
# check and attack blue changelings that imitate you
Misc.SetSharedValue("attack_blue_changelings", 0)
# show overhead messages
Misc.SetSharedValue("use_messages", 1)
# show infos about mobs (HP, weakest resist, karma)
Misc.SetSharedValue("use_mobinfo", 0)
# Bag of Sending: sends gold to bank when almost overweight
Misc.SetSharedValue("use_bagofsending", 1)
# Trapped Crate to escape paralyze
Misc.SetSharedValue("use_trappedcrate", 1)
# Check for Town Buff (City Trade Deal)
Misc.SetSharedValue("use_townbuff", 1)
# Check journal for legendary / astral spawns
Misc.SetSharedValue("use_checkforlegendaries", 1)
# Show overhead message when a Rare mob is near
Misc.SetSharedValue("use_checkforraremobs", 1)
# Stop and go to peace mode when a Rare mob is near
Misc.SetSharedValue("use_stopwarwhenrare", 0)
# Distance markers above target mob
Misc.SetSharedValue("use_distancemarker", 1)
# Use blue arrows instead of colored ones
Misc.SetSharedValue("use_bluemarkermode", 0)
# Arcane Focus check (even 0 SW gives +6 STR for 2h)
Misc.SetSharedValue("use_arcanefocus", 1)
# Dress list: keep armor on
Misc.SetSharedValue("use_dresslist", 0)
# Uses the active list selected in Razor Enhanced's Dress agent.

##################################################################
# Ranges
Misc.SetSharedValue("attackrange", 12)        # mage fights at range
Misc.SetSharedValue("multi_threshold", 2)     # mobs nearby to switch to multi-target spells
Misc.SetSharedValue("mass_threshold", 4)      # mobs nearby to switch to mass AoE spells
Misc.SetSharedValue("honordistance", 10)

##################################################################
# Heal, Cure & Buff — set to 1 to enable
Misc.SetSharedValue("use_heal", 1)            # auto Greater Heal / Heal
Misc.SetSharedValue("heal_threshold", 90)     # cast heal when HP% below this value
Misc.SetSharedValue("use_cure", 1)            # auto Cure when poisoned
Misc.SetSharedValue("use_magicreflect", 1)    # keep Magic Reflect active
Misc.SetSharedValue("use_reactivearmor", 1)   # keep Reactive Armor active
Misc.SetSharedValue("use_protection", 0)      # WARNING: -2 FC penalty while active
Misc.SetSharedValue("use_attuneweapon", 0)    # SW Attune Weapon (absorb phys dmg)
Misc.SetSharedValue("use_giftoflife", 0)      # SW Gift of Life (auto-resurrect)
Misc.SetSharedValue("use_cleansingwinds", 1)  # Mysticism C6: cures poison AND removes debuffs
Misc.SetSharedValue("use_arcaneempowerment", 1)  # SW: boosts spell damage/healing (3s, 50 mana)
Misc.SetSharedValue("use_giftofrenewal", 0)      # SW: Gift of Renewal (heal over time buff, 180s cooldown)
Misc.SetSharedValue("use_reaperform", 0)         # SW: Reaper Form (transform, boosts SW dmg)
Misc.SetSharedValue("use_wraithform", 0)         # Necro: Wraith Form (mana drain on hit)
Misc.SetSharedValue("use_lichform", 0)           # Necro: Lich Form (mana regen from INT, poison immune)
Misc.SetSharedValue("use_vampiricembrace", 0)    # Necro: Vampiric Embrace (life drain on hit, req. 99)
Misc.SetSharedValue("use_stoneform", 0)          # Mysticism: Stone Form (increased phys resistance)

##################################################################
# Mob Debuffs — set to 1 to enable
Misc.SetSharedValue("use_evil_omen", 0)       # Necro: next harmful spell does more damage
Misc.SetSharedValue("use_curse", 0)           # Magery: reduce all stats
Misc.SetSharedValue("use_corpse_skin", 0)     # Necro: lower fire/poison resistance
Misc.SetSharedValue("use_strangle", 0)        # Necro: damage over time
Misc.SetSharedValue("use_mind_rot", 0)        # Necro: increase mana costs (great vs mages)
Misc.SetSharedValue("use_poison", 0)          # Magery: poison the mob
Misc.SetSharedValue("use_sleep", 0)           # Mysticism C2: Sleep single target
Misc.SetSharedValue("use_mass_sleep", 0)      # Mysticism C5: Mass Sleep AoE (req. 50 Mysticism)
Misc.SetSharedValue("use_paralyze", 0)        # Magery C6: Paralyze single target (req. 50 Magery)
Misc.SetSharedValue("use_mana_vampire", 0)    # Magery C7: Mana Vampire (drain mana, req. 60 Magery)

##################################################################
# Single Target Spells — set to 1 to enable (casts strongest available)
Misc.SetSharedValue("use_flamestrike", 0)     # Magery C7 — 40 mana
Misc.SetSharedValue("use_energybolt", 1)      # Magery C6 — 20 mana
Misc.SetSharedValue("use_mindblast", 0)       # Magery C5 — 14 mana
Misc.SetSharedValue("use_lightning", 0)       # Magery C4 — 11 mana
Misc.SetSharedValue("use_fireball", 0)        # Magery C3 — 9 mana
Misc.SetSharedValue("use_harm", 0)            # Magery C2 — 6 mana (close range only!)
Misc.SetSharedValue("use_magicarrow", 0)      # Magery C1 — 4 mana (last resort)
Misc.SetSharedValue("use_wordofdeath", 1)     # SW: instantly kills mob below 10% HP
Misc.SetSharedValue("use_nether_bolt", 0)     # Mysticism C1 — 4 mana
Misc.SetSharedValue("use_eaglestrike", 0)     # Mysticism C3 — 9 mana
Misc.SetSharedValue("use_bombard", 0)         # Mysticism C6 — 20 mana, paralyzes target
# Spell Combo (v0.5) — Explosion has a ~3s travel delay, so the follow-up
# lands at roughly the same time → burst that the target can't react to.
Misc.SetSharedValue("use_explosion_combo", 0) # 1 = enable Explosion + follow-up burst
Misc.SetSharedValue("combo_followup", "energybolt") # energybolt | flamestrike | mindblast | lightning

##################################################################
# Multi Target Spells (2+ mobs nearby) — set to 1 to enable
Misc.SetSharedValue("use_chainlightning", 0)  # Magery C7 — 40 mana
Misc.SetSharedValue("use_meteorswarm", 0)     # Magery C7 — 40 mana
Misc.SetSharedValue("use_thunderstorm", 0)    # SW — 32 mana, self-centered
Misc.SetSharedValue("use_wither", 0)          # Necro — 23 mana, self-centered AoE
Misc.SetSharedValue("use_essenceofwind", 0)   # SW — 40 mana
Misc.SetSharedValue("use_hailstorm", 0)       # Mysticism C7 — 50 mana
Misc.SetSharedValue("use_nethercyclone", 1)   # Mysticism C8 — 50 mana

##################################################################
# Mass Target Spells (4+ mobs nearby) — set to 1 to enable
Misc.SetSharedValue("use_earthquake", 0)      # Magery C8 — 50 mana, self-centered
Misc.SetSharedValue("use_wildfire", 0)        # SW — 50 mana, targeted location
Misc.SetSharedValue("use_spellplague", 0)     # Mysticism C7 — 40 mana

##################################################################
# Summons — set to 1 to enable
Misc.SetSharedValue("use_summonfey", 0)       # SW Summon Fey
Misc.SetSharedValue("use_summonfiend", 0)     # SW Summon Fiend
Misc.SetSharedValue("use_risingcolossus", 1)  # Mysticism Rising Colossus (needs 80+ Myst)
Misc.SetSharedValue("use_summonelemental", 0) # Magery Summon Elemental
Misc.SetSharedValue("elemental_type", 0)      # 0=Air 1=Earth 2=Fire 3=Water
Misc.SetSharedValue("fey_threshold", 3)       # re-summon when followers below this
Misc.SetSharedValue("elemental_threshold", 4) # re-summon elemental when followers below this
Misc.SetSharedValue("use_summon_creature", 1) # Magery C5: Summon Creature
Misc.SetSharedValue("creature_threshold", 4)  # re-summon creature when followers below this
Misc.SetSharedValue("use_summon_daemon", 0)      # Magery C8: Summon Daemon
Misc.SetSharedValue("daemon_threshold", 4)       # re-summon daemon when followers below this
Misc.SetSharedValue("use_blade_spirit", 0)       # Magery C6: Blade Spirits
Misc.SetSharedValue("blade_spirit_threshold", 2) # re-summon blade spirit when followers below this
Misc.SetSharedValue("use_energy_vortex", 0)      # Magery C7: Energy Vortex
Misc.SetSharedValue("energy_vortex_threshold", 2) # re-summon energy vortex when followers below this

##################################################################
# Skill Masteries — requires 90 REAL skill (not modified by items)
Misc.SetSharedValue("use_death_ray", 0)        # Magery mastery: targeted beam (2.25s)
Misc.SetSharedValue("use_ethereal_blast", 0)   # Magery mastery: self-centered AoE (2.25s)
Misc.SetSharedValue("use_mana_shield", 0)      # Spellweaving mastery: damage→mana loss buff
Misc.SetSharedValue("use_summon_reaper", 0)    # Spellweaving mastery: summon reaper
Misc.SetSharedValue("reaper_threshold", 4)     # re-summon reaper when followers below this
Misc.SetSharedValue("use_command_undead", 0)   # Necromancy mastery: control undead (3s)
Misc.SetSharedValue("use_conduit", 0)          # Necromancy mastery: necromantic channel (2.25s)
Misc.SetSharedValue("use_nether_blast", 1)     # Mysticism mastery: targeted blast (2s)
Misc.SetSharedValue("use_mystic_weapon", 0)    # Mysticism mastery: weapon energy buff

##################################################################
# Bard — set to 1 to enable (requires an instrument in backpack)
Misc.SetSharedValue("use_check_instrument", 1)   # warn if no instrument in backpack
Misc.SetSharedValue("use_discordance", 0)         # discord nearest mob (Discordance skill)
Misc.SetSharedValue("use_peace", 0)               # peace nearest mob (Peacemaking skill)
Misc.SetSharedValue("use_area_peace", 0)          # area peace centered on self
Misc.SetSharedValue("use_provocation", 0)         # provoke two closest mobs against each other
Misc.SetSharedValue("use_tribulation", 0)         # Bard Mastery: Tribulation on nearest mob
Misc.SetSharedValue("use_despair", 0)             # Bard Mastery: Despair on nearest mob
Misc.SetSharedValue("use_resilience", 0)          # Bard Mastery buff: Resilience
Misc.SetSharedValue("use_perseverance", 0)        # Bard Mastery buff: Perseverance
Misc.SetSharedValue("use_inspire", 0)             # Bard Mastery buff: Inspire
Misc.SetSharedValue("use_invigorate", 0)          # Bard Mastery buff: Invigorate

##################################################################
# Tamer — set to 1 to enable
Misc.SetSharedValue("use_bandage_agent", 0)       # start/stop RE Bandage Agent
Misc.SetSharedValue("use_auto_heal_pet", 0)       # auto heal pets below HP threshold
Misc.SetSharedValue("use_auto_cure_pet", 0)       # auto cure poisoned pets
Misc.SetSharedValue("pet_hp_threshold", 90)       # pet HP% threshold to trigger heal
Misc.SetSharedValue("pet_heal_option", 1)         # 1=Bandages 2=Magery 3=Mysticism 4=Bandages+Magery
Misc.SetSharedValue("use_pet_giftoflife", 0)      # Gift of Life on all pets (refreshed every 90s)
Misc.SetSharedValue("use_pet_giftofrenewal", 0)   # Gift of Renewal on closest pet (180s cooldown)

##################################################################
# Advanced tuning (v0.6) — re-ranking & UX
Misc.SetSharedValue("use_resist_aware", 1)        # bias spell cascade by mob.weakres (MOBSLIST)
Misc.SetSharedValue("use_nuke_cascade", 1)        # after Evil Omen / Corpse Skin lands, bias next cast to strongest enabled nuke
Misc.SetSharedValue("combo_cooldown_ms", 1500)    # cooldown between Explosion-combo repeats (ms)
Misc.SetSharedValue("urgent_buff_threshold", 60)  # HP% below which protective keep_* buffs get priority
Misc.SetSharedValue("use_status_overlay", 0)      # periodic head-message: HP/MP/Followers/Buffs/TgtHP
Misc.SetSharedValue("status_overlay_ms", 8000)    # throttle for status overlay (ms)
Misc.SetSharedValue("use_summon_counter", 1)      # head-message follower count after each summon
Misc.SetSharedValue("use_skip_debuffs_on_trash", 1)  # don't waste casts on low-HP mobs
Misc.SetSharedValue("use_mana_aware", 1)             # skip Flame Strike on trash when mana < 70%
Misc.SetSharedValue("use_slayer_announce", 1)        # head-message when slayer matches a mob
Misc.SetSharedValue("trash_hp_cap", 250)             # real HP threshold: < => trash
Misc.SetSharedValue("boss_hp_min", 3000)             # real HP threshold: >= => boss
Misc.SetSharedValue("use_low_mana_mode", 1)          # below threshold: skip debuffs + expensive nukes
Misc.SetSharedValue("low_mana_threshold", 25)        # mana % that triggers low-mana mode
Misc.SetSharedValue("use_nb_show_tiles", 0)          # ground-mark valid Nether Blast casting tiles
Misc.SetSharedValue("use_nb_auto_move", 0)           # auto-walk to nearest valid NB tile when misaligned
Misc.SetSharedValue("nb_move_hp_min", 50)            # min HP % to allow NB auto-move
Misc.SetSharedValue("use_slayer_autoswap", 0)        # auto-equip slayer spellbook matching target
Misc.SetSharedValue("slayer_swap_request", 0)        # manual swap request (serial) from Mage GUMP
Misc.SetSharedValue("use_bless", 0)                  # Magery: keep Bless on yourself (+10 all stats)
Misc.SetSharedValue("use_bless_pets", 0)             # Magery: keep Bless on all pets
Misc.SetSharedValue("use_poison_strike", 0)          # Necro multi-target: Poison Strike (req. 65)

##################################################################
# Ignore lists
summonsToIgnore = ["a reaper", "a rising colossus", "a nature's fury", "a blade spirit", "an energy vortex"]
mobsToIgnore = ["addnameshere"]
serialsToIgnore = []
mobileIDsToIgnore = [0x00C9]  # cat

##################################################################
### DON'T TOUCH ANYTHING BELOW! ##################################
##################################################################

use_honor_fix = 0
guardme_pending = False
_colossus_tile_idx = 0  # cycles through candidate tiles when placement is blocked
_RC_OFFSETS = [(1,0),(0,1),(-1,0),(0,-1),(1,1),(-1,1),(1,-1),(-1,-1),(2,0),(0,2),(-2,0),(0,-2)]
_COLOSSUS_SLOTS = 3  # UOAlive shard rule
Misc.SetSharedValue("activeattack", 1)
Misc.SetSharedValue("use_honor", 0)
Misc.SetSharedValue("use_bandages", 0)
guardme_fey   = 0
guardme_fiend = 0
last_debuff_target = 0
last_attack_target = 0
last_distance_marker = None
last_player_hits = Player.Hits
last_cast_failure_check = time.time()
last_cast_failure_signatures = set()
last_target_wait_failure = 0.0
last_target_wait_failure_kind = None
last_offensive_target_state = None
los_rejected_positions = {}
pending_pet_gor_serial = 0
pending_pet_gor_started = 0.0
target_wait_extended_until = 0.0
cast_lock_since = None
nether_pending_since = None
pending_cast_cooldown = None
busy_failure_count = 0
busy_failure_since = None
last_cast_recovery = 0.0
serverdelay = 150  # adjust for lag (ms)

# Always start from clean script-owned cast state.
Timer.Create("spells", 1)
Timer.Create("netherblast_pending", 1)
Timer.Create("arcaneempowerment", 1)
Timer.Create("colossus_confirmation", 1)
Timer.Create("pet_giftofrenewal", 1)
Misc.SetSharedValue("mw_pet_gor_next_attempt", 0.0)

# Last-started attack-script copy owns combat. Older updated copies see the new
# token at the top of their loop and exit instead of racing spell cursors.
_attack_instance_token = "%s-%.6f" % (Player.Serial, time.time())
Misc.SetSharedValue("mw_attack_instance_token", _attack_instance_token)

lmc = (min(40, Player.LowerManaCost)) / 100
lrc = Player.SumAttribute("Lower Reagent Cost")
_cached_fcr        = min(6, Player.FasterCastRecovery)
_cached_fc         = Player.FasterCasting
_cached_castpause  = max(((6 - _cached_fcr) * 250) + serverdelay, serverdelay)

# Razor skill lookups cross the Python/.NET boundary. Cache them only for the
# current 100ms loop; the cache is cleared at the top of every main-loop tick.
_razor_get_skill_value = Player.GetSkillValue
_razor_get_real_skill_value = Player.GetRealSkillValue
_loop_skill_cache = {}

def skill_value(name):
    key = (False, name)
    if key not in _loop_skill_cache:
        _loop_skill_cache[key] = _razor_get_skill_value(name)
    return _loop_skill_cache[key]

def real_skill_value(name):
    key = (True, name)
    if key not in _loop_skill_cache:
        _loop_skill_cache[key] = _razor_get_real_skill_value(name)
    return _loop_skill_cache[key]

def mana_cost(base):
    """Apply LMC reduction. Returns minimum mana needed to cast."""
    return int(base * (1 - lmc))

##################################################################
# Shared value cache — GUMP revision driven, with a 5s external-change fallback
sv = {}

def refresh_sv():
    sv['activeattack']            = Misc.ReadSharedValue("activeattack")
    sv['attackrange']             = Misc.ReadSharedValue("attackrange")
    sv['multi_threshold']         = Misc.ReadSharedValue("multi_threshold")
    sv['mass_threshold']          = Misc.ReadSharedValue("mass_threshold")
    sv['honordistance']           = Misc.ReadSharedValue("honordistance")
    sv['use_messages']            = Misc.ReadSharedValue("use_messages")
    sv['use_mobinfo']             = Misc.ReadSharedValue("use_mobinfo")
    sv['use_bagofsending']        = Misc.ReadSharedValue("use_bagofsending")
    sv['use_trappedcrate']        = Misc.ReadSharedValue("use_trappedcrate")
    sv['use_townbuff']            = Misc.ReadSharedValue("use_townbuff")
    sv['use_checkforlegendaries'] = Misc.ReadSharedValue("use_checkforlegendaries")
    sv['use_checkforraremobs']    = Misc.ReadSharedValue("use_checkforraremobs")
    sv['use_stopwarwhenrare']     = Misc.ReadSharedValue("use_stopwarwhenrare")
    sv['use_distancemarker']      = Misc.ReadSharedValue("use_distancemarker")
    sv['use_bluemarkermode']      = Misc.ReadSharedValue("use_bluemarkermode")
    sv['use_dresslist']           = Misc.ReadSharedValue("use_dresslist")
    sv['attack_blues']            = Misc.ReadSharedValue("attack_blues")
    sv['attack_red_humans']       = Misc.ReadSharedValue("attack_red_humans")
    sv['attack_blue_changelings'] = Misc.ReadSharedValue("attack_blue_changelings")
    sv['use_arcanefocus']         = Misc.ReadSharedValue("use_arcanefocus")
    sv['use_bandages']            = Misc.ReadSharedValue("use_bandages")
    sv['use_heal']                = Misc.ReadSharedValue("use_heal")
    sv['heal_threshold']          = Misc.ReadSharedValue("heal_threshold")
    sv['use_cure']                = Misc.ReadSharedValue("use_cure")
    sv['use_cleansingwinds']      = Misc.ReadSharedValue("use_cleansingwinds")
    sv['use_magicreflect']        = Misc.ReadSharedValue("use_magicreflect")
    sv['use_reactivearmor']       = Misc.ReadSharedValue("use_reactivearmor")
    sv['use_protection']          = Misc.ReadSharedValue("use_protection")
    sv['use_attuneweapon']        = Misc.ReadSharedValue("use_attuneweapon")
    sv['use_giftoflife']          = Misc.ReadSharedValue("use_giftoflife")
    sv['use_evil_omen']           = Misc.ReadSharedValue("use_evil_omen")
    sv['use_curse']               = Misc.ReadSharedValue("use_curse")
    sv['use_corpse_skin']         = Misc.ReadSharedValue("use_corpse_skin")
    sv['use_strangle']            = Misc.ReadSharedValue("use_strangle")
    sv['use_mind_rot']            = Misc.ReadSharedValue("use_mind_rot")
    sv['use_poison']              = Misc.ReadSharedValue("use_poison")
    sv['use_flamestrike']         = Misc.ReadSharedValue("use_flamestrike")
    sv['use_energybolt']          = Misc.ReadSharedValue("use_energybolt")
    sv['use_mindblast']           = Misc.ReadSharedValue("use_mindblast")
    sv['use_lightning']           = Misc.ReadSharedValue("use_lightning")
    sv['use_fireball']            = Misc.ReadSharedValue("use_fireball")
    sv['use_harm']                = Misc.ReadSharedValue("use_harm")
    sv['use_magicarrow']          = Misc.ReadSharedValue("use_magicarrow")
    sv['use_wordofdeath']         = Misc.ReadSharedValue("use_wordofdeath")
    sv['use_nether_bolt']         = Misc.ReadSharedValue("use_nether_bolt")
    sv['use_eaglestrike']         = Misc.ReadSharedValue("use_eaglestrike")
    sv['use_chainlightning']      = Misc.ReadSharedValue("use_chainlightning")
    sv['use_meteorswarm']         = Misc.ReadSharedValue("use_meteorswarm")
    sv['use_thunderstorm']        = Misc.ReadSharedValue("use_thunderstorm")
    sv['use_wither']              = Misc.ReadSharedValue("use_wither")
    sv['use_essenceofwind']       = Misc.ReadSharedValue("use_essenceofwind")
    sv['use_hailstorm']           = Misc.ReadSharedValue("use_hailstorm")
    sv['use_nethercyclone']       = Misc.ReadSharedValue("use_nethercyclone")
    sv['use_earthquake']          = Misc.ReadSharedValue("use_earthquake")
    sv['use_wildfire']            = Misc.ReadSharedValue("use_wildfire")
    sv['use_spellplague']         = Misc.ReadSharedValue("use_spellplague")
    sv['use_summonfey']           = Misc.ReadSharedValue("use_summonfey")
    sv['use_summonfiend']         = Misc.ReadSharedValue("use_summonfiend")
    sv['use_risingcolossus']      = Misc.ReadSharedValue("use_risingcolossus")
    sv['use_summonelemental']     = Misc.ReadSharedValue("use_summonelemental")
    sv['elemental_type']          = Misc.ReadSharedValue("elemental_type")
    sv['fey_threshold']           = Misc.ReadSharedValue("fey_threshold")
    sv['elemental_threshold']     = Misc.ReadSharedValue("elemental_threshold")
    sv['use_summon_creature']     = Misc.ReadSharedValue("use_summon_creature")
    sv['creature_threshold']      = Misc.ReadSharedValue("creature_threshold")
    sv['use_honor']               = Misc.ReadSharedValue("use_honor")
    sv['use_death_ray']           = Misc.ReadSharedValue("use_death_ray")
    sv['use_ethereal_blast']      = Misc.ReadSharedValue("use_ethereal_blast")
    sv['use_mana_shield']         = Misc.ReadSharedValue("use_mana_shield")
    sv['use_summon_reaper']       = Misc.ReadSharedValue("use_summon_reaper")
    sv['reaper_threshold']        = Misc.ReadSharedValue("reaper_threshold")
    sv['use_command_undead']      = Misc.ReadSharedValue("use_command_undead")
    sv['use_conduit']             = Misc.ReadSharedValue("use_conduit")
    sv['use_nether_blast']        = Misc.ReadSharedValue("use_nether_blast")
    sv['use_mystic_weapon']       = Misc.ReadSharedValue("use_mystic_weapon")
    sv['use_bombard']             = Misc.ReadSharedValue("use_bombard")
    sv['use_arcaneempowerment']   = Misc.ReadSharedValue("use_arcaneempowerment")
    sv['use_giftofrenewal']       = Misc.ReadSharedValue("use_giftofrenewal")
    sv['use_reaperform']          = Misc.ReadSharedValue("use_reaperform")
    sv['use_wraithform']          = Misc.ReadSharedValue("use_wraithform")
    sv['use_lichform']            = Misc.ReadSharedValue("use_lichform")
    sv['use_vampiricembrace']     = Misc.ReadSharedValue("use_vampiricembrace")
    sv['use_stoneform']           = Misc.ReadSharedValue("use_stoneform")
    sv['use_sleep']               = Misc.ReadSharedValue("use_sleep")
    sv['use_mass_sleep']          = Misc.ReadSharedValue("use_mass_sleep")
    sv['use_paralyze']            = Misc.ReadSharedValue("use_paralyze")
    sv['use_mana_vampire']        = Misc.ReadSharedValue("use_mana_vampire")
    sv['use_summon_daemon']       = Misc.ReadSharedValue("use_summon_daemon")
    sv['daemon_threshold']        = Misc.ReadSharedValue("daemon_threshold")
    sv['use_blade_spirit']        = Misc.ReadSharedValue("use_blade_spirit")
    sv['blade_spirit_threshold']  = Misc.ReadSharedValue("blade_spirit_threshold")
    sv['use_energy_vortex']       = Misc.ReadSharedValue("use_energy_vortex")
    sv['energy_vortex_threshold'] = Misc.ReadSharedValue("energy_vortex_threshold")
    sv['use_check_instrument']   = Misc.ReadSharedValue("use_check_instrument")
    sv['use_discordance']        = Misc.ReadSharedValue("use_discordance")
    sv['use_peace']              = Misc.ReadSharedValue("use_peace")
    sv['use_area_peace']         = Misc.ReadSharedValue("use_area_peace")
    sv['use_provocation']        = Misc.ReadSharedValue("use_provocation")
    sv['use_tribulation']        = Misc.ReadSharedValue("use_tribulation")
    sv['use_despair']            = Misc.ReadSharedValue("use_despair")
    sv['use_resilience']         = Misc.ReadSharedValue("use_resilience")
    sv['use_perseverance']       = Misc.ReadSharedValue("use_perseverance")
    sv['use_inspire']            = Misc.ReadSharedValue("use_inspire")
    sv['use_invigorate']         = Misc.ReadSharedValue("use_invigorate")
    sv['use_bandage_agent']      = Misc.ReadSharedValue("use_bandage_agent")
    sv['use_auto_heal_pet']      = Misc.ReadSharedValue("use_auto_heal_pet")
    sv['use_auto_cure_pet']      = Misc.ReadSharedValue("use_auto_cure_pet")
    sv['pet_hp_threshold']       = Misc.ReadSharedValue("pet_hp_threshold")
    sv['pet_heal_option']        = Misc.ReadSharedValue("pet_heal_option")
    sv['use_pet_giftoflife']     = Misc.ReadSharedValue("use_pet_giftoflife")
    sv['use_pet_giftofrenewal']  = Misc.ReadSharedValue("use_pet_giftofrenewal")
    sv['use_resist_aware']       = Misc.ReadSharedValue("use_resist_aware")
    sv['use_nuke_cascade']       = Misc.ReadSharedValue("use_nuke_cascade")
    sv['combo_cooldown_ms']      = Misc.ReadSharedValue("combo_cooldown_ms")
    sv['urgent_buff_threshold']  = Misc.ReadSharedValue("urgent_buff_threshold")
    sv['use_status_overlay']     = Misc.ReadSharedValue("use_status_overlay")
    sv['status_overlay_ms']      = Misc.ReadSharedValue("status_overlay_ms")
    sv['use_summon_counter']     = Misc.ReadSharedValue("use_summon_counter")
    sv['use_skip_debuffs_on_trash'] = Misc.ReadSharedValue("use_skip_debuffs_on_trash")
    sv['use_mana_aware']         = Misc.ReadSharedValue("use_mana_aware")
    sv['use_slayer_announce']    = Misc.ReadSharedValue("use_slayer_announce")
    sv['trash_hp_cap']           = Misc.ReadSharedValue("trash_hp_cap")
    sv['boss_hp_min']            = Misc.ReadSharedValue("boss_hp_min")
    sv['use_low_mana_mode']      = Misc.ReadSharedValue("use_low_mana_mode")
    sv['low_mana_threshold']     = Misc.ReadSharedValue("low_mana_threshold")
    sv['use_nb_show_tiles']      = Misc.ReadSharedValue("use_nb_show_tiles")
    sv['use_nb_auto_move']       = Misc.ReadSharedValue("use_nb_auto_move")
    sv['nb_move_hp_min']         = Misc.ReadSharedValue("nb_move_hp_min")
    sv['use_slayer_autoswap']    = Misc.ReadSharedValue("use_slayer_autoswap")
    sv['use_bless']              = Misc.ReadSharedValue("use_bless")
    sv['use_bless_pets']         = Misc.ReadSharedValue("use_bless_pets")
    sv['use_poison_strike']      = Misc.ReadSharedValue("use_poison_strike")
    sv['use_explosion_combo']    = Misc.ReadSharedValue("use_explosion_combo")
    sv['combo_followup']         = Misc.ReadSharedValue("combo_followup")

refresh_sv()
try:
    _settings_revision = int(Misc.ReadSharedValue("mw_settings_revision"))
except Exception:
    _settings_revision = 0
Timer.Create("sv_refresh_fallback", 5000)

##################################################################
# Mob class and MOBSLIST
# Copy the full MOBSLIST from AttackScript_MikeWalker.py for complete mob data.
# The script works without it — you just won't see mob info overhead messages
# and blue-karma mob filtering won't apply.
##################################################################

class Mob:
    name = None; body = None; hp = None; ai = None
    fm = None; fame = None; karma = None
    weakres = None; wrestling = None; slayers = None

    def __init__(self, name, body, hp, ai, fm, fame, karma, weakres, wrestling, slayers):
        self.name = name; self.body = body; self.hp = hp
        self.ai = ai; self.fm = fm; self.fame = fame; self.karma = karma
        self.weakres = weakres; self.wrestling = wrestling; self.slayers = slayers

MOBSLIST = {

    # ════════════════════════════════════════════════════════
    #  BOSSES
    # ════════════════════════════════════════════════════════
    'DespiseBoss': Mob('Adrian', 0x0190, 60000, 'AI_Mage', 'Closest', 22000, 22000, 'Physical', 120.0, []),
    'MedusaClone': Mob('Medusa', 0x02D8, 60000, 'AI_Mage', 'Closest', 22000, -22000, 'Physical', 128.9, []),
    'ServantOfSemidar': Mob('a servant of Semidar', 0x0026, 0, 'AI_Melee', 'None', 0, -1, 'Physical', 0.0, []),
    'Silvani': Mob('Silvani', 0x00B0, 600, 'AI_Mage', 'Evil', 20000, 20000, 'Fire', 100.0, ['Fey']),
    'SoulboundPirateRaider': Mob('a soulbound pirate raider', 0x0190, 250, 'AI_Melee', 'Closest', 2000, -2000, 'Physical', 0.0, []),
    'SoulboundSwashbuckler': Mob('a soulbound swashbuckler', 0x0190, 125, 'AI_Melee', 'Closest', 2000, -2000, 'Physical', 0.0, []),

    # ════════════════════════════════════════════════════════
    #  EVENT
    # ════════════════════════════════════════════════════════
    'TheButcher': Mob('a daemon', 0x0132, 1000, 'AI_Necro', 'Closest', 24000, -24000, 'Fire', 80.0, []),

    # ════════════════════════════════════════════════════════
    #  NPCS
    # ════════════════════════════════════════════════════════
    'MysteriousWisp': Mob('a mysterious wisp', 0x003A, 135, 'AI_Mage', 'None', 0, -1, 'Poison', 80.0, []),
    'Vollem': Mob('a vollem', 0x0125, 315, 'AI_Mage', 'Closest', 0, 0, 'Energy', 87.7, []),

    # ════════════════════════════════════════════════════════
    #  NAMED
    # ════════════════════════════════════════════════════════
    'Abscess': Mob('Abscess', 0x0109, 7540, 'AI_Melee', 'Closest', 0, -1, 'Cold', 143.8, []),
    'Drelgor': Mob('Drelgor the Impaler', 0x0093, 136, 'AI_Melee', 'Closest', 3600, -3600, 'Fire', 60.0, []),
    'Flurry': Mob('Flurry', 0x000D, 477, 'AI_Mage', 'Closest', 4500, -4500, 'Poison', 106.4, []),
    'GrimmochDrummel': Mob('Grimmoch Drummel', 0x0190, 207, 'AI_Archer', 'Closest', 5000, -1000, 'Energy', 0.0, []),
    'LysanderGathenwale': Mob('Lysander Gathenwale', 0x0190, 207, 'AI_Mage', 'Closest', 5000, -10000, 'Fire', 90.0, []),
    'Mistral': Mob('Mistral', 0x000D, 609, 'AI_Mage', 'Closest', 4500, -4500, 'Poison', 104.0, []),
    'MorgBergen': Mob('Morg Bergen', 0x0190, 207, 'AI_Melee', 'Closest', 5000, -1000, 'Fire', 0.0, []),
    'NightTerror': Mob('Night Terror', 0x030C, 50000, 'AI_NecroMage', 'Closest', 8000, -8000, 'Physical', 110.0, []),
    'ShadowKnight': Mob('a shadow knight', 0x0137, 5000, 'AI_NecroMage', 'Closest', 25000, -25000, 'Energy', 100.0, []),
    'TavaraSewel': Mob('Tavara Sewel', 0x0191, 207, 'AI_Melee', 'Closest', 5000, -1000, 'Physical', 0.0, []),
    'Tempest': Mob('Tempest', 0x000D, 602, 'AI_Mage', 'Closest', 4500, -4500, 'Cold', 116.0, []),
    'Thrasher': Mob('Thrasher', 0x00CE, 984, 'AI_Melee', 'Closest', 22400, -22400, 'Cold', 118.3, []),
    'TyballsShadow': Mob("Tyball's Shadow", 0x0190, 3000, 'AI_Mage', 'Closest', 20000, -20000, 'Physical', 100.0, []), #'
    'Virulent': Mob('Virulent', 0x000B, 740, 'AI_Mage', 'Closest', 21000, -21000, 'Fire', 111.7, []),

    # ════════════════════════════════════════════════════════
    #  NORMAL
    # ════════════════════════════════════════════════════════
    'AbysmalHorror': Mob('an abyssmal horror', 0x0138, 6000, 'AI_Mage', 'Closest', 26000, -26000, 'Physical', 88.0, []),
    'AbyssalAbomination': Mob('an Abyssal Abomination', 0x0138, 750, 'AI_NecroMage', 'Closest', 26000, -26000, 'Physical', 88.0, []),
    'AcidElemental': Mob('an acid elemental', 0x009E, 213, 'AI_Mage', 'Closest', 10000, -10000, 'Fire', 90.0, []),
    'AcidSlug': Mob('an acid slug', 0x0033, 370, 'AI_Melee', 'Closest', 0, -1, 'Fire', 80.0, []),
    'AgapiteElemental': Mob('an agapite elemental', 0x006B, 153, 'AI_Melee', 'Closest', 3500, -3500, 'Energy', 100.0, []),
    'AirElemental': Mob('an air elemental', 0x000D, 93, 'AI_Mage', 'Closest', 4500, -4500, 'Cold', 80.0, []),
    'Alligator': Mob('an alligator', 0x00CA, 60, 'AI_Melee', 'Closest', 600, -600, 'Cold', 60.0, []),
    'Allosaurus': Mob('an allosaurus', 0x050A, 18000, 'AI_Melee', 'Closest', 21000, -21000, 'Fire', 150.0, []),
    'Anchisaur': Mob('an anchisaur', 0x050C, 3718, 'AI_Melee', 'Closest', 8000, -8000, 'Cold', 110.0, []),
    'AncientLich': Mob('an ancient lich', 0x004E, 595, 'AI_NecroMage', 'Closest', 23000, -23000, 'Fire', 100.0, ['Undead']),
    'AncientWyrm': Mob('an ancient wyrm', 0x002E, 711, 'AI_Mage', 'Closest', 22500, -22500, 'Poison', 100.0, ['Reptile', 'DragonSlaying']),
    'AntLion': Mob('an ant lion', 0x0313, 162, 'AI_Melee', 'Closest', 4500, -4500, 'Fire', 90.0, []),
    'ArcaneDaemon': Mob('an arcane daemon', 0x0310, 115, 'AI_Mage', 'Closest', 7000, -10000, 'Cold', 80.0, []),
    'ArchDaemon': Mob('an arch deamon', 0x0028, 711, 'AI_Mage', 'Closest', 24000, -24000, 'Energy', 100.0, []),
    'Archaeosaurus': Mob('an Archaeosaurus', 0x0507, 2500, 'AI_Melee', 'Closest', 8100, -8100, 'Physical', 110.0, []),
    'ArcticOgreLord': Mob('an arctic ogre lord', 0x0087, 552, 'AI_Melee', 'Closest', 15000, -15000, 'Fire', 100.0, ['Repond']),
    'BakeKitsune': Mob('a bake kitsune', 0x00F6, 350, 'AI_Mage', 'Closest', 8000, -8000, 'Physical', 55.0, []),
    'Balron': Mob('a balron', 0x0028, 711, 'AI_Mage', 'Closest', 24000, -24000, 'Energy', 100.0, []),
    'BattleChickenLizard': Mob('a battle chicken lizard', 0x02CC, 177, 'AI_Melee', 'Aggressor', 0, 0, 'Cold', 62.0, []),
    'Betrayer': Mob('a betrayer', 0x02FF, 300, 'AI_Mage', 'Closest', 15000, -15000, 'Energy', 100.0, []),
    'Bird': Mob('a crow', 0x0006, 55, 'AI_Melee', 'Aggressor', 150, 0, 'Physical', 6.4, []),
    'BlackBear': Mob('a black bear', 0x00D3, 60, 'AI_Melee', 'Aggressor', 450, 0, 'Fire', 60.0, []),
    'BlackSolenInfiltratorQueen': Mob('a black solen infiltrator', 0x0327, 162, 'AI_Melee', 'Closest', 6500, -6500, 'Cold', 90.0, []),
    'BlackSolenInfiltratorWarrior': Mob('a black solen infiltrator', 0x0326, 107, 'AI_Melee', 'Closest', 3000, -3000, 'Cold', 80.0, []),
    'BlackSolenQueen': Mob('a black solen queen', 0x0327, 162, 'AI_Melee', 'Closest', 4500, -4500, 'Cold', 90.0, []),
    'BlackSolenWarrior': Mob('a black solen warrior', 0x0326, 107, 'AI_Melee', 'Closest', 3000, -3000, 'Cold', 80.0, []),
    'BlackSolenWorker': Mob('a black solen worker', 0x0325, 72, 'AI_Melee', 'Closest', 1500, -1500, 'Cold', 60.0, []),
    'BloodElemental': Mob('a blood elemental', 0x009F, 369, 'AI_Mage', 'Closest', 12500, -12500, 'Fire', 100.0, []),
    'BloodFox': Mob('Blood Fox', 0x058F, 200, 'AI_Melee', 'Closest', 0, -1, 'Fire', 90.0, []),
    'BloodWorm': Mob('a bloodworm', 0x011F, 422, 'AI_Melee', 'Closest', 0, -1, 'Energy', 100.0, []),
    'Boar': Mob('a boar', 0x0122, 15, 'AI_Melee', 'Aggressor', 300, 0, 'Cold', 9.0, []),
    'BogThing': Mob('a bog thing', 0x030C, 540, 'AI_Melee', 'Closest', 8000, -8000, 'Cold', 80.0, []),
    'Bogle': Mob('a bogle', 0x0099, 60, 'AI_Mage', 'Closest', 4000, -4000, 'Physical', 55.0, []),
    'Bogling': Mob('a bogling', 0x030B, 72, 'AI_Melee', 'Closest', 450, -450, 'Fire', 75.0, []),
    'BoneDemon': Mob('a bone demon', 0x0134, 3600, 'AI_Mage', 'Closest', 20000, -20000, 'Fire', 100.0, []),
    'BoneKnight': Mob('a bone knight', 0x0039, 150, 'AI_Melee', 'Closest', 3000, -3000, 'Fire', 95.0, ['Undead']),
    'BoneMagi': Mob('a bone mage', 0x0094, 60, 'AI_NecroMage', 'Closest', 3000, -3000, 'Fire', 55.0, ['Undead']),
    'Brigand_0x0191': Mob('a female', 0x0191, 100, 'AI_Melee', 'Closest', 1000, -1000, 'Physical', 37.5, []),
    'Brigand_0x0190': Mob('a female', 0x0190, 100, 'AI_Melee', 'Closest', 1000, -1000, 'Physical', 37.5, []),
    'BritannianInfantry': Mob('a male', 0x0190, 2400, 'AI_Melee', 'Closest', 7500, 4500, 'Cold', 0.0, []),
    'BronzeElemental': Mob('a bronze elemental', 0x006C, 153, 'AI_Melee', 'Closest', 5000, -5000, 'Cold', 100.0, []),
    'BrownBear': Mob('a brown bear', 0x00A7, 60, 'AI_Melee', 'Aggressor', 450, -1, 'Fire', 60.0, []),
    'BulbousPutrification': Mob('a bulbous putrification', 0x0307, 1231, 'AI_Melee', 'Closest', 0, -1, 'Fire', 114.7, []),
    'Bull_0x00E8': Mob('a bull', 0x00E8, 64, 'AI_Melee', 'Aggressor', 600, 0, 'Fire', 57.5, []),
    'Bull_0x00E9': Mob('a bull', 0x00E9, 64, 'AI_Melee', 'Aggressor', 600, 0, 'Fire', 57.5, []),
    'BullFrog': Mob('a bull frog', 0x0051, 42, 'AI_Melee', 'Aggressor', 350, 0, 'Fire', 60.0, []),
    'Cat': Mob('a cat', 0x00C9, 6, 'AI_Melee', 'Aggressor', 0, 150, 'Fire', 5.0, []),
    'Centaur': Mob('a centaur', 0x0065, 172, 'AI_Melee', 'Aggressor', 6500, -1, 'Cold', 100.0, ['Fey']),
    'Changeling': Mob('Changeling', 0x0108, 211, 'AI_Spellweaving', 'Closest', 15000, -15000, 'Fire', 12.5, []),
    'ChaosDaemon': Mob('a chaos daemon', 0x0318, 110, 'AI_Melee', 'Closest', 3000, -4000, 'Poison', 100.0, []),
    'ChaosDragoon': Mob('a chaos dragoon', 0x0190, 225, 'AI_Melee', 'Closest', 5000, -5000, 'Physical', 0.0, []),
    'ChaosDragoonElite': Mob('a chaos dragoon elite', 0x0190, 350, 'AI_Mage', 'Closest', 8000, -8000, 'Fire', 0.0, []),
    'Chicken': Mob('a chicken', 0x00D0, 3, 'AI_Melee', 'Aggressor', 150, 0, 'Fire', 5.0, []),
    'ChickenLizard': Mob('a chicken lizard', 0x02CC, 95, 'AI_Melee', 'Aggressor', 0, 0, 'Cold', 38.2, []),
    'ClanCA': Mob('Clan Chitter Assistant', 0x008E, 145, 'AI_Archer', 'Closest', 6500, -6500, 'Energy', 75.0, []),
    'ClanCT': Mob('Clan Scratch Tinkerer', 0x008E, 2068, 'AI_Archer', 'Closest', 6500, -6500, 'Poison', 85.0, []),
    'ClanRC': Mob('Clan Ribbon Courtier', 0x002A, 2100, 'AI_Melee', 'Closest', 1500, -1500, 'Fire', 55.0, []),
    'ClanRS': Mob('Clan Ribbon Supplicant', 0x002A, 127, 'AI_Melee', 'Closest', 1500, -1500, 'Energy', 60.0, []),
    'ClanRibbonPlagueRat': Mob('Clan Ribbon Plague Rat', 0x00EE, 92, 'AI_Melee', 'Aggressor', 150, -150, 'Poison', 40.0, []),
    'ClanSH': Mob('Clan Scratch Henchrat', 0x002A, 2065, 'AI_Melee', 'Closest', 1500, -1500, 'Energy', 65.0, []),
    'ClanSS': Mob('Clan Scratch Scrounger', 0x008E, 135, 'AI_Archer', 'Closest', 6500, -6500, 'Poison', 75.0, []),
    'ClanSSW': Mob('Clan Scratch Savage Wolf', 0x0062, 65, 'AI_Melee', 'Closest', 3400, -3400, 'Fire', 45.5, []),
    'ClockworkScorpion': Mob('a clockwork scorpion', 0x02CD, 210, 'AI_Melee', 'Closest', 3500, -3500, 'Energy', 80.0, []),
    'ColdDrake_0x003C': Mob('a cold drake', 0x003C, 500, 'AI_Melee', 'Closest', 12000, -12000, 'Fire', 126.0, []),
    'ColdDrake_0x003D': Mob('a cold drake', 0x003D, 500, 'AI_Melee', 'Closest', 12000, -12000, 'Fire', 126.0, []),
    'CopperElemental': Mob('a copper elemental', 0x006D, 153, 'AI_Melee', 'Closest', 4800, -4800, 'Energy', 100.0, []),
    'CoralSnake': Mob('a coral snake', 0x0034, 200, 'AI_Melee', 'Closest', 300, -300, 'Cold', 105.0, ['Reptile', 'Snake']),
    'CorporealBrume': Mob('a corporeal brume', 0x0104, 1250, 'AI_Melee', 'Closest', 12000, -12000, 'Energy', 115.0, []),
    'Corpser': Mob('a corpser', 0x0008, 108, 'AI_Melee', 'Closest', 1000, -1000, 'Energy', 60.0, []),
    'CorrosiveSlime': Mob('a corrosive slime', 0x0033, 19, 'AI_Melee', 'Closest', 300, -300, 'Fire', 26.1, []),
    'CorruptedSoul': Mob('a corrupted soul', 0x03CA, 69, 'AI_Melee', 'Closest', 5000, -5000, 'Poison', 88.7, []),
    'Cougar': Mob('a cougar', 0x003F, 48, 'AI_Melee', 'Aggressor', 450, 0, 'Energy', 60.0, []),
    'Cow_0x00D8': Mob('a cow', 0x00D8, 18, 'AI_Melee', 'Aggressor', 300, 0, 'Fire', 5.5, []),
    'Cow_0x00E7': Mob('a cow', 0x00E7, 18, 'AI_Melee', 'Aggressor', 300, 0, 'Fire', 5.5, []),
    'Crane': Mob('a crane', 0x00FE, 35, 'AI_Melee', 'Aggressor', 0, 200, 'Fire', 11.0, []),
    'CrystalDaemon': Mob('a crystal daemon', 0x0310, 220, 'AI_Mage', 'Closest', 15000, -15000, 'Fire', 80.0, []),
    'CrystalElemental': Mob('a crystal elemental', 0x012C, 150, 'AI_Mage', 'Closest', 6500, -6500, 'Fire', 75.0, []),
    'CrystalHydra': Mob('a crystal hydra', 0x0109, 1500, 'AI_Melee', 'Closest', 17000, -17000, 'Fire', 120.0, []),
    'CrystalLatticeSeeker': Mob('Crystal Lattice Seeker', 0x007B, 550, 'AI_Mage', 'Closest', 17000, -17000, 'Fire', 100.0, []),
    'CrystalVortex': Mob('a crystal vortex', 0x000D, 400, 'AI_Melee', 'Closest', 17000, -17000, 'Fire', 120.0, []),
    'Cursed': Mob('a male', 0x0190, 120, 'AI_Melee', 'Closest', 1000, -2000, 'Fire', 0.0, []),
    'CursedMetallicKnight': Mob('cursed metallic knight', 0x0093, 150, 'AI_Melee', 'Closest', 3000, -3000, 'Fire', 93.1, []),
    'CursedMetallicMage': Mob('cursed metallic mage', 0x0094, 66, 'AI_Mage', 'Closest', 3000, -3000, 'Fire', 54.0, []),
    'CursedSoul': Mob('a cursed soul', 0x0003, 20, 'AI_Melee', 'Aggressor', 200, -200, 'Cold', 39.0, []),
    'Cyclops': Mob('a cyclopean warrior', 0x004B, 231, 'AI_Melee', 'Closest', 4500, -4500, 'Cold', 90.0, []),
    'Daemon': Mob('a daemon', 0x0009, 303, 'AI_Mage', 'Closest', 15000, -15000, 'Poison', 80.0, []),
    'DarkGuardian': Mob('a dark guardian', 0x004E, 180, 'AI_NecroMage', 'Closest', 5000, -5000, 'Fire', 0.0, []),
    'DarkWisp': Mob('a dark wisp', 0x00A5, 135, 'AI_NecroMage', 'Closest', 4000, -4000, 'Poison', 80.0, []),
    'DarknightCreeper': Mob('a darknight creeper', 0x0139, 4000, 'AI_Mage', 'Closest', 22000, -22000, 'Physical', 90.9, []),
    'DeathwatchBeetle': Mob('a deathwatch beetle', 0x00F2, 145, 'AI_Melee', 'Aggressor', 1400, -1400, 'Fire', 60.0, []),
    'DeathwatchBeetleHatchling': Mob('a deathwatch beetle hatchling', 0x00F2, 60, 'AI_Melee', 'Aggressor', 700, -700, 'Fire', 40.0, []),
    'DeepSeaSerpent': Mob('a deep sea serpent', 0x0096, 255, 'AI_Mage', 'Closest', 6000, -6000, 'Energy', 70.0, ['Reptile', 'Snake']),
    'DemonKnight': Mob('a demon knight', 0x013E, 30000, 'AI_NecroMage', 'Closest', 28000, -28000, 'Fire', 120.0, []),
    'DesertScorpion': Mob('a desert scorpion', 0x02CD, 400, 'AI_Melee', 'Closest', 8100, -8100, 'Cold', 60.0, []),
    'Devourer': Mob('a devourer of souls', 0x012F, 650, 'AI_NecroMage', 'Closest', 9500, -9500, 'Cold', 100.0, []),
    'Dimetrosaur': Mob('a dimetrosaur', 0x0505, 5400, 'AI_Melee', 'Closest', 17000, -17000, 'Fire', 125.0, []),
    'DireWolf': Mob('a dire wolf', 0x0017, 72, 'AI_Melee', 'Closest', 2500, -2500, 'Cold', 80.0, []),
    'Dog': Mob('a dog', 0x00D9, 22, 'AI_Melee', 'Aggressor', 0, 300, 'Fire', 31.0, []),
    'Dolphin': Mob('a dolphin', 0x0097, 27, 'AI_Melee', 'Aggressor', 500, 2000, 'Poison', 29.0, []),
    'Doppleganger': Mob('a doppleganger', 0x0309, 120, 'AI_Melee', 'Closest', 1000, -1000, 'Fire', 90.0, []),
    'Dragon_0x000C': Mob('a dragon', 0x000C, 495, 'AI_Mage', 'Closest', 15000, -15000, 'Poison', 92.5, ['Reptile', 'DragonSlaying']),
    'Dragon_0x003B': Mob('a dragon', 0x003B, 495, 'AI_Mage', 'Closest', 15000, -15000, 'Poison', 92.5, ['Reptile', 'DragonSlaying']),
    'DragonTurtleHatchling': Mob('a dragon turtle hatchling', 0x050E, 850, 'AI_Mage', 'Aggressor', 16000, -16000, 'Cold', 150.0, []),
    'DragonWolf': Mob('a dragon wolf', 0x02CF, 860, 'AI_Melee', 'Closest', 8500, -8500, 'Fire', 105.0, []),
    'Drake_0x003C': Mob('a drake', 0x003C, 258, 'AI_Melee', 'Closest', 5500, -5500, 'Poison', 80.0, ['Reptile', 'DragonSlaying']),
    'Drake_0x003D': Mob('a drake', 0x003D, 258, 'AI_Melee', 'Closest', 5500, -5500, 'Poison', 80.0, ['Reptile', 'DragonSlaying']),
    'DreadSpider': Mob('a dread spider', 0x000B, 132, 'AI_Mage', 'Closest', 5000, -5000, 'Fire', 75.0, ['Arachnid', 'Spider']),
    'DreamWraith': Mob('a dream wraith', 0x02E4, 650, 'AI_NecroMage', 'Closest', 4000, -4000, 'Energy', 100.0, []),
    'DullCopperElemental': Mob('a dull copper elemental', 0x006E, 153, 'AI_Melee', 'Closest', 3500, -3500, 'Cold', 100.0, []),
    'Eagle': Mob('an eagle', 0x0005, 27, 'AI_Melee', 'Aggressor', 300, 0, 'Poison', 30.0, []),
    'EarthElemental': Mob('an earth elemental', 0x000E, 93, 'AI_Melee', 'Closest', 3500, -3500, 'Fire', 100.0, []),
    'EffetePutridGargoyle': Mob('an effete putrid gargoyle', 0x0004, 111, 'AI_Mage', 'Closest', 3500, -3500, 'Energy', 70.0, []),
    'EffeteUndeadGargoyle': Mob('an effete undead gargoyle', 0x02D2, 70, 'AI_Melee', 'Closest', 3500, -3500, 'Fire', 50.0, []),
    'Efreet': Mob('an efreet', 0x0083, 213, 'AI_Mage', 'Closest', 10000, -10000, 'Cold', 80.0, []),
    'ElderGazer': Mob('an elder gazer', 0x0016, 195, 'AI_Mage', 'Closest', 12500, -12500, 'Cold', 100.0, []),
    'EnragedEarthElemental': Mob('Enraged Earth Elemental', 0x000E, 550, 'AI_Melee', 'Closest', 3500, -3500, 'Fire', 120.0, []),
    'EnslavedGargoyle': Mob('an enslaved gargoyle', 0x02F1, 212, 'AI_Melee', 'Closest', 3500, -1, 'Cold', 80.0, []),
    'EnslavedGoblinKeeper': Mob('enslaved goblin keeper', 0x014E, 174, 'AI_Melee', 'Closest', 1500, -1500, 'Poison', 100.7, []),
    'EnslavedGoblinMage': Mob('enslaved goblin mage', 0x014E, 174, 'AI_Melee', 'Closest', 1500, -1500, 'Energy', 106.4, []),
    'EnslavedGoblinScout': Mob('enslaved goblin scout', 0x014E, 182, 'AI_Melee', 'Closest', 1500, -1500, 'Poison', 113.7, []),
    'EnslavedGrayGoblin': Mob('enslaved gray goblin', 0x014E, 179, 'AI_Melee', 'Closest', 1500, -1500, 'Energy', 99.2, []),
    'EnslavedGreenGoblin': Mob('enslaved green goblin', 0x014E, 184, 'AI_Melee', 'Closest', 1500, -1500, 'Energy', 99.4, []),
    'EnslavedGreenGoblinAlchemist': Mob('green goblin alchemist', 0x02D3, 196, 'AI_Melee', 'Closest', 1500, -1500, 'Energy', 94.7, []),
    'EtherealWarrior': Mob('an ethereal warrior', 0x007B, 471, 'AI_Mage', 'Evil', 7000, 7000, 'Fire', 100.0, []),
    'Ettin': Mob('an ettin', 0x0012, 99, 'AI_Melee', 'Closest', 3000, -3000, 'Fire', 60.0, ['Repond']),
    'EvilMage': Mob('an evil mage', 0x007C, 63, 'AI_Mage', 'Closest', 2500, -2500, 'Cold', 60.0, []),
    'EvilMageLord_0x007D': Mob('an evil mage lord', 0x007D, 63, 'AI_Mage', 'Closest', 10500, -10500, 'Fire', 80.0, []),
    'EvilMageLord_0x007E': Mob('an evil mage lord', 0x007E, 63, 'AI_Mage', 'Closest', 10500, -10500, 'Fire', 80.0, []),
    'Executioner_0x0191': Mob('a female', 0x0191, 250, 'AI_Melee', 'Closest', 5000, -5000, 'Poison', 0.0, []),
    'Executioner_0x0190': Mob('a female', 0x0190, 250, 'AI_Melee', 'Closest', 5000, -5000, 'Poison', 0.0, []),
    'ExodusMinion': Mob('exodus minion', 0x02F5, 570, 'AI_Melee', 'Closest', 18000, -18000, 'Cold', 100.0, []),
    'ExodusOverseer': Mob('exodus overseer', 0x02F4, 390, 'AI_Melee', 'Closest', 10000, -10000, 'Cold', 98.0, []),
    'FairyDragon': Mob('fairy dragon', 0x02CE, 403, 'AI_Mystic', 'Closest', 15000, -15000, 'Physical', 92.5, []),
    'FanDancer': Mob('a fan dancer', 0x00F7, 430, 'AI_Melee', 'Closest', 9000, -9000, 'Physical', 95.0, []),
    'FeralTreefellow': Mob('a feral treefellow', 0x012D, 1320, 'AI_Melee', 'Aggressor', 1000, -3000, 'Fire', 85.0, []),
    'Ferret': Mob('a ferret', 0x0117, 50, 'AI_Melee', 'Aggressor', 0, 0, 'Fire', 4.0, []),
    'FetidEssence': Mob('a fetid essence', 0x0111, 650, 'AI_Spellweaving', 'Closest', 3700, -3700, 'Physical', 83.9, []),
    'FireAnt': Mob('a fire ant', 0x02E2, 299, 'AI_Melee', 'Closest', 0, -1, 'Cold', 75.4, []),
    'FireDaemon': Mob('a fire daemon', 0x0009, 1174, 'AI_Mage', 'Closest', 15000, -15000, 'Cold', 78.7, []),
    'FireElemental': Mob('a fire elemental', 0x000F, 93, 'AI_Mage', 'Closest', 4500, -4500, 'Cold', 100.0, []),
    'FireGargoyle': Mob('a fire gargoyle', 0x0082, 240, 'AI_Mage', 'Closest', 3500, -3500, 'Cold', 80.0, []),
    'FleshGolem': Mob('a flesh golem', 0x0130, 120, 'AI_Melee', 'Closest', 1000, -1800, 'Cold', 70.0, []),
    'FleshRenderer': Mob('a fleshrenderer', 0x013B, 4500, 'AI_Melee', 'Closest', 23000, -23000, 'Fire', 100.0, []),
    'ForgottenServant_0x0191': Mob('a female', 0x0191, 123, 'AI_Melee', 'Closest', 2500, -2500, 'Cold', 85.0, []),
    'ForgottenServant_0x0190': Mob('a female', 0x0190, 123, 'AI_Melee', 'Closest', 2500, -2500, 'Cold', 85.0, []),
    'FrostDragon_0x000C': Mob('a frost dragon', 0x000C, 2250, 'AI_Mage', 'Closest', 25000, -25000, 'Fire', 130.0, ['Reptile', 'DragonSlaying']),
    'FrostDragon_0x003B': Mob('a frost dragon', 0x003B, 2250, 'AI_Mage', 'Closest', 25000, -25000, 'Fire', 130.0, ['Reptile', 'DragonSlaying']),
    'FrostMite': Mob('Frost Mite', 0x0590, 1000, 'AI_Melee', 'Closest', 0, -1, 'Fire', 110.0, []),
    'FrostOoze': Mob('a frost ooze', 0x005E, 17, 'AI_Melee', 'Closest', 450, -450, 'Fire', 40.0, []),
    'FrostSpider': Mob('a frost spider', 0x0014, 60, 'AI_Melee', 'Closest', 775, -775, 'Fire', 65.0, []),
    'FrostTroll': Mob('a frost troll', 0x0037, 156, 'AI_Melee', 'Closest', 4000, -4000, 'Fire', 100.0, []),
    'Gallusaurus': Mob('a gallusaurus', 0x0506, 900, 'AI_Melee', 'Closest', 8100, -8100, 'Fire', 91.0, []),
    'Gaman': Mob('a gaman', 0x00F8, 160, 'AI_Melee', 'Aggressor', 2000, -2000, 'Fire', 57.5, []),
    'GargishOutcast_0x029A': Mob('a Gargoyle Male', 0x029A, 1200, 'AI_Mystic', 'Closest', 12000, -12000, 'Physical', 0.0, []),
    'GargishOutcast_0x029B': Mob('a Gargoyle Male', 0x029B, 1200, 'AI_Mystic', 'Closest', 12000, -12000, 'Physical', 0.0, []),
    'Gargoyle': Mob('a gargoyle', 0x0004, 105, 'AI_Mage', 'Closest', 3500, -3500, 'Energy', 80.0, []),
    'GargoyleDestroyer': Mob('Gargoyle Destroyer', 0x02F3, 485, 'AI_Mage', 'Closest', 10000, -10000, 'Cold', 100.0, []),
    'GargoyleEnforcer': Mob('Gargoyle Enforcer', 0x02F2, 485, 'AI_Mage', 'Closest', 5000, -5000, 'Energy', 90.0, []),
    'GargoyleGuardian': Mob('Abyss Guardian', 0x02F3, 485, 'AI_Mage', 'None', 10000, -10000, 'Cold', 100.0, []),
    'GargoyleShade': Mob('a gargoyle shade', 0x0004, 64, 'AI_Mage', 'Closest', 4000, -4000, 'Energy', 55.0, []),
    'Gazer': Mob('a gazer', 0x0016, 75, 'AI_Mage', 'Closest', 3500, -3500, 'Poison', 70.0, []),
    'GazerLarva': Mob('a gazer larva', 0x030A, 47, 'AI_Melee', 'Closest', 900, -900, 'Fire', 70.0, []),
    'Ghoul': Mob('a ghoul', 0x0099, 60, 'AI_Melee', 'Closest', 2500, -2500, 'Fire', 55.0, ['Undead']),
    'GiantBlackWidow': Mob('a giant black widow', 0x009D, 60, 'AI_Melee', 'Closest', 3500, -3500, 'Fire', 85.0, ['Arachnid', 'Spider']),
    'GiantIceWorm': Mob('a giant ice worm', 0x0059, 147, 'AI_Melee', 'Closest', 4500, -4500, 'Fire', 80.0, []),
    'GiantRat': Mob('a giant rat', 0x00D7, 39, 'AI_Melee', 'Closest', 300, -300, 'Cold', 44.0, []),
    'GiantSerpent': Mob('a giant serpent', 0x0015, 129, 'AI_Melee', 'Closest', 2500, -2500, 'Fire', 80.0, ['Reptile', 'Snake']),
    'GiantSpider': Mob('a giant spider', 0x001C, 60, 'AI_Melee', 'Closest', 600, -600, 'Fire', 65.0, ['Arachnid', 'Spider']),
    'GiantToad': Mob('a giant toad', 0x0050, 60, 'AI_Melee', 'Closest', 750, -750, 'Cold', 60.0, []),
    'GiantTurkey': Mob('a giant turkey', 0x0402, 25000, 'AI_Melee', 'Aggressor', 0, -1, 'Cold', 120.0, []),
    'Gibberling': Mob('a gibberling', 0x0133, 99, 'AI_Melee', 'Closest', 1500, -1500, 'Poison', 80.0, []),
    'Goat': Mob('a goat', 0x00D1, 12, 'AI_Melee', 'Aggressor', 150, 0, 'Fire', 5.0, []),
    'GoldenElemental': Mob('a golden elemental', 0x00A6, 153, 'AI_Melee', 'Closest', 3500, -3500, 'Fire', 100.0, []),
    'GolemController': Mob('a golem controller', 0x0190, 90, 'AI_Mage', 'Closest', 4000, -4000, 'Poison', 87.5, []),
    'GoreFiend': Mob('a gore fiend', 0x0131, 111, 'AI_Melee', 'Closest', 1500, -1500, 'Poison', 70.0, []),
    'Gorilla': Mob('a gorilla', 0x001D, 51, 'AI_Melee', 'Aggressor', 450, -1, 'Poison', 58.0, []),
    'GrayGoblin': Mob('a gray goblin', 0x02D3, 194, 'AI_Melee', 'Closest', 1500, -1500, 'Poison', 105.5, []),
    'GrayGoblinKeeper': Mob('a gray goblin keeper', 0x02D3, 186, 'AI_Melee', 'Closest', 1500, -1500, 'Energy', 103.6, []),
    'GrayGoblinMage': Mob('a gray goblin mage', 0x02D3, 151, 'AI_Mage', 'Closest', 1500, -1500, 'Poison', 104.2, []),
    'GreatHart': Mob('a great hart', 0x00EA, 41, 'AI_Melee', 'Aggressor', 300, 0, 'Fire', 47.5, []),
    'GreaterDragon_0x000C': Mob('a greater dragon', 0x000C, 2000, 'AI_Mage', 'Closest', 22000, -15000, 'Cold', 145.0, ['Reptile', 'DragonSlaying']),
    'GreaterDragon_0x003B': Mob('a greater dragon', 0x003B, 2000, 'AI_Mage', 'Closest', 22000, -15000, 'Cold', 145.0, ['Reptile', 'DragonSlaying']),
    'GreaterMongbat': Mob('a greater mongbat', 0x0027, 48, 'AI_Melee', 'Closest', 450, -450, 'Fire', 35.0, []),
    'GreaterPhoenix': Mob('a greater phoenix', 0x0340, 240, 'AI_Mage', 'Closest', 10000, -10000, 'Cold', 77.0, []),
    'GreaterPoisonElemental': Mob('greater poison elemental', 0x00A2, 702, 'AI_Mage', 'Closest', 12500, -12500, 'Fire', 88.3, []),
    'GreenGoblin': Mob('a green goblin', 0x02D3, 208, 'AI_Melee', 'Closest', 1500, -1500, 'Energy', 108.3, []),
    'GreenGoblinAlchemist': Mob('a green goblin alchemist', 0x02D3, 197, 'AI_Melee', 'Closest', 1500, -1500, 'Energy', 106.9, []),
    'GreenGoblinScout': Mob('a green goblin scout', 0x02D3, 198, 'AI_OrcScout', 'Closest', 1500, -1500, 'Energy', 119.5, []),
    'Gremlin': Mob('a gremlin', 0x02D4, 70, 'AI_Archer', 'Closest', 0, -1, 'Poison', 0.0, []),
    'GreyWolf_0x0019': Mob('a grey wolf', 0x0019, 48, 'AI_Melee', 'Aggressor', 450, 0, 'Fire', 60.0, []),
    'GreyWolf_0x001B': Mob('a grey wolf', 0x001B, 48, 'AI_Melee', 'Aggressor', 450, 0, 'Fire', 60.0, []),
    'GrizzlyBear': Mob('a grizzly bear', 0x00D4, 93, 'AI_Melee', 'Aggressor', 1000, 0, 'Fire', 70.0, []),
    'Grubber': Mob('a grubber', 0x010E, 200, 'AI_Melee', 'None', 1000, -1, 'Physical', 5.0, []),
    'Harpy': Mob('a harpy', 0x001E, 72, 'AI_Melee', 'Closest', 2500, -2500, 'Fire', 90.0, []),
    'HeadlessOne': Mob('a headless one', 0x001F, 30, 'AI_Melee', 'Closest', 450, -450, 'Fire', 40.0, []),
    'HellCat': Mob('a hell cat', 0x00C9, 67, 'AI_Melee', 'Closest', 1000, -1000, 'Cold', 40.0, []),
    'HellHound': Mob('a hell hound', 0x0062, 300, 'AI_Melee', 'Closest', 3400, -3400, 'Physical', 80.0, []),
    'HighPlainsBoura': Mob('a high plains boura', 0x02CB, 618, 'AI_Melee', 'Aggressor', 5000, -5000, 'Cold', 115.3, []),
    'Hind': Mob('a hind', 0x00ED, 29, 'AI_Melee', 'Aggressor', 300, 0, 'Fire', 26.0, []),
    'HordeMinion': Mob('a horde minion', 0x0308, 24, 'AI_Melee', 'Closest', 500, -500, 'Cold', 40.0, []),
    'Hydra': Mob('a hydra', 0x0109, 1500, 'AI_Melee', 'Closest', 22000, -22000, 'Cold', 117.4, []),
    'IceElemental': Mob('an ice elemental', 0x00A1, 111, 'AI_Mage', 'Closest', 4000, -4000, 'Fire', 100.0, []),
    'IceFiend': Mob('an ice fiend', 0x002B, 243, 'AI_Mage', 'Closest', 18000, -18000, 'Fire', 100.0, []),
    'IceHound': Mob('an ice hound', 0x0062, 125, 'AI_Melee', 'Closest', 3400, -3400, 'Fire', 0.0, []),
    'IceSerpent': Mob('a giant ice serpent', 0x0059, 147, 'AI_Melee', 'Closest', 3500, -3500, 'Fire', 80.0, ['Reptile', 'Snake']),
    'IceSnake': Mob('an ice snake', 0x0034, 77, 'AI_Melee', 'Closest', 900, -900, 'Fire', 54.0, []),
    'Imp': Mob('an imp', 0x004A, 70, 'AI_Mage', 'Closest', 2500, -2500, 'Cold', 44.0, []),
    'Impaler': Mob('an impaler', 0x0132, 5000, 'AI_Melee', 'Closest', 24000, -24000, 'Fire', 120.0, []),
    'Infernus': Mob('an infernus', 0x009F, 243, 'AI_Melee', 'Closest', 10000, -10000, 'Cold', 80.0, []),
    'InterredGrizzle': Mob('an interred grizzle', 0x0103, 1500, 'AI_Mage', 'Closest', 3700, -3700, 'Fire', 109.4, []),
    'IronBeetle': Mob('an iron beetle', 0x02CA, 830, 'AI_Melee', 'Closest', 15000, -15000, 'Fire', 110.0, []),
    'JackRabbit': Mob('a jack rabbit', 0x00CD, 9, 'AI_Melee', 'Aggressor', 150, 0, 'Fire', 5.0, []),
    'Juggernaut': Mob('a blackthorn juggernaut', 0x0300, 240, 'AI_Melee', 'Closest', 12000, -12000, 'Energy', 100.0, []),
    'JukaLord': Mob('a juka lord', 0x02FE, 300, 'AI_Archer', 'Closest', 15000, -15000, 'Poison', 100.0, []),
    'JukaMage': Mob('a juka mage', 0x02FD, 180, 'AI_Mage', 'Closest', 15000, -15000, 'Poison', 90.0, []),
    'JukaWarrior': Mob('a juka warrior', 0x02FC, 210, 'AI_Melee', 'Closest', 10000, -10000, 'Poison', 90.0, []),
    'Kappa': Mob('a kappa', 0x00F0, 180, 'AI_Melee', 'Closest', 1700, -1700, 'Energy', 70.0, []),
    'KazeKemono': Mob('a kaze kemono', 0x00C4, 330, 'AI_Mage', 'Closest', 8000, -8000, 'Fire', 95.0, []),
    'Kepetch': Mob('a kepetch', 0x02D6, 400, 'AI_Melee', 'Closest', 6000, -6000, 'Fire', 113.9, []),
    'KepetchAmbusher': Mob('a kepetch ambusher', 0x02D6, 544, 'AI_Melee', 'Closest', 2500, -2500, 'Cold', 113.9, []),
    'KhaldunSummoner': Mob('Zealot of Khaldun', 0x0190, 480, 'AI_Mage', 'Closest', 10000, -10000, 'Fire', 100.0, []),
    'KhaldunZealot': Mob('Zealot of Khaldun', 0x0190, 470, 'AI_Melee', 'Closest', 10000, -10000, 'Fire', 80.0, []),
    'Kraken': Mob('a kraken', 0x004D, 468, 'AI_Melee', 'Closest', 11000, -11000, 'Energy', 60.0, []),
    'LadyOfTheSnow': Mob('a lady of the snow', 0x00FC, 625, 'AI_NecroMage', 'Closest', 15200, -15200, 'Fire', 100.0, []),
    'LavaElemental': Mob('a lava elemental', 0x02D0, 290, 'AI_Mage', 'Closest', 0, -1, 'Fire', 85.4, []),
    'LavaLizard': Mob('a lava lizard', 0x00CE, 90, 'AI_Melee', 'Closest', 3000, -3000, 'Cold', 80.0, []),
    'LavaSerpent': Mob('a lava serpent', 0x005A, 249, 'AI_Melee', 'Closest', 4500, -4500, 'Cold', 80.0, ['Reptile', 'Snake']),
    'LavaSnake': Mob('a lava snake', 0x0034, 32, 'AI_Melee', 'Closest', 600, -600, 'Cold', 34.0, []),
    'LeatherWolf': Mob('a leather wolf', 0x02E3, 329, 'AI_Melee', 'Aggressor', 4500, -4500, 'Fire', 88.4, []),
    'Lich': Mob('a lich', 0x0018, 120, 'AI_NecroMage', 'Closest', 8000, -8000, 'Fire', 0.0, ['Undead']),
    'LichLord': Mob('a lich lord', 0x004F, 303, 'AI_NecroMage', 'Closest', 18000, -18000, 'Fire', 80.0, ['Undead']),
    'Lifestealer': Mob('a lifestealer', 0x012F, 4650, 'AI_NecroMage', 'Closest', 9500, -9500, 'Cold', 100.0, []),
    'Lion': Mob('Lion', 0x0592, 370, 'AI_Melee', 'Closest', 11000, -11000, 'Energy', 110.0, []),
    'Lizardman_0x0023': Mob('a lizardman', 0x0023, 72, 'AI_Melee', 'Closest', 1500, -1500, 'Energy', 70.0, []),
    'Lizardman_0x0024': Mob('a lizardman', 0x0024, 72, 'AI_Melee', 'Closest', 1500, -1500, 'Energy', 70.0, []),
    'Llama': Mob('a llama', 0x00DC, 27, 'AI_Melee', 'Aggressor', 300, 0, 'Fire', 29.0, []),
    'LowlandBoura': Mob('a lowland boura', 0x02CB, 553, 'AI_Melee', 'Aggressor', 5000, -3500, 'Cold', 97.3, []),
    'MLDryad': Mob('a dryad', 0x010A, 321, 'AI_Mage', 'Evil', 5000, 5000, 'Fire', 80.0, []),
    'MaddeningHorror': Mob('a maddening horror', 0x02D1, 660, 'AI_NecroMage', 'Closest', 23000, -23000, 'Fire', 85.0, []),
    'MantraEffervescence': Mob('a mantra effervescence', 0x0111, 250, 'AI_Spellweaving', 'Closest', 6500, -6500, 'Fire', 85.0, []),
    'MeerCaptain': Mob('a meer captain', 0x0305, 66, 'AI_Paladin', 'Evil', 2000, 5000, 'Fire', 89.9, []),
    'MeerEternal': Mob('a meer eternal', 0x0304, 303, 'AI_Spellweaving', 'Aggressor', 18000, 18000, 'Fire', 80.0, []),
    'MeerMage': Mob('a meer mage', 0x0302, 120, 'AI_Spellweaving', 'Aggressor', 8000, 8000, 'Fire', 80.0, []),
    'MeerWarrior': Mob('a meer warrior', 0x0303, 60, 'AI_Melee', 'Aggressor', 2000, 5000, 'Fire', 100.0, []),
    'Mimic': Mob('a mimic', 0x02D9, 543, 'AI_Mage', 'Closest', 0, -1, 'Cold', 92.2, []),
    'MinionOfScelestus': Mob('a minion of scelestus', 0x0009, 30000, 'AI_Mage', 'Weakest', 12500, -12500, 'Fire', 120.0, []),
    'Minotaur': Mob('a minotaur', 0x0107, 340, 'AI_Melee', 'Closest', 5000, -5000, 'Fire', 92.1, []),
    'MinotaurCaptain': Mob('a minotaur captain', 0x0118, 440, 'AI_Melee', 'Closest', 7000, -7000, 'Fire', 107.2, []),
    'MinotaurScout': Mob('a minotaur scout', 0x0119, 383, 'AI_Melee', 'Closest', 5000, -5000, 'Fire', 104.5, []),
    'Moloch': Mob('a moloch', 0x0311, 200, 'AI_Melee', 'Closest', 7500, -7500, 'Poison', 90.0, []),
    'Mongbat': Mob('a mongbat', 0x0027, 6, 'AI_Melee', 'Closest', 150, -150, 'Fire', 10.0, []),
    'MoundOfMaggots': Mob('a mound of maggots', 0x013F, 85, 'AI_Melee', 'Closest', 1000, -1000, 'Fire', 60.0, []),
    'MountainGoat': Mob('a mountain goat', 0x0058, 33, 'AI_Melee', 'Aggressor', 300, -1, 'Fire', 44.0, []),
    'Mummy': Mob('a mummy', 0x009A, 222, 'AI_Melee', 'Closest', 4000, -4000, 'Fire', 50.0, ['Undead']),
    'MyrmidexDrone': Mob('a myrmidex drone', 0x057A, 597, 'AI_Melee', 'Closest', 2500, -2500, 'Physical', 49.8, []),
    'MyrmidexLarvae': Mob('a myrmidex larvae', 0x050D, 588, 'AI_Melee', 'Closest', 2500, -2500, 'Fire', 50.0, []),
    'MyrmidexWarrior': Mob('a myrmidex warrior', 0x057B, 3000, 'AI_Mage', 'Closest', 8000, -8000, 'Physical', 100.0, []),
    'Najasaurus': Mob('a najasaurus', 0x0509, 854, 'AI_Melee', 'Closest', 17000, -17000, 'Energy', 100.0, []),
    'Ogre': Mob('an ogre', 0x0001, 117, 'AI_Melee', 'Closest', 3000, -3000, 'Fire', 80.0, ['Repond']),
    'OgreLord': Mob('an ogre lord', 0x0053, 552, 'AI_Melee', 'Closest', 15000, -15000, 'Fire', 100.0, ['Repond']),
    'Oni': Mob('an oni', 0x00F1, 530, 'AI_Mage', 'Closest', 15000, -15000, 'Cold', 100.0, []),
    'OphidianArchmage': Mob('Ophidian Archmage', 0x0055, 183, 'AI_Mage', 'Closest', 11500, -11500, 'Fire', 60.0, []),
    'OphidianKnight': Mob('Ophidian Knight', 0x0056, 342, 'AI_Melee', 'Closest', 10000, -10000, 'Fire', 100.0, []),
    'OphidianMage': Mob('Ophidian Mage', 0x0055, 123, 'AI_Mage', 'Closest', 4000, -4000, 'Physical', 60.0, []),
    'OphidianMatriarch': Mob('an ophidian matriarch', 0x0057, 303, 'AI_Mage', 'Closest', 16000, -16000, 'Fire', 80.0, ['Reptile', 'Ophidian']),
    'OphidianWarrior': Mob('Ophidian Warrior', 0x0056, 155, 'AI_Melee', 'Closest', 4500, -4500, 'Fire', 0.0, ['Reptile', 'Ophidian']),
    'Orc': Mob('an orc', 0x0011, 72, 'AI_Melee', 'Closest', 1500, -1500, 'Cold', 70.0, []),
    'OrcBomber': Mob('an orc bomber', 0x00B6, 123, 'AI_Melee', 'Closest', 2500, -2500, 'Cold', 85.0, []),
    'OrcBrute': Mob('an orc brute', 0x00BD, 552, 'AI_Melee', 'Closest', 15000, -15000, 'Cold', 100.0, []),
    'OrcCaptain': Mob('an orc', 0x0007, 87, 'AI_Melee', 'Closest', 2500, -2500, 'Poison', 0.0, []),
    'OrcChopper': Mob('an orc chopper', 0x0007, 139, 'AI_Melee', 'Closest', 4500, -4500, 'Cold', 85.0, []),
    'OrcScout': Mob('an orc scout', 0x00B5, 72, 'AI_OrcScout', 'Closest', 1500, -1500, 'Cold', 0.0, []),
    'OrcishLord': Mob('an orcish lord', 0x008A, 123, 'AI_Melee', 'Closest', 2500, -2500, 'Cold', 85.0, []),
    'OrcishMage': Mob('an orcish mage', 0x008C, 90, 'AI_Mage', 'Closest', 3000, -3000, 'Cold', 50.0, []),
    'Ortanord': Mob('Ortanord', 0x003A, 100, 'AI_Melee', 'Closest', 8000, -8000, 'Physical', 16.6, []),
    'OsseinRam': Mob('Ossein Ram', 0x0591, 550, 'AI_Melee', 'Closest', 0, -1, 'Fire', 100.0, []),
    'PackHorse': Mob('a pack horse', 0x0123, 80, 'AI_Melee', 'Aggressor', 0, 200, 'Fire', 44.0, []),
    'PackLlama': Mob('a pack llama', 0x0124, 50, 'AI_Melee', 'Aggressor', 0, 200, 'Fire', 29.0, []),
    'Panther': Mob('a panther', 0x00D6, 51, 'AI_Melee', 'Aggressor', 450, 0, 'Energy', 65.0, []),
    'PatchworkSkeleton': Mob('a patchwork skeleton', 0x0135, 72, 'AI_Melee', 'Closest', 500, -500, 'Energy', 70.0, []),
    'PestilentBandage': Mob('a pestilent bandage', 0x009A, 445, 'AI_Melee', 'Closest', 20000, -20000, 'Fire', 75.0, []),
    'Phoenix': Mob('a phoenix', 0x0340, 383, 'AI_Mage', 'Aggressor', 15000, -1, 'Cold', 100.0, []),
    'Pig': Mob('a pig', 0x00CB, 12, 'AI_Melee', 'Aggressor', 150, 0, 'Fire', 5.0, []),
    'PitFiend': Mob('a pit fiend', 0x002B, 243, 'AI_Mage', 'Closest', 18000, -18000, 'Fire', 100.0, []),
    'Pixie': Mob('a pixie', 0x0080, 18, 'AI_Mage', 'Evil', 7000, 7000, 'Fire', 12.5, ['Fey']),
    'PlagueBeast': Mob('a plague beast', 0x0307, 404, 'AI_Melee', 'Closest', 13000, -13000, 'Cold', 100.0, []),
    'PlagueBeastLord': Mob('a plague beast lord', 0x0307, 1800, 'AI_Melee', 'Closest', 2000, -2000, 'Cold', 100.0, []),
    'PlagueRat': Mob('a Clan Ribbon Plague Rat', 0x00D7, 92, 'AI_Melee', 'Closest', 300, -300, 'Poison', 45.0, []),
    'PoisonElemental': Mob('a poison elemental', 0x00A2, 309, 'AI_Mage', 'Closest', 12500, -12500, 'Fire', 90.0, []),
    'PolarBear': Mob('a polar bear', 0x00D5, 84, 'AI_Melee', 'Aggressor', 1500, -1, 'Fire', 70.0, []),
    'PredatorHellCat': Mob('a predator hellcat', 0x007F, 131, 'AI_Melee', 'Closest', 2500, -2500, 'Cold', 65.0, []),
    'Protector': Mob('A Protector', 0x0191, 450, 'AI_Melee', 'Closest', 10000, -10000, 'Fire', 100.0, []),
    'PutridUndeadGargoyle': Mob('a putrid undead gargoyle', 0x02D2, 665, 'AI_Mystic', 'Closest', 3500, -3500, 'Fire', 102.0, ['Undead']),
    'PutridUndeadGuardian': Mob('an putrid undead guardian', 0x02D2, 553, 'AI_Melee', 'Closest', 3000, -3000, 'Fire', 50.7, []),
    'Quagmire': Mob('a quagmire', 0x0315, 105, 'AI_Melee', 'Closest', 1500, -1500, 'Fire', 80.0, []),
    'Rabbit': Mob('a rabbit', 0x00CD, 6, 'AI_Melee', 'Aggressor', 150, 0, 'Fire', 5.0, []),
    'RagingGrizzlyBear': Mob('a raging grizzly bear', 0x00D4, 930, 'AI_Melee', 'Aggressor', 10000, 10000, 'Fire', 88.1, []),
    'RaiJu': Mob('a Rai-Ju', 0x00C7, 280, 'AI_Melee', 'Closest', 8000, -8000, 'Cold', 95.0, []),
    'Rat': Mob('a rat', 0x00EE, 6, 'AI_Melee', 'Aggressor', 150, -150, 'Fire', 4.0, []),
    'Ratman': Mob('a ratman', 0x002A, 72, 'AI_Melee', 'Closest', 1500, -1500, 'Fire', 75.0, ['Repond']),
    'RatmanArcher': Mob('a ratman', 0x008E, 108, 'AI_Archer', 'Closest', 6500, -6500, 'Fire', 75.0, ['Repond']),
    'RatmanMage': Mob('a ratman', 0x008F, 108, 'AI_Mage', 'Closest', 7500, -7500, 'Fire', 75.0, ['Repond']),
    'Ravager': Mob('a ravager', 0x013A, 175, 'AI_Melee', 'Closest', 3500, -3500, 'Energy', 90.0, []),
    'Reaper': Mob('a reaper', 0x002F, 129, 'AI_Mage', 'Closest', 3500, -3500, 'Cold', 60.0, []),
    'RedSolenInfiltratorQueen': Mob('a red solen infiltrator', 0x030F, 162, 'AI_Melee', 'Closest', 6500, -6500, 'Cold', 90.0, []),
    'RedSolenInfiltratorWarrior': Mob('a red solen infiltrator', 0x030E, 107, 'AI_Melee', 'Closest', 3000, -3000, 'Cold', 80.0, []),
    'RedSolenQueen': Mob('a red solen queen', 0x030F, 162, 'AI_Melee', 'Closest', 4500, -4500, 'Cold', 90.0, []),
    'RedSolenWarrior': Mob('a red solen warrior', 0x030E, 107, 'AI_Melee', 'Closest', 3000, -3000, 'Cold', 80.0, []),
    'RedSolenWorker': Mob('a red solen worker', 0x030D, 72, 'AI_Melee', 'Closest', 1500, -1500, 'Cold', 60.0, []),
    'RestlessSoul': Mob('restless soul', 0x03CA, 24, 'AI_Melee', 'Closest', 500, -500, 'Fire', 30.0, []),
    'RevenantLion': Mob('a Revenant Lion', 0x00FB, 280, 'AI_Mage', 'Closest', 4000, -4000, 'Fire', 88.0, []),
    'RottingCorpse': Mob('a rotting corpse', 0x009B, 1200, 'AI_Melee', 'Closest', 6000, -6000, 'Fire', 100.0, ['Undead']),
    'Rotworm': Mob('a rotworm', 0x02DC, 250, 'AI_Melee', 'Closest', 500, -500, 'Cold', 50.0, []),
    'RuddyBoura': Mob('a ruddy boura', 0x02CB, 509, 'AI_Melee', 'Aggressor', 5000, -2500, 'Cold', 87.9, []),
    'RuneBeetle': Mob('a rune beetle', 0x00F4, 360, 'AI_Mage', 'Closest', 15000, -15000, 'Fire', 77.5, []),
    'SAPixie': Mob('a pixie', 0x0080, 18, 'AI_Mage', 'Aggressor', 4000, -4000, 'Fire', 12.5, []),
    'SabreToothedTiger': Mob('sabre-toothed tiger', 0x0588, 423, 'AI_Melee', 'Aggressor', 11000, -11000, 'Fire', 105.0, []),
    'SandVortex': Mob('a sand vortex', 0x0316, 62, 'AI_Melee', 'Closest', 4500, -4500, 'Fire', 80.0, []),
    'Satyr': Mob('a satyr', 0x010F, 400, 'AI_Melee', 'Aggressor', 5000, -1, 'Fire', 100.0, ['Fey']),
    'Saurosaurus': Mob('a saurosaurus', 0x050B, 1468, 'AI_Mage', 'Closest', 11000, -11000, 'Poison', 130.0, []),
    'Savage_0x00B8': Mob('a savage', 0x00B8, 107, 'AI_Melee', 'Closest', 1000, -1000, 'Physical', 0.0, []),
    'Savage_0x00B7': Mob('a savage', 0x00B7, 107, 'AI_Melee', 'Closest', 1000, -1000, 'Physical', 0.0, []),
    'SavageRider': Mob('a savage rider', 0x00B9, 135, 'AI_Melee', 'Closest', 1000, -1000, 'Physical', 0.0, []),
    'SavageShaman': Mob('a savage shaman', 0x00BA, 122, 'AI_Mage', 'Closest', 1000, -1000, 'Fire', 85.0, []),
    'Scorpion': Mob('a scorpion', 0x0030, 63, 'AI_Melee', 'Closest', 2000, -2000, 'Fire', 65.0, []),
    'SeaSerpent': Mob('a sea serpent', 0x0096, 127, 'AI_Mage', 'Closest', 6000, -6000, 'Energy', 70.0, ['Reptile', 'Snake']),
    'SentinelSpider': Mob('a Sentinel spider', 0x009D, 265, 'AI_Melee', 'Closest', 775, -775, 'Fire', 120.0, []),
    'SerpentineDragon': Mob('a serpentine dragon', 0x0067, 480, 'AI_Mage', 'Evil', 15000, 15000, 'Fire', 100.0, ['Reptile', 'DragonSlaying']),
    'Sewerrat': Mob('a sewer rat', 0x00EE, 6, 'AI_Melee', 'Closest', 300, -300, 'Fire', 5.0, []),
    'Shade': Mob('a shade', 0x001A, 60, 'AI_Mage', 'Closest', 4000, -4000, 'Fire', 55.0, ['Undead']),
    'ShadowDweller': Mob('a shadow dweller', 0x02E4, 120, 'AI_Mage', 'Closest', 8000, -8000, 'Fire', 0.0, []),
    'ShadowIronElemental': Mob('a shadow iron elemental', 0x006F, 153, 'AI_Melee', 'Closest', 4500, -4500, 'Poison', 100.0, []),
    'ShadowWisp': Mob('a shadow wisp', 0x00A5, 24, 'AI_Mage', 'Aggressor', 500, -1, 'Cold', 40.0, []),
    'ShadowWyrm': Mob('a shadow wyrm', 0x006A, 599, 'AI_NecroMage', 'Closest', 22500, -22500, 'Poison', 100.0, []),
    'Sheep': Mob('a sheep', 0x00CF, 12, 'AI_Melee', 'Aggressor', 300, 0, 'Fire', 5.0, []),
    'SilverSerpent': Mob('a silver serpent', 0x005C, 216, 'AI_Melee', 'Closest', 7000, -7000, 'Fire', 100.0, ['Reptile', 'Snake']),
    'SilverbackGorilla': Mob('a silverback gorilla', 0x001D, 588, 'AI_Melee', 'Closest', 5000, -5000, 'Fire', 50.0, []),
    'SkeletalDragon': Mob('a skeletal dragon', 0x0068, 599, 'AI_NecroMage', 'Closest', 22500, -22500, 'Fire', 100.0, ['Reptile', 'DragonSlaying', 'Undead']),
    'SkeletalDrake': Mob('a skeletal drake', 0x0068, 400, 'AI_NecroMage', 'Closest', 15000, -15000, 'Fire', 75.0, []),
    'SkeletalKnight': Mob('a skeletal knight', 0x0093, 150, 'AI_Melee', 'Closest', 3000, -3000, 'Fire', 95.0, ['Undead']),
    'SkeletalLich': Mob('a skeletal lich', 0x0135, 1200, 'AI_NecroMage', 'Closest', 6000, -6000, 'Fire', 98.5, ['Undead']),
    'SkeletalMage': Mob('a skeletal mage', 0x0094, 60, 'AI_Mage', 'Closest', 3000, -3000, 'Fire', 55.0, ['Undead']),
    'Skeleton_0x0032': Mob('a skeleton', 0x0032, 48, 'AI_Melee', 'Closest', 450, -450, 'Fire', 55.0, ['Undead']),
    'Skeleton_0x0038': Mob('a skeleton', 0x0038, 48, 'AI_Melee', 'Closest', 450, -450, 'Fire', 55.0, ['Undead']),
    'SkitteringHopper': Mob('a skittering hopper', 0x012E, 45, 'AI_Melee', 'Aggressor', 300, -1, 'Fire', 60.0, []),
    'Skree': Mob('a skree', 0x02DD, 300, 'AI_Mystic', 'Closest', 0, -1, 'Cold', 117.9, []),
    'Slime': Mob('a slime', 0x0033, 19, 'AI_Melee', 'Closest', 300, -300, 'Fire', 34.0, []),
    'Slith': Mob('a slith', 0x02DE, 85, 'AI_Melee', 'Closest', 0, -1, 'Cold', 77.1, []),
    'Snake': Mob('a snake', 0x0034, 19, 'AI_Melee', 'Closest', 300, -300, 'Fire', 34.0, []),
    'SnowElemental': Mob('a snow elemental', 0x00A3, 213, 'AI_Melee', 'Closest', 5000, -5000, 'Fire', 100.0, []),
    'SnowLeopard_0x0040': Mob('a snow leopard', 0x0040, 48, 'AI_Melee', 'Aggressor', 450, 0, 'Fire', 50.0, []),
    'SnowLeopard_0x0041': Mob('a snow leopard', 0x0041, 48, 'AI_Melee', 'Aggressor', 450, 0, 'Fire', 50.0, []),
    'SpectralArmour': Mob('spectral armour', 0x027D, 201, 'AI_Melee', 'Closest', 7000, -7000, 'Fire', 100.0, []),
    'Spectre': Mob('a spectre', 0x001A, 60, 'AI_Mage', 'Closest', 4000, -4000, 'Fire', 55.0, ['Undead']),
    'Spellbinder': Mob('a spectral spellbinder', 0x001A, 50, 'AI_Spellbinder', 'Aggressor', 2500, -2500, 'Fire', 50.0, []),
    'Squirrel': Mob('a squirrel', 0x0116, 50, 'AI_Melee', 'Aggressor', 0, 0, 'Fire', 4.0, []),
    'StoneGargoyle': Mob('a stone gargoyle', 0x0043, 165, 'AI_Melee', 'Closest', 4000, -4000, 'Cold', 100.0, []),
    'StoneHarpy': Mob('a stone harpy', 0x0049, 192, 'AI_Melee', 'Closest', 4500, -4500, 'Cold', 100.0, []),
    'StoneMonster_0x0056': Mob('Stone Monster', 0x0056, 155, 'AI_Mage', 'Closest', 8000, -8000, 'Fire', 70.0, []),
    'StoneMonster_0x02D2': Mob('Stone Monster', 0x02D2, 155, 'AI_Mage', 'Closest', 8000, -8000, 'Fire', 70.0, []),
    'StoneMonster_0x003B': Mob('Stone Monster', 0x003B, 155, 'AI_Mage', 'Closest', 8000, -8000, 'Fire', 70.0, []),
    'StoneMonster_0x0055': Mob('Stone Monster', 0x0055, 155, 'AI_Mage', 'Closest', 8000, -8000, 'Fire', 70.0, []),
    'StoneMonster_0x0136': Mob('Stone Monster', 0x0136, 155, 'AI_Mage', 'Closest', 8000, -8000, 'Fire', 70.0, []),
    'StoneMonster_0x0053': Mob('Stone Monster', 0x0053, 155, 'AI_Mage', 'Closest', 8000, -8000, 'Fire', 70.0, []),
    'StoneSlith': Mob('a stone slith', 0x02DE, 166, 'AI_Melee', 'Closest', 0, -1, 'Cold', 87.4, []),
    'StrongMongbat': Mob('a mongbat', 0x0027, 6, 'AI_Melee', 'Closest', 150, -150, 'Fire', 35.0, []),
    'StygianDrake': Mob('Stygian Drake', 0x058E, 510, 'AI_Mage', 'Closest', 5500, -5500, 'Cold', 100.0, []),
    'Succubus': Mob('a succubus', 0x0095, 353, 'AI_Mage', 'Closest', 24000, -24000, 'Cold', 90.0, []),
    'SwampTentacle': Mob('a swamp tentacle', 0x0042, 72, 'AI_Melee', 'Closest', 3000, -3000, 'Fire', 80.0, []),
    'TanglingRoots': Mob('a tangling root', 0x0008, 246, 'AI_Melee', 'Closest', 3000, -3000, 'Fire', 60.0, []),
    'TerathanAvenger': Mob('a terathan avenger', 0x0098, 372, 'AI_Mage', 'Closest', 15000, -15000, 'Fire', 100.0, []),
    'TerathanDrone': Mob('a terathan drone', 0x0047, 39, 'AI_Melee', 'Closest', 2000, -2000, 'Fire', 50.0, []),
    'TerathanMatriarch': Mob('a terathan matriarch', 0x0048, 243, 'AI_Mage', 'Closest', 10000, -10000, 'Fire', 80.0, []),
    'TerathanWarrior': Mob('a terathan warrior', 0x0046, 129, 'AI_Melee', 'Closest', 4000, -4000, 'Fire', 90.0, []),
    'TimberWolf': Mob('a timber wolf', 0x00E1, 48, 'AI_Melee', 'Aggressor', 450, -1, 'Fire', 60.0, []),
    'Titan': Mob('a titan', 0x004C, 351, 'AI_Mage', 'Closest', 11500, -11500, 'Cold', 50.0, []),
    'TormentedMinotaur': Mob('Tormented Minotaur', 0x0106, 4200, 'AI_Melee', 'Closest', 20000, -20000, 'Cold', 111.0, []),
    'ToxicElemental': Mob('an acid elemental', 0x009E, 213, 'AI_Mage', 'Closest', 10000, -10000, 'Poison', 90.0, []),
    'ToxicSlith': Mob('a toxic slith', 0x02DE, 215, 'AI_Melee', 'Closest', 0, -1, 'Fire', 95.1, []),
    'TrapdoorSpider': Mob('a trapdoor spider', 0x02E1, 144, 'AI_Melee', 'Closest', 0, -1, 'Physical', 94.6, []),
    'Treefellow': Mob('a treefellow', 0x012D, 132, 'AI_Melee', 'Evil', 500, 1500, 'Fire', 85.0, []),
    'TreefellowGuardian': Mob('a Treefellow Guardian', 0x012D, 900, 'AI_Mystic', 'Evil', 500, 1500, 'Fire', 85.0, []),
    'Triceratops': Mob('Triceratops', 0x0587, 1200, 'AI_Melee', 'Closest', 0, -1, 'Poison', 105.0, []),
    'Troglodyte': Mob('a troglodyte', 0x010B, 340, 'AI_Melee', 'Closest', 5000, -5000, 'Fire', 93.5, []),
    'Troll_0x0035': Mob('a troll', 0x0035, 123, 'AI_Melee', 'Closest', 3500, -3500, 'Poison', 70.0, ['Repond']),
    'Troll_0x0036': Mob('a troll', 0x0036, 123, 'AI_Melee', 'Closest', 3500, -3500, 'Poison', 70.0, ['Repond']),
    'TsukiWolf': Mob('a tsuki wolf', 0x00FA, 450, 'AI_Melee', 'Closest', 8500, -8500, 'Physical', 107.5, []),
    'UndeadGargoyle': Mob('an Undead Gargoyle', 0x02D2, 300, 'AI_Melee', 'Closest', 3500, -3500, 'Fire', 70.0, ['Undead']),
    'UndeadGuardian': Mob('an undead guardian', 0x02D2, 138, 'AI_Melee', 'Closest', 0, -1, 'Fire', 86.9, []),
    'UnfrozenMummy': Mob('an unfrozen mummy', 0x009B, 1500, 'AI_Mage', 'Closest', 25000, -25000, 'Fire', 100.0, []),
    'ValoriteElemental': Mob('a valorite elemental', 0x0070, 153, 'AI_Melee', 'Closest', 3500, -3500, 'Energy', 100.0, []),
    'VampireBat': Mob('a vampire bat', 0x013D, 66, 'AI_Melee', 'Closest', 1000, -1000, 'Fire', 55.0, []),
    'VeriteElemental': Mob('a verite elemental', 0x0071, 153, 'AI_Melee', 'Closest', 3500, -3500, 'Fire', 100.0, []),
    'Viscera': Mob('Viscera', 0x0307, 230, 'AI_Melee', 'Closest', 2000, -2000, 'Fire', 100.0, []),
    'VorpalBunny': Mob('a vorpal bunny', 0x00CD, 2000, 'AI_Melee', 'Aggressor', 1000, -1, 'Physical', 5.0, []),
    'WailingBanshee': Mob('a wailing banshee', 0x0136, 90, 'AI_Melee', 'Closest', 1500, -1500, 'Fire', 70.0, []),
    'Walrus': Mob('a walrus', 0x00DD, 17, 'AI_Melee', 'Aggressor', 150, 0, 'Fire', 29.0, []),
    'WandererOfTheVoid': Mob('a wanderer of the void', 0x013C, 400, 'AI_Mage', 'Closest', 20000, -20000, 'Fire', 70.0, []),
    'WaterElemental': Mob('a water elemental', 0x0010, 93, 'AI_Mage', 'Closest', 4500, -4500, 'Energy', 70.0, []),
    'WhippingVine': Mob('a whipping vine', 0x0008, 200, 'AI_Melee', 'Closest', 1000, -1000, 'Fire', 70.0, []),
    'WhiteWolf_0x0022': Mob('a white wolf', 0x0022, 48, 'AI_Melee', 'Aggressor', 450, 0, 'Fire', 60.0, []),
    'WhiteWolf_0x0025': Mob('a white wolf', 0x0025, 48, 'AI_Melee', 'Aggressor', 450, 0, 'Fire', 60.0, []),
    'WhiteWyrm_0x00B4': Mob('a white wyrm', 0x00B4, 456, 'AI_Mage', 'Closest', 18000, -18000, 'Fire', 100.0, ['Reptile', 'DragonSlaying']),
    'WhiteWyrm_0x0031': Mob('a white wyrm', 0x0031, 456, 'AI_Mage', 'Closest', 18000, -18000, 'Fire', 100.0, ['Reptile', 'DragonSlaying']),
    'Wight': Mob('a Wight', 0x00FC, 250, 'AI_NecroMage', 'Closest', 1500, -1500, 'Fire', 60.0, ['Undead']),
    'Wisp': Mob('a wisp', 0x003A, 135, 'AI_Mage', 'Aggressor', 4000, -1, 'Poison', 80.0, []),
    'WolfSpider': Mob('a Wolf spider', 0x02E0, 160, 'AI_Melee', 'Closest', 0, -1, 'Fire', 90.0, []),
    'Wraith': Mob('a wraith', 0x001A, 60, 'AI_Mage', 'Closest', 4000, -4000, 'Fire', 55.0, ['Undead']),
    'Wyvern': Mob('a wyvern', 0x003E, 141, 'AI_Melee', 'Closest', 4000, -4000, 'Cold', 80.0, ['Reptile', 'DragonSlaying']),
    'Yamandon': Mob('a yamandon', 0x00F9, 1800, 'AI_Melee', 'Closest', 22000, -22000, 'Cold', 132.5, []),
    'YomotsuElder': Mob('a yomotsu elder', 0x00FF, 900, 'AI_Melee', 'Closest', 12000, -12000, 'Energy', 130.0, []),
    'YomotsuPriest': Mob('a yomotsu priest', 0x00FD, 530, 'AI_Mage', 'Closest', 9000, -9000, 'Energy', 57.5, []),
    'YomotsuWarrior': Mob('a yomotsu warrior', 0x00F5, 530, 'AI_Melee', 'Closest', 4200, -4200, 'Energy', 107.5, []),
    'Zombie': Mob('a zombie', 0x0003, 42, 'AI_Melee', 'Closest', 600, -600, 'Fire', 50.0, ['Undead']),

    # ════════════════════════════════════════════════════════
    #  SUMMONS
    # ════════════════════════════════════════════════════════
    'SummonedAirElemental': Mob('an air elemental', 0x000D, 150, 'AI_Mage', 'Closest', 0, -1, 'Fire', 80.0, []),
    'SummonedEarthElemental': Mob('an earth elemental', 0x000E, 180, 'AI_Melee', 'Closest', 0, -1, 'Fire', 90.0, []),
    'SummonedWaterElemental': Mob('a water elemental', 0x0010, 165, 'AI_Mage', 'Closest', 0, -1, 'Fire', 85.0, []),
    'Barracoon': Mob('Barracoon the piper', 0x0190, 12000, 'AI_Mage', 'Closest', 22500, -22500, 'Physical', 122.7, ['Repond']),
    'Mephitis': Mob('Mephitis', 0x00AD, 12000, 'AI_Melee', 'Closest', 22500, -22500, 'Fire', 100.0, ['Arachnid']),
    'Rikktor': Mob('Rikktor', 0x00AC, 15000, 'AI_Melee', 'Closest', 22500, -22500, 'Cold', 123.9, ['Reptile']),
    'Semidar': Mob('Semidar', 0x00AE, 10000, 'AI_Mage', 'Closest', 24000, -24000, 'Cold', 105.0, ['Abyss']),
    'Neira': Mob('Neira the necromancer', 0x0191, 4800, 'AI_NecroMage', 'Closest', 22500, -22500, 'Energy', 100.0, ['Undead']),
    'LordOaks': Mob('Lord Oaks', 0x00AF, 12000, 'AI_Mage', 'Closest', 22500, 22500, 'Fire', 100.0, ['Fey']),
    'Serado': Mob('Serado the awakened', 0x00F9, 9000, 'AI_Melee', 'Closest', 22500, -22500, 'Physical', 70.0, []),
    'Harrower': Mob('The Harrower', 0x0092, 550, 'AI_Mage', 'Closest', 22500, -22500, 'Physical', 100.0, []),
    'TrueHarrower': Mob('The True Harrower', 0x030C, 550, 'AI_Mage', 'Closest', 22500, -22500, 'Physical', 100.0, []),
    'DreadHorn': Mob('a Dread Horn', 0x0101, 50000, 'AI_Melee', 'Closest', 32000, -32000, 'Physical', 90.0, ['Fey']),
    'LadyMelisande': Mob('Lady Melisande', 0x0102, 100000, 'AI_Mage', 'Closest', 25000, -25000, 'Physical', 105.0, ['Fey']),
    'ChiefParoxysmus': Mob('a chief paroxysmus', 0x0100, 50000, 'AI_Mage', 'Closest', 25000, -25000, 'Fire', 120.0, []),
    'MonstrousInterredGrizzle': Mob('a monstrous interred grizzle', 0x0103, 50000, 'AI_Melee', 'Closest', 24000, -24000, 'Poison', 116.9, []),
    'Travesty': Mob('Travesty', 0x0108, 35000, 'AI_OmniAI', 'Closest', 30000, -30000, 'Physical', 320.0, []),
    'Medusa': Mob('Medusa', 0x02D8, 60000, 'AI_Mage', 'Closest', 22000, -22000, 'Physical', 128.9, ['Reptile']),
    'SlasherOfVeils': Mob('The Slasher of Veils', 0x02E5, 65000, 'AI_Mage', 'Closest', 35000, -35000, 'Physical', 130.0, []),
    'StygianDragon': Mob('Stygian Dragon', 0x033A, 30000, 'AI_Mage', 'Closest', 15000, -15000, 'Cold', 117.7, ['Reptile', 'DragonSlaying']),
    'CrimsonDragon_boss': Mob('a crimson dragon', 0x00C5, 25000, 'AI_Mage', 'Closest', 20000, -20000, 'Cold', 128.0, ['Reptile', 'DragonSlaying']),
    'AbyssalInfernal': Mob('Abyssal Infernal', 0x02C9, 30000, 'AI_Mage', 'Closest', 28000, -28000, 'Poison', 120.0, []),
    'Navrey': Mob('Navrey Night-Eyes', 0x02DF, 35000, 'AI_Mage', 'Closest', 24000, -24000, 'Fire', 98.2, ['Arachnid', 'Spider']),
    'PrimevalLich': Mob('Primeval Lich', 0x033E, 30000, 'AI_NecroMage', 'Closest', 28000, -28000, 'Energy', 120.0, ['Undead']),
    'CorgulTheSoulbinder': Mob('Corgul the Soulbinder', 0x004C, 65000, 'AI_Melee', 'Closest', 25000, -25000, 'Physical', 120.0, []),
}

# Pre-built body-ID index for O(1) mob lookup
MOBSLIST_BY_BODY = {}
for _mob in MOBSLIST.values():
    _mob._name_normalized = "".join(_mob.name.split())
    MOBSLIST_BY_BODY.setdefault(_mob.body, []).append(_mob)

def mobs_in_range(mob_list, r):
    return [mob for mob in mob_list if Player.DistanceTo(mob) <= r]

def get_mob_real_hp(mob):
    # mob.Hits/HitsMax return a 0-25 bar ratio, not real HP.
    # Look up real max HP from MOBSLIST (cached); scale current via the bar ratio.
    # Returns (cur_hp, max_hp) or (None, None) if mob not in MOBSLIST.
    mobdata = get_mob_data(mob)
    if mobdata is None:
        return (None, None)
    real_max = mobdata.hp
    bar_max = mob.HitsMax
    if bar_max and bar_max > 0 and real_max > 0:
        cur = int(round(real_max * mob.Hits / float(bar_max)))
        return (cur, real_max)
    return (None, real_max)

_mob_data_cache = {}  # serial -> Mob entry or None (identity never changes)

def get_mob_data(mob):
    # Returns the MOBSLIST Mob entry for `mob` or None. Cached per serial.
    if mob is None:
        return None
    if mob.Serial in _mob_data_cache:
        return _mob_data_cache[mob.Serial]
    result = None
    for mobdata in MOBSLIST_BY_BODY.get(mob.MobileID, []):
        if mobdata._name_normalized == "".join(mob.Name.split()):
            result = mobdata
            break
    if len(_mob_data_cache) > 300:
        _mob_data_cache.clear()
    _mob_data_cache[mob.Serial] = result
    return result

def get_weakres(mob):
    """Elemental weakness of the mob ('Fire'/'Cold'/'Poison'/'Energy'/'Physical') or None."""
    m = get_mob_data(mob)
    return m.weakres if m else None

def get_mob_tier(mob):
    """Classify mob by real HP from MOBSLIST. Returns 'trash' / 'elite' / 'boss' / None.
    trash < 250 HP, elite 250-2999, boss >= 3000. Unknown mobs return None
    (callers should default to 'elite' behavior — conservative)."""
    m = get_mob_data(mob)
    if m is None or m.hp <= 0:
        return None
    if m.hp < sv.get('trash_hp_cap', 250):
        return 'trash'
    if m.hp >= sv.get('boss_hp_min', 3000):
        return 'boss'
    return 'elite'

def equipped_slayer():
    """Return the slayer category string from the equipped weapon/shield/spellbook, or None.
    Best-effort: scans item Properties for 'Slayer' substring."""
    layers = ('FirstValid', 'RightHand', 'LeftHand')
    for layer in layers:
        try:
            item = Player.GetItemOnLayer(layer)
        except Exception:
            continue
        if not item:
            continue
        try:
            for p in item.Properties:
                ps = str(p)
                if 'Slayer' in ps:
                    return ps.strip()
        except Exception:
            pass
    return None

# Nuke cascade flag — set after Evil Omen / Corpse Skin lands; biases next cast
# to the strongest enabled nuke for a short window.
nuke_cascade_until = 0.0

# Debuff expiry tracking — parallel to the debuff_* timers, so the status
# overlay can show remaining seconds (Timer has no "remaining" query).
debuff_expiry = {}
DEBUFF_BADGES = {
    'debuff_evil_omen':   'EO',
    'debuff_curse':       'CU',
    'debuff_corpse_skin': 'CS',
    'debuff_strangle':    'STR',
    'debuff_mind_rot':    'MRot',
    'debuff_poison':      'PSN',
    'debuff_paralyze':    'PAR',
    'debuff_sleep':       'SLP',
    'debuff_mass_sleep':  'MSLP',
    'debuff_mana_vampire':'MV',
}

def track_debuff(key, ms):
    Timer.Create(key, ms)
    debuff_expiry[key] = time.time() + ms / 1000.0

def debuff_status_line():
    """Remaining seconds of tracked debuffs on the current debuff target, e.g. 'EO:4 CS:18'."""
    now = time.time()
    parts = []
    for key, badge in DEBUFF_BADGES.items():
        rem = debuff_expiry.get(key, 0) - now
        if rem > 1:
            parts.append("%s:%d" % (badge, int(rem)))
    return " ".join(parts)

def nuke_cascade_active():
    return time.time() < nuke_cascade_until

def is_under_attack():
    """True when HP is below the urgent-buff threshold (urgent_buff_threshold %).
    Used to bypass the 120s re-cast throttle on protective buffs."""
    thr = sv.get('urgent_buff_threshold', 60) / 100.0
    if Player.HitsMax <= 0:
        return False
    return Player.Hits < Player.HitsMax * thr

def low_mana():
    """True when low-mana mode is enabled and mana is below low_mana_threshold %.
    While active: debuffs are skipped and expensive nukes (>14 base mana) are avoided."""
    if sv.get('use_low_mana_mode', 1) == 0:
        return False
    if Player.ManaMax <= 0:
        return False
    return Player.Mana < Player.ManaMax * (sv.get('low_mana_threshold', 25) / 100.0)

def release_disturbed_cast_for_heal():
    """Check promptly for a server-confirmed interruption after taking damage.

    Damage alone is not enough to unlock casting: doing so can race the server
    and cause an "already casting" loop.
    """
    global last_player_hits
    current_hits = Player.Hits
    took_damage = current_hits < last_player_hits
    last_player_hits = current_hits
    if not took_damage or sv['use_heal'] == 0 or Player.HitsMax <= 0:
        return
    heal_at = Player.HitsMax * (sv['heal_threshold'] / 100.0)
    if current_hits <= heal_at and Timer.Check('spells') == True:
        Misc.Pause(25)
        apply_cast_failure(consume_cast_failure(), True)

_healer_cache = {}  # serial -> True if red healer (skip permanently)

def mobs_list(rng):
    # Always scan current mobiles. Property-heavy healer/rare checks remain cached.
    fil = Mobiles.Filter()
    fil.Enabled = True
    fil.RangeMax = rng
    if sv['attack_blues'] == 0:
        fil.Notorieties = List[Byte](bytes([3, 4, 5, 6]))
    else:
        fil.Notorieties = List[Byte](bytes([1, 3, 4, 5, 6]))
    fil.IsGhost = False
    fil.CheckIgnoreObject = True
    fil.IgnorePets = True
    fil.Friend = False
    mobs = Mobiles.ApplyFilter(fil)
    mobsTemp = []
    check_rares = sv['use_checkforraremobs'] == 1 and Timer.Check("rarecheck") == False
    if check_rares:
        # Throttle the property scan even when no rare is found.
        Timer.Create("rarecheck", 1000)
    for mob in mobs:
        # A filter result can disappear before its properties are inspected.
        mob = Mobiles.FindBySerial(mob.Serial)
        if mob is None:
            continue
        exclude = False
        rejected_position = los_rejected_positions.get(mob.Serial)
        if rejected_position is not None:
            current_position = (
                Player.Position.X, Player.Position.Y, Player.Position.Z,
                mob.Position.X, mob.Position.Y, mob.Position.Z)
            if current_position == rejected_position:
                exclude = True
            else:
                # Player or mob moved: the server LOS may now be different.
                los_rejected_positions.pop(mob.Serial, None)
        candidates = MOBSLIST_BY_BODY.get(mob.MobileID, [])
        if candidates:
            norm = "".join((mob.Name or "").split())
            for mobdata in candidates:
                if mobdata._name_normalized == norm:
                    if Timer.Check("mobslistspam") == False and sv['use_mobinfo'] == 1:
                        Player.HeadMessage(60, "Info: %s" % mobdata.name)
                        Player.HeadMessage(60, "HP: %s  Karma: %s  WeakRes: %s  Wrest: %s" % (
                            mobdata.hp, mobdata.karma, mobdata.weakres, mobdata.wrestling))
                        Timer.Create("mobslistspam", 1500)
                    if (sv.get('use_slayer_announce', 1) == 1
                            and Timer.Check("slayerspam") == False
                            and slayer_matches(mob)):
                        Player.HeadMessage(53, "Slayer match: %s" % mobdata.name)
                        Mobiles.Message(mob, 53, "[SLAYER]")
                        Timer.Create("slayerspam", 4000)
                    if mobdata.karma >= 0 and sv['attack_blues'] == 0:
                        exclude = True
                    break

        if check_rares:
            if Mobiles.GetPropStringByIndex(mob, 0) == "Rare" or Mobiles.GetPropStringByIndex(mob, 1) == "Rare":
                Player.HeadMessage(20, "Rare {} around!".format(mob.Name))
                Mobiles.Message(mob, 20, 'Rare!')
                Mobiles.Message(mob, 15, "♥")
                Timer.Create("rarecheck", 2000)
                check_rares = False
                if sv['use_stopwarwhenrare'] == 1:
                    Player.SetWarMode(False)
                    Misc.ScriptStopAll(False)

        if mob.IsHuman and mob.Notoriety == 6 and sv['attack_red_humans'] == 0:
            if sv['use_messages'] == 1 and Timer.Check("reds") == False:
                Player.HeadMessage(40, "Ignore red: %s" % mob.Name)
                Timer.Create("reds", 3000)
            exclude = True
        if mob.Name in mobsToIgnore:
            exclude = True
        elif mob.Name in summonsToIgnore and mob.Notoriety == 6:
            exclude = True
        elif mob.MobileID in mobileIDsToIgnore:
            exclude = True
        elif mob.Serial in serialsToIgnore:
            exclude = True

        if not exclude:
            # Red healer check reads Properties (IPC) — do it once per serial
            if mob.Serial not in _healer_cache:
                is_healer = False
                if mob.Notoriety == 6:
                    for p in mob.Properties:
                        if "healer" in str(p):
                            is_healer = True
                            break
                if len(_healer_cache) > 300:
                    _healer_cache.clear()
                _healer_cache[mob.Serial] = is_healer
            if _healer_cache[mob.Serial]:
                exclude = True

        if not exclude:
            mobsTemp.append(mob)

    return mobsTemp

def mobs_in_line_of_sight(mobs, rng):
    """Return only candidates currently visible from the player."""
    if not mobs:
        return []
    fil = Mobiles.Filter()
    fil.Enabled = True
    fil.RangeMax = rng
    fil.CheckLineOfSight = True
    visible = Mobiles.ApplyFilter(fil)
    visible_serials = set(mob.Serial for mob in visible)
    return [mob for mob in mobs if mob.Serial in visible_serials]

def changelings_list():
    fil = Mobiles.Filter()
    fil.Enabled = True
    fil.RangeMax = 1
    fil.Notorieties = List[Byte](bytes([1]))
    fil.IsGhost = False
    fil.CheckIgnoreObject = False
    fil.CheckLineOfSight = True
    fil.IgnorePets = True
    fil.Friend = False
    mobs = Mobiles.ApplyFilter(fil)
    return [mob for mob in mobs if mob.Name == Player.Name]

def remember_offensive_target(target):
    """Remember exact positions so a server LOS rejection can be quarantined."""
    global last_offensive_target_state
    last_offensive_target_state = (
        target.Serial, time.time(),
        Player.Position.X, Player.Position.Y, Player.Position.Z,
        target.Position.X, target.Position.Y, target.Position.Z)

def execute_target_confirmed(target):
    """Send a mobile target and verify Razor consumed the open cursor."""
    if not Target.HasTarget() or target is None:
        return False
    serial = target.Serial if hasattr(target, 'Serial') else target
    Target.TargetExecute(serial)
    Misc.Pause(100)
    if Target.HasTarget():
        # Retry once with the live Mobile overload in case the original wrapper
        # was stale. A successful TargetExecute closes the local cursor.
        live_target = Mobiles.FindBySerial(serial)
        if live_target is not None:
            Target.TargetExecute(live_target)
            Misc.Pause(100)
    consumed = not Target.HasTarget()
    if not consumed:
        # Prevent another function later in this same loop from casting over
        # the still-open cursor. The main-loop barrier will resolve or cancel it.
        Timer.Create('spells', 250)
    return consumed

def target_current_visible_hostile(preferred=None):
    """Use an open cursor only on a hostile that is visible right now.

    A mobile can move after the spell starts. Prefer the originally selected
    target while it remains visible; otherwise retarget the nearest visible mob.
    """
    global last_target_wait_failure, last_target_wait_failure_kind
    if not Target.HasTarget():
        return None

    victims = mobs_in_line_of_sight(mobs_list(sv['attackrange']), sv['attackrange'])
    if sv['attack_blue_changelings'] == 1:
        for changeling in changelings_list():
            if not any(mob.Serial == changeling.Serial for mob in victims):
                victims.append(changeling)

    target = None
    if preferred is not None:
        for mob in victims:
            if mob.Serial == preferred.Serial:
                target = mob
                break
    if target is None and len(victims) > 0:
        target = min(victims, key=lambda mob: Player.DistanceTo(mob))
    if target is None:
        # The spell has already produced its cursor; cancelling here cannot
        # interrupt its cast and prevents an orphaned cursor from blocking combat.
        Target.Cancel()
        last_target_wait_failure = time.time()
        last_target_wait_failure_kind = "invalid_target"
        Timer.Create('spells', 250)
        return None

    remember_offensive_target(target)
    if execute_target_confirmed(target):
        return target

    # Never report a targeted cast as successful while its cursor is still up.
    Target.Cancel()
    last_target_wait_failure = time.time()
    last_target_wait_failure_kind = "invalid_target"
    Timer.Create('spells', 250)
    return None

##################################################################
# Cast speed helpers
# Mage/Necro/Mysticism: FC capped at 2
# Spellweaving:         FC capped at 4

def calc_castpause():
    # Even at maximum FCR, UOAlive needs a short post-target recovery before
    # accepting the next spell. 150ms caused intermittent "already casting".
    castpause = max(_cached_castpause, serverdelay, 250)
    return castpause

def calc_castspeed(spellcasttime):
    """Magery / Necromancy / Mysticism — FC cap 2."""
    fcmin = 250
    fc = min(2, _cached_fc)
    if Player.BuffsExist('Protection'):
        fc = _cached_fc - 2
    castspeed = spellcasttime - (fc * 250) + serverdelay + fcmin
    if castspeed < (serverdelay + fcmin):
        castspeed = serverdelay + fcmin
    return castspeed

def calc_castspeed_sw(spellcasttime):
    """Spellweaving — FC cap 4."""
    fcmin = 250
    fc = min(4, _cached_fc)
    if Player.BuffsExist('Protection'):
        fc = _cached_fc - 2
    castspeed = spellcasttime - (fc * 250) + serverdelay + fcmin
    if castspeed < (serverdelay + fcmin):
        castspeed = serverdelay + fcmin
    return castspeed

def classify_cast_failure_entries(entries):
    """Classify server rejection text, preferring a real spell interruption."""
    busy = False
    action_wait = False
    invalid_target = False
    unseen_target = False
    spell_cooldown = False
    for entry in entries:
        text = (entry.Text or "").lower()
        if "disturbed" in text or "fizzle" in text:
            return "interrupted"
        if "already casting a spell" in text:
            busy = True
        # "frozen and cannot move" commonly means the character attempted to
        # move while a spell was casting. It does not mean that cast failed.
        if "must wait to perform another action" in text:
            action_wait = True
        if ("must wait before trying again" in text or
                "already in effect" in text):
            spell_cooldown = True
        if "too far away" in text:
            invalid_target = True
        if ("cannot be seen" in text or "cannot see" in text or
                "can't see" in text or "no line of sight" in text):
            unseen_target = True
    if busy:
        return "busy"
    if unseen_target:
        return "unseen_target"
    if invalid_target:
        return "invalid_target"
    if spell_cooldown:
        return "spell_cooldown"
    if action_wait:
        return "action_wait"
    return None

def cast_failure_since(pre_cast_time):
    """Return the strongest cast failure reported since this cast began."""
    if last_target_wait_failure >= pre_cast_time:
        return last_target_wait_failure_kind or "failed"
    try:
        entries = Journal.GetJournalEntry(pre_cast_time)
    except Exception:
        # A concurrent global Journal.Clear must not stop combat.
        return None
    return classify_cast_failure_entries(entries)

def did_fizzle(pre_cast_time):
    """Return True if the server rejected or interrupted this cast."""
    return cast_failure_since(pre_cast_time) is not None

def consume_cast_failure():
    """Return the newest server cast-failure type, if any."""
    global last_cast_failure_check, last_cast_failure_signatures
    try:
        entries = Journal.GetJournalEntry(last_cast_failure_check)
    except Exception:
        # Razor can throw if another script clears/rotates the global journal.
        # Reset to "now" so old lines are neither replayed nor fatal.
        last_cast_failure_check = time.time()
        last_cast_failure_signatures = set()
        return None

    new_entries = []
    for entry in entries:
        signature = (entry.Timestamp, entry.Serial, entry.Text)
        if signature not in last_cast_failure_signatures:
            new_entries.append(entry)
    if entries:
        # Razor returns a .NET List; negative indexes can reach the raw .NET
        # indexer and throw ArgumentOutOfRangeException in IronPython.
        last_entry = entries[len(entries) - 1]
        last_cast_failure_check = last_entry.Timestamp
        # Timestamp queries may include the boundary. Remember every entry at
        # that timestamp so none is replayed on the next poll.
        last_cast_failure_signatures = set(
            (entry.Timestamp, entry.Serial, entry.Text) for entry in entries
            if entry.Timestamp == last_cast_failure_check)
    return classify_cast_failure_entries(new_entries)

def recover_cast_state(reason):
    """Clear script/server cast state without requiring a script restart."""
    global last_cast_failure_check, last_cast_failure_signatures
    global cast_lock_since, nether_pending_since, pending_cast_cooldown
    global busy_failure_count, busy_failure_since, last_cast_recovery
    Target.Cancel()
    try:
        Spells.Interrupt()
    except Exception:
        pass
    # Interrupt performs an equip cycle, so respect its short action lock.
    Timer.Create('spells', 750)
    Timer.Create('netherblast_pending', 1)
    if pending_cast_cooldown is not None:
        Timer.Create(pending_cast_cooldown, 1)
        pending_cast_cooldown = None
    last_cast_failure_check = time.time()
    last_cast_failure_signatures = set()
    cast_lock_since = None
    nether_pending_since = None
    busy_failure_count = 0
    busy_failure_since = None
    last_cast_recovery = time.time()
    if sv.get('use_messages', 1) == 1:
        Player.HeadMessage(33, "Cast state recovered: %s" % reason)

def apply_cast_failure(failure, preserve_active=False):
    """Synchronize the local spell timer with the server cast state."""
    global pending_cast_cooldown, busy_failure_count, busy_failure_since
    global target_wait_extended_until
    global los_rejected_positions
    if failure is not None:
        # Any real server failure enables the longer target allowance for the
        # next casts, including untargeted buffs that failed outside a wait.
        target_wait_extended_until = time.time() + 15.0
    if failure is not None and pending_cast_cooldown is not None:
        # Untargeted buffs record their normal cooldown immediately. Roll it
        # back if the server rejected/interrupted that cast.
        Timer.Create(pending_cast_cooldown, 1)
        pending_cast_cooldown = None
    if failure == "interrupted":
        Timer.Create('spells', 1)
        return True
    if failure == "busy":
        now = time.time()
        if busy_failure_since is None or now - busy_failure_since > 6.0:
            busy_failure_since = now
            busy_failure_count = 0
        busy_failure_count += 1
        if busy_failure_count >= 2 and now - last_cast_recovery > 5.0:
            recover_cast_state("repeated server busy")
            return True
        # One busy response usually means the shard is still finishing the
        # previous cast. Give it a full second; do not hammer another spell.
        Timer.Create('spells', 1000)
        return True
    if failure == "action_wait":
        # Global journal action-lock lines can belong to attacks, items, pets,
        # or another script. They must not recreate a spell lock every loop.
        # Only a rejection consumed inside this cast's target wait delays retry.
        if not preserve_active:
            Timer.Create('spells', max(250, serverdelay))
        return True
    if failure == "unseen_target":
        if (last_offensive_target_state is not None and
                time.time() - last_offensive_target_state[1] <= 5.0):
            serial = last_offensive_target_state[0]
            los_rejected_positions[serial] = last_offensive_target_state[2:]
            if len(los_rejected_positions) > 100:
                los_rejected_positions.clear()
        Timer.Create('spells', 250)
        return True
    if failure == "invalid_target":
        Timer.Create('spells', 250)
        return True
    if failure == "spell_cooldown":
        Timer.Create('spells', 750)
        return True
    return False

def cast_state_watchdog():
    """Recover locks that outlive every legitimate cast in this script."""
    global cast_lock_since, nether_pending_since
    now = time.time()

    if Timer.Check('spells') == True:
        if cast_lock_since is None:
            cast_lock_since = now
        elif now - cast_lock_since > 6.0:
            recover_cast_state("spell lock")
            return
    else:
        cast_lock_since = None

    if Timer.Check('netherblast_pending') == True:
        if nether_pending_since is None:
            nether_pending_since = now
        elif now - nether_pending_since > 8.0:
            recover_cast_state("Nether Blast")
    else:
        nether_pending_since = None

def release_failed_cast_from_journal():
    """Synchronize the local cast timer when the server reports a failure."""
    global pending_cast_cooldown
    failure = consume_cast_failure()
    apply_cast_failure(failure, True)
    if failure is None and Timer.Check('spells') == False:
        # The cast completed its expected recovery window without an error.
        pending_cast_cooldown = None

def create_rollback_cooldown(name, duration):
    """Create a cooldown that is removed if this untargeted cast fails."""
    global pending_cast_cooldown
    Timer.Create(name, duration)
    pending_cast_cooldown = name

_razor_wait_for_target = Target.WaitForTarget

def wait_for_target_responsive(delay, noshow=False):
    """Wait through lag for a cursor, but abort immediately on a cast failure."""
    global last_target_wait_failure, last_target_wait_failure_kind
    global target_wait_extended_until
    # Spell cursor waits use a longer base timeout than item/skill waits. After
    # any failure/timeout, temporarily allow extra time for a lagging server.
    if delay >= 4000:
        if time.time() < target_wait_extended_until:
            delay = max(delay, 8000)
        else:
            delay = max(delay, 6000)
    deadline = time.time() + (delay / 1000.0)
    while True:
        remaining = int((deadline - time.time()) * 1000)
        if remaining <= 0:
            last_target_wait_failure = time.time()
            last_target_wait_failure_kind = "timeout"
            target_wait_extended_until = time.time() + 15.0
            Timer.Create('spells', 250)
            return False
        ready = _razor_wait_for_target(min(100, remaining), noshow)
        if ready or Target.HasTarget():
            last_target_wait_failure_kind = None
            return True
        failure = consume_cast_failure()
        if apply_cast_failure(failure):
            last_target_wait_failure = time.time()
            last_target_wait_failure_kind = failure
            target_wait_extended_until = time.time() + 15.0
            return False

def is_cardinal_or_diagonal(mob):
    """Returns True if mob is on the same X-axis, Y-axis, or a 45° diagonal from the player."""
    dx = abs(mob.Position.X - Player.Position.X)
    dy = abs(mob.Position.Y - Player.Position.Y)
    return dx == 0 or dy == 0 or dx == dy

def nether_blast_ready_for(mob, nearby_count):
    """True only when Nether Blast can start against this target now."""
    return (
        mob is not None and
        sv['use_nether_blast'] == 1 and
        Timer.Check('spells') == False and
        Timer.Check('netherblast') == False and
        Timer.Check('netherblast_pending') == False and
        not Player.Paralized and
        Player.Mana >= mana_cost(40) and
        real_skill_value('Mysticism') >= 90 and
        Player.DistanceTo(mob) <= 6 and
        (nearby_count != 1 or is_cardinal_or_diagonal(mob)))

def place_nether_blast_target(serial, x, y, z):
    """Target a living mob, or its saved ground tile if it died mid-cast."""
    live_target = Mobiles.FindBySerial(serial)
    if live_target is not None and live_target.Hits > 0:
        Target.TargetExecute(live_target)
        return False
    Target.TargetExecute(x, y, z)
    return True

_DIRECTION_ARROWS = {
    "N": "▲", "S": "▼", "E": "►", "W": "◄",
    "NE": "↗", "NW": "↖", "SE": "↘", "SW": "↙",
}

def nether_blast_move_hint(mob):
    """Return (direction_label, target_x, target_y) for the nearest aligned tile.
    Finds the closest tile (by Chebyshev/UO steps) on any of the 4 axis lines
    through the mob — N/S, E/W, NE/SW diagonal, NW/SE diagonal."""
    px = Player.Position.X
    py = Player.Position.Y
    mx = mob.Position.X
    my = mob.Position.Y

    candidates = []

    def try_tile(tx, ty):
        d = max(abs(tx - px), abs(ty - py))   # Chebyshev = UO diagonal steps
        ns = "N" if ty < py else ("S" if ty > py else "")
        ew = "E" if tx > px else ("W" if tx < px else "")
        label = (ns + ew) or "?"
        candidates.append((d, tx, ty, label))

    # 1. Same column as mob (player moves E or W)
    try_tile(mx, py)
    # 2. Same row as mob (player moves N or S)
    try_tile(px, my)
    # 3. NE/SW diagonal through mob: y − x = my − mx
    #    Perpendicular projection of player onto this line, rounded to tile
    c = my - mx
    t = int(round((px + py - c) / 2.0))
    try_tile(t, t + c)
    # 4. NW/SE diagonal through mob: y + x = my + mx
    s = mx + my
    t = int(round((s + px - py) / 2.0))
    try_tile(t, s - t)

    candidates.sort()
    _, tx, ty, label = candidates[0]
    return label, tx, ty

##################################################################
# Nether Blast positioning aids (v0.6)
# 1) Ground markers on valid casting tiles (fake item packets, client-only)
# 2) Auto-move to the nearest valid tile via pathfinding

_NB_MARKER_BASE   = 0x7FEE0000   # fake serial range, never collides with real objects
_NB_MARKER_GRAPHIC = 0x1F14      # recall rune — small, flat, visible
_NB_MARKER_HUE    = 66           # green
_nb_marker_count  = 0

def _nb_marker_packet(serial, graphic, x, y, z, hue):
    """Packet 0xF3 — spawn a client-side ghost item at a world tile."""
    b = bytearray(26)
    b[0] = 0xF3
    b[2] = 0x01                       # count = 1
    b[3] = 0x00                       # datatype: item
    b[4] = (serial >> 24) & 0xFF; b[5] = (serial >> 16) & 0xFF
    b[6] = (serial >> 8) & 0xFF;  b[7] = serial & 0xFF
    b[8] = (graphic >> 8) & 0xFF; b[9] = graphic & 0xFF
    b[12] = 0x01                      # amount = 1
    b[14] = 0x01
    b[15] = (x >> 8) & 0xFF; b[16] = x & 0xFF
    b[17] = (y >> 8) & 0xFF; b[18] = y & 0xFF
    b[19] = z & 0xFF
    b[21] = (hue >> 8) & 0xFF; b[22] = hue & 0xFF
    return bytes(b)

def nb_clear_tiles():
    """Remove all ground markers (packet 0x1D per fake serial)."""
    global _nb_marker_count
    for i in range(_nb_marker_count):
        serial = _NB_MARKER_BASE + i
        pkt = bytes(bytearray([0x1D,
            (serial >> 24) & 0xFF, (serial >> 16) & 0xFF,
            (serial >> 8) & 0xFF, serial & 0xFF]))
        PacketLogger.SendToClient(List[Byte](pkt))
    _nb_marker_count = 0

def _nb_valid_tiles(mob):
    """All tiles on the 4 lines through the mob, within NB range (6) of the mob
    and within 6 tiles of the player. Excludes mob + player tiles."""
    mx, my = mob.Position.X, mob.Position.Y
    px, py = Player.Position.X, Player.Position.Y
    tiles = []
    for ddx, ddy in ((1,0), (0,1), (1,1), (1,-1)):
        for sign in (1, -1):
            for dist in range(1, 7):
                tx = mx + ddx * dist * sign
                ty = my + ddy * dist * sign
                if (tx, ty) == (px, py):
                    continue
                if max(abs(tx - px), abs(ty - py)) <= 6:
                    tiles.append((tx, ty))
    return tiles

def _tile_z(x, y):
    """Terrain height at a tile — a wrong Z renders the marker visually shifted
    along the screen diagonal (UO iso view)."""
    try:
        return Statics.GetLandZ(x, y, Player.Map)
    except Exception:
        return Player.Position.Z

def nb_show_tiles(mob):
    """Ground-mark valid NB casting tiles around the mob. Throttled; client-only."""
    global _nb_marker_count
    if Timer.Check('nb_tiles') == True:
        return
    Timer.Create('nb_tiles', 900)
    nb_clear_tiles()
    for i, (tx, ty) in enumerate(_nb_valid_tiles(mob)[:32]):
        pkt = _nb_marker_packet(_NB_MARKER_BASE + i, _NB_MARKER_GRAPHIC, tx, ty, _tile_z(tx, ty), _NB_MARKER_HUE)
        PacketLogger.SendToClient(List[Byte](pkt))
        _nb_marker_count = i + 1

def nb_auto_move(mob):
    """Walk to the nearest valid NB tile when misaligned. Safety gates:
    no move while casting, poisoned, bleeding, or below nb_move_hp_min % HP."""
    if Timer.Check('nb_move') == True or Timer.Check('spells') == True:
        return
    if is_cardinal_or_diagonal(mob):
        return
    if Player.Poisoned or Player.BuffsExist('Bleed') or Player.Paralized:
        return
    if Player.Hits < Player.HitsMax * (sv.get('nb_move_hp_min', 50) / 100.0):
        return
    label, tx, ty = nether_blast_move_hint(mob)
    # Hint tile must still be inside NB cast range of the mob
    if max(abs(tx - mob.Position.X), abs(ty - mob.Position.Y)) > 6:
        return
    Timer.Create('nb_move', 1500)
    if sv['use_messages'] == 1:
        Player.HeadMessage(53, "NB move %s -> (%d,%d)" % (label, tx, ty))
    r = PathFinding.Route()
    r.X = tx
    r.Y = ty
    r.MaxRetry = 1
    r.StopIfStuck = True
    PathFinding.Go(r)

def refresh_gear_cache():
    """Refresh LMC/LRC/FC values — call on gear change."""
    global lmc, lrc, _cached_fc, _cached_fcr, _cached_castpause, _cached_slayer
    lmc             = (min(40, Player.LowerManaCost)) / 100
    lrc             = Player.SumAttribute("Lower Reagent Cost")
    _cached_fc      = Player.FasterCasting
    _cached_fcr     = min(6, Player.FasterCastRecovery)
    _cached_castpause = max(((6 - _cached_fcr) * 250) + serverdelay, serverdelay)
    _cached_slayer  = equipped_slayer()
    refresh_slayer_books()

_cached_slayer = None

# Slayer category -> list of mob 'slayers' tags that match.
# (Only the common groupings — extend as needed.)
SLAYER_GROUPS = {
    'Reptile':     ['Reptile', 'DragonSlaying', 'Snake', 'Lizardman'],
    'Dragon':      ['DragonSlaying', 'Reptile'],
    'Repond':      ['Repond'],
    'Fey':         ['Fey'],
    'Undead':      ['Undead'],
    'Elemental':   ['Elemental'],
    'Demon':       ['Demon'],
    'Arachnid':    ['Arachnid'],
}

def slayer_matches(mob):
    """Returns True if the equipped slayer matches any tag in this mob's slayers list."""
    if not _cached_slayer:
        return False
    m = get_mob_data(mob)
    if not m or not m.slayers:
        return False
    # Best-effort: substring match equipped-slayer string against group keys.
    for group, tags in SLAYER_GROUPS.items():
        if group in _cached_slayer:
            for tag in tags:
                if tag in m.slayers:
                    return True
    return False

##################################################################
# Slayer spellbook auto-swap (v0.7)
# Registry of slayer spellbooks in backpack; auto-equip the one matching the
# current target's MOBSLIST slayers. Manual swaps come from the integrated
# Mage GUMP section via the "slayer_swap_request" shared value.

SPELLBOOK_IDS = [0x0EFA, 0x2253, 0x2D50, 0x2D9D]  # Magery, Necro, SW, Mysticism
_slayer_books = {}    # group -> serial
_default_book = None  # serial of the non-slayer (baseline) book

def _hand_layers():
    return ('LeftHand', 'RightHand')

def _equipped_book():
    """Returns (item, layer) of the currently equipped spellbook, or (None, None)."""
    for layer in _hand_layers():
        it = Player.GetItemOnLayer(layer)
        if it and it.ItemID in SPELLBOOK_IDS:
            return it, layer
    return None, None

def _book_slayer_group(item):
    """Slayer group of a spellbook via its Properties, or None if no slayer."""
    try:
        for p in item.Properties:
            ps = str(p).lower()
            if 'slayer' in ps or 'slaying' in ps or 'silver' == ps.strip():
                for group in SLAYER_GROUPS:
                    if group.lower() in ps:
                        return group
                if 'silver' in ps:  # Silver = undead slayer
                    return 'Undead'
    except Exception:
        pass
    return None

def refresh_slayer_books():
    """Scan backpack + hands for spellbooks; build slayer registry. Called on gearcache timer."""
    global _default_book
    _slayer_books.clear()
    _default_book = None
    books = []
    for bid in SPELLBOOK_IDS:
        found = Items.FindAllByID(bid, -1, Player.Backpack.Serial, 2)
        if found:
            books.extend(found)
    eq, _ = _equipped_book()
    if eq:
        books.append(eq)
    for book in books:
        group = _book_slayer_group(book)
        if group:
            _slayer_books[group] = book.Serial
        elif _default_book is None and book.ItemID == 0x0EFA:
            _default_book = book.Serial

def _equip_book(serial):
    """Equip spellbook by serial; unequips current book first. Blocks ~1.2s."""
    cur, cur_layer = _equipped_book()
    if cur and cur.Serial == serial:
        return
    if cur:
        Player.UnEquipItemByLayer(cur_layer)
        Misc.Pause(600)
    Player.EquipItem(serial)
    Misc.Pause(600)
    # Equipping uses the server action lock. Do not cast during its remainder.
    Timer.Create('spells', 750)

def _target_slayer_group(mob):
    """Best slayer group in registry for this mob, or None."""
    m = get_mob_data(mob)
    if not m or not m.slayers:
        return None
    for group, tags in SLAYER_GROUPS.items():
        if group in _slayer_books:
            for tag in tags:
                if tag in m.slayers:
                    return group
    return None

def process_slayer_swap(target=None):
    """Manual swap requests (from Mage GUMP) + auto-swap to match target.
    Never swaps mid-cast."""
    if Timer.Check('spells') == True or Player.Paralized:
        return
    # Manual request — always honored, even with auto-swap off
    req = Misc.ReadSharedValue("slayer_swap_request")
    if req and req != 0:
        Misc.SetSharedValue("slayer_swap_request", 0)
        if sv['use_messages'] == 1:
            Player.HeadMessage(53, "Swap book (manual)")
        _equip_book(req)
        Timer.Create('slayer_swap', 3000)  # manual choice sticks for a moment
        return
    # Auto-swap
    if sv.get('use_slayer_autoswap', 0) != 1 or target is None:
        return
    if Timer.Check('slayer_swap') == True:
        return
    group = _target_slayer_group(target)
    want = _slayer_books.get(group) if group else _default_book
    if not want:
        return
    cur, _ = _equipped_book()
    if cur and cur.Serial == want:
        return
    Timer.Create('slayer_swap', 2000)
    if sv['use_messages'] == 1:
        Player.HeadMessage(53, "Swap book: %s" % (group if group else "default"))
    _equip_book(want)
    refresh_gear_cache()  # slayer announce cache must follow the new book

##################################################################
# Utility functions

def longalarm():
    for i in range(0, 5):
        winsound.Beep(1000, 300)
        winsound.Beep(1000, 800)

def legendarycheck():
    if sv['use_checkforlegendaries'] == 1:
        if Journal.Search("you sense a legendary") or Journal.Search("senses a legendary"):
            Player.HeadMessage(20, "Legendary pet around!")
            Player.HeadMessage(20, "Legendary pet around!")
            longalarm()
        elif Journal.Search("a curious creature apparates nearby"):
            Player.HeadMessage(40, "Astral Pet around!")
            longalarm()

def trappedcrate():
    if (sv['use_trappedcrate'] == 0 or not Player.BuffsExist("Paralyze") or
            Timer.Check('trappedcrate') == True):
        return
    tc = Items.FindByID(0x0E7E, -1, Player.Backpack.Serial, 0, False)
    if tc:
        Player.HeadMessage(50, "Use trapped crate!")
        Items.UseItem(tc)
        Timer.Create('trappedcrate', 1000)
        Timer.Create('spells', 750)
    else:
        Player.HeadMessage(20, "No trapped crate!")

def dresslist():
    if sv['use_dresslist'] == 1 and Timer.Check('dress') == False:
        Dress.DressFStart()
        Timer.Create('dress', 2500)
        Timer.Create('spells', 750)

def check_townbuff():
    if sv['use_townbuff'] == 1 and Timer.Check("towncheck") == False:
        if not Player.BuffsExist("City Trade Deal Buff"):
            Player.HeadMessage(20, "NO Town Bonus!")
        Timer.Create("towncheck", 4000)

def check_arcanefocus():
    if sv['use_arcanefocus'] == 1 and Timer.Check("arcanecheck") == False:
        if not Items.BackpackCount(0x3155, 0):
            Player.HeadMessage(40, "NO ARCANE FOCUS!")
        Timer.Create("arcanecheck", 4000)

def check_bandages():
    if sv['use_bandages'] == 1 and Timer.Check("bandagecheck") == False:
        amt = Items.ContainerCount(Player.Backpack.Serial, 0x0E21, 0, False)
        if amt < 50:
            Player.HeadMessage(30, "Warning: %s bandages left" % amt)
        Timer.Create("bandagecheck", 4000)

def checkweight():
    if sv['use_bagofsending'] == 1:
        bag = Items.FindByName("a bag of sending", -1, Player.Backpack.Serial, 0, False)
        if not bag:
            if Timer.Check("bagofsending") == False:
                Player.HeadMessage(20, "NO Bag of Sending!")
                Timer.Create("bagofsending", 10000)
        else:
            if Player.Weight >= Player.MaxWeight * 0.95:
                gold = Items.FindByID(0x0EED, 0, Player.Backpack.Serial, 1, False)
                if gold:
                    if sv['use_messages'] == 1:
                        Player.HeadMessage(10, "Overweight! Sending gold...")
                    Items.UseItem(bag)
                    if wait_for_target_responsive(4000, True):
                        Target.TargetExecute(gold)
                    Timer.Create('spells', 750)
                    Misc.Pause(100)
            if Timer.Check("bagofsending") == False:
                charges = Items.GetPropValue(bag, "Charges")
                if charges < 4:
                    Player.HeadMessage(30, "Bag of Sending: %i charges left!" % charges)
                Timer.Create("bagofsending", 10000)

##################################################################
# Heal / Cure / Buff

def auto_heal():
    """Heal/Greater Heal based on HP threshold. """
    if sv['use_heal'] == 0 or Player.Paralized or Player.Poisoned:
        return False
    if Timer.Check('spells') == True:
        return False
    threshold = sv['heal_threshold'] / 100.0
    if Player.Hits > Player.HitsMax * threshold:
        return False
    # Greater Heal only when below 50% HP; otherwise use the smaller Heal
    if Player.Hits <= Player.HitsMax * 0.5 and Player.Mana >= mana_cost(20) and skill_value('Magery') >= 60:
        if sv['use_cleansingwinds'] == 1:
            if sv['use_messages'] == 1:
                Player.HeadMessage(68, "Cleansing Winds (cure)!")
            pre_cast = time.time()
            Spells.CastMysticism("Cleansing Winds")
        else:
            if sv['use_messages'] == 1:
                Player.HeadMessage(68, "Greater Heal!")
            pre_cast = time.time()
            Spells.CastMagery("Greater Heal")
        wait_for_target_responsive(4000, True)
        Target.TargetExecute(Player.Serial)
        if not did_fizzle(pre_cast):
            Timer.Create('spells', calc_castpause())
        return True
    elif Player.Mana >= mana_cost(4):
#        if sv['use_cleansingwinds'] == 1:
#            if sv['use_messages'] == 1:
#                Player.HeadMessage(68, "Cleansing Winds (cure)!")
#            pre_cast = time.time()
#            Spells.CastMysticism("Cleansing Winds")
#        else:
        if sv['use_messages'] == 1:
            Player.HeadMessage(68, "Heal!")
        pre_cast = time.time()
        Spells.CastMagery("Heal")
        wait_for_target_responsive(4000, True)
        Target.TargetExecute(Player.Serial)
        if not did_fizzle(pre_cast):
            Timer.Create('spells', calc_castpause())
        return True
    return False

def auto_cure():
    """Cure poisoned player in priority order: Cure, Arch Cure, Cleansing Winds."""
    if not Player.Poisoned:
        return False
    if Timer.Check('spells') == True or Player.Paralized:
        return False

    # Emergency Cure is always allowed, independent of the use_cure toggle.
    if Player.Hits <= Player.HitsMax * 0.5 and Player.Mana >= mana_cost(9):
        if sv['use_messages'] == 1:
            Player.HeadMessage(68, "Cure!")
        pre_cast = time.time()
        Spells.CastMagery("Cure")
        wait_for_target_responsive(4000, True)
        Target.TargetExecute(Player.Serial)
        if not did_fizzle(pre_cast):
            Timer.Create('spells', calc_castpause())
        return True

    # Arch Cure (C6): cures all poison types including Greater and Deadly.
    if sv['use_cure'] == 1 and Player.Mana >= mana_cost(20) and skill_value('Magery') >= 50:
        if sv['use_messages'] == 1:
            Player.HeadMessage(68, "Arch Cure!")
        pre_cast = time.time()
        Spells.CastMagery("Arch Cure")
        wait_for_target_responsive(4000, True)
        Target.TargetExecute(Player.Serial)
        if not did_fizzle(pre_cast):
            Timer.Create('spells', calc_castpause())
        return True

    # Cleansing Winds is the final fallback and also removes many debuffs.
    if sv['use_cleansingwinds'] == 1 and Player.Mana >= mana_cost(20) and skill_value('Mysticism') >= 51:
        if sv['use_messages'] == 1:
            Player.HeadMessage(68, "Cleansing Winds (cure)!")
        pre_cast = time.time()
        Spells.CastMysticism("Cleansing Winds")
        wait_for_target_responsive(4000, True)
        Target.TargetExecute(Player.Serial)
        if not did_fizzle(pre_cast):
            Timer.Create('spells', calc_castpause())
        return True
    return False

def cleansing_winds():
    """Cast Cleansing Winds when player is cursed or has harmful debuffs."""
    if sv['use_cleansingwinds'] == 0 or Timer.Check('spells') == True or Player.Paralized:
        return False
    if Player.Mana < mana_cost(20) or skill_value('Mysticism') < 51:
        return False
    cursed = (Player.BuffsExist("Curse") or Player.BuffsExist("Evil Omen") or
              Player.BuffsExist("Corpse Skin") or Player.BuffsExist("Strangle") or
              Player.BuffsExist("Mind Rot") or Player.BuffsExist("Paralyze") or
              Player.BuffsExist("Bleed"))
    if cursed:
        if sv['use_messages'] == 1:
            Player.HeadMessage(68, "Cleansing Winds!")
        pre_cast = time.time()
        Spells.CastMysticism("Cleansing Winds")
        wait_for_target_responsive(4000, True)
        Target.TargetExecute(Player.Serial)
        if not did_fizzle(pre_cast):
            Timer.Create('spells', calc_castpause())
        return True
    return False

def keep_magic_reflect():
    if sv['use_magicreflect'] == 0 or Timer.Check('spells') == True or Player.Paralized:
        return
    if not Player.BuffsExist("Magic Reflection") and (Timer.Check("magicreflect") == False or is_under_attack()):
        if Player.Mana >= mana_cost(40) and skill_value('Magery') >= 17:
            if sv['use_messages'] == 1:
                Player.HeadMessage(68, "Magic Reflect!")
            Spells.CastMagery("Magic Reflection")
            Timer.Create('spells', calc_castspeed(2000) + calc_castpause())
            create_rollback_cooldown("magicreflect", 120000)

def keep_reactive_armor():
    if sv['use_reactivearmor'] == 0 or Timer.Check('spells') == True or Player.Paralized:
        return
    if not Player.BuffsExist("Reactive Armor") and (Timer.Check("reactivearmor") == False or is_under_attack()):
        if Player.Mana >= mana_cost(4):
            if sv['use_messages'] == 1:
                Player.HeadMessage(68, "Reactive Armor!")
            Spells.CastMagery("Reactive Armor")
            Timer.Create('spells', calc_castspeed(1000) + calc_castpause())
            create_rollback_cooldown("reactivearmor", 120000)

def keep_protection():
    if sv['use_protection'] == 0 or Timer.Check('spells') == True or Player.Paralized:
        return
    if not Player.BuffsExist("Protection") and Timer.Check("protection") == False:
        if Player.Mana >= mana_cost(11):
            if sv['use_messages'] == 1:
                Player.HeadMessage(68, "Protection!")
            Spells.CastMagery("Protection")
            Timer.Create('spells', calc_castspeed(1250) + calc_castpause())
            create_rollback_cooldown("protection", 120000)

def keep_bless():
    """Self-cast Bless (Magery C3) — +10 to all stats. Re-cast on expiry."""
    if sv['use_bless'] == 0 or Timer.Check('spells') == True or Player.Paralized:
        return
    if Player.BuffsExist("Bless") or Timer.Check("bless") == True:
        return
    if Player.Mana >= mana_cost(5) and skill_value('Magery') >= 22:
        if sv['use_messages'] == 1:
            Player.HeadMessage(68, "Bless!")
        pre_cast = time.time()
        Spells.CastMagery("Bless")
        wait_for_target_responsive(4000, True)
        Target.TargetExecute(Player.Serial)
        if not did_fizzle(pre_cast):
            Timer.Create('spells', calc_castpause())
            # Bless lasts ~90-120s. Re-check after 60s to avoid spamming.
            Timer.Create("bless", 60000)

def bless_pets():
    """Bless each pet on a per-pet timer. Pet buffs aren't visible to the client,
    so we don't try to detect them — fixed 144s re-cast per pet."""
    if sv['use_bless_pets'] == 0 or Timer.Check('spells') == True or Player.Paralized:
        return
    if Player.Mana < mana_cost(5) or skill_value('Magery') < 22:
        return
    for pet in Player.Pets:
        bls_key = 'pet_bless_%d' % pet.Serial
        if Timer.Check(bls_key) == True:
            continue
        if sv['use_messages'] == 1:
            Player.HeadMessage(68, "Bless: %s!" % pet.Name)
        pre_cast = time.time()
        Spells.CastMagery("Bless")
        wait_for_target_responsive(4000, True)
        Target.TargetExecute(pet)
        if not did_fizzle(pre_cast):
            Timer.Create('spells', calc_castpause())
            Timer.Create(bls_key, 144000)
        return

def attune_weapon():
    if sv['use_attuneweapon'] == 0 or Timer.Check('spells') == True or Player.Paralized:
        return
    if not Player.BuffsExist("Attunement", True) and Timer.Check("attuneweapon") == False:
        if Player.Mana >= mana_cost(24):
            if sv['use_messages'] == 1:
                Player.HeadMessage(68, "Attune Weapon!")
            Spells.CastSpellweaving("Attune Weapon")
            Timer.Create('spells', calc_castspeed_sw(1000) + calc_castpause())
            create_rollback_cooldown("attuneweapon", 120000)

def gift_of_life():
    if sv['use_giftoflife'] == 0 or Timer.Check('spells') == True or Player.Paralized:
        return
    if not Player.BuffsExist("Gift Of Life"):
        if Player.Mana >= mana_cost(70) and skill_value('Spellweaving') >= 80:
            if sv['use_messages'] == 1:
                Player.HeadMessage(68, "Gift of Life!")
            pre_cast = time.time()
            Spells.CastSpellweaving("Gift of Life")
            wait_for_target_responsive(4000, True)
            Target.Self()
            if not did_fizzle(pre_cast):
                Timer.Create('spells', calc_castpause())


def gift_of_renewal():
    """SW: Gift of Renewal — healing over time buff on self. 180s cooldown."""
    if sv['use_giftofrenewal'] == 0 or Timer.Check('spells') == True or Player.Paralized:
        return
    if not Player.BuffsExist("Gift Of Renewal") and Timer.Check("giftofrenewal") == False:
        if Player.Mana >= mana_cost(24):
            if sv['use_messages'] == 1:
                Player.HeadMessage(68, "Gift of Renewal!")
            Timer.Create("giftofrenewal", 180000)
            pre_cast = time.time()
            Spells.CastSpellweaving("Gift of Renewal")
            target_ready = wait_for_target_responsive(4000, True)
            if target_ready:
                Target.Self()
                Misc.Pause(max(250, serverdelay))
            failure = cast_failure_since(pre_cast)
            if target_ready and failure is None:
                Timer.Create('spells', calc_castpause())
                Timer.Create("giftofrenewal", 180000)
            elif failure == "spell_cooldown":
                Timer.Create("giftofrenewal", 180000)

def keep_mana_shield():
    """Spellweaving mastery: converts damage received into mana loss. Keep active."""
    if sv['use_mana_shield'] == 0 or Timer.Check('spells') == True or Player.Paralized:
        return
    if not Player.BuffsExist("Mana Shield") and (Timer.Check("mana_shield") == False or is_under_attack()):
        if Player.Mana >= mana_cost(20) and real_skill_value('Spellweaving') >= 90:
            if sv['use_messages'] == 1:
                Player.HeadMessage(68, "Mana Shield!")
            Spells.CastMastery("Mana Shield")
            Timer.Create('spells', calc_castspeed_sw(2250) + calc_castpause())
            create_rollback_cooldown("mana_shield", 120000)

def keep_mystic_weapon():
    """Mysticism mastery: imbues weapon with mystical energy. Keep active."""
    if sv['use_mystic_weapon'] == 0 or Timer.Check('spells') == True or Player.Paralized:
        return
    if not Player.BuffsExist("Mystic Weapon") and Timer.Check("mystic_weapon") == False:
        if Player.Mana >= mana_cost(20) and real_skill_value('Mysticism') >= 90:
            if sv['use_messages'] == 1:
                Player.HeadMessage(68, "Mystic Weapon!")
            Spells.CastMastery("Mystic Weapon")
            Timer.Create('spells', calc_castspeed(2250) + calc_castpause())
            create_rollback_cooldown("mystic_weapon", 120000)

def has_arcane_empowerment():
    """Razor Enhanced misspells this buff as Enpowerment."""
    return (Player.BuffsExist("Arcane Enpowerment") or
            Player.BuffsExist("Arcane Enpowerment (new)") or
            Player.BuffsExist("Arcane Empowerment"))

def arcane_empowerment():
    """SW: Arcane Empowerment — boosts spell damage and healing. Keep active."""
    if sv['use_arcaneempowerment'] == 0 or Timer.Check('spells') == True or Player.Paralized:
        return
    if not has_arcane_empowerment() and Timer.Check("arcaneempowerment") == False:
        if Player.Mana >= mana_cost(50) and skill_value('Spellweaving') >= 24:
            if sv['use_messages'] == 1:
                Player.HeadMessage(68, "Arcane Empowerment!")
            Spells.CastSpellweaving("Arcane Empowerment")
            Timer.Create('spells', calc_castspeed_sw(3000) + calc_castpause())
            # Short retry throttle. BuffsExist prevents recasting while active;
            # a failed/expired buff must not block summons for two minutes.
            create_rollback_cooldown("arcaneempowerment", 5000)

def keep_reaper_form():
    """SW: Reaper Form — transforms into a reaper, boosting spellweaving spell damage."""
    if sv['use_reaperform'] == 0 or Timer.Check('spells') == True or Player.Paralized:
        return
    if Player.BuffsExist("Stone Form") or Player.BuffsExist("Wraith Form") or Player.BuffsExist("Lich Form") or Player.BuffsExist("Vampiric Embrace"):
        return
    if not Player.BuffsExist("Reaper Form") and Timer.Check("reaperform") == False:
        if Player.Mana >= mana_cost(34):
            if sv['use_messages'] == 1:
                Player.HeadMessage(68, "Reaper Form!")
            Spells.CastSpellweaving("Reaper Form")
            Timer.Create('spells', calc_castspeed_sw(3000) + calc_castpause())
            create_rollback_cooldown("reaperform", 120000)

def keep_wraith_form():
    """Necro: Wraith Form — drains mana from enemies on hit. Mutually exclusive with Lich/Vampiric."""
    if sv['use_wraithform'] == 0 or Timer.Check('spells') == True or Player.Paralized:
        return
    if Player.BuffsExist("Lich Form") or Player.BuffsExist("Vampiric Embrace"):
        return
    if not Player.BuffsExist("Wraith Form") and Timer.Check("wraithform") == False:
        if Player.Mana >= mana_cost(17) and skill_value('Necromancy') >= 15:
            if sv['use_messages'] == 1:
                Player.HeadMessage(68, "Wraith Form!")
            Spells.CastNecro("Wraith Form")
            Timer.Create('spells', calc_castspeed(2000) + calc_castpause())
            create_rollback_cooldown("wraithform", 120000)

def keep_lich_form():
    """Necro: Lich Form — mana regenerates from INT, immune to poison. Req. 70 Necromancy."""
    if sv['use_lichform'] == 0 or Timer.Check('spells') == True or Player.Paralized:
        return
    if Player.BuffsExist("Wraith Form") or Player.BuffsExist("Vampiric Embrace"):
        return
    if not Player.BuffsExist("Lich Form") and Timer.Check("lichform") == False:
        if Player.Mana >= mana_cost(23) and skill_value('Necromancy') >= 70:
            if sv['use_messages'] == 1:
                Player.HeadMessage(68, "Lich Form!")
            Spells.CastNecro("Lich Form")
            Timer.Create('spells', calc_castspeed(2000) + calc_castpause())
            create_rollback_cooldown("lichform", 120000)

def keep_vampiric_embrace():
    """Necro: Vampiric Embrace — life drain on hit. Mutually exclusive with Wraith/Lich. Req. 99 Necromancy."""
    if sv['use_vampiricembrace'] == 0 or Timer.Check('spells') == True or Player.Paralized:
        return
    if Player.BuffsExist("Wraith Form") or Player.BuffsExist("Lich Form"):
        return
    if not Player.BuffsExist("Vampiric Embrace") and Timer.Check("vampiricembrace") == False:
        if Player.Mana >= mana_cost(23) and skill_value('Necromancy') >= 99:
            if sv['use_messages'] == 1:
                Player.HeadMessage(68, "Vampiric Embrace!")
            Spells.CastNecro("Vampiric Embrace")
            Timer.Create('spells', calc_castspeed(2000) + calc_castpause())
            create_rollback_cooldown("vampiricembrace", 120000)

def keep_stone_form():
    """Mysticism: Stone Form — increased physical resistance. Req. 33 Mysticism."""
    if sv['use_stoneform'] == 0 or Timer.Check('spells') == True or Player.Paralized:
        return
    if Player.BuffsExist("Reaper Form") or Player.BuffsExist("Wraith Form") or Player.BuffsExist("Lich Form") or Player.BuffsExist("Vampiric Embrace"):
        return
    if not Player.BuffsExist("Stone Form") and Timer.Check("stoneform") == False:
        if Player.Mana >= mana_cost(11) and skill_value('Mysticism') >= 33:
            if sv['use_messages'] == 1:
                Player.HeadMessage(68, "Stone Form!")
            Spells.CastMysticism("Stone Form")
            Timer.Create('spells', calc_castspeed(1750) + calc_castpause())
            create_rollback_cooldown("stoneform", 120000)

##################################################################
# Mob Debuffs

def apply_debuffs(nearest, nearby_count=1):
    """Applies one debuff per call. Returns True if a spell was cast."""
    global last_debuff_target, nuke_cascade_until
    if Timer.Check('spells') == True or Player.Paralized:
        return False
    if Player.Poisoned:
        auto_cure()
        return False

    # Skip slow / expensive debuffs on trash mobs — they die before payoff lands.
    # 'trash' = real HP below `trash_hp_cap` (default 250). Unknown mobs => allow.
    _tier = get_mob_tier(nearest)
    if _tier == 'trash' and sv.get('use_skip_debuffs_on_trash', 1) == 1:
        return False

    # Low-mana mode: conserve — no debuffs until mana recovers
    if low_mana():
        return False

    # Reset debuff cooldowns when switching to a new target
    if nearest.Serial != last_debuff_target:
        last_debuff_target = nearest.Serial
        for t in ['debuff_evil_omen', 'debuff_curse', 'debuff_corpse_skin',
                  'debuff_strangle', 'debuff_mind_rot', 'debuff_poison',
                  'debuff_command_undead', 'debuff_conduit',
                  'debuff_sleep', 'debuff_mass_sleep', 'debuff_paralyze', 'debuff_mana_vampire']:
            Timer.Create(t, 1)
            debuff_expiry.pop(t, None)

    # Command Undead — Necromancy mastery (3000ms, req. 90 real Necromancy)
    if sv['use_command_undead'] == 1 and Timer.Check('debuff_command_undead') == False:
        if Player.Mana >= mana_cost(30) and real_skill_value('Necromancy') >= 90:
            if sv['use_messages'] == 1:
                Player.HeadMessage(90, "Command Undead!")
            pre_cast = time.time()
            Spells.CastMastery("Command Undead")
            wait_for_target_responsive(4000, True)
            target_current_visible_hostile(nearest)
            if not did_fizzle(pre_cast):
                Timer.Create('spells', calc_castpause())
                Timer.Create('debuff_command_undead', 30000)
            return True

    # Conduit — Necromancy mastery (2250ms, self-centered, req. 90 real Necromancy)
    if sv['use_conduit'] == 1 and Timer.Check('debuff_conduit') == False:
        if Player.Mana >= mana_cost(20) and real_skill_value('Necromancy') >= 90:
            if sv['use_messages'] == 1:
                Player.HeadMessage(90, "Conduit!")
            Spells.CastMastery("Conduit")
            Timer.Create('spells', calc_castspeed(2250) + calc_castpause())
            create_rollback_cooldown('debuff_conduit', 30000)
            return True

    # Evil Omen: cast before each main attack spell (empowers next harmful spell, Necro req. 20)
    if sv['use_evil_omen'] == 1 and Timer.Check('debuff_evil_omen') == False:
        if Player.Mana >= mana_cost(11) and skill_value('Necromancy') >= 20:
            if sv['use_messages'] == 1:
                Player.HeadMessage(90, "Evil Omen!")
            pre_cast = time.time()
            Spells.CastNecro("Evil Omen")
            wait_for_target_responsive(4000, True)
            target_current_visible_hostile(nearest)
            if not did_fizzle(pre_cast):
                Timer.Create('spells', calc_castpause())
                if sv.get('use_nuke_cascade', 1) == 1:
                    nuke_cascade_until = time.time() + (3.0 if get_mob_tier(nearest) == 'boss' else 1.5)
                track_debuff('debuff_evil_omen', 6000)
            return True

    # Curse: reduces all stats (Magery C4 = 1750ms, req. skill 20)
    if sv['use_curse'] == 1 and Timer.Check('debuff_curse') == False:
        if Player.Mana >= mana_cost(20) and skill_value('Magery') >= 20:
            if sv['use_messages'] == 1:
                Player.HeadMessage(90, "Curse!")
            pre_cast = time.time()
            Spells.CastMagery("Curse")
            wait_for_target_responsive(4000, True)
            target_current_visible_hostile(nearest)
            if not did_fizzle(pre_cast):
                Timer.Create('spells', calc_castpause())
                track_debuff('debuff_curse', 55000)
            return True

    # Corpse Skin: lowers fire & poison resistance (Necro req. 20)
    if sv['use_corpse_skin'] == 1 and Timer.Check('debuff_corpse_skin') == False:
        if Player.Mana >= mana_cost(11) and skill_value('Necromancy') >= 20:
            if sv['use_messages'] == 1:
                Player.HeadMessage(90, "Corpse Skin!")
            pre_cast = time.time()
            Spells.CastNecro("Corpse Skin")
            wait_for_target_responsive(4000, True)
            target_current_visible_hostile(nearest)
            if not did_fizzle(pre_cast):
                Timer.Create('spells', calc_castpause())
                if sv.get('use_nuke_cascade', 1) == 1:
                    nuke_cascade_until = time.time() + (3.0 if get_mob_tier(nearest) == 'boss' else 1.5)
                track_debuff('debuff_corpse_skin', 25000)
            return True

    # Strangle: damage over time (Necro req. 65)
    if sv['use_strangle'] == 1 and Timer.Check('debuff_strangle') == False:
        if Player.Mana >= mana_cost(29) and skill_value('Necromancy') >= 65:
            if sv['use_messages'] == 1:
                Player.HeadMessage(90, "Strangle!")
            pre_cast = time.time()
            Spells.CastNecro("Strangle")
            wait_for_target_responsive(4000, True)
            target_current_visible_hostile(nearest)
            if not did_fizzle(pre_cast):
                Timer.Create('spells', calc_castpause())
                track_debuff('debuff_strangle', 15000)
            return True

    # Mind Rot: increases mana costs — very effective vs mage and caster mobs (Necro req. 30)
    if sv['use_mind_rot'] == 1 and Timer.Check('debuff_mind_rot') == False:
        if Player.Mana >= mana_cost(17) and skill_value('Necromancy') >= 30:
            if sv['use_messages'] == 1:
                Player.HeadMessage(90, "Mind Rot!")
            pre_cast = time.time()
            Spells.CastNecro("Mind Rot")
            wait_for_target_responsive(4000, True)
            target_current_visible_hostile(nearest)
            if not did_fizzle(pre_cast):
                Timer.Create('spells', calc_castpause())
                track_debuff('debuff_mind_rot', 25000)
            return True

    # Poison (Magery C3 = 1500ms)
    if sv['use_poison'] == 1 and Timer.Check('debuff_poison') == False:
        if Player.Mana >= mana_cost(9):
            if sv['use_messages'] == 1:
                Player.HeadMessage(90, "Poison!")
            pre_cast = time.time()
            Spells.CastMagery("Poison")
            wait_for_target_responsive(4000, True)
            target_current_visible_hostile(nearest)
            if not did_fizzle(pre_cast):
                Timer.Create('spells', calc_castpause())
                track_debuff('debuff_poison', 20000)
            return True

    # Paralyze — Magery C6: freezes target in place (req. 50 Magery)
    if sv['use_paralyze'] == 1 and Timer.Check('debuff_paralyze') == False:
        if Player.Mana >= mana_cost(20) and skill_value('Magery') >= 50:
            if sv['use_messages'] == 1:
                Player.HeadMessage(90, "Paralyze!")
            pre_cast = time.time()
            Spells.CastMagery("Paralyze")
            wait_for_target_responsive(4000, True)
            target_current_visible_hostile(nearest)
            if not did_fizzle(pre_cast):
                Timer.Create('spells', calc_castpause())
                track_debuff('debuff_paralyze', 8000)
            return True

    # Sleep — Mysticism C2: puts target to sleep (broken by damage)
    if sv['use_sleep'] == 1 and Timer.Check('debuff_sleep') == False:
        if Player.Mana >= mana_cost(9):
            if sv['use_messages'] == 1:
                Player.HeadMessage(90, "Sleep!")
            pre_cast = time.time()
            Spells.CastMysticism("Sleep")
            wait_for_target_responsive(4000, True)
            target_current_visible_hostile(nearest)
            if not did_fizzle(pre_cast):
                Timer.Create('spells', calc_castpause())
                track_debuff('debuff_sleep', 10000)
            return True

    # Mass Sleep — Mysticism C5: AoE sleep around target (req. 50 Mysticism, 2+ mobs)
    if sv['use_mass_sleep'] == 1 and Timer.Check('debuff_mass_sleep') == False and nearby_count >= 2:
        if Player.Mana >= mana_cost(20) and skill_value('Mysticism') >= 50:
            if sv['use_messages'] == 1:
                Player.HeadMessage(90, "Mass Sleep!")
            pre_cast = time.time()
            Spells.CastMysticism("Mass Sleep")
            wait_for_target_responsive(4000, True)
            target_current_visible_hostile(nearest)
            if not did_fizzle(pre_cast):
                Timer.Create('spells', calc_castpause())
                track_debuff('debuff_mass_sleep', 10000)
            return True

    # Mana Vampire — Magery C7: drains mana from target (req. 60 Magery)
    if sv['use_mana_vampire'] == 1 and Timer.Check('debuff_mana_vampire') == False:
        if Player.Mana >= mana_cost(40) and skill_value('Magery') >= 60:
            if sv['use_messages'] == 1:
                Player.HeadMessage(90, "Mana Vampire!")
            pre_cast = time.time()
            Spells.CastMagery("Mana Vampire")
            wait_for_target_responsive(4000, True)
            target_current_visible_hostile(nearest)
            if not did_fizzle(pre_cast):
                Timer.Create('spells', calc_castpause())
                track_debuff('debuff_mana_vampire', 20000)
            return True

    return False

##################################################################
# Bard

# Common instrument item IDs — extend if needed
INSTRUMENT_IDS = [0x0EB1, 0x0EB2, 0x0EB3, 0x0E9C, 0x0E9D, 0x0E9E, 0x2B5F]

def get_instrument():
    """Find the first instrument in the player's backpack. Returns item or None."""
    for iid in INSTRUMENT_IDS:
        item = Items.FindByID(iid, -1, Player.Backpack.Serial, 1, False)
        if item:
            return item
    return None

def check_instrument():
    """Warn player if no instrument is found in backpack."""
    if sv['use_check_instrument'] == 0:
        return
    if get_instrument() is None:
        Player.HeadMessage(33, "No instrument in backpack!")

def bard_resilience():
    """Bard Mastery buff: Resilience — increases HP regeneration."""
    if sv['use_resilience'] == 0 or Timer.Check('spells') == True or Player.Paralized:
        return
    if not Player.BuffsExist("Resilience") and Timer.Check("bard_resilience") == False:
        if sv['use_messages'] == 1:
            Player.HeadMessage(68, "Resilience!")
        Spells.CastMastery("Resilience")
        Timer.Create('spells', calc_castspeed(2250) + calc_castpause())
        create_rollback_cooldown("bard_resilience", 120000)

def bard_perseverance():
    """Bard Mastery buff: Perseverance — reduces damage taken."""
    if sv['use_perseverance'] == 0 or Timer.Check('spells') == True or Player.Paralized:
        return
    if not Player.BuffsExist("Perseverance") and Timer.Check("bard_perseverance") == False:
        if sv['use_messages'] == 1:
            Player.HeadMessage(68, "Perseverance!")
        Spells.CastMastery("Perseverance")
        Timer.Create('spells', calc_castspeed(2250) + calc_castpause())
        create_rollback_cooldown("bard_perseverance", 120000)

def bard_inspire():
    """Bard Mastery buff: Inspire — boosts damage for you and nearby allies."""
    if sv['use_inspire'] == 0 or Timer.Check('spells') == True or Player.Paralized:
        return
    if not Player.BuffsExist("Inspire") and Timer.Check("bard_inspire") == False:
        if sv['use_messages'] == 1:
            Player.HeadMessage(68, "Inspire!")
        Spells.CastMastery("Inspire")
        Timer.Create('spells', calc_castspeed(2250) + calc_castpause())
        create_rollback_cooldown("bard_inspire", 120000)

def bard_invigorate():
    """Bard Mastery buff: Invigorate — regenerates stamina for you and nearby allies."""
    if sv['use_invigorate'] == 0 or Timer.Check('spells') == True or Player.Paralized:
        return
    if not Player.BuffsExist("Invigorate") and Timer.Check("bard_invigorate") == False:
        if sv['use_messages'] == 1:
            Player.HeadMessage(68, "Invigorate!")
        Spells.CastMastery("Invigorate")
        Timer.Create('spells', calc_castspeed(2250) + calc_castpause())
        create_rollback_cooldown("bard_invigorate", 120000)

def apply_bard(nearest, victims, victims_dist):
    """Apply one bard skill or mastery debuff per call. Returns True if an action was taken."""
    if Player.Paralized or Timer.Check('spells') == True:
        return False
    if Player.Poisoned:
        auto_cure()
        return False

    has_instrument = get_instrument() is not None

    # Area Peace — self-centered, uses bard timer
    if sv['use_area_peace'] == 1 and has_instrument and Timer.Check('bard_area_peace') == False and Timer.Check('bard') == False:
        if sv['use_messages'] == 1:
            Player.HeadMessage(68, "Area Peace!")
        Player.UseSkill('Peacemaking')
        target_ready = wait_for_target_responsive(2000, True)
        if target_ready:
            Target.Self()
        Timer.Create('bard', 1500)
        if target_ready:
            Timer.Create('bard_area_peace', 12000)
        Timer.Create('spells', 750)
        return True

    # Discordance — reduces mob skills/stats
    if sv['use_discordance'] == 1 and has_instrument and Timer.Check('bard_discord') == False and Timer.Check('bard') == False:
        if sv['use_messages'] == 1:
            Player.HeadMessage(68, "Discordance!")
        Player.UseSkill('Discordance')
        target_ready = wait_for_target_responsive(2000, True)
        if target_ready:
            target_current_visible_hostile(nearest)
        Timer.Create('bard', 1500)
        if target_ready:
            Timer.Create('bard_discord', 12000)
        Timer.Create('spells', 750)
        return True

    # Peacemaking — single target; skip if Discordance is active (mutex)
    if sv['use_peace'] == 1 and has_instrument and Timer.Check('bard_discord') == False and Timer.Check('bard_peace') == False and Timer.Check('bard') == False:
        if sv['use_messages'] == 1:
            Player.HeadMessage(68, "Peace!")
        Player.UseSkill('Peacemaking')
        target_ready = wait_for_target_responsive(2000, True)
        if target_ready:
            target_current_visible_hostile(nearest)
        Timer.Create('bard', 1500)
        if target_ready:
            Timer.Create('bard_peace', 12000)
        Timer.Create('spells', 750)
        return True

    # Provocation — needs 2+ mobs; provokes mob2 to attack mob1
    if sv['use_provocation'] == 1 and has_instrument and Timer.Check('bard_provo') == False and Timer.Check('bard') == False:
        if len(victims_dist) >= 2:
            sorted_mobs = [m for m, d in sorted(victims_dist, key=lambda x: x[1])]
            mob1 = sorted_mobs[0]
            mob2 = sorted_mobs[1]
            if sv['use_messages'] == 1:
                Player.HeadMessage(68, "Provocation!")
            Player.UseSkill('Provocation')
            first_ready = wait_for_target_responsive(2000, True)
            second_ready = False
            if first_ready:
                Target.TargetExecute(mob1)
                second_ready = wait_for_target_responsive(2000, True)
                if second_ready:
                    Target.TargetExecute(mob2)
            Timer.Create('bard', 1500)
            if first_ready and second_ready:
                Timer.Create('bard_provo', 12000)
            Timer.Create('spells', 750)
            return True

    # Tribulation — Bard Mastery targeted debuff (uses spells timer)
    if sv['use_tribulation'] == 1 and Timer.Check('bard_tribulation') == False and Timer.Check('spells') == False:
        if sv['use_messages'] == 1:
            Player.HeadMessage(68, "Tribulation!")
        pre_cast = time.time()
        Spells.CastMastery("Tribulation")
        wait_for_target_responsive(4000, True)
        target_current_visible_hostile(nearest)
        if not did_fizzle(pre_cast):
            Timer.Create('spells', calc_castpause())
            Timer.Create('bard_tribulation', 15000)
        return True

    # Despair — Bard Mastery targeted debuff (uses spells timer)
    if sv['use_despair'] == 1 and Timer.Check('bard_despair') == False and Timer.Check('spells') == False:
        if sv['use_messages'] == 1:
            Player.HeadMessage(68, "Despair!")
        pre_cast = time.time()
        Spells.CastMastery("Despair")
        wait_for_target_responsive(4000, True)
        target_current_visible_hostile(nearest)
        if not did_fizzle(pre_cast):
            Timer.Create('spells', calc_castpause())
            Timer.Create('bard_despair', 15000)
        return True

    return False

##################################################################
# Tamer

_bandage_agent_state = -1  # -1 = unknown, 0 = stopped, 1 = running

def manage_bandage_agent():
    """Start or stop the RE Bandage Agent only when the state actually changes."""
    global _bandage_agent_state
    want = sv['use_bandage_agent']
    if want == _bandage_agent_state:
        return
    if want == 1:
        BandageHeal.Start()
    else:
        BandageHeal.Stop()
    _bandage_agent_state = want

def heal_pets():
    """Heal all pets below the HP threshold using the selected method."""
    if sv['use_auto_heal_pet'] == 0 or Player.Paralized or Timer.Check('spells') == True:
        return
    threshold = sv['pet_hp_threshold'] / 100.0
    option = sv['pet_heal_option']
    for pet in Player.Pets:
        if pet.Hits >= pet.HitsMax * threshold:
            continue
        # Bandages (option 1 or 4)
        if option in (1, 4):
            bandage_key = 'pet_bandage_%d' % pet.Serial
            bandage = Items.FindByID(0x0E21, -1, Player.Backpack.Serial, 1, False)
            if bandage and Timer.Check(bandage_key) == False:
                if sv['use_messages'] == 1:
                    Player.HeadMessage(68, "Bandage: %s!" % pet.Name)
                Items.UseItem(bandage)
                target_ready = wait_for_target_responsive(2000, True)
                if target_ready:
                    Target.TargetExecute(pet)
                    Timer.Create(bandage_key, 5000)
                Timer.Create('spells', 750)
                return
        # Magery: Greater Heal (option 2 or 4)
        if option in (2, 4):
            if Timer.Check('spells') == False and Player.Mana >= mana_cost(20):
                if sv['use_messages'] == 1:
                    Player.HeadMessage(68, "Greater Heal: %s!" % pet.Name)
                pre_cast = time.time()
                Spells.CastMagery("Greater Heal")
                wait_for_target_responsive(4000, True)
                Target.TargetExecute(pet)
                if not did_fizzle(pre_cast):
                    Timer.Create('spells', calc_castpause())
                return
        # Mysticism: Cleansing Winds (option 3)
        if option == 3:
            if Timer.Check('spells') == False and Player.Mana >= mana_cost(20):
                if sv['use_messages'] == 1:
                    Player.HeadMessage(68, "Cleansing Winds: %s!" % pet.Name)
                pre_cast = time.time()
                Spells.CastMysticism("Cleansing Winds")
                wait_for_target_responsive(4000, True)
                Target.TargetExecute(pet)
                if not did_fizzle(pre_cast):
                    Timer.Create('spells', calc_castpause())
                return
        return  # only heal one pet per cycle

def cure_pets():
    """Cure all poisoned pets using the selected method."""
    if sv['use_auto_cure_pet'] == 0 or Player.Paralized or Timer.Check('spells') == True:
        return
    option = sv['pet_heal_option']
    for pet in Player.Pets:
        if not pet.Poisoned:
            continue
        # Bandages (option 1 or 4)
        if option in (1, 4):
            bandage_key = 'pet_bandage_%d' % pet.Serial
            bandage = Items.FindByID(0x0E21, -1, Player.Backpack.Serial, 1, False)
            if bandage and Timer.Check(bandage_key) == False:
                if sv['use_messages'] == 1:
                    Player.HeadMessage(68, "Bandage (cure): %s!" % pet.Name)
                Items.UseItem(bandage)
                target_ready = wait_for_target_responsive(2000, True)
                if target_ready:
                    Target.TargetExecute(pet)
                    Timer.Create(bandage_key, 5000)
                Timer.Create('spells', 750)
                return
        # Magery: Arch Cure (option 2 or 4)
        if option in (2, 4):
            if Timer.Check('spells') == False and Player.Mana >= mana_cost(20):
                if sv['use_messages'] == 1:
                    Player.HeadMessage(68, "Arch Cure: %s!" % pet.Name)
                pre_cast = time.time()
                Spells.CastMagery("Arch Cure")
                wait_for_target_responsive(4000, True)
                Target.TargetExecute(pet)
                if not did_fizzle(pre_cast):
                    Timer.Create('spells', calc_castpause())
                return
        # Mysticism: Cleansing Winds (option 3)
        if option == 3:
            if Timer.Check('spells') == False and Player.Mana >= mana_cost(20):
                if sv['use_messages'] == 1:
                    Player.HeadMessage(68, "Cleansing Winds (cure): %s!" % pet.Name)
                pre_cast = time.time()
                Spells.CastMysticism("Cleansing Winds")
                wait_for_target_responsive(4000, True)
                Target.TargetExecute(pet)
                if not did_fizzle(pre_cast):
                    Timer.Create('spells', calc_castpause())
                return
        return  # only cure one pet per cycle

def pet_gift_of_life():
    """Cast Gift of Life on each pet that doesn't have it. Refreshed every 90s per pet."""
    if sv['use_pet_giftoflife'] == 0 or Timer.Check('spells') == True or Player.Paralized:
        return
    if Player.Mana < mana_cost(70) or skill_value('Spellweaving') < 80:
        return
    eligible_pets = [pet for pet in Player.Pets if Player.DistanceTo(pet) <= 10]
    eligible_pets = mobs_in_line_of_sight(eligible_pets, 10)
    for pet in eligible_pets:
        gol_key = 'pet_gol_%d' % pet.Serial
        if Timer.Check(gol_key) == False:
            if sv['use_messages'] == 1:
                Player.HeadMessage(68, "Gift of Life: %s!" % pet.Name)
            # Always throttle the attempt first; success replaces this timer.
            Timer.Create(gol_key, 5000)
            pre_cast = time.time()
            Spells.CastSpellweaving("Gift of Life")
            target_ready = wait_for_target_responsive(4000, True)
            if target_ready:
                Target.TargetExecute(pet)
                Misc.Pause(max(250, serverdelay))
            failure = cast_failure_since(pre_cast)
            if target_ready and failure is None:
                Timer.Create('spells', calc_castpause())
                Timer.Create(gol_key, 90000)
            elif failure == "spell_cooldown":
                Timer.Create(gol_key, 30000)
            return

def pet_gift_of_renewal():
    """Cast Gift of Renewal on the closest pet. 180s cooldown."""
    global pending_pet_gor_serial, pending_pet_gor_started
    if sv['use_pet_giftofrenewal'] == 0 or Timer.Check('spells') == True or Player.Paralized:
        return
    if Target.HasTarget():
        return
    if Timer.Check('pet_giftofrenewal') == True:
        return
    now = time.time()
    try:
        shared_next_attempt = float(Misc.ReadSharedValue('mw_pet_gor_next_attempt'))
    except Exception:
        shared_next_attempt = 0.0
    if now < shared_next_attempt:
        return
    if Player.Mana < mana_cost(24):
        return
    pets = [pet for pet in Player.Pets if Player.DistanceTo(pet) <= 10]
    pets = mobs_in_line_of_sight(pets, 10)
    if not pets:
        Timer.Create('pet_giftofrenewal', 2000)
        return
    closest = min(pets, key=lambda p: Player.DistanceTo(p))
    if sv['use_messages'] == 1:
        Player.HeadMessage(68, "Gift of Renewal: %s!" % closest.Name)
    # Every real cast attempt uses the requested 180-second cooldown. Cursor
    # ownership below still resolves a late target without starting a new cast.
    Timer.Create('pet_giftofrenewal', 180000)
    Misc.SetSharedValue('mw_pet_gor_next_attempt', now + 180.0)
    pending_pet_gor_serial = closest.Serial
    pre_cast = time.time()
    pending_pet_gor_started = pre_cast
    Timer.Create('spells', calc_castspeed_sw(3000) + calc_castpause())
    Spells.CastSpellweaving("Gift of Renewal")
    target_ready = wait_for_target_responsive(4000, True)
    if target_ready:
        target_ready = execute_target_confirmed(closest)
    elif Target.HasTarget():
        # A cursor that arrived on the final poll still belongs to this cast.
        target_ready = execute_target_confirmed(closest)
    failure = cast_failure_since(pre_cast)
    target_rejected = failure in (
        "busy", "interrupted", "invalid_target", "unseen_target",
        "spell_cooldown", "timeout")
    if target_ready and not target_rejected:
        Timer.Create('spells', calc_castpause())
        Timer.Create('pet_giftofrenewal', 180000)
        Misc.SetSharedValue('mw_pet_gor_next_attempt', time.time() + 180.0)
        pending_pet_gor_serial = 0
        pending_pet_gor_started = 0.0
    elif failure == "spell_cooldown":
        # Gift of Renewal has a caster-wide lock while an existing Gift is
        # active, plus the shard's post-effect delay. Do not hammer the server.
        Timer.Create('pet_giftofrenewal', 180000)
        Misc.SetSharedValue('mw_pet_gor_next_attempt', time.time() + 180.0)
        pending_pet_gor_serial = 0
        pending_pet_gor_started = 0.0
    elif (not Target.HasTarget() and
            failure in ("busy", "interrupted", "invalid_target", "unseen_target", "timeout")):
        # Cast was rejected before producing a cursor. The attempt still keeps
        # the requested 180-second Gift of Renewal cooldown.
        pending_pet_gor_serial = 0
        pending_pet_gor_started = 0.0

def resolve_orphan_target_cursor():
    """Resolve a cursor left after a synchronous cast; block all new casts."""
    global pending_pet_gor_serial, pending_pet_gor_started
    if not Target.HasTarget():
        # An unrelated action-wait can arrive while Gift is still casting.
        # Keep ownership briefly so a late legitimate cursor is targeted, not
        # mistaken for an orphan or followed by another spell.
        if (pending_pet_gor_serial and
                time.time() - pending_pet_gor_started < 6.0):
            Timer.Create('spells', 250)
            return True
        pending_pet_gor_serial = 0
        pending_pet_gor_started = 0.0
        return False

    if pending_pet_gor_serial:
        pet = Mobiles.FindBySerial(pending_pet_gor_serial)
        if pet is not None and execute_target_confirmed(pet):
            Misc.Pause(max(250, serverdelay))
            failure = cast_failure_since(pending_pet_gor_started)
            if failure in (None, "spell_cooldown"):
                cooldown = 180000
                Timer.Create('pet_giftofrenewal', cooldown)
                Misc.SetSharedValue('mw_pet_gor_next_attempt',
                                    time.time() + (cooldown / 1000.0))
                Timer.Create('spells', calc_castpause())
                pending_pet_gor_serial = 0
                pending_pet_gor_started = 0.0
                return True

    # Every cast in this script waits synchronously for its cursor. Therefore a
    # cursor visible at the top of the main loop is orphaned and must not coexist
    # with another Spells.Cast* call.
    Target.Cancel()
    Timer.Create('spells', 250)
    if pending_pet_gor_serial:
        Timer.Create('pet_giftofrenewal', 180000)
        Misc.SetSharedValue('mw_pet_gor_next_attempt', time.time() + 180.0)
    pending_pet_gor_serial = 0
    pending_pet_gor_started = 0.0
    return True

##################################################################
# Attack spell functions

def cast_explosion_combo(nearest):
    """v0.5: Explosion (delayed dmg) + immediate follow-up = double-hit burst.
    Both spells land ~3 s after Explosion is cast. No cast pause between them."""
    if Timer.Check('combo_cd') == True:
        return False
    followup = sv.get('combo_followup', 'energybolt')
    followup_costs = {'flamestrike': 40, 'energybolt': 20, 'mindblast': 14, 'lightning': 11}
    fu_mana = followup_costs.get(followup, 20)
    total_mana = mana_cost(11) + mana_cost(fu_mana)
    if Player.Mana < total_mana:
        return False
    if skill_value('Magery') < 40:
        return False
    if sv['use_messages'] == 1:
        Player.HeadMessage(45, "Explosion combo!")
    # Cast Explosion — do NOT set spells timer yet
    pre_cast = time.time()
    Spells.CastMagery("Explosion")
    wait_for_target_responsive(4000, True)
    target_current_visible_hostile(nearest)
    if did_fizzle(pre_cast):
        Timer.Create('spells', calc_castpause())
        return True
    # Respect current FCR and server delay before starting the follow-up.
    Misc.Pause(calc_castpause())
    # Immediately cast follow-up
    followup_cast = time.time()
    if followup == 'flamestrike' and skill_value('Magery') >= 60:
        Spells.CastMagery("Flame Strike")
    elif followup == 'mindblast' and skill_value('Magery') >= 40:
        Spells.CastMagery("Mind Blast")
    elif followup == 'lightning':
        Spells.CastMagery("Lightning")
    else:
        Spells.CastMagery("Energy Bolt")
    wait_for_target_responsive(4000, True)
    target_current_visible_hostile(nearest)
    if did_fizzle(followup_cast):
        Timer.Create('spells', 250)
    else:
        Timer.Create('spells', calc_castpause())
        Timer.Create('combo_cd', max(500, int(sv.get('combo_cooldown_ms', 1500))))
    return True


def cast_single_target(nearest):
    """Cascade: strongest available single-target spell."""
    if Timer.Check('spells') == True or Player.Paralized:
        return
    if Player.Poisoned:
        auto_cure()
        return

    # Explosion combo (v0.5) — takes priority when enabled
    if sv.get('use_explosion_combo', 0) == 1:
        if cast_explosion_combo(nearest):
            return

    # Death Ray — Magery mastery (2250ms, req. 90 real Magery)
    if sv['use_death_ray'] == 1 and not Player.BuffsExist('Death Ray') and Player.Mana >= mana_cost(30):
        if real_skill_value('Magery') >= 90:
            if sv['use_messages'] == 1:
                Player.HeadMessage(32, "Death Ray!")
            pre_cast = time.time()
            Spells.CastMastery("Death Ray")
            wait_for_target_responsive(4000, True)
            target_current_visible_hostile(nearest)
            if not did_fizzle(pre_cast):
                Timer.Create('spells', calc_castpause())
            return

    # Word of Death: instant kill on very low HP mobs — only worth it on tough mobs (SW req. 83)
    # nearest.Hits is the bar value (low bar = near death). Real max from MOBSLIST when known.
    if sv['use_wordofdeath'] == 1:
        _, _wod_max = get_mob_real_hp(nearest)
        if _wod_max is None:
            _wod_max = 501
        if 0 < nearest.Hits < 8 and _wod_max > 500:
            if Player.Mana >= mana_cost(50) and skill_value('Spellweaving') >= 83:
                if sv['use_messages'] == 1:
                    Player.HeadMessage(32, "Word of Death!")
                pre_cast = time.time()
                Spells.CastSpellweaving("Word of Death")
                wait_for_target_responsive(4000, True)
                target_current_visible_hostile(nearest)
                if not did_fizzle(pre_cast):
                    Timer.Create('spells', calc_castpause())
                return

    # Resist-aware bias + nuke cascade — fire strongest enabled spell matching
    # mob.weakres (or strongest enabled if cascade is active post-debuff).
    global nuke_cascade_until
    _bias = None
    if sv.get('use_resist_aware', 1) == 1:
        _bias = get_weakres(nearest)
    _cascade = nuke_cascade_active()
    if _bias or _cascade:
        # (sv_key, school, spell_name, mana, skill_req)
        _PREF_BY_WEAK = {
            'Fire':     [('flamestrike','Magery','Flame Strike',40,60),
                         ('fireball','Magery','Fireball',9,30)],
            'Energy':   [('energybolt','Magery','Energy Bolt',20,50),
                         ('eaglestrike','Mysticism','Eagle Strike',9,9),
                         ('lightning','Magery','Lightning',11,40)],
            'Cold':     [('mindblast','Magery','Mind Blast',14,40),
                         ('nether_bolt','Mysticism','Nether Bolt',4,9)],
            'Physical': [('bombard','Mysticism','Bombard',20,51)],
        }
        _STRONGEST = [('flamestrike','Magery','Flame Strike',40,60),
                      ('energybolt','Magery','Energy Bolt',20,50),
                      ('mindblast','Magery','Mind Blast',14,40),
                      ('lightning','Magery','Lightning',11,40)]
        _cands = _STRONGEST if _cascade else _PREF_BY_WEAK.get(_bias, [])
        _low = low_mana()
        for _key, _school, _name, _mn, _sk in _cands:
            if sv.get('use_' + _key, 0) != 1:
                continue
            if _low and _mn > 14:
                continue
            if Player.Mana < mana_cost(_mn):
                continue
            if skill_value(_school) < _sk:
                continue
            if sv['use_messages'] == 1:
                _tag = 'NUK' if _cascade else (_bias[:3] if _bias else '')
                Player.HeadMessage(46, "%s [%s]!" % (_name, _tag))
            pre_cast = time.time()
            if _school == 'Magery':       Spells.CastMagery(_name)
            elif _school == 'Mysticism':  Spells.CastMysticism(_name)
            elif _school == 'Necromancy': Spells.CastNecro(_name)
            wait_for_target_responsive(4000, True)
            target_current_visible_hostile(nearest)
            if not did_fizzle(pre_cast):
                Timer.Create('spells', calc_castpause())
            nuke_cascade_until = 0.0  # consume cascade
            return

    # Mana-aware: skip expensive top-tier nukes on trash mobs (let cascade fall through
    # to cheaper Energy Bolt / Mind Blast / Lightning). Only kicks in when mana is short.
    # Low-mana mode (< low_mana_threshold %) conserves regardless of mob tier.
    _tier_for_mana = get_mob_tier(nearest)
    _low = low_mana()
    _mana_conserve = _low or (sv.get('use_mana_aware', 1) == 1
                      and _tier_for_mana == 'trash'
                      and Player.ManaMax > 0
                      and Player.Mana < Player.ManaMax * 0.7)

    # Flame Strike — Magery C7 (2500ms)
    if not _mana_conserve and sv['use_flamestrike'] == 1 and Player.Mana >= mana_cost(40):
        if skill_value('Magery') >= 60:
            if sv['use_messages'] == 1:
                Player.HeadMessage(45, "Flame Strike!")
            pre_cast = time.time()
            Spells.CastMagery("Flame Strike")
            wait_for_target_responsive(4000, True)
            target_current_visible_hostile(nearest)
            if not did_fizzle(pre_cast):
                Timer.Create('spells', calc_castpause())
            return

    # Energy Bolt — Magery C6 (2250ms) — skipped in low-mana mode (>14 base mana)
    if not _low and sv['use_energybolt'] == 1 and Player.Mana >= mana_cost(20):
        if skill_value('Magery') >= 50:
            if sv['use_messages'] == 1:
                Player.HeadMessage(45, "Energy Bolt!")
            pre_cast = time.time()
            Spells.CastMagery("Energy Bolt")
            wait_for_target_responsive(4000, True)
            target_current_visible_hostile(nearest)
            if not did_fizzle(pre_cast):
                Timer.Create('spells', calc_castpause())
            return

    # Eagle Strike — Mysticism C3 (1500ms)
    if sv['use_eaglestrike'] == 1 and Player.Mana >= mana_cost(9):
        if skill_value('Mysticism') >= 9:
            if sv['use_messages'] == 1:
                Player.HeadMessage(45, "Eagle Strike!")
            pre_cast = time.time()
            Spells.CastMysticism("Eagle Strike")
            wait_for_target_responsive(4000, True)
            target_current_visible_hostile(nearest)
            if not did_fizzle(pre_cast):
                Timer.Create('spells', calc_castpause())
            return

    # Bombard — Mysticism C6 (2250ms, physical damage, paralyzes target briefly)
    if not _low and sv['use_bombard'] == 1 and Player.Mana >= mana_cost(20):
        if skill_value('Mysticism') >= 51:
            if sv['use_messages'] == 1:
                Player.HeadMessage(45, "Bombard!")
            pre_cast = time.time()
            Spells.CastMysticism("Bombard")
            wait_for_target_responsive(4000, True)
            target_current_visible_hostile(nearest)
            if not did_fizzle(pre_cast):
                Timer.Create('spells', calc_castpause())
            return

    # Mind Blast — Magery C5 (2000ms)
    if sv['use_mindblast'] == 1 and Player.Mana >= mana_cost(14):
        if skill_value('Magery') >= 40:
            if sv['use_messages'] == 1:
                Player.HeadMessage(45, "Mind Blast!")
            pre_cast = time.time()
            Spells.CastMagery("Mind Blast")
            wait_for_target_responsive(4000, True)
            target_current_visible_hostile(nearest)
            if not did_fizzle(pre_cast):
                Timer.Create('spells', calc_castpause())
            return

    # Lightning — Magery C4 (1750ms)
    if sv['use_lightning'] == 1 and Player.Mana >= mana_cost(11):
        if sv['use_messages'] == 1:
            Player.HeadMessage(45, "Lightning!")
        pre_cast = time.time()
        Spells.CastMagery("Lightning")
        wait_for_target_responsive(4000, True)
        target_current_visible_hostile(nearest)
        if not did_fizzle(pre_cast):
            Timer.Create('spells', calc_castpause())
        return

    # Fireball — Magery C3 (1500ms)
    if sv['use_fireball'] == 1 and Player.Mana >= mana_cost(9):
        if sv['use_messages'] == 1:
            Player.HeadMessage(45, "Fireball!")
        pre_cast = time.time()
        Spells.CastMagery("Fireball")
        wait_for_target_responsive(4000, True)
        target_current_visible_hostile(nearest)
        if not did_fizzle(pre_cast):
            Timer.Create('spells', calc_castpause())
        return

    # Harm — Magery C2 (1500ms), close range only (2 tiles)
    if sv['use_harm'] == 1 and Player.Mana >= mana_cost(6) and Player.DistanceTo(nearest) <= 2:
        if sv['use_messages'] == 1:
            Player.HeadMessage(45, "Harm!")
        pre_cast = time.time()
        Spells.CastMagery("Harm")
        wait_for_target_responsive(4000, True)
        target_current_visible_hostile(nearest)
        if not did_fizzle(pre_cast):
            Timer.Create('spells', calc_castpause())
        return

    # Nether Bolt — Mysticism C1 (1000ms)
    if sv['use_nether_bolt'] == 1 and Player.Mana >= mana_cost(4):
        if sv['use_messages'] == 1:
            Player.HeadMessage(45, "Nether Bolt!")
        pre_cast = time.time()
        Spells.CastMysticism("Nether Bolt")
        wait_for_target_responsive(4000, True)
        target_current_visible_hostile(nearest)
        if not did_fizzle(pre_cast):
            Timer.Create('spells', calc_castpause())
        return

    # Magic Arrow — Magery C1 (1250ms), last resort
    if sv['use_magicarrow'] == 1 and Player.Mana >= mana_cost(4):
        if sv['use_messages'] == 1:
            Player.HeadMessage(45, "Magic Arrow!")
        pre_cast = time.time()
        Spells.CastMagery("Magic Arrow")
        wait_for_target_responsive(4000, True)
        target_current_visible_hostile(nearest)
        if not did_fizzle(pre_cast):
            Timer.Create('spells', calc_castpause())
        return

    # Harm — Magery C2 (1250ms, only effective at very close range)
    if sv['use_harm'] == 1 and Player.Mana >= mana_cost(6) and Player.DistanceTo(nearest) <= 2:
        if sv['use_messages'] == 1:
            Player.HeadMessage(45, "Harm!")
        pre_cast = time.time()
        Spells.CastMagery("Harm")
        wait_for_target_responsive(4000, True)
        target_current_visible_hostile(nearest)
        if not did_fizzle(pre_cast):
            Timer.Create('spells', calc_castpause())
        return

    # Magic Arrow — last resort (Magery C1 = 1000ms)
    if sv['use_magicarrow'] == 1 and Player.Mana >= mana_cost(4):
        if sv['use_messages'] == 1:
            Player.HeadMessage(45, "Magic Arrow!")
        pre_cast = time.time()
        Spells.CastMagery("Magic Arrow")
        wait_for_target_responsive(4000, True)
        target_current_visible_hostile(nearest)
        if not did_fizzle(pre_cast):
            Timer.Create('spells', calc_castpause())

def cast_multi_target(nearest):
    """Multi-target spells for 2+ mobs nearby. Falls back to single target."""
    if Timer.Check('spells') == True or Player.Paralized:
        return
    if Player.Poisoned:
        auto_cure()
        return

    # Ethereal Blast — Magery mastery (2250ms, self-centered AoE, req. 90 real Magery)
    # Only cast when mana is low; 5-minute cooldown
    if sv['use_ethereal_blast'] == 1 and Timer.Check('ethereal_blast') == False:
        if Player.Mana >= mana_cost(40) and Player.Mana < Player.ManaMax * 0.4:
            if real_skill_value('Magery') >= 90:
                if sv['use_messages'] == 1:
                    Player.HeadMessage(32, "Ethereal Blast!")
                Spells.CastMastery("Ethereal Blast")
                Timer.Create('spells', calc_castspeed(2250) + calc_castpause())
                create_rollback_cooldown('ethereal_blast', 300000)
                return

    # Chain Lightning — Magery C7 (2500ms)
    if sv['use_chainlightning'] == 1 and Player.Mana >= mana_cost(40):
        if skill_value('Magery') >= 60:
            if sv['use_messages'] == 1:
                Player.HeadMessage(45, "Chain Lightning!")
            pre_cast = time.time()
            Spells.CastMagery("Chain Lightning")
            wait_for_target_responsive(4000, True)
            target_current_visible_hostile(nearest)
            if not did_fizzle(pre_cast):
                Timer.Create('spells', calc_castpause())
            return

    # Meteor Swarm — Magery C7 (2500ms)
    if sv['use_meteorswarm'] == 1 and Player.Mana >= mana_cost(40):
        if skill_value('Magery') >= 60:
            if sv['use_messages'] == 1:
                Player.HeadMessage(45, "Meteor Swarm!")
            pre_cast = time.time()
            Spells.CastMagery("Meteor Swarm")
            wait_for_target_responsive(4000, True)
            target_current_visible_hostile(nearest)
            if not did_fizzle(pre_cast):
                Timer.Create('spells', calc_castpause())
            return

    # Wither — Necro, self-centered AoE cold damage (req. 60, 1500ms)
    # Self-centered — only worth casting when the target is actually close.
    if sv['use_wither'] == 1 and Player.Mana >= mana_cost(23) and Player.DistanceTo(nearest) <= 3:
        if skill_value('Necromancy') >= 60:
            if sv['use_messages'] == 1:
                Player.HeadMessage(45, "Wither!")
            Spells.CastNecro("Wither")
            Timer.Create('spells', calc_castspeed(1500) + calc_castpause())
            return

    # Poison Strike — Necro, targeted AoE poison damage (req. 65, 1750ms)
    # Closer mobs to the target take more damage.
    if sv['use_poison_strike'] == 1 and Player.Mana >= mana_cost(17):
        if skill_value('Necromancy') >= 65:
            if sv['use_messages'] == 1:
                Player.HeadMessage(45, "Poison Strike!")
            pre_cast = time.time()
            Spells.CastNecro("Poison Strike")
            wait_for_target_responsive(4000, True)
            target_current_visible_hostile(nearest)
            if not did_fizzle(pre_cast):
                Timer.Create('spells', calc_castpause())
            return

    # Hail Storm — Mysticism C7 (2500ms, req. ~66)
    if sv['use_hailstorm'] == 1 and Player.Mana >= mana_cost(50):
        if skill_value('Mysticism') >= 66:
            if sv['use_messages'] == 1:
                Player.HeadMessage(45, "Hail Storm!")
            Spells.CastMysticism("Hail Storm")
            Timer.Create('spells', calc_castspeed(2500) + calc_castpause())
            return

    # Nether Cyclone — Mysticism C8 (2750ms, req. ~80)
    if sv['use_nethercyclone'] == 1 and Player.Mana >= mana_cost(50):
        if skill_value('Mysticism') >= 80:
            if sv['use_messages'] == 1:
                Player.HeadMessage(45, "Nether Cyclone!")
            pre_cast = time.time()
            Spells.CastMysticism("Nether Cyclone")
            wait_for_target_responsive(4000, True)
            target_current_visible_hostile(nearest)
            if not did_fizzle(pre_cast):
                Timer.Create('spells', calc_castpause())
            return

    # Essence of Wind — SW (req. 52, 3000ms)
    if sv['use_essenceofwind'] == 1 and Player.Mana >= mana_cost(40):
        if skill_value('Spellweaving') >= 52:
            if sv['use_messages'] == 1:
                Player.HeadMessage(45, "Essence of Wind!")
            pre_cast = time.time()
            Spells.CastSpellweaving("Essence of Wind")
            wait_for_target_responsive(4000, True)
            target_current_visible_hostile(nearest)
            if not did_fizzle(pre_cast):
                Timer.Create('spells', calc_castpause())
            return

    # Nothing available — fall back to single target
    cast_single_target(nearest)

def cast_mass_target(nearest):
    """Mass AoE spells for 4+ mobs. Falls back to multi-target."""
    if Timer.Check('spells') == True or Player.Paralized:
        return
    if Player.Poisoned:
        auto_cure()
        return

    # Earthquake — Magery C8 (2750ms), self-centered, no targeting
    if sv['use_earthquake'] == 1 and Player.Mana >= mana_cost(50):
        if skill_value('Magery') >= 70:
            if sv['use_messages'] == 1:
                Player.HeadMessage(32, "Earthquake!")
            Spells.CastMagery("Earthquake")
            Timer.Create('spells', calc_castspeed(2750) + calc_castpause())
            return

    # Thunderstorm — SW, self-centered, no targeting needed (req. 10)
    if sv['use_thunderstorm'] == 1 and Player.Mana >= mana_cost(32):
        if skill_value('Spellweaving') >= 10:
            if sv['use_messages'] == 1:
                Player.HeadMessage(32, "Thunderstorm!")
            Spells.CastSpellweaving("Thunderstorm")
            Timer.Create('spells', calc_castspeed_sw(1500) + calc_castpause())
            return

    # Wildfire — SW (req. 66, 2500ms), targeted location
    if sv['use_wildfire'] == 1 and Player.Mana >= mana_cost(50):
        if skill_value('Spellweaving') >= 66:
            if sv['use_messages'] == 1:
                Player.HeadMessage(32, "Wildfire!")
            pre_cast = time.time()
            Spells.CastSpellweaving("Wildfire")
            wait_for_target_responsive(4000, True)
            target_current_visible_hostile(nearest)
            if not did_fizzle(pre_cast):
                Timer.Create('spells', calc_castpause())
            return

    # Spell Plague — Mysticism C7 (req. ~66, 2500ms)
    if sv['use_spellplague'] == 1 and Player.Mana >= mana_cost(40):
        if skill_value('Mysticism') >= 66:
            if sv['use_messages'] == 1:
                Player.HeadMessage(32, "Spell Plague!")
            pre_cast = time.time()
            Spells.CastMysticism("Spell Plague")
            wait_for_target_responsive(4000, True)
            target_current_visible_hostile(nearest)
            if not did_fizzle(pre_cast):
                Timer.Create('spells', calc_castpause())
            return

    # Nothing available — fall back
    cast_multi_target(nearest)

##################################################################
# Summon management

def manage_reaper(nearest):
    global guardme_pending
    # Summon Reaper — Spellweaving mastery (2250ms, req. 90 real SW)
    if sv['use_summon_reaper'] == 1 and real_skill_value('Spellweaving') >= 90:
        if Player.Followers < sv['reaper_threshold']:
            if Player.Mana >= mana_cost(38):
                if sv['use_messages'] == 1:
                    Player.HeadMessage(80, "Summon Reaper!")
                pre_cast = time.time()
                Spells.CastMastery("Summon Reaper")
                target_ready = wait_for_target_responsive(4000, True)
                if target_ready:
                    Target.TargetExecuteRelative(nearest, -2)
                if target_ready and not did_fizzle(pre_cast):
                    Timer.Create('spells', calc_castpause())
                    guardme_pending = True
                return

def say_guardme_if_pending():
    """Say 'all guard me' once after any summon cast completes.
    Called every tick from the main loop — manage_summons is gated by the spell
    timer and would miss the window after a successful summon."""
    global guardme_pending
    if (guardme_pending and not Player.Paralized and
            Timer.Check('spells') == False and
            Timer.Check('guardme_delay') == False):
        Player.ChatSay("all guard me")
        if sv.get('use_summon_counter', 1) == 1:
            Player.HeadMessage(88, "Followers: %d/%d" % (Player.Followers, Player.FollowersMax))
        guardme_pending = False

_BUFF_BADGES = [
    ('Magic Reflect', 'MR'), ('Reactive Armor', 'RA'), ('Mana Shield', 'MS'),
    ('Arcane Empowerment', 'AE'), ('Vampiric Embrace', 'VE'),
    ('Stone Form', 'SF'), ('Reaper Form', 'RF'), ('Lich Form', 'LF'),
    ('Wraith Form', 'WF'), ('Gift of Renewal', 'GoR'), ('Protection', 'PR'),
    ('Death Ray', 'DR'), ('Honored', 'HNR'),
]

def status_overlay(nearest=None):
    """Throttled head-message: HP%/MP% F:n/N badges TgtHP."""
    if sv.get('use_status_overlay', 0) == 0:
        return
    if Timer.Check('status_overlay') == True:
        return
    Timer.Create('status_overlay', max(2000, int(sv.get('status_overlay_ms', 8000))))
    hp_pct = int(round(100.0 * Player.Hits / max(1, Player.HitsMax)))
    mp_pct = int(round(100.0 * Player.Mana / max(1, Player.ManaMax)))
    badges = " ".join(short for buff, short in _BUFF_BADGES if Player.BuffsExist(buff))
    parts = ["HP:%d%% MP:%d%% F:%d/%d" % (hp_pct, mp_pct, Player.Followers, Player.FollowersMax)]
    if badges:
        parts.append(badges)
    if nearest is not None:
        cur, mx = get_mob_real_hp(nearest)
        if cur is not None and mx:
            parts.append("Tgt:%d/%d" % (cur, mx))
        if nearest.Serial == last_debuff_target:
            dbg = debuff_status_line()
            if dbg:
                parts.append(dbg)
    Player.HeadMessage(88, " | ".join(parts))

def manage_summons(hostiles_nearby=False):
    """Maintain summons, preferring Arcane Empowerment while it is safe.

    Out of combat, wait for Arcane Empowerment before summoning. Nearby
    hostiles bypass the buff requirement so follower recovery is not delayed.
    """
    global guardme_fey, guardme_fiend, guardme_pending
    if Timer.Check('spells') == True or Player.Paralized:
        return False

    if not hostiles_nearby and not has_arcane_empowerment():
        arcane_empowerment()
        return False

    # Rising Colossus — Mysticism C8 (2750ms, req. ~80); cycles tiles if placement is blocked
    if sv['use_risingcolossus'] == 1 and skill_value('Mysticism') >= 80:
        free_slots = Player.FollowersMax - Player.Followers
        if free_slots >= _COLOSSUS_SLOTS:
            # Target placement was accepted; allow the follower update to reach
            # Razor before deciding that another Colossus cast is required.
            if Timer.Check('colossus_confirmation') == True:
                return True
            if Player.Mana >= mana_cost(50):
                global _colossus_tile_idx
                if sv['use_messages'] == 1:
                    Player.HeadMessage(80, "Rising Colossus!")
                dx, dy = _RC_OFFSETS[_colossus_tile_idx % len(_RC_OFFSETS)]
                px = Player.Position.X
                py = Player.Position.Y
                pz = Player.Position.Z
                pre_cast = time.time()
                Spells.CastMysticism("Rising Colossus")
                target_ready = wait_for_target_responsive(4000, True)
                if target_ready:
                    Target.TargetExecute(px + dx, py + dy, pz)
                    Misc.Pause(max(500, serverdelay))
                rc_blocked = any("location is blocked" in e.Text.lower()
                                 for e in Journal.GetJournalEntry(pre_cast))
                if not target_ready:
                    Timer.Create('spells', 250)
                elif rc_blocked:
                    _colossus_tile_idx += 1
                    Timer.Create('spells', 700)  # short pause, retry next tile next cycle
                elif did_fizzle(pre_cast):
                    Timer.Create('spells', 250)
                else:
                    _colossus_tile_idx = 0  # reset on success so next summon starts fresh
                    Timer.Create('spells', max(750, calc_castpause()))
                    Timer.Create('colossus_confirmation', 2000)
                    guardme_pending = True
            # Colossus is required: reserve combat until it appears or slots fill.
            return True

    # Summon Elemental — Magery C8 (2750ms)
    if sv['use_summonelemental'] == 1 and skill_value('Magery') >= 70:
        if Player.Followers < sv['elemental_threshold']:
            if Player.Mana >= mana_cost(50):
                names = ["Summon Air Elemental", "Summon Earth Elemental",
                         "Summon Fire Elemental", "Summon Water Elemental"]
                spell = names[min(3, sv['elemental_type'])]
                if sv['use_messages'] == 1:
                    Player.HeadMessage(80, spell)
                Spells.CastMagery(spell)
                Timer.Create('spells', calc_castspeed(2750) + calc_castpause())
                guardme_pending = True
                return True

    # Summon Daemon — Magery C8 (req. 70 Magery; targeted near player)
    if sv['use_summon_daemon'] == 1 and skill_value('Magery') >= 70:
        if Player.Followers < sv['daemon_threshold']:
            if Player.Mana >= mana_cost(50):
                if sv['use_messages'] == 1:
                    Player.HeadMessage(80, "Summon Daemon!")
                pre_cast = time.time()
                Spells.CastMagery("Summon Daemon")
                target_ready = wait_for_target_responsive(4000, True)
                if target_ready:
                    Target.TargetExecuteRelative(Player.Serial, 1)
                if target_ready and not did_fizzle(pre_cast):
                    Timer.Create('spells', calc_castpause())
                    guardme_pending = True
                return True

    # Energy Vortex — Magery C7 (2500ms, req. 60 Magery; targeted near player)
    if sv['use_energy_vortex'] == 1 and skill_value('Magery') >= 60:
        if Player.Followers < sv['energy_vortex_threshold']:
            if Player.Mana >= mana_cost(50):
                if sv['use_messages'] == 1:
                    Player.HeadMessage(80, "Energy Vortex!")
                pre_cast = time.time()
                Spells.CastMagery("Energy Vortex")
                target_ready = wait_for_target_responsive(4000, True)
                if target_ready:
                    Target.TargetExecuteRelative(Player.Serial, 1)
                if target_ready and not did_fizzle(pre_cast):
                    Timer.Create('spells', calc_castpause())
                    guardme_pending = True
                return True

    # Blade Spirits — Magery C6 (2250ms, req. 50 Magery; targeted near player)
    if sv['use_blade_spirit'] == 1 and skill_value('Magery') >= 50:
        if Player.Followers < sv['blade_spirit_threshold']:
            if Player.Mana >= mana_cost(40):
                if sv['use_messages'] == 1:
                    Player.HeadMessage(80, "Blade Spirits!")
                pre_cast = time.time()
                Spells.CastMagery("Blade Spirits")
                target_ready = wait_for_target_responsive(4000, True)
                if target_ready:
                    Target.TargetExecuteRelative(Player.Serial, 1)
                if target_ready and not did_fizzle(pre_cast):
                    Timer.Create('spells', calc_castpause())
                    guardme_pending = True
                return True

    # Summon Creature — Magery C5 (2000ms)
    if sv['use_summon_creature'] == 1 and skill_value('Magery') >= 0:
        if Player.Followers < sv['creature_threshold']:
            if Player.Mana >= mana_cost(14):
                if sv['use_messages'] == 1:
                    Player.HeadMessage(80, "Summon Creature!")
                Spells.CastMagery("Summon Creature")
                summon_creature_cast_ms = calc_castspeed(2000) + calc_castpause()
                Timer.Create('spells', summon_creature_cast_ms)
                # Let the summon finish materializing before issuing its order.
                Timer.Create('guardme_delay', summon_creature_cast_ms + 2000)
                guardme_pending = True
                return True

    # Summon Fey — SW
    if sv['use_summonfey'] == 1:
        if Player.Followers < sv['fey_threshold']:
            if Player.Mana >= mana_cost(10) and Timer.Check('spells') == False:
                if sv['use_messages'] == 1:
                    Player.HeadMessage(80, "Summon Fey")
                Spells.CastSpellweaving("Summon Fey")
                guardme_fey = 1
                Timer.Create('spells', calc_castspeed_sw(1500) + calc_castpause())
                return True
        elif guardme_fey == 1:
            Player.ChatSay("all guard me")
            guardme_fey = 0

    # Summon Fiend — SW
    if sv['use_summonfiend'] == 1:
        if Player.Followers < sv['fey_threshold']:
            if Player.Mana >= mana_cost(10) and Timer.Check('spells') == False:
                if sv['use_messages'] == 1:
                    Player.HeadMessage(80, "Summon Fiend")
                Spells.CastSpellweaving("Summon Fiend")
                guardme_fiend = 1
                Timer.Create('spells', calc_castspeed_sw(2000) + calc_castpause())
                return True
        elif guardme_fiend == 1:
            Player.ChatSay("all guard me")
            guardme_fiend = 0

    return False

##################################################################
# Startup: auto-load this character's settings, with one-time legacy migration.

_profile_path = PROFILE_PATH
_migrate_legacy_profile = False
if not os.path.exists(_profile_path) and os.path.exists(LEGACY_PROFILE_PATH):
    _profile_path = LEGACY_PROFILE_PATH
    _migrate_legacy_profile = True
if os.path.exists(_profile_path):
    try:
        with open(_profile_path, 'r') as _f:
            _saved = json.load(_f)
        for _k, _v in _saved.items():
            Misc.SetSharedValue(_k, _v)
        if _migrate_legacy_profile:
            with open(PROFILE_PATH, 'w') as _f:
                json.dump(_saved, _f, indent=2, sort_keys=True)
        refresh_sv()
        if _migrate_legacy_profile:
            Player.HeadMessage(68, "Legacy settings migrated: %s" % PROFILE_FILENAME)
        else:
            Player.HeadMessage(68, "Settings loaded: %s" % PROFILE_FILENAME)
    except Exception as _e:
        Player.HeadMessage(33, "Profile load failed: %s" % str(_e))

##################################################################
# Startup: skill-based feature gating

if skill_value('Magery') < 20:
    Misc.SetSharedValue("use_curse", 0)
if skill_value('Magery') < 50:
    Misc.SetSharedValue("use_energybolt", 0)
    Misc.SetSharedValue("use_chainlightning", 0)
    Misc.SetSharedValue("use_meteorswarm", 0)
    Misc.SetSharedValue("use_blade_spirit", 0)
if skill_value('Magery') < 50:
    Misc.SetSharedValue("use_paralyze", 0)
if skill_value('Magery') < 60:
    Misc.SetSharedValue("use_flamestrike", 0)
    Misc.SetSharedValue("use_energy_vortex", 0)
    Misc.SetSharedValue("use_mana_vampire", 0)
if skill_value('Magery') < 70:
    Misc.SetSharedValue("use_earthquake", 0)
    Misc.SetSharedValue("use_summonelemental", 0)
    Misc.SetSharedValue("use_summon_daemon", 0)
if skill_value('Necromancy') < 15:
    Misc.SetSharedValue("use_wraithform", 0)
if skill_value('Necromancy') < 20:
    Misc.SetSharedValue("use_evil_omen", 0)
    Misc.SetSharedValue("use_corpse_skin", 0)
if skill_value('Necromancy') < 30:
    Misc.SetSharedValue("use_mind_rot", 0)
if skill_value('Necromancy') < 60:
    Misc.SetSharedValue("use_wither", 0)
if skill_value('Necromancy') < 65:
    Misc.SetSharedValue("use_strangle", 0)
if skill_value('Necromancy') < 70:
    Misc.SetSharedValue("use_lichform", 0)
if skill_value('Necromancy') < 99:
    Misc.SetSharedValue("use_vampiricembrace", 0)
if skill_value('Mysticism') < 33:
    Misc.SetSharedValue("use_stoneform", 0)
if skill_value('Mysticism') < 50:
    Misc.SetSharedValue("use_mass_sleep", 0)
if skill_value('Mysticism') < 51:
    Misc.SetSharedValue("use_cleansingwinds", 0)
    Misc.SetSharedValue("use_bombard", 0)
if skill_value('Mysticism') < 66:
    Misc.SetSharedValue("use_hailstorm", 0)
    Misc.SetSharedValue("use_spellplague", 0)
if skill_value('Mysticism') < 80:
    Misc.SetSharedValue("use_risingcolossus", 0)
    Misc.SetSharedValue("use_nethercyclone", 0)
if skill_value('Spellweaving') < 10:
    Misc.SetSharedValue("use_thunderstorm", 0)
if skill_value('Spellweaving') < 24:
    Misc.SetSharedValue("use_arcaneempowerment", 0)
if skill_value('Spellweaving') < 38:
    Misc.SetSharedValue("use_summonfey", 0)
    Misc.SetSharedValue("use_summonfiend", 0)
if skill_value('Spellweaving') < 52:
    Misc.SetSharedValue("use_essenceofwind", 0)
if skill_value('Spellweaving') < 66:
    Misc.SetSharedValue("use_wildfire", 0)
if skill_value('Spellweaving') < 83:
    Misc.SetSharedValue("use_wordofdeath", 0)

# Masteries require 90 REAL skill
if real_skill_value('Magery') < 90:
    Misc.SetSharedValue("use_death_ray", 0)
    Misc.SetSharedValue("use_ethereal_blast", 0)
if real_skill_value('Spellweaving') < 90:
    Misc.SetSharedValue("use_mana_shield", 0)
    Misc.SetSharedValue("use_summon_reaper", 0)
if real_skill_value('Necromancy') < 90:
    Misc.SetSharedValue("use_command_undead", 0)
    Misc.SetSharedValue("use_conduit", 0)
if real_skill_value('Mysticism') < 90:
    Misc.SetSharedValue("use_nether_blast", 0)
    Misc.SetSharedValue("use_mystic_weapon", 0)

# Bard masteries require 90 REAL Musicianship
if real_skill_value('Musicianship') < 90:
    Misc.SetSharedValue("use_tribulation", 0)
    Misc.SetSharedValue("use_despair", 0)
    Misc.SetSharedValue("use_resilience", 0)
    Misc.SetSharedValue("use_perseverance", 0)
    Misc.SetSharedValue("use_inspire", 0)
    Misc.SetSharedValue("use_invigorate", 0)
if skill_value('Discordance') <= 0:
    Misc.SetSharedValue("use_discordance", 0)
if skill_value('Peacemaking') <= 0:
    Misc.SetSharedValue("use_peace", 0)
    Misc.SetSharedValue("use_area_peace", 0)
if skill_value('Provocation') <= 0:
    Misc.SetSharedValue("use_provocation", 0)
if skill_value('Spellweaving') < 80:
    Misc.SetSharedValue("use_pet_giftoflife", 0)

if skill_value('Healing') > 30 or skill_value('Veterinary') > 30:
    Misc.SetSharedValue("use_bandages", 1)

refresh_gear_cache()

Player.HeadMessage(90, "Start Ultimate Mage Attack Script by Mike|Walker")
Player.HeadMessage(40, "Dont forget to start the GUMP script")

##################################################################
# Main loop

while not Player.IsGhost:

    _loop_skill_cache.clear()

    if str(Misc.ReadSharedValue("mw_attack_instance_token")) != _attack_instance_token:
        Player.HeadMessage(33, "Older attack-script copy stopped")
        break

    # GUMP changes increment one revision value. Poll that cheaply and retain a
    # 5-second full refresh fallback for settings changed by another script.
    if Timer.Check("sv_revision_check") == False:
        Timer.Create("sv_revision_check", 250)
        try:
            current_revision = int(Misc.ReadSharedValue("mw_settings_revision"))
        except Exception:
            current_revision = _settings_revision
        if (current_revision != _settings_revision or
                Timer.Check("sv_refresh_fallback") == False):
            refresh_sv()
            _settings_revision = current_revision
            Timer.Create("sv_refresh_fallback", 5000)

    cast_state_watchdog()

    # Server failures invalidate the synthetic cast timer immediately.
    release_failed_cast_from_journal()

    # After damage, unlock healing only when the server confirms interruption.
    release_disturbed_cast_for_heal()

    # A cursor left from a completed/failed wait owns the loop. Resolve Gift of
    # Renewal to its pet when possible; otherwise clear the orphan before any
    # heal, summon, buff, or attack can start another spell.
    if resolve_orphan_target_cursor():
        Misc.Pause(100)
        continue

    # --- Always-on: paralyze escape & blood oath ---
    trappedcrate()
    if Player.BuffsExist('Bload Oath (curse)'):
        if Timer.Check('blood_oath_warning') == False:
            Player.HeadMessage(40, "Blood Oath! RUN!")
            Timer.Create('blood_oath_warning', 1000)
        if Player.WarMode:
            Player.SetWarMode(False)

    # --- Healing: highest priority (take care of yourself first) ---
    care_attempted = auto_heal()
    if not care_attempted:
        care_attempted = auto_cure()
    if not care_attempted:
        care_attempted = cleansing_winds()
    if not care_attempted:
        manage_bandage_agent()
        heal_pets()
        cure_pets()

    # --- Maintenance: throttled ---
    if Timer.Check("maintenance") == False:
        if Timer.Check('spells') == False and not Target.HasTarget():
            checkweight()
        check_bandages()
        check_townbuff()
        check_arcanefocus()
        if Timer.Check('spells') == False and not Target.HasTarget():
            dresslist()
        check_instrument()
        Timer.Create("maintenance", 4000)

    if Timer.Check("legendarycheck") == False:
        legendarycheck()
        Timer.Create("legendarycheck", 1000)

    # A self-care attempt owns this loop. Never follow a failed/disturbed heal
    # or cure with an offensive cast while the server resolves cast state.
    if care_attempted:
        Misc.Pause(100)
        continue

    # Say "all guard me" right after a successful summon, before any spell-timer gate.
    say_guardme_if_pending()

    # Journal recovery, emergency care, maintenance, and legendary protection
    # above remain active while casting. Combat scans cannot do useful work until
    # the current spell recovery finishes.
    if Timer.Check('spells') == True:
        Misc.Pause(100)
        continue

    all_victims = mobs_list(sv['attackrange'])
    visible_changelings = []
    if sv['attack_blue_changelings'] == 1:
        visible_changelings = changelings_list()
    nether_blast_pending = Timer.Check('netherblast_pending')

    # --- Summons: require Arcane Empowerment while safe; bypass it in danger ---
    summon_attempted = False
    if not nether_blast_pending and Timer.Check('spells') == False:
        # Nearby hostiles remain a danger even through a wall, so summons may
        # still bypass Arcane Empowerment. Offensive targeting is LOS-filtered below.
        summon_attempted = manage_summons(len(all_victims) > 0 or len(visible_changelings) > 0)

    # Summoning owns the loop. Never follow it with Eagle Strike or another
    # offensive cast while the server is still creating the follower.
    if summon_attempted:
        Misc.Pause(100)
        continue

    if (len(all_victims) > 0 or len(visible_changelings) > 0) and sv['activeattack'] == 1:

        # Refresh gear cache on timer
        if Timer.Check("gearcache") == False:
            refresh_gear_cache()
            Timer.Create("gearcache", 5000)

        # Do not start a long buff when Nether Blast can be cast now.
        prebuff_victims = mobs_in_line_of_sight(all_victims, sv['attackrange'])
        prebuff_serials = set(mob.Serial for mob in prebuff_victims)
        for changeling in visible_changelings:
            if changeling.Serial not in prebuff_serials:
                prebuff_victims.append(changeling)
                prebuff_serials.add(changeling.Serial)
        nether_blast_due = False
        if len(prebuff_victims) > 0:
            prebuff_dist = [(mob, Player.DistanceTo(mob)) for mob in prebuff_victims]
            prebuff_nearby_count = len([mob for mob, distance in prebuff_dist if distance <= 8])
            prebuff_nearest = min(prebuff_dist, key=lambda mob_dist: mob_dist[1])[0]
            nether_blast_due = nether_blast_ready_for(prebuff_nearest, prebuff_nearby_count)

        # Buffs — throttled to 750ms (each BuffsExist is an IPC call); urgent
        # re-buff when under attack bypasses the throttle.
        if (not nether_blast_pending and not nether_blast_due and
                (Timer.Check('buffcheck') == False or is_under_attack())):
            Timer.Create('buffcheck', 750)
            keep_magic_reflect()
            keep_reactive_armor()
            keep_protection()
            keep_bless()
            attune_weapon()
            gift_of_life()
            gift_of_renewal()
            keep_mana_shield()
            keep_mystic_weapon()
            arcane_empowerment()
            keep_reaper_form()
            keep_wraith_form()
            keep_lich_form()
            keep_vampiric_embrace()
            keep_stone_form()
            bard_resilience()
            bard_perseverance()
            bard_inspire()
            bard_invigorate()
            pet_gift_of_life()
            pet_gift_of_renewal()
            bless_pets()

        # A buff cast owns this loop. Next tick performs a fresh mobile scan;
        # scanning repeatedly during its recovery cannot change an action.
        if Timer.Check('spells') == True or Target.HasTarget():
            Misc.Pause(100)
            continue

        # Use the initial fresh LOS scan for pre-combat helpers. A second fresh
        # scan remains immediately before the actual combat spell below.
        victims = prebuff_victims
        if len(victims) == 0:
            last_attack_target = 0
            last_distance_marker = None
            if _nb_marker_count > 0:
                nb_clear_tiles()
            process_slayer_swap(None)
            status_overlay(None)
            Misc.Pause(100)
            continue

        # Distance data — visible mobs only, single pass.
        victims_dist = [(mob, Player.DistanceTo(mob)) for mob in victims]
        nearby_count = len([m for m, d in victims_dist if d <= 8])

        # Always attack the nearest current visible hostile. The old lowest-HP
        # override kept an older/distant target when a new mob spawned nearby.
        nearest = min(victims_dist, key=lambda mob_dist: mob_dist[1])[0]

        if nearest is None:
            Misc.Pause(100)
            continue
        live_nearest = Mobiles.FindBySerial(nearest.Serial)
        if live_nearest is None:
            Misc.Pause(100)
            continue
        nearest = live_nearest
        nether_blast_ready = nether_blast_ready_for(nearest, nearby_count)

        # Distance marker
        if sv['use_distancemarker'] == 1:
            dist = Player.DistanceTo(nearest)
            marker_band = 0 if dist <= 3 else (1 if dist <= 8 else 2)
            marker_state = (nearest.Serial, marker_band, sv['use_bluemarkermode'])
            show_marker = (marker_state != last_distance_marker
                           or Timer.Check('distance_marker') == False)
            last_distance_marker = marker_state
            if show_marker:
                Timer.Create('distance_marker', 1000)
                if marker_band == 0:
                    Mobiles.Message(nearest, 70, "▼") if sv['use_bluemarkermode'] == 0 else Mobiles.Message(nearest, 90, "▼")
                elif marker_band == 1:
                    Mobiles.Message(nearest, 45, "▼") if sv['use_bluemarkermode'] == 0 else Mobiles.Message(nearest, 100, "▼▼")
                else:
                    Mobiles.Message(nearest, 28, "▼") if sv['use_bluemarkermode'] == 0 else Mobiles.Message(nearest, 110, "▼▼▼")
        else:
            last_distance_marker = None

        if (not nether_blast_pending and not nether_blast_ready and
                Timer.Check('spells') == False):
            manage_reaper(nearest)

        # Honor
        if (not nether_blast_pending and not nether_blast_ready and
                Timer.Check('spells') == False and
                not Target.HasTarget() and sv['use_honor'] == 1 and
                nearest.Hits == nearest.HitsMax and
                Player.DistanceTo(nearest) <= sv['honordistance']):
            if not Player.BuffsExist('Honored') or use_honor_fix == 1:
                if Timer.Check('spamhonor') == False and sv['use_messages'] == 1:
                    Player.HeadMessage(55, "Honor: {}".format(nearest.Name))
                    Timer.Create('spamhonor', 1500)
                Player.InvokeVirtue("Honor")
                if wait_for_target_responsive(1500, True):
                    target_current_visible_hostile(nearest)
                    use_honor_fix = 0
                else:
                    use_honor_fix = 1

        # Slayer book: manual requests + auto-swap to match target
        if not nether_blast_pending and not nether_blast_ready:
            process_slayer_swap(nearest)

        if Timer.Check('spells') == True or Target.HasTarget():
            Misc.Pause(100)
            continue

        # Honor targeting or a Slayer equip can block while mobs spawn, die, or
        # move. Rebuild again immediately before combat and use the new nearest.
        all_victims = mobs_list(sv['attackrange'])
        visible_changelings = []
        if sv['attack_blue_changelings'] == 1:
            visible_changelings = changelings_list()
        if manage_summons(len(all_victims) > 0 or len(visible_changelings) > 0):
            Misc.Pause(100)
            continue
        victims = mobs_in_line_of_sight(all_victims, sv['attackrange'])
        victim_serials = set(mob.Serial for mob in victims)
        for changeling in visible_changelings:
            if changeling.Serial not in victim_serials:
                victims.append(changeling)
                victim_serials.add(changeling.Serial)
        if len(victims) == 0:
            last_attack_target = 0
            last_distance_marker = None
            Misc.Pause(100)
            continue
        victims_dist = [(mob, Player.DistanceTo(mob)) for mob in victims]
        nearby_count = len([m for m, distance in victims_dist if distance <= 8])
        current_nearest = min(victims_dist, key=lambda mob_dist: mob_dist[1])[0]
        # Do not restart merely because another mob became nearest between
        # scans. Crowded spawns can reorder continuously and starve all casts.
        nearest = current_nearest
        nether_blast_ready = nether_blast_ready_for(nearest, nearby_count)

        # Harmful spells establish combat themselves. Player.Attack shares the
        # server action lock and was blocking the spell cast that followed it.
        last_attack_target = nearest.Serial

        # Status overlay (throttled)
        status_overlay(nearest)

        # Debuffs → then attack spell
        nether_blast_pending = Timer.Check('netherblast_pending')
        nether_blast_ready = nether_blast_ready_for(nearest, nearby_count)
        if (nether_blast_pending or nether_blast_ready or
                not apply_bard(nearest, victims, victims_dist)):
            if (nether_blast_pending or nether_blast_ready or
                    not apply_debuffs(nearest, nearby_count)):
                # Nether Blast — always cast regardless of mob count
                nether_blast_attempted = False
                if sv['use_nether_blast'] == 1 and Timer.Check('spells') == False and Timer.Check('netherblast') == False and not Player.Paralized:
                    # Positioning aids: ground markers + auto-move to a valid tile
                    if real_skill_value('Mysticism') >= 90 and Player.DistanceTo(nearest) <= 8:
                        if sv.get('use_nb_show_tiles', 0) == 1:
                            nb_show_tiles(nearest)
                        elif _nb_marker_count > 0:
                            nb_clear_tiles()
                        if sv.get('use_nb_auto_move', 0) == 1 and nearby_count == 1:
                            nb_auto_move(nearest)
                    if Player.Mana >= mana_cost(40) and real_skill_value('Mysticism') >= 90 and Player.DistanceTo(nearest) <= 6:
                        if nearby_count == 1 and not is_cardinal_or_diagonal(nearest):
                            if Timer.Check('netherblast_hint') == False:
                                hint, tx, ty = nether_blast_move_hint(nearest)
                                arrow = _DIRECTION_ARROWS.get(hint, hint)
                                Player.HeadMessage(53, "NB: %s %s" % (arrow, hint))
                                Mobiles.Message(nearest, 53, "%s move %s to (%d,%d)" % (arrow, hint, tx, ty), False)
                                Misc.SendMessage("NB: step %s -> (%d, %d)" % (hint, tx, ty), 53)
                                Timer.Create('netherblast_hint', 2000)
                    if Player.Mana >= mana_cost(40) and real_skill_value('Mysticism') >= 90 and Player.DistanceTo(nearest) <= 6 and (nearby_count != 1 or is_cardinal_or_diagonal(nearest)):
                        nether_blast_attempted = True
                        if sv['use_messages'] == 1:
                            Player.HeadMessage(32, "Nether Blast!")
                        # Preserve the tile before casting. The mobile may be
                        # deleted while the mastery spell is producing its cursor.
                        nb_target_serial = nearest.Serial
                        nb_target_x = nearest.Position.X
                        nb_target_y = nearest.Position.Y
                        nb_target_z = nearest.Position.Z
                        pre_cast = time.time()
                        Timer.Create('netherblast_pending', 5100)
                        if Target.HasTarget():
                            # Finish an orphaned spell cursor instead of
                            # cancelling it, then retry Nether Blast.
                            place_nether_blast_target(nb_target_serial, nb_target_x,
                                                      nb_target_y, nb_target_z)
                            Timer.Create('spells', 250)
                            Timer.Create('netherblast_pending', 3000)
                            target_ready = False
                        else:
                            # Cooldown is cast-start to cast-start. Starting it
                            # after placement added the full cast time again.
                            Timer.Create('netherblast', 5100)
                            Spells.CastMastery("Nether Blast")
                            # Long enough for lag, but journal failures still
                            # abort immediately instead of blocking blindly.
                            target_ready = wait_for_target_responsive(6000, True)
                        if target_ready:
                            place_nether_blast_target(nb_target_serial, nb_target_x,
                                                      nb_target_y, nb_target_z)
                            Misc.Pause(max(250, serverdelay))
                            nb_failure = cast_failure_since(pre_cast)
                            if nb_failure:
                                if nb_failure == "interrupted":
                                    Timer.Create('spells', 1)
                                    Timer.Create('netherblast_pending', 1)
                                    Timer.Create('netherblast', 1)
                                else:
                                    if Timer.Check('spells') == False:
                                        Timer.Create('spells', 250)
                                    Timer.Create('netherblast_pending', 1000)
                                    Timer.Create('netherblast', 1000)
                            else:
                                Timer.Create('netherblast_pending', 1)
                                Timer.Create('spells', calc_castpause())
                        else:
                            # Cursor timeout/failure: synchronize briefly and
                            # never fire a second spell in this same loop.
                            nb_failure = cast_failure_since(pre_cast)
                            if nb_failure == "interrupted":
                                Timer.Create('spells', 1)
                                Timer.Create('netherblast_pending', 1)
                                Timer.Create('netherblast', 1)
                            else:
                                if Timer.Check('spells') == False:
                                    Timer.Create('spells', 250)
                                Timer.Create('netherblast_pending', 1000)
                                Timer.Create('netherblast', 1000)
                if not nether_blast_attempted and Timer.Check('netherblast_pending') == False:
                    if nearby_count >= sv['mass_threshold']:
                        cast_mass_target(nearest)
                    elif nearby_count >= sv['multi_threshold']:
                        cast_multi_target(nearest)
                    else:
                        cast_single_target(nearest)

    else:
        last_attack_target = 0
        last_distance_marker = None

        # No mobs — clear any leftover NB ground markers
        if _nb_marker_count > 0:
            nb_clear_tiles()

        # Slayer book: manual requests still processed while idle
        process_slayer_swap(None)

        # Passive buffs and healing (throttled like combat branch)
        if Timer.Check('buffcheck') == False or is_under_attack():
            Timer.Create('buffcheck', 750)
            keep_magic_reflect()
            keep_reactive_armor()
            keep_protection()
            keep_bless()
            attune_weapon()
            gift_of_life()
            gift_of_renewal()
            keep_mana_shield()
            keep_mystic_weapon()
            arcane_empowerment()
            keep_reaper_form()
            keep_wraith_form()
            keep_lich_form()
            keep_vampiric_embrace()
            keep_stone_form()
            bard_resilience()
            bard_perseverance()
            bard_inspire()
            bard_invigorate()
            pet_gift_of_life()
            pet_gift_of_renewal()
            bless_pets()
        # Status overlay (throttled)
        status_overlay(None)

        if sv['use_honor'] == 1 and Player.BuffsExist('Honored'):
            use_honor_fix = 1

        Misc.Pause(100)

    Misc.Pause(100)
