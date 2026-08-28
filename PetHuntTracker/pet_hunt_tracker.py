### Standalone pet hunt tracker by Mike|Walker for Razor Enhanced / UOAlive

import json
import os
import time

from System import Byte
from System.Collections.Generic import List


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

TRACKER_VERSION = "1.3.1"
SCAN_RANGE = 40
REFRESH_MS = 1000
SAVE_INTERVAL_MS = 10000
BACKUP_INTERVAL_SECONDS = 3600
BACKUP_RETENTION = 30
RECENT_SERIAL_SECONDS = 86400
LEGENDARY_ASSOCIATION_SECONDS = 60

MAIN_GUMP_ID = 947580
OPTIONS_GUMP_ID = 947581
MAIN_GUMP_X = 10
MAIN_GUMP_Y = 10
OPTIONS_GUMP_X = 10
OPTIONS_GUMP_Y = 10

try:
    SCRIPT_DIRECTORY = os.path.dirname(os.path.abspath(__file__))
except:
    SCRIPT_DIRECTORY = Misc.CurrentScriptDirectory()
DATA_FILE = os.path.join(SCRIPT_DIRECTORY, "pet_hunt_tracker.json")
BACKUP_DIRECTORY = os.path.join(
    SCRIPT_DIRECTORY, "pet_hunt_tracker_backups")

RARITIES = (
    ("normal", "Normal", 1150),
    ("exotic", "Exotic", 68),
    ("exquisite", "Exquisite", 1153),
    ("rare", "Rare", 88),
    ("legendary", "Legendary", 33),
)

# Body IDs cover standard forms. Name aliases also catch custom variants whose
# body changes, such as Shadowmanes and legendary Murder Bears.
PETS = (
    {
        "key": "kirin",
        "label": "Ki-Rin",
        "bodies": (0x0084,),
        "aliases": ("ki-rin", "ki rin", "khamet ki-rin"),
    },
    {
        "key": "nightmare",
        "label": "Nightmare",
        "bodies": (0x0074, 0x00B1, 0x00B2, 0x00B3),
        "aliases": ("nightmare", "shadowmane"),
    },
    {
        "key": "undead_ossein_ram",
        "label": "Undead Ossein Ram",
        "bodies": (0x0591,),
        "aliases": ("undead ossein ram", "ossein ram"),
    },
    {
        "key": "shadow_wyrm",
        "label": "Shadow Wyrm",
        "bodies": (0x006A,),
        "aliases": ("shadow wyrm",),
    },
    {
        "key": "phoenix",
        "label": "Phoenix",
        "bodies": (0x0340,),
        "aliases": ("phoenix",),
    },
    {
        "key": "cu_sidhe",
        "label": "Cu Sidhe",
        "bodies": (0x0115,),
        "aliases": ("cu sidhe", "cusidhe"),
    },
    {
        "key": "polar_bear",
        "label": "Polar Bear",
        "bodies": (0x00D5,),
        "aliases": ("polar bear", "murder bear"),
    },
    {
        "key": "tsuki_wolf",
        "label": "Tsuki Wolf",
        "bodies": (0x00FA,),
        "aliases": ("tsuki wolf",),
    },
)

HOSTILE_NOTORIETIES = List[Byte](bytes([3, 4, 5, 6]))


# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------

RARITY_KEYS = [rarity[0] for rarity in RARITIES]
PET_KEYS = [pet["key"] for pet in PETS]
PET_BY_KEY = dict((pet["key"], pet) for pet in PETS)


def empty_counts():
    return dict(
        (pet_key, dict((rarity, 0) for rarity in RARITY_KEYS))
        for pet_key in PET_KEYS)


def default_pet_rarities():
    return dict(
        (pet_key, dict((rarity, True) for rarity in RARITY_KEYS))
        for pet_key in PET_KEYS)


def default_data():
    return {
        "version": 4,
        "total_seconds": 0.0,
        "pet_seconds": dict((pet_key, 0.0) for pet_key in PET_KEYS),
        "counts": empty_counts(),
        "enabled_pets": dict((pet_key, True) for pet_key in PET_KEYS),
        "enabled_pet_rarities": default_pet_rarities(),
        "collapsed_pets": dict((pet_key, False) for pet_key in PET_KEYS),
        "recent_serials": {},
    }


