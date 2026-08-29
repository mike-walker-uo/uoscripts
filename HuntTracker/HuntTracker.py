# -*- coding: utf-8 -*-
from __future__ import print_function

import os
import re
import sys
import time

from System import Byte
from System.Collections.Generic import List


try:
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
except Exception:
    SCRIPT_DIR = Misc.CurrentScriptDirectory()
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from hunttracker_core import (  # noqa: E402
    SessionTracker,
    atomic_json_write,
    export_session,
    fmt_number,
    fmt_time,
    history_records,
    load_config,
    observation,
    read_json,
    update_history,
)


GUMP_ID = 0x48544B52
CONFIG_PATH = os.path.join(SCRIPT_DIR, "hunttracker_config.json")
DATA_DIR = os.path.join(SCRIPT_DIR, "data")
LOG_DIR = os.path.join(SCRIPT_DIR, "logs")
CHECKPOINT_PATH = os.path.join(DATA_DIR, "HuntTracker_checkpoint.json")
HISTORY_PATH = os.path.join(DATA_DIR, "HuntTracker_history.json")

HUE_TITLE = 68
HUE_HEADER = 52
HUE_KEY = 1153
HUE_VALUE = 1150
HUE_SUB = 88
HUE_WARN = 33
HUE_MUTED = 900
HUE_GOOD = 63

BUTTON_RESET = 1
BUTTON_PAUSE = 2
BUTTON_SAVE = 3
BUTTON_STOP = 4
BUTTON_COMPACT = 5
BUTTON_OVERVIEW = 10
BUTTON_MONSTERS = 11
BUTTON_LOOT = 12
BUTTON_RECORDS = 13

PAGE_BUTTONS = {
    BUTTON_OVERVIEW: "overview",
    BUTTON_MONSTERS: "monsters",
    BUTTON_LOOT: "loot",
    BUTTON_RECORDS: "records",
}


def _byte_list(values):
    result = List[Byte]()
    for value in values:
        result.Add(Byte(int(value)))
    return result


