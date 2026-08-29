# -*- coding: utf-8 -*-
from __future__ import print_function

import copy
import csv
import io
import json
import os
import shutil
import tempfile
import unittest

from hunttracker_core import (
    DEFAULT_CONFIG,
    SessionTracker,
    export_session,
    history_records,
    observation,
    update_history,
)


def config(**tracking_overrides):
    value = copy.deepcopy(DEFAULT_CONFIG)
    value["tracking"].update(tracking_overrides)
    return value


def mob(serial=1, name="dragon", hits=100, meter=0, deleted=False):
    return observation(serial, name, hits, meter, deleted, 1, 1200, 800)


class TrackingTests(unittest.TestCase):
    def tracker(self, settings=None, now=1000.0):
        tracker = SessionTracker(settings or config(), now=now)
        tracker.seed_inventory(100, {"Gold": 100})
        return tracker

    def update(self, tracker, now, mobs, gold=100, loot=None):
        return tracker.update(
            mobs,
            gold,
            {"Gold": gold} if loot is None else loot,
            {"map": 1, "x": 1200, "y": 800},
            now,
        )

    def test_balanced_kill_requires_own_damage_and_grace(self):
        tracker = self.tracker()
        self.update(tracker, 1000.0, [mob(meter=50)])
        self.update(tracker, 1001.0, [mob(hits=50, meter=90)])
        self.update(tracker, 1001.2, [])
        self.update(tracker, 1003.0, [])
        self.assertEqual(0, tracker.total_kills())
        self.update(tracker, 1003.8, [])
        self.assertEqual(1, tracker.total_kills())
        self.assertEqual(40, tracker.total_damage())
        self.assertEqual("kill", tracker.encounters[0]["result"])
        self.assertEqual(1, tracker.metrics()["current_streak"])
        self.assertGreater(tracker.metrics()["peak_dps"], 0)
        self.assertGreater(tracker.monster_rows()[0]["average_dps"], 0)

    def test_reappearance_cancels_pending_kill(self):
        tracker = self.tracker()
        self.update(tracker, 1000.0, [mob(meter=20)])
        self.update(tracker, 1001.0, [mob(meter=40)])
        self.update(tracker, 1001.2, [])
        self.update(tracker, 1002.0, [mob(meter=40)])
        self.assertIn(1, tracker.active)
        self.assertNotIn(1, tracker.pending)
        self.assertEqual(0, tracker.total_kills())

    def test_player_mode_rejects_damage_done_only_by_others(self):
        tracker = self.tracker()
        self.update(tracker, 1000.0, [mob(hits=100, meter=10)])
        self.update(tracker, 1001.0, [mob(hits=20, meter=10)])
        self.update(tracker, 1001.1, [])
        self.update(tracker, 1004.0, [])
        self.assertEqual(0, tracker.total_kills())
        self.assertEqual("escaped", tracker.encounters[0]["result"])

    def test_party_mode_accepts_observed_hp_damage(self):
        tracker = self.tracker(config(damage_mode="party"))
        self.update(tracker, 1000.0, [mob(hits=100, meter=10)])
        self.update(tracker, 1001.0, [mob(hits=20, meter=10)])
        self.update(tracker, 1001.1, [])
        self.update(tracker, 1004.0, [])
        self.assertEqual(1, tracker.total_kills())
        self.assertEqual(80, tracker.total_damage())

    def test_strict_mode_requires_zero_hits_or_deleted(self):
        tracker = self.tracker(config(kill_confirmation="strict"))
        self.update(tracker, 1000.0, [mob(meter=10)])
        self.update(tracker, 1001.0, [mob(hits=0, meter=50)])
        self.update(tracker, 1001.1, [])
        self.update(tracker, 1004.0, [])
        self.assertEqual(1, tracker.total_kills())

    def test_pause_excludes_time_and_inventory_changes(self):
        tracker = self.tracker()
        self.update(tracker, 1001.0, [], gold=110)
        tracker.set_paused(True, 1001.0)
        self.update(tracker, 1101.0, [], gold=500)
        tracker.set_paused(False, 1101.0)
        self.update(tracker, 1102.0, [], gold=510)
        self.assertEqual(2.0, tracker.elapsed)
        self.assertEqual(20, tracker.gold_gained)

    def test_goals_alert_once(self):
        settings = config()
        settings["goals"]["gold"] = 20
        tracker = self.tracker(settings)
        self.assertEqual(["Gold goal reached"], self.update(tracker, 1001.0, [], gold=120))
        self.assertEqual([], self.update(tracker, 1002.0, [], gold=130))

    def test_checkpoint_restores_aggregates_and_active_mob(self):
        tracker = self.tracker()
        self.update(tracker, 1001.0, [mob(meter=10)], gold=120)
        self.update(tracker, 1002.0, [mob(meter=35)], gold=125)
        restored = SessionTracker(config(), now=1003.0, restored=tracker.checkpoint())
        restored.seed_inventory(125, {"Gold": 125})
        self.assertEqual(tracker.session_id, restored.session_id)
        self.assertEqual(25, restored.total_damage())
        self.assertEqual(25, restored.gold_gained)
        self.assertIn(1, restored.active)

    def test_unknown_name_is_replaced(self):
        tracker = self.tracker()
        self.update(tracker, 1000.0, [mob(name="Unknown")])
        self.update(tracker, 1001.0, [mob(name="ancient wyrm")])
        self.assertEqual("ancient wyrm", tracker.active[1].name)


class ExportTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.mkdtemp(prefix="hunttracker-")

    def tearDown(self):
        shutil.rmtree(self.directory)

    def completed_tracker(self):
        tracker = SessionTracker(config(), now=1000.0)
        tracker.seed_inventory(0, {"Gold": 0})
        tracker.update([mob(name='dragon, "elder"', meter=0)], 0, {"Gold": 0},
                       {"map": 1, "x": 100, "y": 200}, 1000.0)
        tracker.update([mob(name='dragon, "elder"', hits=0, meter=200)], 0, {"Gold": 0},
                       {"map": 1, "x": 100, "y": 200}, 1001.0)
        tracker.update([], 0, {"Gold": 0}, {"map": 1, "x": 100, "y": 200}, 1001.1)
        tracker.update([], 0, {"Gold": 0}, {"map": 1, "x": 100, "y": 200}, 1004.0)
        return tracker

    def test_csv_quotes_monster_names_and_json_has_all_sections(self):
        tracker = self.completed_tracker()
        paths, summary = export_session(tracker, self.directory, "test")
        with io.open(paths[0], "r", encoding="utf-8") as source:
            payload = json.load(source)
        self.assertEqual('dragon, "elder"', payload["encounters"][0]["monster"])
        self.assertIn("locations", payload)
        with io.open(paths[1], "r", encoding="utf-8", newline="") as source:
            rows = list(csv.DictReader(source))
        self.assertEqual('dragon, "elder"', rows[0]["monster"])
        self.assertEqual(3, len(paths))
        self.assertEqual("test", summary["end_reason"])

    def test_history_upserts_and_calculates_records(self):
        tracker = self.completed_tracker()
        summary = tracker.summary("test")
        history_path = os.path.join(self.directory, "history.json")
        history = update_history(history_path, summary, 10)
        history = update_history(history_path, summary, 10)
        self.assertEqual(1, len(history["sessions"]))
        records = history_records(history)
        self.assertEqual(1, records["sessions"])
        self.assertEqual("dragon, \"elder\"", records["best_monster"])


if __name__ == "__main__":
    unittest.main()