def load_data():
    data = default_data()
    if not os.path.exists(DATA_FILE):
        return data
    try:
        with open(DATA_FILE, "r") as data_file:
            saved = json.load(data_file)
        data["total_seconds"] = float(saved.get("total_seconds", 0.0))
        saved_counts = saved.get("counts", {})
        saved_pet_seconds = saved.get("pet_seconds", {})
        saved_pet_rarities = saved.get("enabled_pet_rarities", {})
        legacy_rarities = saved.get("enabled_rarities", {})
        for pet_key in PET_KEYS:
            saved_pet = saved_counts.get(pet_key, {})
            for rarity in RARITY_KEYS:
                data["counts"][pet_key][rarity] = int(
                    saved_pet.get(rarity, 0))
            legacy_seconds = (
                data["total_seconds"] if pet_key in saved_counts else 0.0)
            data["pet_seconds"][pet_key] = float(
                saved_pet_seconds.get(pet_key, legacy_seconds))
            data["enabled_pets"][pet_key] = bool(
                saved.get("enabled_pets", {}).get(pet_key, True))
            data["collapsed_pets"][pet_key] = bool(
                saved.get("collapsed_pets", {}).get(pet_key, False))
            for rarity in RARITY_KEYS:
                data["enabled_pet_rarities"][pet_key][rarity] = bool(
                    saved_pet_rarities.get(pet_key, {}).get(
                        rarity, legacy_rarities.get(rarity, True)))
        data["recent_serials"] = saved.get("recent_serials", {})
    except Exception as error:
        Player.HeadMessage(33, "Pet tracker data load failed: %s" % error)
    return data


data = load_data()
session_counts = empty_counts()
session_pet_seconds = dict((pet_key, 0.0) for pet_key in PET_KEYS)
session_seconds = 0.0
last_time_update = time.time()
last_save_at = time.time()
last_backup_at = 0.0
session_seen_serials = set()
pending_property_attempts = {}
known_visible_serials = set()
legendary_journal_timestamp = time.time()
legendary_pending_until = 0.0
options_open = False
mini_pet_key = None


def update_time():
    global session_seconds, last_time_update
    now = time.time()
    elapsed = max(0.0, now - last_time_update)
    last_time_update = now
    tracking_active = any(
        data["enabled_pets"][pet_key] and
        any(data["enabled_pet_rarities"][pet_key].values())
        for pet_key in PET_KEYS)
    if tracking_active:
        session_seconds += elapsed
        data["total_seconds"] += elapsed
        for pet_key in PET_KEYS:
            if (data["enabled_pets"][pet_key] and
                    any(data["enabled_pet_rarities"][pet_key].values())):
                session_pet_seconds[pet_key] += elapsed
                data["pet_seconds"][pet_key] += elapsed


def prune_recent_serials():
    cutoff = time.time() - RECENT_SERIAL_SECONDS
    recent = data["recent_serials"]
    for serial_text in list(recent.keys()):
        try:
            if float(recent[serial_text]) < cutoff:
                del recent[serial_text]
        except:
            del recent[serial_text]


def save_data():
    global last_save_at
    prune_recent_serials()
    temporary = DATA_FILE + ".tmp"
    try:
        with open(temporary, "w") as data_file:
            json.dump(data, data_file, indent=2, sort_keys=True)
        if os.path.exists(DATA_FILE):
            os.remove(DATA_FILE)
        os.rename(temporary, DATA_FILE)
        last_save_at = time.time()
    except Exception as error:
        Player.HeadMessage(33, "Pet tracker save failed: %s" % error)


