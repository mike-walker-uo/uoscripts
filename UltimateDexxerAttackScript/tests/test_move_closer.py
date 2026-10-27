"""Melee approach timing, one-step movement and saved GUMP toggles."""
import ast
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace as Obj
import unittest

import test_combat_flow as fixtures
import test_combat_review as review
import test_df_stamina as settings_fixtures

ROOT = Path(__file__).resolve().parents[1]


class MoveCloserTests(unittest.TestCase):
    def setUp(self):
        self.world = fixtures.CombatFlowTests(methodName='runTest')
        self.world.setUp()
        self.ns = self.world.ns
        self.calls = self.world.calls
        self.ns['sv'].update(use_move_closer_message=1, use_auto_move_closer=0)
        self.world.player.Position = Obj(X=0, Y=0)
        self.world.player.Run = lambda direction: self.calls.append(('run', direction))
        self.scans = []
        self.path = [Obj(X=1, Y=0), Obj(X=2, Y=0), Obj(X=3, Y=0)]
        self.ns['PathFinding'] = Obj(GetPath=self.get_path)
        self.mob = self.world.mob(distance=3)
        self.mob.Position = Obj(X=3, Y=0)

    def get_path(self, x, y, ignore_mobile):
        self.scans.append((x, y, ignore_mobile))
        return self.path

    def warn(self, distance=2):
        self.ns['check_move_closer']([(self.mob, distance)])

    def test_warning_waits_one_second_and_repeats_every_three(self):
        self.warn()
        self.world.tick(999)
        self.warn(3)
        self.assertEqual(self.calls, [])
        self.world.tick(2)
        self.warn()
        self.assertEqual(self.calls, [('message', (33, 'move closer'))])
        self.world.tick(2999)
        self.warn()
        self.assertEqual(len(self.calls), 1)
        self.world.tick(1)
        self.warn()
        self.assertEqual(len(self.calls), 2)

    def test_warning_resets_when_closer_farther_or_no_mobs(self):
        for distances in ([], [(self.mob, 1)], [(self.mob, 4)]):
            with self.subTest(distances=distances):
                self.warn()
                self.world.tick(900)
                self.ns['check_move_closer'](distances)
                self.warn()
                self.world.tick(900)
                self.warn()
                self.assertEqual(self.calls, [])
                self.ns['check_move_closer']([])

    def test_disabled_messages_and_ranged_builds_never_warn(self):
        for messages, ranged, active in ((0, False, 1), (1, True, 1), (1, False, 0)):
            self.ns['sv'].update(use_move_closer_message=messages, activeattack=active)
            self.ns['_is_ranged_build'] = ranged
            self.warn()
            self.world.tick(5000)
            self.warn()
        self.assertEqual(self.calls, [])

    def test_adjacent_mob_prevents_warning_for_farther_mob(self):
        self.ns['check_move_closer']([(self.mob, 2), (self.world.mob(3), 1)])
        self.world.tick(2000)
        self.ns['check_move_closer']([(self.mob, 2), (self.world.mob(3), 1)])
        self.assertEqual(self.calls, [])

    def test_auto_move_is_independent_of_messages_and_takes_one_step(self):
        self.ns['auto_move_closer'](self.mob)
        self.assertEqual(self.scans, [])
        self.ns['sv'].update(use_auto_move_closer=1, use_move_closer_message=0)
        self.world.create_timer('attack_controller_target', 5000)
        self.ns['auto_move_closer'](self.mob)
        self.assertEqual(self.calls, [('run', 'East')])
        self.assertEqual(self.scans, [(3, 0, True)])
        self.ns['auto_move_closer'](self.mob)
        self.assertEqual(len(self.scans), 1)
        self.world.tick(250)
        self.mob.distance = 1
        self.ns['auto_move_closer'](self.mob)
        self.assertEqual(len(self.scans), 1)

    def test_auto_move_requires_melee_active_and_two_to_three_tiles(self):
        self.ns['sv']['use_auto_move_closer'] = 1
        for distance in (-1, 0, 1, 4, 10):
            self.mob.distance = distance
            self.ns['auto_move_closer'](self.mob)
        self.mob.distance = 2
        self.ns['_is_ranged_build'] = True
        self.ns['auto_move_closer'](self.mob)
        self.ns['_is_ranged_build'] = False
        self.ns['sv']['activeattack'] = 0
        self.ns['auto_move_closer'](self.mob)
        self.assertEqual(self.scans, [])

    def test_auto_move_yields_to_casting_hidden_paralysis_and_blood_oath(self):
        self.ns['sv']['use_auto_move_closer'] = 1
        self.world.create_timer('spells', 1000)
        self.ns['auto_move_closer'](self.mob)
        self.world.timers.clear()
        self.world.player.Visible = False
        self.ns['auto_move_closer'](self.mob)
        self.world.player.Visible = True
        self.world.player.Paralized = True
        self.ns['auto_move_closer'](self.mob)
        self.world.player.Paralized = False
        self.world.buffs.add('Bload Oath (curse)')
        self.ns['auto_move_closer'](self.mob)
        self.assertEqual(self.scans, [])

    def test_unreachable_path_is_throttled_and_does_not_move(self):
        self.ns['sv']['use_auto_move_closer'] = 1
        self.path = None
        self.ns['auto_move_closer'](self.mob)
        self.ns['auto_move_closer'](self.mob)
        self.assertEqual(len(self.scans), 1)
        self.assertEqual(self.calls, [])

    def test_deleted_dead_or_missing_targets_do_not_move(self):
        self.ns['sv']['use_auto_move_closer'] = 1
        self.ns['auto_move_closer'](None)
        self.mob.Deleted = True
        self.ns['auto_move_closer'](self.mob)
        self.mob.Deleted = False
        self.mob.Hits = 0
        self.ns['auto_move_closer'](self.mob)
        self.assertEqual(self.scans, [])

    def test_diagonal_step_and_no_step_onto_target(self):
        self.ns['sv']['use_auto_move_closer'] = 1
        self.path = [Obj(X=1, Y=-1)]
        self.ns['auto_move_closer'](self.mob)
        self.assertEqual(self.calls, [('run', 'NorthEast')])
        self.world.tick(250)
        self.path = [self.mob.Position]
        self.ns['auto_move_closer'](self.mob)
        self.assertEqual(len(self.calls), 1)

    def test_combat_engages_before_approach(self):
        world = review.CombatReviewTests(methodName='runTest')
        world.setUp()
        mobs, distances, cursor = world.prepare_honor_tick()
        world.ns['sv']['use_auto_move_closer'] = 1
        world.ns['Player'].Position = Obj(X=0, Y=0)
        world.ns['Player'].Visible = True
        world.ns['Player'].Paralized = False
        world.ns['Player'].Run = lambda direction: world.calls.append(('run', direction))
        mobs[0].Position = Obj(X=2, Y=0)
        world.ns['PathFinding'] = Obj(GetPath=lambda *args: [Obj(X=1, Y=0)])
        world.ns['run_tick']()
        self.assertLess(world.calls.index(('fight', mobs[0].Serial)),
                        world.calls.index(('run', 'East')))

    def test_defaults_saved_toggles_and_attack_load(self):
        settings = {}
        player = self.world.player
        misc = Obj(ReadSharedValue=lambda key: settings.get(key, 0),
                   SetSharedValue=settings.__setitem__)
        attack = dict(Player=player, Misc=misc, sv={}, json=json, os=os)
        tree = settings_fixtures.load_script('AttackScript_MikeWalker.py', attack)
        keys = ('use_move_closer_message', 'use_auto_move_closer')
        for node in tree.body:
            if (isinstance(node, ast.Expr) and isinstance(node.value, ast.Call)
                    and isinstance(node.value.func, ast.Attribute)
                    and node.value.func.attr == 'SetSharedValue' and node.value.args
                    and isinstance(node.value.args[0], ast.Constant)
                    and node.value.args[0].value in keys):
                exec(compile(ast.Module(body=[node], type_ignores=[]), 'defaults', 'exec'), attack)
        self.assertEqual([settings[key] for key in keys], [1, 0])
        gump = dict(Player=player, Misc=misc, json=json, os=os)
        settings_fixtures.load_script('AttackScript_MikeWalker_GUMP.py', gump)
        with TemporaryDirectory() as directory:
            filename = os.path.join(directory, 'character.json')
            gump['SETTINGS_FILE'] = filename
            actions = gump['sections']['3: Attacks']
            gd = Obj(buttonid=0)
            gump.update(_active_tab='settings', Gumps=Obj(WaitForGump=lambda *a: None,
                CloseGump=lambda *a: None, GetGumpData=lambda *a: gd))
            for label, key in (('Move Closer Msg', keys[0]), ('Auto Move Closer', keys[1])):
                self.assertIn(key, attack['SETTINGS_KEYS'])
                self.assertIn(key, gump['SETTINGS_KEYS'])
                gd.buttonid = gump['_section_indices']['3: Attacks'] * 1000 + list(actions).index(label) + 1
                gump['buttoncheck'](1)
            saved = json.loads(Path(filename).read_text())
            self.assertEqual([saved[key] for key in keys], [0, 1])
            settings.clear()
            attack.update(SETTINGS_FILE=filename, LEGACY_SETTINGS_FILE='', ignored_mob_names=set(),
                          ignored_mob_serials=set(), ignored_summon_names=set())
            self.assertTrue(attack['load_settings']())
            attack['refresh_sv']()
            self.assertEqual([attack['sv'][key] for key in keys], [0, 1])


if __name__ == '__main__':
    unittest.main()