class RazorAdapter(object):
    EQUIPMENT_LAYERS = [
        "RightHand", "LeftHand", "Shoes", "Pants", "Shirt", "Head",
        "Gloves", "Ring", "Neck", "Waist", "InnerTorso", "Bracelet",
        "MiddleTorso", "Earrings", "Arms", "Cloak", "OuterTorso",
        "OuterLegs", "InnerLegs",
    ]

    def __init__(self, config):
        self.config = config
        self._filter = self._create_filter()
        self._reported_errors = set()

    def _create_filter(self):
        settings = self.config["tracking"]
        mobile_filter = Mobiles.Filter()
        mobile_filter.Enabled = True
        mobile_filter.RangeMax = int(settings["mobile_range"])
        mobile_filter.Notorieties = _byte_list(settings["notorieties"])
        if hasattr(mobile_filter, "IgnorePets"):
            mobile_filter.IgnorePets = bool(settings["ignore_pets"])
        if hasattr(mobile_filter, "CheckLineOfSight"):
            mobile_filter.CheckLineOfSight = bool(settings["check_line_of_sight"])
        elif hasattr(mobile_filter, "CheckLineOfSite"):
            mobile_filter.CheckLineOfSite = bool(settings["check_line_of_sight"])
        return mobile_filter

    def report_once(self, key, message):
        if key in self._reported_errors:
            return
        self._reported_errors.add(key)
        self.message(message, HUE_WARN)

    def message(self, text, hue=HUE_SUB):
        Misc.SendMessage("[HuntTracker] " + str(text), int(hue))

    def head_message(self, text, hue=HUE_TITLE):
        Player.HeadMessage(int(hue), str(text))

    def alert(self, text):
        self.message(text, HUE_TITLE)
        self.head_message(text, HUE_TITLE)
        alerts = self.config.get("alerts", {})
        if alerts.get("sound"):
            sound_id = int(alerts.get("sound_id", 85))
            try:
                Sound.PlaySound(sound_id, Player.Position)
            except Exception:
                try:
                    Sound.PlaySound(sound_id)
                except Exception:
                    try:
                        Misc.Beep()
                    except Exception:
                        self.report_once("sound", "Sound alerts are unavailable in this client build")

    def damage(self, serial):
        try:
            value = DPSMeter.GetDamage(int(serial))
            return max(0, int(value or 0))
        except Exception as error:
            self.report_once("dps", "DPSMeter read failed: " + str(error))
            return 0

    def observations(self):
        settings = self.config["tracking"]
        ignored = [str(name).lower() for name in settings.get("ignored_names", [])]
        result = []
        try:
            mobiles = Mobiles.ApplyFilter(self._filter)
        except Exception as error:
            self.report_once("mobiles", "Mobile scan failed: " + str(error))
            return result

        for mobile in mobiles:
            try:
                name = str(mobile.Name or "Unknown")
                if any(fragment in name.lower() for fragment in ignored):
                    continue
                if settings.get("exclude_humans") and bool(mobile.IsHuman):
                    continue
                hits = int(mobile.Hits) if mobile.Hits is not None else -1
                position = mobile.Position
                try:
                    map_id = int(mobile.Map)
                except Exception:
                    map_id = self.location()["map"]
                result.append(observation(
                    mobile.Serial,
                    name,
                    hits,
                    self.damage(mobile.Serial),
                    bool(mobile.Deleted),
                    map_id,
                    int(position.X),
                    int(position.Y),
                ))
            except Exception as error:
                self.report_once("mobile_fields", "One mobile could not be read: " + str(error))
        return result

    def player_gold(self):
        try:
            return int(Player.Gold)
        except Exception:
            return 0

    def loot_counts(self):
        counts = {}
        for entry in self.config.get("loot", []):
            name = str(entry["name"])
            try:
                if entry.get("use_player_gold"):
                    counts[name] = self.player_gold()
                else:
                    counts[name] = int(Items.BackpackCount(
                        int(entry["item_id"]), int(entry.get("hue", -1))
                    ))
            except Exception as error:
                counts[name] = 0
                self.report_once("loot_" + name, "Could not count %s: %s" % (name, error))
        return counts

    def location(self):
        try:
            position = Player.Position
            try:
                map_id = int(Player.Map)
            except Exception:
                map_id = 0
            return {"map": map_id, "x": int(position.X), "y": int(position.Y)}
        except Exception:
            return {"map": 0, "x": 0, "y": 0}

    def weight_percent(self):
        try:
            maximum = float(Player.MaxWeight)
            return float(Player.Weight) * 100.0 / maximum if maximum > 0 else 0.0
        except Exception:
            return 0.0

    def minimum_durability(self):
        lowest = None
        pattern = re.compile(r"durability\s+(\d+)\s*/\s*(\d+)", re.IGNORECASE)
        for layer in self.EQUIPMENT_LAYERS:
            try:
                item = Player.GetItemOnLayer(layer)
                if item is None:
                    continue
                lines = Items.GetPropStringList(item)
                for line in lines:
                    match = pattern.search(str(line))
                    if match:
                        current = int(match.group(1))
                        candidate = {"name": str(item.Name or layer), "current": current,
                                     "maximum": int(match.group(2))}
                        if lowest is None or current < lowest["current"]:
                            lowest = candidate
            except Exception:
                continue
        return lowest