def backup_data(force=False):
    global last_backup_at
    now = time.time()
    if not force and now - last_backup_at < BACKUP_INTERVAL_SECONDS:
        return
    if not os.path.exists(DATA_FILE):
        return
    try:
        if not os.path.exists(BACKUP_DIRECTORY):
            os.makedirs(BACKUP_DIRECTORY)
        filename = "pet_hunt_tracker_%s.json" % time.strftime(
            "%Y%m%d_%H%M%S")
        destination = os.path.join(BACKUP_DIRECTORY, filename)
        temporary = destination + ".tmp"
        with open(DATA_FILE, "rb") as source_file:
            contents = source_file.read()
        with open(temporary, "wb") as backup_file:
            backup_file.write(contents)
        if os.path.exists(destination):
            os.remove(destination)
        os.rename(temporary, destination)

        backups = sorted(
            filename for filename in os.listdir(BACKUP_DIRECTORY)
            if (filename.startswith("pet_hunt_tracker_") and
                filename.endswith(".json")))
        while len(backups) > BACKUP_RETENTION:
            oldest = backups.pop(0)
            os.remove(os.path.join(BACKUP_DIRECTORY, oldest))
        last_backup_at = now
    except Exception as error:
        Player.HeadMessage(33, "Pet tracker backup failed: %s" % error)


# ---------------------------------------------------------------------------
# Formatting and gumps
# ---------------------------------------------------------------------------

