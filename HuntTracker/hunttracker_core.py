# -*- coding: utf-8 -*-
from __future__ import print_function

import copy
import csv
import datetime
import io
import json
import os
import time


VERSION = "1.0.0"


DEFAULT_CONFIG = {
    "tracking": {
        "tick_ms": 250,
        "gump_refresh_ms": 1000,
        "mobile_range": 20,
        "notorieties": [3, 4, 5, 6],
        "ignore_pets": True,
        "check_line_of_sight": False,
        "exclude_humans": False,
        "ignored_names": [],
        "damage_mode": "player",
        "missing_grace_seconds": 2.5,
        "kill_confirmation": "balanced",
        "recent_damage_seconds": 3.0,
        "combat_timeout_seconds": 5.0,
        "location_grid_size": 32
    },
    "ui": {
        "x": 100,
        "y": 100,
        "compact": False,
        "page": "overview",
        "remember_position": True,
        "top_monsters": 10,
        "recent_kills": 5
    },
    "goals": {
        "kills": 0,
        "gold": 0,
        "duration_minutes": 0
    },
    "alerts": {
        "enabled": True,
        "sound": True,
        "sound_id": 85,
        "weight_percent": 90,
        "gold_capacity": 0,
        "gold_capacity_warning_percent": 90,
        "durability_minimum": 20,
        "durability_check_seconds": 30
    },
    "loot": [
        {
            "name": "Gold",
            "item_id": 3821,
            "hue": -1,
            "unit_value": 1,
            "use_player_gold": True
        }
    ],
    "persistence": {
        "checkpoint_seconds": 15,
        "resume_interrupted_session": True,
        "maximum_resume_age_hours": 12,
        "auto_save_on_death": True,
        "auto_save_on_disconnect": True,
        "save_on_stop": True,
        "save_on_reset": False,
        "history_limit": 100
    }
}


def _deep_merge(base, override):
    result = copy.deepcopy(base)
    for key, value in (override or {}).items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def load_config(path):
    with io.open(path, "r", encoding="utf-8") as source:
        supplied = json.load(source)
    config = _deep_merge(DEFAULT_CONFIG, supplied)
    validate_config(config)
    return config


def validate_config(config):
    tracking = config["tracking"]
    if tracking["damage_mode"] not in ("player", "party", "pet"):
        raise ValueError("tracking.damage_mode must be player, party, or pet")
    if tracking["kill_confirmation"] not in ("strict", "balanced", "permissive"):
        raise ValueError("tracking.kill_confirmation must be strict, balanced, or permissive")
    if int(tracking["tick_ms"]) < 50:
        raise ValueError("tracking.tick_ms must be at least 50")
    if int(tracking["gump_refresh_ms"]) < 250:
        raise ValueError("tracking.gump_refresh_ms must be at least 250")
    if int(tracking["mobile_range"]) < 1:
        raise ValueError("tracking.mobile_range must be positive")
    names = set()
    for entry in config.get("loot", []):
        name = str(entry.get("name", "")).strip()
        if not name or name in names:
            raise ValueError("Every loot entry needs a unique name")
        names.add(name)


def now_stamp(now=None):
    value = datetime.datetime.fromtimestamp(now if now is not None else time.time())
    return value.strftime("%Y-%m-%d_%H-%M-%S")


def iso_stamp(now=None):
    value = datetime.datetime.fromtimestamp(now if now is not None else time.time())
    return value.strftime("%Y-%m-%dT%H:%M:%S")


def atomic_json_write(path, data):
    directory = os.path.dirname(path)
    if directory and not os.path.isdir(directory):
        os.makedirs(directory)
    temporary = path + ".tmp"
    with io.open(temporary, "w", encoding="utf-8") as output:
        json.dump(data, output, indent=2, sort_keys=True, ensure_ascii=False)
        output.write("\n")
    if os.path.exists(path):
        os.remove(path)
    os.rename(temporary, path)


def read_json(path, fallback):
    try:
        with io.open(path, "r", encoding="utf-8") as source:
            return json.load(source)
    except Exception:
        return copy.deepcopy(fallback)