class HuntGump(object):
    def __init__(self, config):
        self.config = config
        self.reset_armed_until = 0.0

    @property
    def ui(self):
        return self.config["ui"]

    def capture_position(self, data):
        if data is None or not self.ui.get("remember_position"):
            return False
        changed = False
        for field, key in (("x", "x"), ("X", "x"), ("gumpX", "x"),
                           ("y", "y"), ("Y", "y"), ("gumpY", "y")):
            if hasattr(data, field):
                value = int(getattr(data, field))
                if value >= 0 and self.ui.get(key) != value:
                    self.ui[key] = value
                    changed = True
        return changed

    def poll_action(self):
        try:
            data = Gumps.GetGumpData(GUMP_ID)
            if data is None or not bool(data.hasResponse):
                return None, False
            moved = self.capture_position(data)
            button = int(data.buttonid)
            data.buttonid = -1
            return button, moved
        except Exception:
            return None, False

    def close(self):
        try:
            Gumps.CloseGump(GUMP_ID)
        except Exception:
            pass

    def _label(self, data, x, y, hue, text):
        Gumps.AddLabel(data, int(x), int(y), int(hue), str(text))

    def _button(self, data, x, y, button_id, label, hue=HUE_KEY):
        Gumps.AddButton(data, int(x), int(y), 9762, 9763, int(button_id), 1, 0)
        self._label(data, x + 20, y, hue, label)

    def _row(self, data, y, label, value, sub="", value_hue=HUE_VALUE):
        self._label(data, 10, y, HUE_KEY, label)
        self._label(data, 155, y, value_hue, value)
        if sub:
            self._label(data, 285, y, HUE_SUB, sub)
        return y + 18

    def _divider(self, data, y, width):
        Gumps.AddImageTiled(data, 4, y, width - 8, 2, 30547)
        return y + 7

    def draw(self, tracker, history, now=None):
        current = float(time.time() if now is None else now)
        compact = bool(self.ui.get("compact"))
        width = 330 if compact else 440
        height = 154 if compact else 390
        self.close()
        data = Gumps.CreateGump(movable=True)
        Gumps.AddPage(data, 0)
        Gumps.AddBackground(data, 0, 0, width, height, 30546)
        Gumps.AddAlphaRegion(data, 0, 0, width, height)
        self._label(data, 10, 5, HUE_TITLE, "HuntTracker v1.0")
        status = "PAUSED" if tracker.paused else "ACTIVE"
        self._label(data, width - 75, 5, HUE_WARN if tracker.paused else HUE_GOOD, status)

        metrics = tracker.metrics()
        encounter = tracker.current_encounter(current)
        if compact:
            y = 27
            y = self._row(data, y, "Runtime / kills:", "%s / %d" % (
                fmt_time(metrics["elapsed"]), metrics["kills"]))
            y = self._row(data, y, "Gold / hour:", fmt_number(metrics["gold_per_hour"]))
            y = self._row(data, y, "Damage / DPS:", "%s / %.1f" % (
                fmt_number(metrics["damage"]), metrics["average_dps"]))
            target = encounter["name"][:22] if encounter else "No active encounter"
            y = self._row(data, y, "Target:", target,
                          "%.1f DPS" % encounter["dps"] if encounter else "")
            y = self._divider(data, y, width)
            self._controls(data, y, width, tracker.paused)
        else:
            y = 27
            self._tabs(data, y)
            y += 22
            y = self._divider(data, y, width)
            page = self.ui.get("page", "overview")
            if page == "monsters":
                y = self._draw_monsters(data, tracker, y, width)
            elif page == "loot":
                y = self._draw_loot(data, tracker, y, width)
            elif page == "records":
                y = self._draw_records(data, tracker, history, y, width)
            else:
                y = self._draw_overview(data, tracker, encounter, y, width)
            y = self._divider(data, 340, width)
            self._controls(data, y, width, tracker.paused)

        Gumps.SendGump(
            GUMP_ID,
            Player.Serial,
            int(self.ui.get("x", 100)),
            int(self.ui.get("y", 100)),
            data.gumpDefinition,
            data.gumpStrings,
        )

    def _tabs(self, data, y):
        selected = self.ui.get("page", "overview")
        x = 10
        for button_id, page, label in (
            (BUTTON_OVERVIEW, "overview", "Overview"),
            (BUTTON_MONSTERS, "monsters", "Monsters"),
            (BUTTON_LOOT, "loot", "Loot"),
            (BUTTON_RECORDS, "records", "Records"),
        ):
            self._button(data, x, y, button_id, label, HUE_TITLE if page == selected else HUE_KEY)
            x += 105

    def _controls(self, data, y, width, paused):
        reset_label = "CONFIRM" if time.time() < self.reset_armed_until else "Reset"
        self._button(data, 10, y, BUTTON_RESET, reset_label, HUE_WARN)
        self._button(data, 95, y, BUTTON_PAUSE, "Resume" if paused else "Pause")
        self._button(data, 180, y, BUTTON_SAVE, "Save")
        if width > 350:
            self._button(data, 255, y, BUTTON_COMPACT, "Compact")
            self._button(data, 355, y, BUTTON_STOP, "Stop", HUE_WARN)
        else:
            self._button(data, 255, y, BUTTON_STOP, "Stop", HUE_WARN)

    def _draw_overview(self, data, tracker, encounter, y, width):
        metrics = tracker.metrics()
        y = self._row(data, y, "Runtime:", fmt_time(metrics["elapsed"]))
        y = self._row(data, y, "Combat time:", fmt_time(metrics["combat_time"]))
        y = self._row(data, y, "Kills:", str(metrics["kills"]),
                      "%.1f/min | streak %d/%d" % (
                          metrics["kills_per_minute"], metrics["current_streak"], metrics["best_streak"]))
        y = self._row(data, y, "Gold gained:", fmt_number(metrics["gold"]),
                      "%s/h" % fmt_number(metrics["gold_per_hour"]))
        y = self._row(data, y, "Tracked damage:", fmt_number(metrics["damage"]))
        y = self._row(data, y, "Active DPS:", "%.1f" % metrics["average_dps"],
                      "peak %.1f" % metrics["peak_dps"])
        y += 3
        self._label(data, 10, y, HUE_HEADER, "CURRENT ENCOUNTER")
        y += 18
        if encounter:
            activity = "dealing damage" if encounter["recent"] else "idle"
            y = self._row(data, y, encounter["name"][:28], fmt_time(encounter["duration"]), activity)
            y = self._row(data, y, "Damage / DPS:", "%s / %.1f" % (
                fmt_number(encounter["damage"]), encounter["dps"]),
                "peak %.1f" % encounter["peak_dps"])
        else:
            self._label(data, 10, y, HUE_MUTED, "No active encounter")
            y += 18
        y += 3
        self._label(data, 10, y, HUE_HEADER, "LAST KILLS")
        y += 18
        limit = int(self.ui.get("recent_kills", 5))
        recent = tracker.recent_kills[:limit]
        if not recent:
            self._label(data, 10, y, HUE_MUTED, "No kills yet")
        for item in recent:
            self._label(data, 10, y, HUE_KEY, item["monster"][:28])
            self._label(data, 245, y, HUE_VALUE, "%ss" % item["seconds"])
            self._label(data, 325, y, HUE_SUB, fmt_number(item["damage"]))
            y += 18
        return y

    def _draw_monsters(self, data, tracker, y, width):
        self._label(data, 10, y, HUE_HEADER, "#  MONSTER")
        self._label(data, 220, y, HUE_HEADER, "K")
        self._label(data, 255, y, HUE_HEADER, "TIME")
        self._label(data, 315, y, HUE_HEADER, "DPS")
        self._label(data, 375, y, HUE_HEADER, "DMG")
        y += 20
        rows = tracker.monster_rows()[:int(self.ui.get("top_monsters", 10))]
        if not rows:
            self._label(data, 10, y, HUE_MUTED, "No completed encounters")
        for index, row in enumerate(rows):
            hue = HUE_TITLE if index == 0 else (HUE_SUB if index < 3 else HUE_KEY)
            self._label(data, 10, y, hue, "%d. %s" % (index + 1, row["name"][:22]))
            self._label(data, 225, y, hue, row["kills"])
            self._label(data, 255, y, hue, "%.1fs" % row["average_kill_seconds"])
            self._label(data, 315, y, hue, "%.1f" % row["average_dps"])
            self._label(data, 375, y, hue, fmt_number(row["damage"]))
            y += 20
        return y

    def _draw_loot(self, data, tracker, y, width):
        self._label(data, 10, y, HUE_HEADER, "TRACKED LOOT")
        self._label(data, 275, y, HUE_HEADER, "COUNT")
        self._label(data, 355, y, HUE_HEADER, "VALUE")
        y += 22
        all_rows = tracker.loot_rows()
        total_value = sum(row["value"] for row in all_rows)
        rows = all_rows[:10]
        for row in rows:
            self._label(data, 10, y, HUE_KEY, row["name"][:30])
            self._label(data, 275, y, HUE_VALUE, fmt_number(row["count"]))
            self._label(data, 355, y, HUE_SUB, fmt_number(row["value"]))
            y += 20
        if not rows:
            self._label(data, 10, y, HUE_MUTED, "Add items in hunttracker_config.json")
            y += 20
        y += 5
        y = self._divider(data, y, width)
        y = self._row(data, y, "Estimated value:", fmt_number(total_value))
        y = self._row(data, y, "Value / hour:", fmt_number(
            float(total_value) * 3600.0 / tracker.elapsed if tracker.elapsed > 0 else 0))
        return y

    def _draw_records(self, data, tracker, history, y, width):
        records = history_records(history)
        metrics = tracker.metrics()
        self._label(data, 10, y, HUE_HEADER, "PERSONAL BESTS")
        y += 20
        y = self._row(data, y, "Gold / hour:", fmt_number(records["best_gold_per_hour"]))
        y = self._row(data, y, "Kills / hour:", "%.1f" % records["best_kills_per_hour"])
        y = self._row(data, y, "Average DPS:", "%.1f" % records["best_average_dps"])
        y = self._row(data, y, "Peak DPS:", "%.1f" % records["best_peak_dps"])
        y += 5
        self._label(data, 10, y, HUE_HEADER, "CURRENT VS LAST 7")
        y += 20
        gold_hue = HUE_GOOD if metrics["gold_per_hour"] >= records["average_gold_per_hour_7"] else HUE_WARN
        kill_hue = HUE_GOOD if metrics["kills_per_hour"] >= records["average_kills_per_hour_7"] else HUE_WARN
        y = self._row(data, y, "Gold / hour:", fmt_number(metrics["gold_per_hour"]),
                      "avg %s" % fmt_number(records["average_gold_per_hour_7"]), gold_hue)
        y = self._row(data, y, "Kills / hour:", "%.1f" % metrics["kills_per_hour"],
                      "avg %.1f" % records["average_kills_per_hour_7"], kill_hue)
        y += 5
        self._label(data, 10, y, HUE_HEADER, "BEST HUNT")
        y += 20
        y = self._row(data, y, "Monster:", records["best_monster"] or "-")
        location = records["best_location"]
        location_text = "Map %s: %s, %s" % (
            location.get("map", 0), location.get("x", 0), location.get("y", 0)
        ) if location else "-"
        y = self._row(data, y, "Location:", location_text)
        y = self._row(data, y, "Saved sessions:", records["sessions"])
        return y