def format_time(seconds):
    seconds = int(seconds)
    days = seconds // 86400
    hours = (seconds // 3600) % 24
    minutes = (seconds // 60) % 60
    if days > 0:
        return "%id %02ih %02im" % (days, hours, minutes)
    return "%02ih %02im" % (hours, minutes)


def format_short_time(seconds):
    seconds = int(seconds)
    if seconds < 60:
        return "%is" % seconds
    if seconds < 3600:
        return "%im%02is" % (seconds // 60, seconds % 60)
    if seconds < 86400:
        return "%ih%02im" % (seconds // 3600, (seconds // 60) % 60)
    return "%id%02ih" % (seconds // 86400, (seconds // 3600) % 24)


def count_total(counts, pet_key):
    return sum(counts[pet_key][rarity] for rarity in RARITY_KEYS)


def chance_text(count, observed):
    if observed <= 0:
        return "0.00%"
    return "%.2f%%" % (float(count) * 100.0 / observed)


def average_amount_text(count, observed):
    if count <= 0:
        return "--"
    return "%.1f" % (float(observed) / count)


def average_time_text(count, seconds):
    if count <= 0:
        return "--"
    return format_short_time(float(seconds) / count)


def active_pets():
    return [pet for pet in PETS if data["enabled_pets"][pet["key"]]]


def active_rarities():
    return [rarity for rarity in RARITIES
            if any(
                data["enabled_pets"][pet["key"]] and
                data["enabled_pet_rarities"][pet["key"]][rarity[0]]
                for pet in PETS)]


def pet_rarities(pet_key):
    return [rarity for rarity in RARITIES
            if data["enabled_pet_rarities"][pet_key][rarity[0]]]


def draw_mini_gump(pet):
    pet_key = pet["key"]
    rarities = pet_rarities(pet_key)
    width = 660
    height = 92 + max(1, len(rarities)) * 24
    session_observed = count_total(session_counts, pet_key)
    total_observed = count_total(data["counts"], pet_key)

    gd = Gumps.CreateGump(movable=True)
    Gumps.AddPage(gd, 0)
    Gumps.AddBackground(gd, 0, 0, width, height, 30546)
    Gumps.AddAlphaRegion(gd, 0, 0, width, height)
    Gumps.AddLabel(
        gd, 8, 5, 68, "%s - Pet Hunt Tracker v%s" % (
            pet["label"], TRACKER_VERSION))
    Gumps.AddButton(gd, width - 70, 5, 9762, 9763, 3, 1, 0)
    Gumps.AddLabel(gd, width - 50, 5, 1153, "BACK")
    Gumps.AddLabel(
        gd, 8, 27, 1153,
        "Observed %i / %i     Time %s / %s" % (
            session_observed, total_observed,
            format_time(session_pet_seconds[pet_key]),
            format_time(data["pet_seconds"][pet_key])))
    Gumps.AddLabel(gd, 8, 51, 1150, "RARITY")
    Gumps.AddLabel(gd, 125, 51, 1150, "COUNT")
    Gumps.AddLabel(gd, 215, 51, 1150, "CHANCE")
    Gumps.AddLabel(gd, 355, 51, 1150, "AVG AMOUNT")
    Gumps.AddLabel(gd, 485, 51, 1150, "AVG TIME")

    if len(rarities) == 0:
        Gumps.AddLabel(gd, 8, 73, 33, "No rarity enabled")
    for row, rarity in enumerate(rarities):
        rarity_key = rarity[0]
        y = 73 + row * 24
        session_count = session_counts[pet_key][rarity_key]
        total_count = data["counts"][pet_key][rarity_key]
        Gumps.AddLabel(gd, 8, y, rarity[2], rarity[1])
        Gumps.AddLabel(gd, 125, y, rarity[2], "%i / %i" % (
            session_count, total_count))
        Gumps.AddLabel(gd, 215, y, rarity[2], "%s / %s" % (
            chance_text(session_count, session_observed),
            chance_text(total_count, total_observed)))
        Gumps.AddLabel(gd, 355, y, 1150, "%s / %s" % (
            average_amount_text(session_count, session_observed),
            average_amount_text(total_count, total_observed)))
        Gumps.AddLabel(gd, 485, y, 1150, "%s / %s" % (
            average_time_text(
                session_count, session_pet_seconds[pet_key]),
            average_time_text(
                total_count, data["pet_seconds"][pet_key])))

    Gumps.CloseGump(MAIN_GUMP_ID)
    Gumps.SendGump(
        MAIN_GUMP_ID, Player.Serial, MAIN_GUMP_X, MAIN_GUMP_Y,
        gd.gumpDefinition, gd.gumpStrings)


def draw_main_gump():
    pets = active_pets()
    if (mini_pet_key in PET_BY_KEY and
            data["enabled_pets"].get(mini_pet_key, False)):
        draw_mini_gump(PET_BY_KEY[mini_pet_key])
        return

    rarities = active_rarities()
    label_width = 180
    column_width = 125
    width = max(520, label_width + len(rarities) * column_width + 10)
    row_heights = [42 if data["collapsed_pets"][pet["key"]] else 76
                   for pet in pets]
    content_height = sum(row_heights) if len(row_heights) > 0 else 42
    height = 96 + content_height
    all_collapsed = bool(pets) and all(
        data["collapsed_pets"][pet["key"]] for pet in pets)

    gd = Gumps.CreateGump(movable=True)
    Gumps.AddPage(gd, 0)
    Gumps.AddBackground(gd, 0, 0, width, height, 30546)
    Gumps.AddAlphaRegion(gd, 0, 0, width, height)
    Gumps.AddLabel(gd, 8, 5, 68, "Pet Hunt Tracker v%s" % TRACKER_VERSION)
    Gumps.AddButton(gd, width - 190, 5, 9762, 9763, 2, 1, 0)
    Gumps.AddLabel(
        gd, width - 170, 5, 1153,
        "EXPAND" if all_collapsed else "COLLAPSE")
    Gumps.AddButton(gd, width - 82, 5, 9762, 9763, 1, 1, 0)
    Gumps.AddLabel(gd, width - 62, 5, 1153, "OPTIONS")
    Gumps.AddLabel(
        gd, 8, 27, 1150,
        "Session / total: C=count  %=chance  N=avg amount  T=avg time")
    Gumps.AddLabel(gd, 8, 49, 1153, "Pet and observed totals")

    for index, rarity in enumerate(rarities):
        x = label_width + index * column_width
        Gumps.AddLabel(gd, x, 49, rarity[2], rarity[1][:10])

    if len(pets) == 0:
        Gumps.AddLabel(gd, 8, 71, 33, "No pets enabled")
    y = 71
    for row, pet in enumerate(pets):
        pet_key = pet["key"]
        collapsed = data["collapsed_pets"][pet_key]
        pet_index = PET_KEYS.index(pet_key)
        Gumps.AddButton(
            gd, 8, y, 9762, 9763, 300 + pet_index, 1, 0)
        Gumps.AddLabel(gd, 28, y, 1153, "+" if collapsed else "-")
        Gumps.AddLabel(gd, 45, y, 1150, pet["label"][:20])
        session_observed = count_total(session_counts, pet_key)
        total_observed = count_total(data["counts"], pet_key)
        Gumps.AddButton(
            gd, 8, y + 20, 9762, 9763, 400 + pet_index, 1, 0)
        Gumps.AddLabel(gd, 28, y + 20, 68, "MINI")
        Gumps.AddLabel(
            gd, 75, y + 20, 1153,
            "O %i / %i" % (session_observed, total_observed))
        for column, rarity in enumerate(rarities):
            rarity_key = rarity[0]
            x = label_width + column * column_width
            if not data["enabled_pet_rarities"][pet_key][rarity_key]:
                continue
            session_count = session_counts[pet_key][rarity_key]
            total_count = data["counts"][pet_key][rarity_key]
            Gumps.AddLabel(gd, x, y, rarity[2], "C %i / %i" % (
                session_count, total_count))
            if collapsed:
                continue
            Gumps.AddLabel(gd, x, y + 18, rarity[2], "%% %s / %s" % (
                chance_text(session_count, session_observed),
                chance_text(total_count, total_observed)))
            Gumps.AddLabel(gd, x, y + 36, 1150, "N %s / %s" % (
                average_amount_text(session_count, session_observed),
                average_amount_text(total_count, total_observed)))
            Gumps.AddLabel(gd, x, y + 54, 1150, "T %s / %s" % (
                average_time_text(
                    session_count, session_pet_seconds[pet_key]),
                average_time_text(
                    total_count, data["pet_seconds"][pet_key])))
        y += 42 if collapsed else 76

    footer_y = y + 2
    Gumps.AddLabel(
        gd, 8, footer_y, 1153,
        "Time  %s / %s" % (
            format_time(session_seconds),
            format_time(data["total_seconds"])))
    Gumps.CloseGump(MAIN_GUMP_ID)
    Gumps.SendGump(
        MAIN_GUMP_ID, Player.Serial, MAIN_GUMP_X, MAIN_GUMP_Y,
        gd.gumpDefinition, gd.gumpStrings)


def add_toggle(gd, x, y, button_id, enabled, label):
    Gumps.AddButton(gd, x, y, 9762, 9763, button_id, 1, 0)
    Gumps.AddLabel(
        gd, x + 20, y, 68 if enabled else 33,
        "[ON] %s" % label if enabled else "[OFF] %s" % label)


def draw_options_gump():
    pet_width = 155
    tracking_width = 72
    rarity_width = 92
    width = pet_width + tracking_width + len(RARITIES) * rarity_width + 10
    height = 78 + len(PETS) * 26
    gd = Gumps.CreateGump(movable=True)
    Gumps.AddPage(gd, 0)
    Gumps.AddBackground(gd, 0, 0, width, height, 30546)
    Gumps.AddAlphaRegion(gd, 0, 0, width, height)
    Gumps.AddLabel(gd, 8, 5, 68, "Pet Hunt Tracker options")
    Gumps.AddButton(gd, width - 65, 5, 9762, 9763, 1, 1, 0)
    Gumps.AddLabel(gd, width - 45, 5, 1153, "DONE")
    Gumps.AddLabel(gd, 8, 29, 1150, "PET")
    Gumps.AddLabel(gd, pet_width, 29, 1150, "TRACK")
    for rarity_index, rarity in enumerate(RARITIES):
        Gumps.AddLabel(
            gd, pet_width + tracking_width + rarity_index * rarity_width,
            29, rarity[2], rarity[1][:10])

    for pet_index, pet in enumerate(PETS):
        y = 51 + pet_index * 26
        pet_key = pet["key"]
        Gumps.AddLabel(gd, 8, y, 1150, pet["label"][:20])
        add_toggle(
            gd, pet_width, y, 100 + pet_index,
            data["enabled_pets"][pet_key], "")
        for rarity_index, rarity in enumerate(RARITIES):
            enabled = data["enabled_pet_rarities"][pet_key][rarity[0]]
            x = pet_width + tracking_width + rarity_index * rarity_width
            button_id = 1000 + pet_index * len(RARITIES) + rarity_index
            Gumps.AddButton(gd, x, y, 9762, 9763, button_id, 1, 0)
            Gumps.AddLabel(
                gd, x + 20, y, 68 if enabled else 33,
                "ON" if enabled else "OFF")

    Gumps.CloseGump(OPTIONS_GUMP_ID)
    Gumps.SendGump(
        OPTIONS_GUMP_ID, Player.Serial, OPTIONS_GUMP_X, OPTIONS_GUMP_Y,
        gd.gumpDefinition, gd.gumpStrings)


def read_gump_button(gump_id):
    Misc.Pause(REFRESH_MS)
    response = Gumps.GetGumpData(gump_id)
    Gumps.CloseGump(gump_id)
    if response is None:
        return 0
    try:
        return int(response.buttonid)
    except:
        return 0


def handle_button(button):
    global options_open, mini_pet_key
    if not options_open:
        if button == 1:
            options_open = True
        elif button == 2:
            pets = active_pets()
            collapse = not (bool(pets) and all(
                data["collapsed_pets"][pet["key"]] for pet in pets))
            for pet in pets:
                data["collapsed_pets"][pet["key"]] = collapse
            save_data()
        elif button == 3:
            mini_pet_key = None
        elif 300 <= button < 300 + len(PETS):
            pet_key = PETS[button - 300]["key"]
            data["collapsed_pets"][pet_key] = not (
                data["collapsed_pets"][pet_key])
            save_data()
        elif 400 <= button < 400 + len(PETS):
            mini_pet_key = PETS[button - 400]["key"]
        return
    if button == 1:
        options_open = False
        return
    if 100 <= button < 100 + len(PETS):
        pet_key = PETS[button - 100]["key"]
        data["enabled_pets"][pet_key] = not data["enabled_pets"][pet_key]
        save_data()
    elif 1000 <= button < 1000 + len(PETS) * len(RARITIES):
        offset = button - 1000
        pet_index = offset // len(RARITIES)
        rarity_index = offset % len(RARITIES)
        pet_key = PETS[pet_index]["key"]
        rarity_key = RARITIES[rarity_index][0]
        current = data["enabled_pet_rarities"][pet_key][rarity_key]
        data["enabled_pet_rarities"][pet_key][rarity_key] = not current
        save_data()


# ---------------------------------------------------------------------------
# Spawn detection
# ---------------------------------------------------------------------------

def visible_wild_mobiles():
    mobile_filter = Mobiles.Filter()
    mobile_filter.Enabled = True
    mobile_filter.RangeMax = SCAN_RANGE
    mobile_filter.Notorieties = HOSTILE_NOTORIETIES
    mobile_filter.Friend = False
    mobile_filter.IgnorePets = True
    mobile_filter.CheckIgnoreObject = False
    mobile_filter.CheckLineOfSight = False
    return Mobiles.ApplyFilter(mobile_filter)


def property_lines(mobile):
    lines = []
    try:
        Mobiles.WaitForProps(mobile, 300)
    except:
        pass
    empty_after_content = 0
    for index in range(12):
        try:
            line = (Mobiles.GetPropStringByIndex(mobile, index) or "").strip()
        except:
            line = ""
        if line:
            lines.append(line)
            empty_after_content = 0
        elif len(lines) > 0:
            empty_after_content += 1
            if empty_after_content >= 2:
                break
    return lines


def identify_pet(mobile, lines):
    text = " ".join([mobile.Name or ""] + lines).lower()
    for pet in PETS:
        if any(alias in text for alias in pet["aliases"]):
            return pet
    for pet in PETS:
        if int(mobile.MobileID) in pet["bodies"]:
            return pet
    return None


def identify_rarity(mobile, lines):
    values = [mobile.Name or ""] + lines
    normalized = [value.strip().lower() for value in values]
    checks = (
        ("legendary", "legendary"),
        ("rare", "rare"),
        ("exquisite", "exquisite"),
        ("exotic", "exotic"),
    )
    for rarity, marker in checks:
        for value in normalized:
            words = value.replace("[", " ").replace("]", " ")
            words = words.replace(":", " ").replace("-", " ").split()
            if marker in words:
                return rarity
    return "normal"


def check_legendary_journal():
    global legendary_journal_timestamp, legendary_pending_until
    previous = legendary_journal_timestamp
    latest = previous
    found = False
    for entry in Journal.GetJournalEntry(previous):
        if entry.Timestamp <= previous:
            continue
        if entry.Timestamp > latest:
            latest = entry.Timestamp
        text = (entry.Text or "").lower()
        if ("you sense a legendary" in text or
                "senses a legendary creature" in text):
            found = True
    legendary_journal_timestamp = latest
    if found:
        legendary_pending_until = time.time() + LEGENDARY_ASSOCIATION_SECONDS


def serial_recently_counted(serial):
    if serial in session_seen_serials:
        return True
    serial_text = str(int(serial))
    timestamp = data["recent_serials"].get(serial_text)
    if timestamp is None:
        return False
    try:
        return float(timestamp) >= time.time() - RECENT_SERIAL_SECONDS
    except:
        return False


def record_spawn(mobile, pet, rarity):
    serial = int(mobile.Serial)
    pet_key = pet["key"]
    session_seen_serials.add(serial)
    data["recent_serials"][str(serial)] = time.time()
    session_counts[pet_key][rarity] += 1
    data["counts"][pet_key][rarity] += 1
    save_data()
    Mobiles.Message(
        mobile, 68,
        "%s %s #%i" % (
            rarity.upper(), pet["label"],
            data["counts"][pet_key][rarity]))


def scan_spawns():
    global known_visible_serials, legendary_pending_until
    mobiles = visible_wild_mobiles()
    current_serials = set(int(mobile.Serial) for mobile in mobiles)
    candidates = []

    for mobile in mobiles:
        serial = int(mobile.Serial)
        if serial_recently_counted(serial):
            continue
        pet = identify_pet(mobile, [])
        if pet is None or not data["enabled_pets"][pet["key"]]:
            continue
        lines = property_lines(mobile)
        if len(lines) == 0:
            attempts = pending_property_attempts.get(serial, 0) + 1
            pending_property_attempts[serial] = attempts
            if attempts < 3:
                continue
        pet = identify_pet(mobile, lines) or pet
        rarity = identify_rarity(mobile, lines)
        candidates.append((mobile, pet, rarity, serial not in known_visible_serials))

    legendary_candidates = [
        candidate for candidate in candidates
        if (candidate[2] == "normal" and candidate[3] and
            data["enabled_pet_rarities"][candidate[1]["key"]][
                "legendary"] and
            time.time() <= legendary_pending_until)]
    if len(legendary_candidates) == 1:
        forced = legendary_candidates[0]
        candidates.remove(forced)
        candidates.append((forced[0], forced[1], "legendary", forced[3]))
        legendary_pending_until = 0.0

    for mobile, pet, rarity, unused_new in candidates:
        if not data["enabled_pet_rarities"][pet["key"]].get(
                rarity, False):
            continue
        record_spawn(mobile, pet, rarity)

    known_visible_serials = current_serials
    for serial in list(pending_property_attempts.keys()):
        if serial not in current_serials or serial in session_seen_serials:
            del pending_property_attempts[serial]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

save_data()
backup_data(True)
Player.HeadMessage(68, "Pet Hunt Tracker v%s started" % TRACKER_VERSION)
draw_main_gump()

try:
    while Player.Connected:
        active_gump = OPTIONS_GUMP_ID if options_open else MAIN_GUMP_ID
        button = read_gump_button(active_gump)
        update_time()
        handle_button(button)
        check_legendary_journal()
        scan_spawns()
        if time.time() - last_save_at >= SAVE_INTERVAL_MS / 1000.0:
            save_data()
        backup_data()
        if options_open:
            draw_options_gump()
        else:
            draw_main_gump()
finally:
    update_time()
    save_data()
    Gumps.CloseGump(MAIN_GUMP_ID)
    Gumps.CloseGump(OPTIONS_GUMP_ID)
