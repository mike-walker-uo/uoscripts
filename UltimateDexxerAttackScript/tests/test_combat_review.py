import ast
from pathlib import Path
from types import SimpleNamespace as Obj
import unittest

SOURCE = Path(__file__).resolve().parents[1] / 'AttackScript_MikeWalker.py'


class CombatReviewTests(unittest.TestCase):
    def setUp(self):
        self.now = 0
        self.timers = {}
        self.calls = []
        self.ns = {
            'Timer': Obj(Check=lambda n: self.timers.get(n, 0) > self.now,
                         Create=lambda n, ms: self.timers.update({n: self.now + ms})),
            'Misc': Obj(Pause=lambda ms: self.calls.append(('pause', ms))),
        }
        tree = ast.parse(SOURCE.read_text())
        exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n, ast.FunctionDef)],
                                type_ignores=[]), str(SOURCE), 'exec'), self.ns)

    def test_blood_oath_blocks_prearm_and_clears_early_return(self):
        self.ns.update(sv={'activeattack': 1, 'disable_weaponspecials': 0},
                       Player=Obj(BuffsExist=lambda n: True, HasSpecial=True, WarMode=False,
                                  WeaponClearSA=lambda: self.calls.append('clear')))
        self.ns['prearm_weaponspecial']()
        self.ns['fighting'](None, [], [], [], 2)
        self.assertEqual(self.calls, ['clear', 'clear'])

    def test_disarm_retries_last_weapon_with_shield_equipped(self):
        weapon = Obj(Serial=17, ItemID=0xF61, Container=99)
        shield = Obj(Serial=18, ItemID=0x1B76)
        replacement = Obj(Serial=19, ItemID=0x9999, Container=99)
        hands = {'RightHand': weapon, 'LeftHand': shield}
        self.ns.update(
            _last_equipped_weapon_serial=weapon.Serial,
            _last_equipped_weapon_layer='RightHand',
            _last_other_hand_serial=shield.Serial,
            Player=Obj(Backpack=Obj(Serial=99),
                       GetItemOnLayer=lambda layer: hands[layer],
                       EquipItem=lambda serial: self.calls.append(serial)),
            Items=Obj(FindBySerial=lambda serial: weapon if serial == weapon.Serial else None))
        self.ns['reequip_last_weapon']()
        self.assertEqual(self.calls, [])

        hands['RightHand'] = None
        self.ns['reequip_last_weapon']()
        self.ns['reequip_last_weapon']()
        self.assertEqual(self.calls, [weapon.Serial])
        self.assertEqual(self.ns['_last_equipped_weapon_serial'], weapon.Serial)
        self.now = 1000
        self.ns['reequip_last_weapon']()
        self.assertEqual(self.calls, [weapon.Serial, weapon.Serial])

        hands['LeftHand'] = replacement
        self.ns['reequip_last_weapon']()
        self.assertEqual(self.ns['_last_equipped_weapon_serial'], replacement.Serial)
        self.assertEqual(self.ns['_last_equipped_weapon_layer'], 'LeftHand')
        self.assertEqual(self.calls, [weapon.Serial, weapon.Serial])

    def test_honor_chooses_closest_full_health_mob_in_range(self):
        mobs = [Obj(Serial=n, Name=str(n), Hits=hits, HitsMax=100, Deleted=False)
                for n, hits in [(1, 70), (2, 100), (3, 100), (4, 100)]]
        distances = {1: 2, 2: 4, 3: 3, 4: 11}
        cursor = [False]
        self.timers.update({name: 1000 for name in
                            ('sv_refresh', 'dress', 'mobscan', 'weaponcheck')})
        self.ns.update(
            sv={'activeattack': 1, 'nearbyrange': 1, 'use_df': 0, 'use_cw': 0,
                'use_thunderstorm': 0, 'use_smart_target': 0, 'use_distancemarker': 0,
                'use_honor': 1, 'honordistance': 10, 'use_messages': 1},
            use_honor_fix=0, _pending_honor_target=None,
            _victims_cache=mobs, _changelings_cache=[],
            Misc=Obj(ReadSharedValue=lambda name: 1,
                     Pause=lambda ms: None),
            Player=Obj(DistanceTo=lambda mob: distances[mob.Serial],
                       BuffsExist=lambda name: False,
                       InvokeVirtue=lambda name: self.calls.append(('virtue', name)),
                       HeadMessage=lambda color, message: self.calls.append(('message', message))),
            Target=Obj(HasTarget=lambda: cursor[0],
                       WaitForTarget=lambda *args: self.fail('Honor must not wait'),
                       TargetExecute=lambda mob: (self.calls.append(('honor', mob.Serial)),
                                                  cursor.__setitem__(0, False))),
            fighting=lambda mob, *args: self.calls.append(('fight', mob.Serial)))
        for name in ('reequip_last_weapon', 'track_weapon_special_state',
                     'track_backstab_execution', 'clear_stuck_target_cursor',
                     'binding_bracelet', 'trappedcrate', 'checkbloodoath', 'auto_potion',
                     'checkhits', 'evasion', 'curseweapon', 'divinefury_lowstam',
                     'checkweight', 'castsummonfey', 'checkwhitetigerform', 'dresslist',
                     'drop_heirloom_chests', 'move_artifacts_to_lootbag',
                     'release_one_mirror_image', 'castmirrorimage', 'checkweapon',
                     'attuneweapon', 'immolatingweapon', 'counterattack', 'holylight',
                     'removepoison', 'removecurse', 'closewounds', 'slayer_swap_tick',
                     'prearm_weaponspecial', 'playingtheodds'):
            self.ns[name] = lambda *args: None
        self.ns['continue_hidden_backstab'] = lambda: False
        self.ns['backstab_locked_target'] = lambda victims: None

        self.ns['run_tick']()
        self.assertIn(('fight', 1), self.calls)
        self.assertLess(self.calls.index(('fight', 1)), self.calls.index(('virtue', 'Honor')))
        self.assertNotIn(('honor', 3), self.calls)
        self.assertEqual(self.ns['_pending_honor_target'].Serial, 3)

        self.calls.clear()
        cursor[0] = True
        self.ns['run_tick']()
        self.assertIn(('honor', 3), self.calls)
        self.assertIn(('fight', 1), self.calls)
        self.assertIn(('message', 'Honor mob: 3'), self.calls)

        self.calls.clear()
        self.timers.pop('honorattempt')
        distances.update({2: 11, 3: 12})
        self.ns['run_tick']()
        self.assertFalse(any(call[0] == 'honor' for call in self.calls))

    def test_pet_cursor_timeout_retries_same_target(self):
        cursor = [False]
        self.ns.update(sv={'use_pet_sync': 1}, _last_pet_target_serial=0,
                       Player=Obj(Followers=1, ChatSay=lambda s: self.calls.append(s)),
                       Target=Obj(HasTarget=lambda: cursor[0],
                                  WaitForTarget=lambda *a: None,
                                  TargetExecute=lambda s: self.calls.append(s)))
        target = Obj(Serial=123)
        self.ns['sync_pet_target'](target)
        self.assertEqual(self.ns['_last_pet_target_serial'], 0)
        self.now = 2000
        self.ns['Target'].WaitForTarget = lambda *a: cursor.__setitem__(0, True)
        self.ns['sync_pet_target'](target)
        self.assertEqual(self.calls, ['all kill', 'all kill', 123])
        self.assertEqual(self.ns['_last_pet_target_serial'], 123)

    def test_each_potion_confirms_consumption_or_retries(self):
        for kind, enabled, graphic in [('pot_refresh', 'use_pot_refresh', 0xF0B),
                                       ('pot_cure', 'use_pot_cure', 0xF07),
                                       ('pot_heal', 'use_pot_heal_emergency', 0xF0C)]:
            with self.subTest(kind=kind):
                self.timers.clear()
                self.now = 0
                self.calls.clear()
                pot = Obj(Serial=10, Amount=5, Deleted=False)
                settings = dict(use_pot_refresh=0, use_pot_cure=0,
                                use_pot_heal_emergency=0, stam_pot_pct=30, heal_pot_pct=20)
                settings[enabled] = 1
                self.ns.update(sv=settings, _pending_potions={}, lmc=0,
                               Player=Obj(Stam=0, StamMax=100, Poisoned=True, Mana=0,
                                          Hits=1, HitsMax=100, Backpack=Obj(Serial=1)),
                               Items=Obj(FindByID=lambda *a: pot,
                                         FindBySerial=lambda s: pot,
                                         UseItem=lambda p: self.calls.append(p.Serial)))
                self.ns['auto_potion']()
                self.now = 1000
                self.ns['auto_potion']()
                self.assertIn(kind, self.ns['_pending_potions'])
                self.assertNotIn(kind, self.timers)
                self.assertEqual(self.calls, [10])
                self.now = 3000
                self.ns['auto_potion']()
                pot.Amount = 4
                self.ns['auto_potion']()
                self.assertEqual(self.calls, [10, 10])
                self.assertEqual(self.timers[kind], 13500)

    def test_artifact_moves_are_paced_without_sleep(self):
        bag = Obj(Serial=1)
        artifacts = [Obj(Serial=n, Container=99, Deleted=False) for n in (2, 3, 4)]
        items = {i.Serial: i for i in [bag] + artifacts}
        scans = []
        self.ns.update(sv={'use_move_artis': 1, 'lootbag_serial': 1, 'use_messages': 0},
                       _artifact_scan_queue=[], _artifact_move_queue=[],
                       _artifact_name_cache={}, ARTIFACT_NAMES={'artifact'},
                       Player=Obj(Backpack=Obj(Serial=99)),
                       Items=Obj(FindBySerial=items.get, Move=lambda *a: self.calls.append(a[0].Serial)),
                       item_is_in_backpack=lambda item: item is not None,
                       backpack_items_except=lambda *a: scans.append(True) or artifacts,
                       cached_item_name=lambda *a: 'artifact')
        self.ns['move_artifacts_to_lootbag']()
        self.ns['move_artifacts_to_lootbag']()
        self.assertEqual(self.calls, [2])
        self.now = 600
        self.ns['move_artifacts_to_lootbag']()
        self.assertEqual(self.calls, [2, 3])
        self.assertEqual(len(scans), 1)
        self.ns['sv']['use_move_artis'] = 0
        self.ns['move_artifacts_to_lootbag']()
        self.assertEqual(self.ns['_artifact_move_queue'], [])

    def test_artifact_scan_does_not_reset_before_queue_drains(self):
        bag = Obj(Serial=1, Deleted=False)
        artifacts = [Obj(Serial=n, Container=99, Deleted=False) for n in range(2, 202)]
        items = {item.Serial: item for item in [bag] + artifacts}
        self.ns.update(
            sv={'use_move_artis': 1, 'lootbag_serial': 1, 'use_messages': 0},
            _artifact_scan_queue=[201, 200], _artifact_move_queue=[],
            _artifact_name_cache={}, ARTIFACT_NAMES={'artifact'},
            Player=Obj(Backpack=Obj(Serial=99)),
            Items=Obj(FindBySerial=items.get,
                      Move=lambda item, *args: self.calls.append(item.Serial)),
            item_is_in_backpack=lambda item: item is not None,
            backpack_items_except=lambda *args: artifacts,
            cached_item_name=lambda *args: 'artifact')
        self.ns['move_artifacts_to_lootbag']()
        self.assertEqual(self.calls, [201])
        self.assertEqual(self.ns['_artifact_scan_queue'], [200])

    def test_heirloom_decoy_does_not_block_real_chest(self):
        decoy = Obj(Serial=2, ItemID=0x2811, Hue=0, Name='ordinary chest',
                    Container=99, Deleted=False)
        chest = Obj(Serial=3, ItemID=0x2811, Hue=0, Name='Chest of Heirlooms',
                    Container=99, Deleted=False)
        items = {2: decoy, 3: chest}
        self.ns.update(
            _heirloom_candidate_queue=[], _heirloom_drop_queue=[],
            _heirloom_drop_state=None, _artifact_name_cache={},
            HEIRLOOM_CHEST_ID=0x2811, HEIRLOOM_CHEST_HUE=0,
            HEIRLOOM_CHEST_NAME='chest of heirlooms', HEIRLOOM_DROP_OFFSETS=((0, 0),),
            sv={'use_messages': 0},
            Player=Obj(Backpack=Obj(Serial=99), Position=Obj(X=10, Y=20, Z=0),
                       HeadMessage=lambda *a: None),
            Items=Obj(FindBySerial=items.get, WaitForProps=lambda *a: None,
                      MoveOnGround=lambda item, *a: self.calls.append(item.Serial)),
            backpack_items_except=lambda *a: [decoy, chest],
            item_is_in_backpack=lambda item: item is not None and item.Container == 99)
        self.ns['drop_heirloom_chests']()
        self.assertEqual(self.calls, [])
        self.ns['drop_heirloom_chests']()
        self.assertEqual(self.calls, [3])

    def test_mirror_release_checks_one_candidate_per_tick(self):
        first = Obj(Serial=2, Deleted=False, Name='Hero', MobileID=1)
        second = Obj(Serial=3, Deleted=False, Name='Hero', MobileID=1)
        mobs = {2: first, 3: second}
        waits = []
        replies = []
        self.ns.update(
            _mirror_release_candidates=[],
            sv={'use_releasemirrorimage': 1, 'attackrange': 1, 'use_messages': 0},
            Player=Obj(Serial=1, Name='Hero', MobileID=1, Followers=4,
                       HeadMessage=lambda *a: None),
            Mobiles=Obj(Filter=lambda: Obj(), ApplyFilter=lambda f: [first, second],
                        FindBySerial=mobs.get),
            Misc=Obj(WaitForContext=lambda serial, ms: waits.append(serial) or
                     ([] if serial == 2 else [Obj(Entry='Release', Response=7)]),
                     ContextReply=lambda serial, response: replies.append((serial, response))))
        self.ns['release_one_mirror_image'](True)
        self.assertEqual(waits, [2])
        self.assertEqual(replies, [])
        self.ns['release_one_mirror_image'](True)
        self.assertEqual(waits, [2, 3])
        self.assertEqual(replies, [(3, 7)])

    def test_hidden_cycle_still_refreshes_settings_and_alerts(self):
        self.ns.update(sv={}, Misc=Obj(ReadSharedValue=lambda n: 1, Pause=lambda ms: None),
                       refresh_sv=lambda: self.calls.append('settings'),
                       legendarycheck=lambda: self.calls.append('alert'),
                       track_weapon_special_state=lambda: None,
                       track_backstab_execution=lambda: None, clear_stuck_target_cursor=lambda: None,
                       continue_hidden_backstab=lambda: self.calls.append('backstab') or True,
                       reequip_last_weapon=lambda: None,
                       complete_pending_honor=lambda: None)
        self.ns['run_tick']()
        self.assertEqual(self.calls, ['settings', 'alert', 'backstab'])

    def test_momentum_with_specials_off_at_high_mana(self):
        self.ns.update(sv=dict(disable_weaponspecials=1, use_onslaught=0, use_eoo=0,
                               use_momentumstrike=1, use_messages=0),
                       Player=Obj(HasSpecial=False, WarMode=True, Mana=100,
                                  BuffsExist=lambda n: False, SpellIsEnabled=lambda n: False,
                                  Attack=lambda n: None),
                       selected_ninjitsu_attack=lambda: None, backstab_cycle_attack=lambda *a: False,
                       honorable_execution=lambda n: None, sync_pet_target=lambda n: None,
                       get_weaponabilitiesmanacost=lambda m: m, lmc=0,
                       weapons={0: Obj(weaponspecial_primary='Armor Ignore',
                                       weaponspecial_secondary='Double Strike')}, weapon_set=0,
                       Spells=Obj(CastBushido=lambda name: self.calls.append(name)))
        self.ns['fighting'](Obj(Serial=1), [], [], [1, 2], 2)
        self.assertIn('Momentum Strike', self.calls)


if __name__ == '__main__':
    unittest.main()