def fmt_time(seconds):
    seconds = max(0, int(seconds))
    return "%02d:%02d:%02d" % (
        seconds // 3600,
        (seconds % 3600) // 60,
        seconds % 60,
    )


def fmt_number(value):
    return "{:,}".format(int(value))


def rate(value, elapsed, scale):
    return float(value) * float(scale) / float(elapsed) if elapsed > 0 else 0.0


def observation(serial, name, hits, damage_meter, is_deleted=False,
                map_id=0, x=0, y=0):
    return {
        "serial": int(serial),
        "name": str(name or "Unknown"),
        "hits": int(hits) if hits is not None else -1,
        "damage_meter": max(0, int(damage_meter or 0)),
        "is_deleted": bool(is_deleted),
        "map": int(map_id),
        "x": int(x),
        "y": int(y),
    }


class MobState(object):
    def __init__(self, item, now):
        self.serial = int(item["serial"])
        self.name = str(item.get("name") or "Unknown")
        self.first_seen = float(now)
        self.last_seen = float(now)
        self.last_sample = float(now)
        self.last_damage = 0.0
        self.last_hits = int(item.get("hits", -1))
        self.baseline_meter = int(item.get("damage_meter", 0))
        self.player_damage = 0
        self.observed_damage = 0
        self.peak_dps = 0.0
        self.map = int(item.get("map", 0))
        self.x = int(item.get("x", 0))
        self.y = int(item.get("y", 0))
        self.deleted = bool(item.get("is_deleted", False))
        self.missing_since = None

    def effective_damage(self, damage_mode):
        if damage_mode == "player":
            return self.player_damage
        return max(self.player_damage, self.observed_damage)

    def update(self, item, now, damage_mode):
        old_effective = self.effective_damage(damage_mode)
        meter = int(item.get("damage_meter", 0))
        raw_meter_damage = meter - self.baseline_meter
        if raw_meter_damage < self.player_damage:
            self.baseline_meter = meter - self.player_damage
            raw_meter_damage = self.player_damage
        self.player_damage = max(self.player_damage, raw_meter_damage)

        hits = int(item.get("hits", -1))
        if hits >= 0 and self.last_hits >= 0 and hits < self.last_hits:
            self.observed_damage += self.last_hits - hits
        if hits >= 0:
            self.last_hits = hits

        new_effective = self.effective_damage(damage_mode)
        delta = new_effective - old_effective
        sample_seconds = max(0.001, float(now) - self.last_sample)
        if delta > 0:
            self.last_damage = float(now)
            self.peak_dps = max(self.peak_dps, float(delta) / sample_seconds)

        supplied_name = str(item.get("name") or "Unknown")
        if self.name == "Unknown" and supplied_name != "Unknown":
            self.name = supplied_name
        self.last_seen = float(now)
        self.last_sample = float(now)
        self.map = int(item.get("map", self.map))
        self.x = int(item.get("x", self.x))
        self.y = int(item.get("y", self.y))
        self.deleted = bool(item.get("is_deleted", False))
        self.missing_since = None
        return delta

    def to_dict(self):
        return dict(self.__dict__)

    @classmethod
    def from_dict(cls, data):
        item = {
            "serial": data["serial"],
            "name": data.get("name", "Unknown"),
            "hits": data.get("last_hits", -1),
            "damage_meter": data.get("baseline_meter", 0),
            "map": data.get("map", 0),
            "x": data.get("x", 0),
            "y": data.get("y", 0),
            "is_deleted": data.get("deleted", False),
        }
        state = cls(item, data.get("first_seen", time.time()))
        state.__dict__.update(data)
        return state