class HuntController(object):
    def __init__(self):
        self.config = load_config(CONFIG_PATH)
        self.adapter = RazorAdapter(self.config)
        self.gump = HuntGump(self.config)
        self.history = read_json(HISTORY_PATH, {"sessions": []})
        self.tracker = self._load_or_create_tracker()
        self.tracker.seed_inventory(self.adapter.player_gold(), self.adapter.loot_counts())
        self.running = True
        self.stop_reason = "stopped"
        self.started_dpsmeter = False
        self.last_checkpoint = time.time()
        self.last_durability_check = 0.0
        self.weight_alerted = False
        self.gold_alerted = False
        self.durability_alerted = False
        self.was_ghost = bool(Player.IsGhost)
        self.waiting_for_resurrection = self.was_ghost

    def _load_or_create_tracker(self):
        persistence = self.config["persistence"]
        checkpoint = read_json(CHECKPOINT_PATH, None)
        if checkpoint and persistence.get("resume_interrupted_session"):
            age = time.time() - float(checkpoint.get("saved_at_epoch", 0))
            maximum = float(persistence.get("maximum_resume_age_hours", 12)) * 3600.0
            if 0 <= age <= maximum:
                self.adapter.message("Resumed interrupted session " + checkpoint.get("session_id", ""), HUE_TITLE)
                return SessionTracker(self.config, restored=checkpoint)
        return SessionTracker(self.config)

    def save_preferences(self):
        try:
            atomic_json_write(CONFIG_PATH, self.config)
        except Exception as error:
            self.adapter.report_once("preferences", "Could not save UI preferences: " + str(error))

    def checkpoint(self):
        try:
            atomic_json_write(CHECKPOINT_PATH, self.tracker.checkpoint())
            self.last_checkpoint = time.time()
        except Exception as error:
            self.adapter.report_once("checkpoint", "Checkpoint failed: " + str(error))

    def export(self, reason, finish=False):
        if finish:
            self.tracker.flush_active("interrupted")
        paths, summary = export_session(self.tracker, LOG_DIR, reason)
        self.history = update_history(
            HISTORY_PATH,
            summary,
            self.config["persistence"].get("history_limit", 100),
        )
        self.adapter.message("Saved %s" % os.path.basename(paths[0]), HUE_TITLE)
        return paths

    def new_session(self, paused=False):
        self.tracker = SessionTracker(self.config)
        self.tracker.seed_inventory(self.adapter.player_gold(), self.adapter.loot_counts())
        self.tracker.set_paused(paused)
        if os.path.exists(CHECKPOINT_PATH):
            try:
                os.remove(CHECKPOINT_PATH)
            except Exception:
                pass

    def handle_action(self, button, now):
        if button is None:
            return
        if button in PAGE_BUTTONS:
            self.config["ui"]["page"] = PAGE_BUTTONS[button]
            self.save_preferences()
        elif button == BUTTON_COMPACT:
            self.config["ui"]["compact"] = not bool(self.config["ui"].get("compact"))
            self.save_preferences()
        elif button == BUTTON_PAUSE:
            paused = self.tracker.set_paused(not self.tracker.paused, now)
            self.adapter.head_message("Hunt paused" if paused else "Hunt resumed", HUE_WARN if paused else HUE_GOOD)
        elif button == BUTTON_SAVE:
            self.export("manual save", finish=False)
        elif button == BUTTON_STOP:
            self.stop_reason = "user stop"
            self.running = False
        elif button == BUTTON_RESET:
            if now <= self.gump.reset_armed_until:
                if self.config["persistence"].get("save_on_reset") and self.tracker.elapsed > 0:
                    self.export("reset", finish=True)
                self.new_session()
                self.gump.reset_armed_until = 0.0
                self.adapter.head_message("Hunt reset", HUE_WARN)
            else:
                self.gump.reset_armed_until = now + 3.0
                self.adapter.head_message("Press RESET again to confirm", HUE_WARN)

    def _health_alerts(self, now):
        alerts = self.config.get("alerts", {})
        if not alerts.get("enabled"):
            return
        weight = self.adapter.weight_percent()
        threshold = float(alerts.get("weight_percent", 0))
        if threshold > 0 and weight >= threshold and not self.weight_alerted:
            self.adapter.alert("Weight at %.0f%%" % weight)
            self.weight_alerted = True
        elif weight < max(0, threshold - 5):
            self.weight_alerted = False

        capacity = int(alerts.get("gold_capacity", 0))
        capacity_percent = float(alerts.get("gold_capacity_warning_percent", 90))
        warning_amount = capacity * capacity_percent / 100.0
        gold = self.adapter.player_gold()
        if capacity > 0 and gold >= warning_amount and not self.gold_alerted:
            self.adapter.alert("Gold capacity at %.0f%%" % (float(gold) * 100.0 / capacity))
            self.gold_alerted = True
        elif capacity > 0 and gold < warning_amount * 0.9:
            self.gold_alerted = False

        interval = float(alerts.get("durability_check_seconds", 30))
        if now - self.last_durability_check >= interval:
            self.last_durability_check = now
            durability = self.adapter.minimum_durability()
            minimum = int(alerts.get("durability_minimum", 0))
            if durability and minimum > 0 and durability["current"] <= minimum:
                if not self.durability_alerted:
                    self.adapter.alert("Low durability: %s (%d/%d)" % (
                        durability["name"], durability["current"], durability["maximum"]))
                    self.durability_alerted = True
            else:
                self.durability_alerted = False

    def _handle_death(self, now):
        ghost = bool(Player.IsGhost)
        if ghost and not self.was_ghost:
            if self.config["persistence"].get("auto_save_on_death") and self.tracker.elapsed > 0:
                self.export("death", finish=True)
                self.new_session(paused=True)
                self.waiting_for_resurrection = True
                self.adapter.message("Session saved; waiting for resurrection", HUE_WARN)
            else:
                self.tracker.set_paused(True, now)
                self.waiting_for_resurrection = True
        elif not ghost and self.was_ghost and self.waiting_for_resurrection:
            self.tracker.seed_inventory(self.adapter.player_gold(), self.adapter.loot_counts())
            self.tracker.set_paused(False, now)
            self.waiting_for_resurrection = False
            self.adapter.head_message("New hunt session started", HUE_TITLE)
        self.was_ghost = ghost

    def run(self):
        self.adapter.message("HuntTracker v1.0 loaded", HUE_TITLE)
        self.adapter.head_message("HuntTracker active", HUE_TITLE)
        try:
            if not bool(DPSMeter.Status()):
                DPSMeter.Start()
                self.started_dpsmeter = True
        except Exception as error:
            self.adapter.report_once("dps_start", "Could not start DPSMeter: " + str(error))

        tick_seconds = float(self.config["tracking"]["tick_ms"]) / 1000.0
        draw_seconds = float(self.config["tracking"]["gump_refresh_ms"]) / 1000.0
        next_tick = time.time()
        next_draw = time.time()
        dps_check = time.time() + 5.0

        try:
            while self.running and Player.Connected:
                now = time.time()
                button, moved = self.gump.poll_action()
                if moved:
                    self.save_preferences()
                self.handle_action(button, now)
                self._handle_death(now)

                if now >= next_tick:
                    events = self.tracker.update(
                        self.adapter.observations(),
                        self.adapter.player_gold(),
                        self.adapter.loot_counts(),
                        self.adapter.location(),
                        now,
                    )
                    for event in events:
                        self.adapter.alert(event)
                    self._health_alerts(now)
                    next_tick = now + tick_seconds

                checkpoint_seconds = float(self.config["persistence"].get("checkpoint_seconds", 15))
                if now - self.last_checkpoint >= checkpoint_seconds:
                    self.checkpoint()

                if now >= dps_check:
                    try:
                        if not DPSMeter.Status():
                            DPSMeter.Start()
                            self.started_dpsmeter = True
                    except Exception:
                        pass
                    dps_check = now + 5.0

                if now >= next_draw:
                    self.gump.draw(self.tracker, self.history, now)
                    next_draw = now + draw_seconds
                Misc.Pause(50)
        except SystemExit:
            self.stop_reason = "script exit"
        except Exception as error:
            self.stop_reason = "error"
            self.adapter.message("Fatal error: " + str(error), HUE_WARN)
            raise
        finally:
            self.gump.close()
            connected = bool(Player.Connected)
            save_enabled = (
                self.config["persistence"].get("save_on_stop") if connected else
                self.config["persistence"].get("auto_save_on_disconnect")
            )
            should_save = self.tracker.elapsed > 0 and save_enabled
            if should_save:
                try:
                    reason = "disconnect" if not connected else self.stop_reason
                    self.export(reason, finish=True)
                    if os.path.exists(CHECKPOINT_PATH):
                        os.remove(CHECKPOINT_PATH)
                except Exception as error:
                    self.adapter.message("Final save failed: " + str(error), HUE_WARN)
                    self.checkpoint()
            else:
                self.checkpoint()
            if self.started_dpsmeter:
                try:
                    DPSMeter.Pause()
                except Exception:
                    pass


HuntController().run()
