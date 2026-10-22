"""Mage item attacks use damage spells and retain normal cast ownership."""
import ast
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace as Obj
import unittest

import test_mage_reliability as fixtures

ROOT = Path(__file__).resolve().parents[1]


class GenericList:
    def __class_getitem__(cls, unused):
        return list


class MageLighthouseTests(unittest.TestCase):
    def setUp(self):
        self.world = fixtures.MageReliabilityTests(methodName='runTest')
        self.world.setUp()
        self.ns = self.world.ns
        self.calls = self.world.calls
        self.items = {}
        self.scans = []
        self.settings = {}
        self.buffs = set()
        self.ns.update(List=GenericList, LIGHTHOUSE_ITEM_IDS=(0x4724, 0x9983, 0x9984),
                       _lighthouse_cache=[], skill_value=lambda school: 120,
                       mana_cost=lambda mana: mana, low_mana=lambda: False,
                       did_fizzle=lambda started: False)
        self.ns['sv'].update(activeattack=1, attackrange=12, use_attack_lighthouses=1)
        self.ns['Player'] = Obj(Paralized=False, Poisoned=False, Mana=100,
            Position=Obj(X=0, Y=0, Z=0),
            BuffsExist=lambda name: name in self.buffs,
            DistanceTo=lambda target: self.items[target].distance if isinstance(target, int) else target.distance,
            HeadMessage=lambda *args: None)
        self.ns['Items'] = Obj(Filter=Obj, ApplyFilter=self.scan, FindBySerial=self.items.get)
        self.ns['Misc'].ReadSharedValue = lambda key: self.settings.get(key, 0)
        self.ns['Misc'].SetSharedValue = self.settings.__setitem__
        self.ns['Spells'].CastMagery = lambda spell: self.calls.append(('Magery', spell))
        self.ns['Spells'].CastMysticism = lambda spell: self.calls.append(('Mysticism', spell))
        self.original_wait_for_spell_target = self.ns['wait_for_spell_target']
        self.ns['wait_for_spell_target'] = lambda *args: self.calls.append(('wait', args[2], args[3].Serial)) or True

    def item(self, serial=0x40000001, graphic=0x4724, distance=4):
        item = Obj(Serial=serial, ItemID=graphic, distance=distance, Visible=True,
                   OnGround=True, Movable=False, Deleted=False, Position=Obj(X=distance, Y=0, Z=0))
        self.items[serial] = item
        return item

    def scan(self, fil):
        self.scans.append(fil)
        return [item for item in self.items.values() if item.ItemID in fil.Graphics
                and item.OnGround and not item.Movable and item.distance <= fil.RangeMax]

    def test_disabled_default_and_attack_off_never_scan(self):
        source = ast.parse(fixtures.SCRIPT.read_text())
        for node in source.body:
            if (isinstance(node, ast.Expr) and isinstance(node.value, ast.Call)
                    and isinstance(node.value.func, ast.Attribute)
                    and node.value.func.attr == 'SetSharedValue'
                    and isinstance(node.value.args[0], ast.Constant)
                    and node.value.args[0].value == 'use_attack_lighthouses'):
                exec(compile(ast.Module(body=[node], type_ignores=[]), 'defaults', 'exec'), self.ns)
        self.assertEqual(self.settings['use_attack_lighthouses'], 0)
        for enabled, active in [(0, 1), (1, 0)]:
            self.ns['sv'].update(use_attack_lighthouses=enabled, activeattack=active)
            self.assertIsNone(self.ns['find_lighthouse']())
        self.assertEqual(self.scans, [])

    def test_three_graphics_and_nearest_item_survive_damage_changes(self):
        first, second = self.item(distance=6), self.item(0x40000002, distance=3)
        for graphic in (0x4724, 0x9983, 0x9984):
            second.ItemID = graphic
            self.assertIs(self.ns['find_lighthouse'](), second)
        self.assertEqual(len(self.scans), 1)
        self.assertEqual(set(self.scans[0].Graphics), {0x4724, 0x9983, 0x9984})
        self.assertEqual((self.scans[0].OnGround, self.scans[0].Movable), (1, 0))
        second.ItemID = 1
        self.assertIs(self.ns['find_lighthouse'](), first)

    def test_invalid_or_unreachable_cached_item_is_not_selected(self):
        item = self.item()
        self.ns['find_lighthouse']()
        for field, invalid, valid in [('Deleted', True, False), ('Visible', False, True),
                ('OnGround', False, True), ('Movable', True, False), ('distance', 13, 4)]:
            with self.subTest(field=field):
                setattr(item, field, invalid)
                self.assertIsNone(self.ns['find_lighthouse']())
                setattr(item, field, valid)
        item.ItemID = 0x472F
        self.assertIsNone(self.ns['find_lighthouse']())
        self.assertEqual(len(self.scans), 1)
        self.world.clock.now = 0.2
        self.ns['find_lighthouse']()
        self.assertEqual(len(self.scans), 2)

    def test_server_los_rejection_requires_player_or_item_movement(self):
        item = self.item()
        self.ns['remember_offensive_target'](item)
        self.ns['apply_cast_failure']('unseen_target')
        self.assertFalse(self.ns['valid_lighthouse'](item))
        self.ns['Player'].Position.X = 1
        self.assertTrue(self.ns['valid_lighthouse'](item))
        self.assertNotIn(item.Serial, self.ns['los_rejected_positions'])

    def test_enabled_supported_spell_is_cast_and_uses_item_cursor_kind(self):
        for key, school, spell in [
                ('flamestrike', 'Magery', 'Flame Strike'), ('energybolt', 'Magery', 'Energy Bolt'),
                ('eaglestrike', 'Mysticism', 'Eagle Strike'), ('bombard', 'Mysticism', 'Bombard'),
                ('lightning', 'Magery', 'Lightning'), ('fireball', 'Magery', 'Fireball'),
                ('harm', 'Magery', 'Harm'), ('nether_bolt', 'Mysticism', 'Nether Bolt'),
                ('magicarrow', 'Magery', 'Magic Arrow')]:
            with self.subTest(spell=spell):
                self.setUp()
                item = self.item(distance=1)
                self.ns['sv']['use_' + key] = 1
                self.assertTrue(self.ns['cast_lighthouse'](item))
                self.assertEqual(self.calls, [(school, spell), ('wait', 'lighthouse', item.Serial)])
                self.assertTrue(self.ns['Timer'].Check('spells'))

    def test_mobile_only_spells_never_cast_on_items(self):
        self.ns['sv'].update(use_mindblast=1, use_wordofdeath=1, use_death_ray=1,
                             use_explosion_combo=1, use_nether_blast=1)
        self.assertFalse(self.ns['cast_lighthouse'](self.item()))
        self.assertEqual(self.calls, [])

    def test_low_mana_and_skill_checks_select_cheaper_enabled_spell(self):
        item = self.item()
        self.ns['sv'].update(use_flamestrike=1, use_energybolt=1, use_fireball=1)
        self.ns['low_mana'] = lambda: True
        self.assertTrue(self.ns['cast_lighthouse'](item))
        self.assertEqual(self.calls[0], ('Magery', 'Fireball'))
        self.world.timers.clear()
        self.calls.clear()
        self.ns['skill_value'] = lambda school: 0
        self.assertFalse(self.ns['cast_lighthouse'](item))
        self.assertEqual(self.calls, [])

    def test_harm_range_and_mana_are_checked(self):
        item = self.item(distance=3)
        self.ns['sv']['use_harm'] = 1
        self.assertFalse(self.ns['cast_lighthouse'](item))
        item.distance = 1
        self.ns['Player'].Mana = 5
        self.assertFalse(self.ns['cast_lighthouse'](item))
        self.assertEqual(self.calls, [])

    def test_cast_guards_protect_active_casts_cursors_and_blood_oath(self):
        for guard in ('spells', 'cursor', 'external', 'paralyzed', 'poisoned', 'oath'):
            with self.subTest(guard=guard):
                self.setUp()
                self.ns['sv']['use_fireball'] = 1
                item = self.item()
                if guard == 'spells': self.ns['Timer'].Create('spells', 1000)
                elif guard == 'cursor': self.world.cursor = True
                elif guard == 'external': self.settings['attack_gump_targeting'] = 1
                elif guard == 'paralyzed': self.ns['Player'].Paralized = True
                elif guard == 'poisoned': self.ns['Player'].Poisoned = True
                else: self.buffs.add('Bload Oath (curse)')
                self.assertFalse(self.ns['cast_lighthouse'](item))
                self.assertEqual(self.calls, [])

    def test_pending_cursor_targets_item_serial_and_clears_ownership(self):
        item = self.item()
        self.world.cursor = True
        self.ns['pending_target_cursor'] = {'kind': 'lighthouse', 'target': item.Serial}
        self.assertTrue(self.ns['execute_pending_target']())
        self.assertEqual(self.calls, [('target', (item.Serial,))])
        self.assertIsNone(self.ns['pending_target_cursor'])

    def test_pending_target_is_revalidated_and_cancelled_when_invalid(self):
        for change in ('destroyed', 'missing', 'range', 'disabled'):
            with self.subTest(change=change):
                self.setUp()
                item = self.item()
                self.world.cursor = True
                self.ns['pending_target_cursor'] = {'kind': 'lighthouse', 'target': item.Serial}
                if change == 'destroyed': item.ItemID = 1
                elif change == 'missing': self.items.clear()
                elif change == 'range': item.distance = 15
                else: self.ns['sv']['use_attack_lighthouses'] = 0
                self.assertFalse(self.ns['execute_pending_target']())
                self.assertEqual(self.calls, ['cancel'])
                self.assertIsNone(self.ns['pending_target_cursor'])

    def test_late_cursor_uses_existing_cast_recovery_path(self):
        item = self.item()
        self.ns['wait_for_spell_target'] = self.original_wait_for_spell_target
        self.ns['spell_target_wait_ms'] = lambda *args: 500
        self.ns['wait_for_target_responsive'] = lambda *args: False
        self.ns['last_target_wait_failure_kind'] = 'timeout'
        self.assertFalse(self.ns['wait_for_spell_target'](0.0, 1500, 'lighthouse', item))
        self.world.clock.now = 0.6
        self.world.cursor = True
        self.ns['resolve_orphan_target_cursor']()
        self.assertIn(('target', (item.Serial,)), self.calls)
        self.assertIsNone(self.ns['pending_target_cursor'])

    def test_main_loop_keeps_mobs_first_and_lighthouse_out_of_mobile_rotation(self):
        for hostiles in ([], [Obj(Serial=7, distance=4)]):
            with self.subTest(hostiles=bool(hostiles)):
                self.setUp()
                item = self.item()
                player = self.ns['Player']
                self.world.configure_combat(hostiles)
                self.ns['Player'] = player
                self.ns['sv']['use_attack_lighthouses'] = 1
                self.ns['cast_lighthouse'] = lambda item: self.calls.append(('lighthouse', item.Serial))
                exec(self.world.combat_tick, self.ns)
                if hostiles:
                    self.assertIn(('attack', 7), self.calls)
                    self.assertEqual(self.scans, [])
                    self.assertNotIn(('lighthouse', item.Serial), self.calls)
                else:
                    self.assertIn(('lighthouse', item.Serial), self.calls)
                    self.assertTrue(self.ns['_mage_combat'])
                    self.assertNotIn('keep_bless', self.calls)

    def test_gump_toggle_is_saved_in_character_profile_and_restored(self):
        gump = fixtures.load_functions(fixtures.GUMP)
        with tempfile.TemporaryDirectory() as directory:
            filename = os.path.join(directory, 'mage_character.json')
            gump.update(Misc=self.ns['Misc'], Player=self.ns['Player'], json=json, os=os,
                        PROFILE_PATH=filename, PROFILE_FILENAME='mage_character.json',
                        LEGACY_PROFILE_PATH=os.path.join(directory, 'absent.json'))
            tree = ast.parse(fixtures.GUMP.read_text())
            sections = next(node for node in tree.body if isinstance(node, ast.Assign)
                            and isinstance(node.targets[0], ast.Name) and node.targets[0].id == 'sections')
            exec(compile(ast.Module(body=[sections], type_ignores=[]), 'gump', 'exec'), gump)
            actions = gump['sections']['5: Single Target']
            button = list(gump['sections']).index('5: Single Target') * 1000 + list(actions).index('Attack Lighthouses') + 1
            gump['Gumps'] = Obj(WaitForGump=lambda *args: None, CloseGump=lambda *args: None,
                               GetGumpData=lambda *args: Obj(buttonid=button))
            self.assertIn('use_attack_lighthouses', gump['get_all_sv_keys']())
            gump['buttoncheck'](1)
            self.assertEqual(json.loads(Path(filename).read_text())['use_attack_lighthouses'], 1)
            self.settings['use_attack_lighthouses'] = 0
            gump['load_settings']()
            self.assertEqual(self.settings['use_attack_lighthouses'], 1)
            gump['buttoncheck'](1)
            self.assertEqual(json.loads(Path(filename).read_text())['use_attack_lighthouses'], 0)


if __name__ == '__main__':
    unittest.main()