class SessionTracker(object):
    def __init__(self, config, now=None, restored=None):
        self.config = config
        current = float(time.time() if now is None else now)
        self.session_id = now_stamp(current)
        self.started_at = iso_stamp(current)
        self.elapsed = 0.0
        self.combat_time = 0.0
        self.last_tick = current
        self.last_damage = 0.0
        self.current_target = 0
        self.paused = False
        self.completed_damage = 0
        self.gold_gained = 0
        self.previous_gold = None
        self.loot_gained = {}
        self.previous_loot = {}
        self.active = {}
        self.pending = {}
        self.monsters = {}
        self.encounters = []
        self.recent_kills = []
        self.current_streak = 0
        self.best_streak = 0
        self.locations = {}
        self.goal_alerts = {}
        self.last_location = {"map": 0, "x": 0, "y": 0}
        if restored:
            self._restore(restored, current)

    @property
    def tracking(self):
        return self.config["tracking"]

    def _restore(self, data, now):
        self.session_id = data.get("session_id", self.session_id)
        self.started_at = data.get("started_at", self.started_at)
        self.elapsed = float(data.get("elapsed", 0))
        self.combat_time = float(data.get("combat_time", 0))
        self.last_damage = float(data.get("last_damage", 0))
        self.current_target = int(data.get("current_target", 0))
        self.paused = bool(data.get("paused", False))
        self.completed_damage = int(data.get("completed_damage", 0))
        self.gold_gained = int(data.get("gold_gained", 0))
        self.loot_gained = data.get("loot_gained", {}) or {}
        self.monsters = data.get("monsters", {}) or {}
        self.encounters = data.get("encounters", []) or []
        self.recent_kills = data.get("recent_kills", []) or []
        self.current_streak = int(data.get("current_streak", 0))
        self.best_streak = int(data.get("best_streak", 0))
        self.locations = data.get("locations", {}) or {}
        self.goal_alerts = data.get("goal_alerts", {}) or {}
        self.last_location = data.get("last_location", self.last_location)
        self.active = dict(
            (int(key), MobState.from_dict(value))
            for key, value in (data.get("active", {}) or {}).items()
        )
        self.pending = dict(
            (int(key), MobState.from_dict(value))
            for key, value in (data.get("pending", {}) or {}).items()
        )
        self.last_tick = now

    def seed_inventory(self, gold, loot_counts):
        self.previous_gold = int(gold)
        self.previous_loot = dict(loot_counts or {})

    def set_paused(self, paused, now=None):
        self.paused = bool(paused)
        self.last_tick = float(time.time() if now is None else now)
        return self.paused

    def update(self, observations, gold, loot_counts, location, now=None):
        current = float(time.time() if now is None else now)
        tick_seconds = max(0.0, min(5.0, current - self.last_tick))
        self.last_tick = current
        self.last_location = dict(location or self.last_location)

        if self.paused:
            self.previous_gold = int(gold)
            self.previous_loot = dict(loot_counts or {})
            return []

        self.elapsed += tick_seconds
        if self.last_damage and current - self.last_damage <= float(self.tracking["combat_timeout_seconds"]):
            self.combat_time += tick_seconds
        self._record_location_time(tick_seconds)
        self._record_inventory(gold, loot_counts)

        current_serials = set()
        damage_mode = self.tracking["damage_mode"]
        for item in observations:
            serial = int(item["serial"])
            current_serials.add(serial)
            if serial in self.pending:
                self.active[serial] = self.pending.pop(serial)
            state = self.active.get(serial)
            if state is None:
                state = MobState(item, current)
                self.active[serial] = state
            delta = state.update(item, current, damage_mode)
            if delta > 0:
                self.last_damage = current
                self.current_target = serial

        for serial in list(self.active.keys()):
            if serial not in current_serials:
                state = self.active.pop(serial)
                state.missing_since = current
                self.pending[serial] = state

        grace = float(self.tracking["missing_grace_seconds"])
        for serial in list(self.pending.keys()):
            state = self.pending[serial]
            if current - float(state.missing_since or current) >= grace:
                result = "kill" if self._qualifies_as_kill(state, current) else "escaped"
                self._finalize(state, result, current)
                del self.pending[serial]
                if self.current_target == serial:
                    self.current_target = 0
        return self.check_goals()

    def _record_inventory(self, gold, loot_counts):
        gold = int(gold)
        if self.previous_gold is not None and gold > self.previous_gold:
            self.gold_gained += gold - self.previous_gold
        self.previous_gold = gold

        counts = dict(loot_counts or {})
        for name, count in counts.items():
            previous = self.previous_loot.get(name)
            if previous is not None and int(count) > int(previous):
                self.loot_gained[name] = self.loot_gained.get(name, 0) + int(count) - int(previous)
        self.previous_loot = counts

    def _record_location_time(self, seconds):
        location = self.last_location
        grid = max(1, int(self.tracking["location_grid_size"]))
        map_id = int(location.get("map", 0))
        x = int(location.get("x", 0))
        y = int(location.get("y", 0))
        key = "%d:%d:%d" % (map_id, x // grid, y // grid)
        bucket = self.locations.setdefault(key, {
            "map": map_id,
            "x": (x // grid) * grid,
            "y": (y // grid) * grid,
            "seconds": 0.0,
            "kills": 0,
            "damage": 0,
        })
        bucket["seconds"] += float(seconds)

    def _qualifies_as_kill(self, state, now):
        damage = state.effective_damage(self.tracking["damage_mode"])
        if damage <= 0:
            return False
        mode = self.tracking["kill_confirmation"]
        hard_confirmation = state.deleted or state.last_hits == 0
        if mode == "strict":
            return hard_confirmation
        if mode == "permissive":
            return True
        recent = state.last_damage and now - state.last_damage <= float(self.tracking["recent_damage_seconds"])
        return bool(hard_confirmation or recent)

    def _finalize(self, state, result, now):
        damage = int(state.effective_damage(self.tracking["damage_mode"]))
        self.completed_damage += damage
        duration = max(0.0, state.last_seen - state.first_seen)
        encounter = {
            "session_id": self.session_id,
            "started_at": iso_stamp(state.first_seen),
            "ended_at": iso_stamp(now),
            "serial": state.serial,
            "monster": state.name,
            "result": result,
            "damage": damage,
            "player_damage": int(state.player_damage),
            "duration_seconds": round(duration, 3),
            "average_dps": round(float(damage) / duration, 2) if duration > 0 else 0.0,
            "peak_dps": round(float(state.peak_dps), 2),
            "map": state.map,
            "x": state.x,
            "y": state.y,
        }
        self.encounters.append(encounter)
        stats = self.monsters.setdefault(state.name, {
            "encounters": 0,
            "kills": 0,
            "escapes": 0,
            "damage": 0,
            "kill_seconds": 0.0,
            "best_kill_seconds": None,
            "last_killed": "",
        })
        stats["encounters"] += 1
        stats["damage"] += damage
        if result == "kill":
            stats["kills"] += 1
            stats["kill_seconds"] += duration
            best = stats.get("best_kill_seconds")
            stats["best_kill_seconds"] = duration if best is None else min(float(best), duration)
            stats["last_killed"] = encounter["ended_at"]
            self.recent_kills.insert(0, {
                "monster": state.name,
                "at": encounter["ended_at"],
                "damage": damage,
                "seconds": round(duration, 1),
            })
            self.recent_kills = self.recent_kills[:20]
            self.current_streak += 1
            self.best_streak = max(self.best_streak, self.current_streak)
        else:
            stats["escapes"] += 1
            self.current_streak = 0

        grid = max(1, int(self.tracking["location_grid_size"]))
        key = "%d:%d:%d" % (state.map, state.x // grid, state.y // grid)
        bucket = self.locations.setdefault(key, {
            "map": state.map,
            "x": (state.x // grid) * grid,
            "y": (state.y // grid) * grid,
            "seconds": 0.0,
            "kills": 0,
            "damage": 0,
        })
        bucket["damage"] += damage
        if result == "kill":
            bucket["kills"] += 1

    def flush_active(self, result="interrupted", now=None):
        current = float(time.time() if now is None else now)
        for state in list(self.active.values()) + list(self.pending.values()):
            self._finalize(state, result, current)
        self.active = {}
        self.pending = {}
        self.current_target = 0

    def total_damage(self):
        active = list(self.active.values()) + list(self.pending.values())
        return self.completed_damage + sum(
            state.effective_damage(self.tracking["damage_mode"]) for state in active
        )

    def total_kills(self):
        return sum(int(stats.get("kills", 0)) for stats in self.monsters.values())

    def monster_rows(self):
        rows = []
        for name, stats in self.monsters.items():
            kills = int(stats.get("kills", 0))
            damage = int(stats.get("damage", 0))
            rows.append({
                "name": name,
                "kills": kills,
                "encounters": int(stats.get("encounters", 0)),
                "escapes": int(stats.get("escapes", 0)),
                "damage": damage,
                "average_damage": float(damage) / kills if kills else 0.0,
                "average_kill_seconds": float(stats.get("kill_seconds", 0)) / kills if kills else 0.0,
                "average_dps": float(damage) / float(stats.get("kill_seconds", 0)) if stats.get("kill_seconds", 0) else 0.0,
                "best_kill_seconds": stats.get("best_kill_seconds"),
                "last_killed": stats.get("last_killed", ""),
            })
        return sorted(rows, key=lambda row: (-row["kills"], -row["damage"], row["name"].lower()))

    def current_encounter(self, now=None):
        current = float(time.time() if now is None else now)
        state = self.active.get(self.current_target)
        if state is None and self.active:
            state = max(self.active.values(), key=lambda mob: (mob.last_damage, mob.last_seen))
        if state is None:
            return None
        duration = max(0.0, current - state.first_seen)
        damage = state.effective_damage(self.tracking["damage_mode"])
        return {
            "name": state.name,
            "duration": duration,
            "damage": damage,
            "dps": float(damage) / duration if duration > 0 else 0.0,
            "peak_dps": state.peak_dps,
            "recent": bool(state.last_damage and current - state.last_damage <= 2.0),
        }

    def loot_rows(self):
        rows = []
        for entry in self.config.get("loot", []):
            name = entry["name"]
            count = int(self.loot_gained.get(name, 0))
            value = count * float(entry.get("unit_value", 0))
            rows.append({"name": name, "count": count, "value": value})
        return rows

    def best_location(self):
        if not self.locations:
            return None
        return max(self.locations.values(), key=lambda item: (item.get("kills", 0), item.get("damage", 0)))

    def metrics(self):
        kills = self.total_kills()
        damage = self.total_damage()
        return {
            "elapsed": self.elapsed,
            "combat_time": self.combat_time,
            "kills": kills,
            "kills_per_minute": rate(kills, self.elapsed, 60),
            "kills_per_hour": rate(kills, self.elapsed, 3600),
            "gold": self.gold_gained,
            "gold_per_hour": rate(self.gold_gained, self.elapsed, 3600),
            "damage": damage,
            "average_dps": rate(damage, self.combat_time, 1),
            "peak_dps": max(
                [float(item.get("peak_dps", 0)) for item in self.encounters] +
                [float(item.peak_dps) for item in self.active.values()] + [0.0]
            ),
            "current_streak": self.current_streak,
            "best_streak": self.best_streak,
        }

    def check_goals(self):
        events = []
        metrics = self.metrics()
        goals = self.config.get("goals", {})
        checks = [
            ("kills", float(goals.get("kills", 0)), float(metrics["kills"]), "Kill goal reached"),
            ("gold", float(goals.get("gold", 0)), float(metrics["gold"]), "Gold goal reached"),
            ("duration", float(goals.get("duration_minutes", 0)) * 60.0, self.elapsed, "Duration goal reached"),
        ]
        for key, target, value, message in checks:
            if target > 0 and value >= target and not self.goal_alerts.get(key):
                self.goal_alerts[key] = True
                events.append(message)
        return events

    def checkpoint(self):
        return {
            "version": VERSION,
            "saved_at_epoch": time.time(),
            "session_id": self.session_id,
            "started_at": self.started_at,
            "elapsed": self.elapsed,
            "combat_time": self.combat_time,
            "last_damage": self.last_damage,
            "current_target": self.current_target,
            "paused": self.paused,
            "completed_damage": self.completed_damage,
            "gold_gained": self.gold_gained,
            "loot_gained": self.loot_gained,
            "active": dict((str(key), value.to_dict()) for key, value in self.active.items()),
            "pending": dict((str(key), value.to_dict()) for key, value in self.pending.items()),
            "monsters": self.monsters,
            "encounters": self.encounters,
            "recent_kills": self.recent_kills,
            "current_streak": self.current_streak,
            "best_streak": self.best_streak,
            "locations": self.locations,
            "goal_alerts": self.goal_alerts,
            "last_location": self.last_location,
        }

    def summary(self, end_reason="saved"):
        result = self.metrics()
        result.update({
            "version": VERSION,
            "session_id": self.session_id,
            "started_at": self.started_at,
            "saved_at": iso_stamp(),
            "end_reason": end_reason,
            "damage_mode": self.tracking["damage_mode"],
            "kill_confirmation": self.tracking["kill_confirmation"],
            "loot": self.loot_rows(),
            "monsters": self.monster_rows(),
            "locations": sorted(self.locations.values(), key=lambda row: (-row.get("kills", 0), -row.get("damage", 0))),
            "encounters": self.encounters,
        })
        return result


def export_session(tracker, output_dir, end_reason="saved"):
    if not os.path.isdir(output_dir):
        os.makedirs(output_dir)
    summary = tracker.summary(end_reason)
    base = "HuntSession_" + tracker.session_id
    json_path = os.path.join(output_dir, base + ".json")
    csv_path = os.path.join(output_dir, base + "_encounters.csv")
    monsters_path = os.path.join(output_dir, base + "_monsters.csv")
    atomic_json_write(json_path, summary)

    encounter_fields = [
        "session_id", "started_at", "ended_at", "serial", "monster", "result",
        "damage", "player_damage", "duration_seconds", "average_dps", "peak_dps",
        "map", "x", "y",
    ]
    with io.open(csv_path, "w", encoding="utf-8", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=encounter_fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(summary["encounters"])

    monster_fields = [
        "name", "kills", "encounters", "escapes", "damage", "average_damage",
        "average_kill_seconds", "average_dps", "best_kill_seconds", "last_killed",
    ]
    with io.open(monsters_path, "w", encoding="utf-8", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=monster_fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(summary["monsters"])
    return [json_path, csv_path, monsters_path], summary


def update_history(path, summary, limit=100):
    history = read_json(path, {"version": VERSION, "sessions": []})
    sessions = [
        item for item in history.get("sessions", [])
        if item.get("session_id") != summary.get("session_id")
    ]
    compact = dict(
        (key, value) for key, value in summary.items()
        if key not in ("encounters", "monsters", "locations")
    )
    best_location = None
    locations = summary.get("locations", [])
    if locations:
        best_location = locations[0]
    compact["best_location"] = best_location
    monsters = summary.get("monsters", [])
    compact["best_monster"] = monsters[0]["name"] if monsters else ""
    sessions.insert(0, compact)
    history["sessions"] = sessions[:max(1, int(limit))]
    atomic_json_write(path, history)
    return history


def history_records(history):
    sessions = history.get("sessions", []) if isinstance(history, dict) else []
    recent = sessions[:7]
    result = {
        "sessions": len(sessions),
        "best_gold_per_hour": 0.0,
        "best_kills_per_hour": 0.0,
        "best_average_dps": 0.0,
        "best_peak_dps": 0.0,
        "average_gold_per_hour_7": 0.0,
        "average_kills_per_hour_7": 0.0,
        "best_monster": "",
        "best_location": None,
    }
    if not sessions:
        return result
    result["best_gold_per_hour"] = max(float(item.get("gold_per_hour", 0)) for item in sessions)
    result["best_kills_per_hour"] = max(float(item.get("kills_per_hour", 0)) for item in sessions)
    result["best_average_dps"] = max(float(item.get("average_dps", 0)) for item in sessions)
    result["best_peak_dps"] = max(float(item.get("peak_dps", 0)) for item in sessions)
    result["average_gold_per_hour_7"] = sum(float(item.get("gold_per_hour", 0)) for item in recent) / len(recent)
    result["average_kills_per_hour_7"] = sum(float(item.get("kills_per_hour", 0)) for item in recent) / len(recent)
    best = max(sessions, key=lambda item: (item.get("kills_per_hour", 0), item.get("gold_per_hour", 0)))
    result["best_monster"] = best.get("best_monster", "")
    result["best_location"] = best.get("best_location")
    return result
