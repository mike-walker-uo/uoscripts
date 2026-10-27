"""Opt-in damageable-item targeting, combat priority and saved GUMP control."""
import ast
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace as Obj
import unittest

import test_combat_flow as fixtures
import test_df_stamina as settings_fixtures

ROOT = Path(__file__).resolve().parents[1]


class GenericList:
    def __class_getitem__(cls, value):
        return list


class LighthouseTests(unittest.TestCase):
    def setUp(self):
        self.world = fixtures.CombatFlowTests(methodName='runTest')
        self.world.setUp()
        self.ns = self.world.ns
        self.calls = self.world.calls
        self.scans = []
        self.ns['sv']['use_attack_lighthouses'] = 1
        self.ns['List'] = GenericList
        self.ns['Int32'] = int
        tree = ast.parse((ROOT / 'AttackScript_MikeWalker.py').read_text())
        self.ns['LIGHTHOUSE_ITEM_IDS'] = ast.literal_eval(next(n.value for n in tree.body
            if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name)
            and n.targets[0].id == 'LIGHTHOUSE_ITEM_IDS'))
        self.ns['Items'].Filter = Obj
        self.ns['Items'].ApplyFilter = self.scan
        self.world.player.DistanceTo = lambda target: (
            self.world.items[target].distance if isinstance(target, int) else target.distance)
        self.world.player.Attack = lambda serial: self.calls.append(('attack', serial))

    def item(self, serial=0x40000001, graphic=0x4724, distance=1):
        item = Obj(Serial=serial, ItemID=graphic, distance=distance, Deleted=False,
                   Visible=True, OnGround=True, Movable=False)
        self.world.items[serial] = item
        return item

    def scan(self, fil):
        self.scans.append(fil)
        return [item for item in self.world.items.values()
                if item.ItemID in fil.Graphics and item.OnGround and not item.Movable
                and item.distance <= fil.RangeMax]

    def test_default_is_opt_in_and_attack_off_never_scans(self):
        settings = {}
        tree = ast.parse((ROOT / 'AttackScript_MikeWalker.py').read_text())
        for node in tree.body:
            if (isinstance(node, ast.Expr) and isinstance(node.value, ast.Call)
                    and isinstance(node.value.func, ast.Attribute)
                    and node.value.func.attr == 'SetSharedValue' and node.value.args
                    and isinstance(node.value.args[0], ast.Constant)
                    and node.value.args[0].value == 'use_attack_lighthouses'):
                exec(compile(ast.Module(body=[node], type_ignores=[]), 'default', 'exec'),
                     {'Misc': Obj(SetSharedValue=settings.__setitem__)})
        self.assertEqual(settings['use_attack_lighthouses'], 0)
        for enabled, active in ((0, 1), (1, 0)):
            self.ns['sv'].update(use_attack_lighthouses=enabled, activeattack=active)
            self.assertIsNone(self.ns['find_lighthouse']())
        self.assertEqual(self.scans, [])

    def test_all_three_graphics_are_attacked_by_serial_in_war_mode(self):
        for graphic in (0x4724, 0x9983, 0x9984):
            with self.subTest(graphic=graphic):
                self.setUp()
                item = self.item(graphic=graphic)
                self.world.player.WarMode = False
                selected = self.ns['find_lighthouse']()
                self.assertIs(selected, item)
                self.ns['attack_lighthouse'](selected)
                self.assertTrue(self.world.player.WarMode)
                self.assertEqual(self.calls, [('attack', item.Serial)])
                self.assertEqual(set(self.scans[0].Graphics), {0x4724, 0x9983, 0x9984})
                self.assertEqual((self.scans[0].OnGround, self.scans[0].Movable), (1, 0))

    def test_nearest_valid_lighthouse_selected_and_decorations_ignored(self):
        self.item(graphic=0x472F)  # Non-attackable secondary component.
        self.item(0x40000002, distance=2).Visible = False
        self.item(0x40000003, distance=2).Deleted = True
        self.item(0x40000004, distance=1).OnGround = False
        self.item(0x40000005, distance=1).Movable = True
        self.item(0x40000006, distance=13)
        self.item(0x40000007, distance=5)
        nearest = self.item(0x40000008, distance=3)
        self.assertIs(self.ns['find_lighthouse'](), nearest)

    def test_scan_is_cached_but_range_and_destroyed_graphics_rechecked(self):
        item = self.item()
        self.assertIs(self.ns['find_lighthouse'](), item)
        self.world.tick(100)
        item.distance = 13
        self.assertIsNone(self.ns['find_lighthouse']())
        item.distance = 1
        item.ItemID = 1
        self.assertIsNone(self.ns['find_lighthouse']())
        self.assertEqual(len(self.scans), 1)
        self.world.tick(100)
        self.ns['find_lighthouse']()
        self.assertEqual(len(self.scans), 2)

    def test_deleted_cached_item_is_removed_without_waiting_for_rescan(self):
        item = self.item()
        self.ns['find_lighthouse']()
        item.Deleted = True
        self.assertIsNone(self.ns['find_lighthouse']())
        self.assertEqual(len(self.scans), 1)

    def test_graphic_changes_keep_same_item_attackable(self):
        item = self.item()
        self.ns['find_lighthouse']()
        for graphic in (0x9983, 0x9984):
            item.ItemID = graphic
            self.world.tick(50)
            self.assertIs(self.ns['find_lighthouse'](), item)

    def test_repeated_requests_throttled_but_target_changes_immediate(self):
        first, second = self.item(), self.item(0x40000002)
        self.ns['attack_lighthouse'](first)
        self.world.tick(200)
        self.ns['attack_lighthouse'](first)
        self.assertEqual(self.calls, [('attack', first.Serial)])
        self.ns['attack_lighthouse'](second)
        self.assertEqual(self.calls[-1], ('attack', second.Serial))
        self.world.tick(1000)
        self.ns['attack_lighthouse'](second)
        self.assertEqual(len(self.calls), 3)

    def test_blood_oath_and_disabled_controls_block_item_attacks(self):
        item = self.item()
        self.world.player.WarMode = False
        self.world.buffs.add('Bload Oath (curse)')
        self.ns['attack_lighthouse'](item)
        self.world.buffs.clear()
        self.ns['sv']['use_attack_lighthouses'] = 0
        self.ns['attack_lighthouse'](item)
        self.ns['sv'].update(use_attack_lighthouses=1, activeattack=0)
        self.ns['attack_lighthouse'](item)
        self.assertFalse(self.world.player.WarMode)
        self.assertEqual(self.calls, [])

    def test_lighthouse_tick_uses_item_path_and_sets_combat_busy(self):
        item = self.item()
        self.world.setup_loop([])
        self.ns['run_tick']()
        self.assertIn(('attack', item.Serial), self.calls)
        self.assertTrue(self.ns['_flow']['combat'])
        self.assertTrue(self.ns['Timer'].Check('attack_combat_busy'))
        for forbidden in ('fighting', 'drop_heirloom_chests', 'move_artifacts_to_lootbag', 'closewounds'):
            self.assertNotIn(forbidden, self.calls)
        self.assertIsNone(self.ns['_flow']['cursor'])  # No Honor or pet commands on items.

    def test_hostile_mobs_keep_priority_and_lighthouse_scan_is_skipped(self):
        self.item()
        self.world.setup_loop([self.world.mob()])
        self.ns['run_tick']()
        self.assertIn('fighting', self.calls)
        self.assertEqual(self.scans, [])
        self.assertFalse(any(isinstance(call, tuple) and call[0] == 'attack' for call in self.calls))

    def test_gump_button_dispatch_persists_and_character_load_restores(self):
        settings = {'use_attack_lighthouses': 0}
        misc = Obj(ReadSharedValue=lambda key: settings.get(key, 0), SetSharedValue=settings.__setitem__)
        player = Obj(Serial=1, HeadMessage=lambda *args: None, GetSkillValue=lambda name: 0)
        gump = dict(Misc=misc, Player=player, json=json, os=os)
        settings_fixtures.load_script('AttackScript_MikeWalker_GUMP.py', gump)
        attack = dict(Misc=misc, Player=player, json=json, os=os)
        settings_fixtures.load_script('AttackScript_MikeWalker.py', attack)
        actions = gump['sections']['3: Attacks']
        action = actions['Attack Lighthouses']
        self.assertTrue(gump['action_skills_met'](action))
        gd = Obj(buttonid=gump['_section_indices']['3: Attacks'] * 1000 + list(actions).index('Attack Lighthouses') + 1)
        gump.update(_active_tab='settings', Gumps=Obj(WaitForGump=lambda *args: None,
            CloseGump=lambda *args: None, GetGumpData=lambda *args: gd))
        for ns in (attack, gump):
            self.assertIn('use_attack_lighthouses', ns['SETTINGS_KEYS'])
        with TemporaryDirectory() as directory:
            filename = os.path.join(directory, 'character.json')
            gump['SETTINGS_FILE'] = filename
            gump['buttoncheck'](1)
            self.assertEqual(settings['use_attack_lighthouses'], 1)
            self.assertEqual(json.loads(Path(filename).read_text())['use_attack_lighthouses'], 1)
            settings['use_attack_lighthouses'] = 0
            attack.update(SETTINGS_FILE=filename, LEGACY_SETTINGS_FILE='', ignored_mob_names=set(),
                          ignored_mob_serials=set(), ignored_summon_names=set())
            self.assertTrue(attack['load_settings']())
            self.assertEqual(settings['use_attack_lighthouses'], 1)
            attack['sv'] = {}
            attack['refresh_sv']()
            self.assertEqual(attack['sv']['use_attack_lighthouses'], 1)
            gump['buttoncheck'](1)
            self.assertEqual(settings['use_attack_lighthouses'], 0)
            self.assertEqual(json.loads(Path(filename).read_text())['use_attack_lighthouses'], 0)


if __name__ == '__main__':
    unittest.main()
