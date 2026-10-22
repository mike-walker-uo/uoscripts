"""Exercise equipment acknowledgements, action ownership and target stability."""
import ast
import json
from pathlib import Path
from types import SimpleNamespace as Obj
import unittest

ROOT = Path(__file__).resolve().parents[1]


def load_functions(path, ns):
    tree = ast.parse(path.read_text())
    nodes = [n for n in tree.body if isinstance(n, ast.FunctionDef)]
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(path), 'exec'), ns)
    for node in tree.body:
        if (isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name)
                and node.targets[0].id == '_flow'):
            ns['_flow'] = ast.literal_eval(node.value)


class CombatFlowTests(unittest.TestCase):
    def setUp(self):
        self.now = 0
        self.timers = {}
        self.calls = []
        self.shared = {}
        self.cursor = False
        self.buffs = set()
        self.items = {}
        self.hands = {'RightHand': None, 'LeftHand': None, 'Talisman': None}
        self.player = Obj(
            Serial=1, Backpack=Obj(Serial=99), HasSpecial=False, Visible=True,
            WarMode=True, Mana=100, Paralized=False, Followers=1,
            LowerManaCost=40, FasterCasting=2, FasterCastRecovery=6,
            SumAttribute=lambda name: 100,
            BuffsExist=lambda name, *args: name in self.buffs,
            SpellIsEnabled=lambda name: False,
            GetItemOnLayer=lambda layer: self.hands.get('RightHand' if layer == 'FirstValid' else layer),
            DistanceTo=lambda mob: mob.distance,
            EquipItem=lambda serial: self.calls.append(('equip', serial)),
            UnEquipItemByLayer=self.unequip,
            WeaponPrimarySA=lambda: self.calls.append('primary'),
            WeaponSecondarySA=lambda: self.calls.append('secondary'),
            WeaponClearSA=lambda: self.calls.append('clear'),
            HeadMessage=lambda *args: self.calls.append(('message', args)),
            SetWarMode=lambda mode: setattr(self.player, 'WarMode', mode),
            Attack=lambda mob: self.calls.append(('attack', mob.Serial)),
            ChatSay=lambda text: self.calls.append(('say', text)),
            InvokeVirtue=lambda name: self.calls.append(('virtue', name)))
        self.ns = dict(
            Player=self.player, json=json, sv={'activeattack': 1, 'attackrange': 12,
                'honordistance': 10, 'use_honor': 1, 'use_pet_sync': 1,
                'use_messages': 0, 'use_smart_target': 0},
            Timer=Obj(Check=lambda name: self.timers.get(name, 0) > self.now,
                      Create=self.create_timer),
            Misc=Obj(ReadSharedValue=lambda name: self.shared.get(name, 0),
                     SetSharedValue=self.shared.__setitem__, Pause=self.no_wait),
            Target=Obj(HasTarget=lambda flag=None: self.cursor if flag is None else False, Cancel=self.cancel,
                       TargetExecute=self.target),
            Items=Obj(FindBySerial=self.items.get,
                      UseItem=lambda item: self.calls.append(('use', item.Serial))),
            _last_equipped_weapon_serial=17, _last_equipped_weapon_layer='RightHand',
            _last_other_hand_serial=0, _last_pet_target_serial=0, use_honor_fix=0,
            SMART_TARGET_CASTER_IDS={10}, SMART_TARGET_HEALER_IDS={11},
            serverdelay=100, lmc=0, equippedweapon=None, _is_ranged_build=False,
            _weapon_key_by_item_id={0xF61: 'sword', 0x27A5: 'bow'},
            weapons={'default': Obj(ItemID=None)}, WEAPON_SPECIAL_ARM_DEBOUNCE_MS=800)
        load_functions(ROOT / 'AttackScript_MikeWalker.py', self.ns)
        self.ns['backstab_locked_target'] = lambda mobs: None

    def create_timer(self, name, ms):
        if ms <= 0:
            raise ValueError('Timer interval must be greater than zero')
        self.timers[name] = self.now + ms

    def no_wait(self, ms):
        self.fail('Unexpected blocking wait: %s' % ms)

    def unequip(self, layer):
        self.calls.append(('unequip', layer))
        self.hands[layer] = None

    def cancel(self):
        self.calls.append('cancel')
        self.cursor = False

    def target(self, serial):
        self.calls.append(('target', serial))
        self.cursor = False

    def tick(self, ms=100):
        self.now += ms
        self.ns['_flow'].update(spell_used=False, ability_used=False, cursor_used=False)

    def mob(self, serial=2, distance=1, hp=100, body=1):
        return Obj(Serial=serial, Deleted=False, Name='Mob %s' % serial,
                   Hits=hp, HitsMax=100, distance=distance, MobileID=body, YellowHits=False)

    def item(self, serial=17, graphic=0xF61):
        item = Obj(Serial=serial, ItemID=graphic, Container=99, Deleted=False)
        self.items[serial] = item
        return item

    def test_manual_gap_is_not_immediately_treated_as_disarm(self):
        old = self.item()
        self.ns['reequip_last_weapon']()
        self.assertEqual(self.ns['_flow']['weapon'], 'SWAPPING')
        self.tick(1000)
        self.ns['reequip_last_weapon']()
        self.assertEqual(self.calls, [])
        new = self.item(18, 0x27A5)
        self.hands['LeftHand'] = new
        self.ns['reequip_last_weapon']()
        self.assertEqual(self.ns['_flow']['weapon'], 'EQUIPPED')
        self.assertEqual(self.ns['_last_equipped_weapon_serial'], new.Serial)
        self.assertNotIn(('equip', old.Serial), self.calls)

    def test_persistent_empty_hand_recovers_weapon_with_retry_limit(self):
        self.item()
        self.ns['reequip_last_weapon']()
        self.tick(1200)
        self.ns['reequip_last_weapon']()
        self.ns['reequip_last_weapon']()
        self.assertEqual(self.calls, [('equip', 17)])
        self.assertEqual(self.ns['_flow']['weapon'], 'RECOVERING')
        self.tick(1000)
        self.ns['reequip_last_weapon']()
        self.assertEqual(self.calls, [('equip', 17), ('equip', 17)])

    def test_equipment_transaction_waits_for_server_confirmation(self):
        self.hands['RightHand'] = self.item()
        new = self.item(18, 0x27A5)
        self.assertTrue(self.ns['_slayer_equip']({'serial': 18}, True))
        self.ns['advance_equipment']()
        self.assertEqual(self.calls, [('unequip', 'RightHand')])
        self.tick(599)
        self.ns['advance_equipment']()
        self.assertNotIn(('equip', 18), self.calls)
        self.assertFalse(self.ns['weapon_ready']())
        self.tick(1)
        self.ns['advance_equipment']()
        self.assertEqual(self.calls[-1], ('equip', 18))
        self.assertEqual(self.ns['_flow']['equipment']['stage'], 'CONFIRM')
        self.hands['LeftHand'] = new
        self.ns['advance_equipment']()
        self.assertIsNone(self.ns['_flow']['equipment'])
        self.assertEqual(self.ns['weapon_set'], 'bow')
        self.assertTrue(self.ns['weapon_ready']())

    def test_failed_equip_times_out_without_premature_old_weapon_recovery(self):
        self.item(18)
        self.ns['_slayer_equip']({'serial': 18}, True)
        self.ns['advance_equipment']()
        self.tick(600)
        self.ns['advance_equipment']()
        self.ns['reequip_last_weapon']()
        self.assertEqual(self.calls, [('equip', 18)])
        self.tick(1500)
        self.ns['advance_equipment']()
        self.assertIsNone(self.ns['_flow']['equipment'])
        self.assertTrue(any(call[0] == 'message' for call in self.calls))

    def test_gump_queues_equipment_without_touching_hands(self):
        item = self.item(18)
        load_functions(ROOT / 'AttackScript_MikeWalker_GUMP.py', self.ns)
        self.ns['manual_slayer_equip']({'serial': item.Serial, 'name': 'Sword'}, True)
        request = json.loads(self.shared['attack_equip_request'])
        self.assertEqual(request['serial'], item.Serial)
        self.assertTrue(request['is_weapon'])
        self.assertEqual(self.shared['slayer_hold'], 1)
        self.assertFalse(any(call[0] in ('equip', 'unequip') for call in self.calls))

    def test_pet_and_honor_cannot_share_a_cursor(self):
        mob = self.mob()
        self.assertTrue(self.ns['start_cursor']('honor', mob, lambda: None))
        self.ns['sync_pet_target'](mob)
        self.assertEqual(self.calls, [])
        self.cursor = True
        self.tick()
        self.ns['service_cursor']()
        self.assertEqual(self.calls, [('target', mob.Serial)])
        self.assertIsNone(self.ns['_flow']['cursor'])
        self.assertEqual(self.shared['attack_cursor_owner'], '')

    def test_honor_rechecks_full_hp_before_targeting(self):
        mob = self.mob()
        self.ns['start_cursor']('honor', mob, lambda: None)
        mob.Hits = 99
        self.cursor = True
        self.tick()
        self.ns['service_cursor']()
        self.assertEqual(self.calls, ['cancel'])
        self.assertIsNone(self.ns['_flow']['cursor'])

    def test_cursor_timeout_cancels_owned_cursor_only(self):
        self.ns['start_cursor']('honor', self.mob(), lambda: None)
        self.cursor = True
        self.tick(1000)
        self.ns['service_cursor']()
        self.assertEqual(self.calls, ['cancel'])
        self.cursor = True  # A later manually opened cursor is unowned.
        self.ns['service_cursor']()
        self.assertTrue(self.cursor)
        self.assertEqual(self.calls, ['cancel'])

    def test_unknown_cursor_and_gump_prompt_block_automated_actions(self):
        for manual_cursor, gump_prompt in ((True, 0), (False, 1)):
            with self.subTest(cursor=manual_cursor, prompt=gump_prompt):
                self.cursor = manual_cursor
                self.shared['attack_gump_targeting'] = gump_prompt
                self.assertFalse(self.ns['start_cursor']('honor', self.mob(), lambda: self.fail()))
                self.assertFalse(self.ns['cast_action'](lambda *args: self.fail(), 'Confidence'))
                self.assertFalse(self.ns['_flow']['spell_used'])

    def test_cursor_request_failure_releases_reservation(self):
        def failure():
            raise RuntimeError('request rejected')
        with self.assertRaises(RuntimeError):
            self.ns['start_cursor']('honor', self.mob(), failure)
        self.assertIsNone(self.ns['_flow']['cursor'])
        self.assertEqual(self.shared['attack_cursor_owner'], '')

    def test_defensive_cast_wins_over_optional_buff(self):
        def attempt(name):
            self.ns['cast_action'](lambda spell: self.calls.append(spell), name)
        self.ns['run_spell_priority']((lambda: None, lambda: attempt('Evasion'),
                                       lambda: attempt('Divine Fury')))
        self.assertEqual(self.calls, ['Evasion'])
        self.tick(250)
        self.assertTrue(self.ns['cast_action'](lambda spell: self.calls.append(spell), 'Divine Fury'))

    def test_only_one_attack_ability_per_tick(self):
        self.hands['RightHand'] = self.item()
        self.assertTrue(self.ns['arm_weapon_special']('primary'))
        self.assertFalse(self.ns['arm_weapon_special']('secondary'))
        self.assertFalse(self.ns['cast_action'](lambda *args: self.fail(), 'Onslaught'))
        self.assertEqual(self.calls, ['primary'])

    def test_owned_cursor_blocks_spells_without_starting_cooldowns(self):
        self.ns['start_cursor']('honor', self.mob(), lambda: None)
        self.assertFalse(self.ns['cast_action'](lambda *args: self.fail(), 'Confidence'))
        self.assertNotIn('spells', self.timers)

    def test_bag_targeting_returns_before_cursor_arrives(self):
        bag, gold = self.item(18), self.item(19)
        self.ns['sv']['use_bagofsending'] = 1
        self.player.Weight, self.player.MaxWeight = 100, 100
        self.ns['find_bag_of_sending'] = lambda: bag
        self.ns['Items'].FindByID = lambda *args: gold
        self.ns['Items'].GetPropValue = lambda *args: 10
        self.ns['checkweight']()
        self.assertEqual(self.calls, [('use', 18)])
        self.cursor = True
        self.tick()
        self.ns['service_cursor']()
        self.assertEqual(self.calls[-1], ('target', 19))

    def test_missing_lootbag_warns_without_prompting(self):
        self.ns.update(_artifact_move_queue=[], _artifact_scan_queue=[])
        self.ns['sv'].update(use_move_artis=1, lootbag_serial=0)
        self.ns['select_lootbag'] = lambda *args: self.fail('Combat must not prompt')
        self.ns['move_artifacts_to_lootbag']()
        self.assertTrue(any(call[0] == 'message' for call in self.calls))

    def test_properties_are_requested_without_waiting(self):
        item = self.item()
        item.Name = None
        self.ns['Items'].WaitForProps = lambda serial, delay: self.calls.append((serial, delay))
        cache = {}
        self.assertIsNone(self.ns['cached_item_name'](item, cache))
        self.assertIsNone(self.ns['cached_item_name'](item, cache))
        self.assertEqual(self.calls, [(17, 0)])
        item.Name = 'Sword'
        self.assertEqual(self.ns['cached_item_name'](item, cache), 'sword')

    def test_melee_target_stays_when_weaker_melee_mob_appears(self):
        current, newcomer = self.mob(2, 1), self.mob(3, 1, hp=10)
        self.assertIs(self.ns['select_combat_target']([(current, 1)], set()), current)
        self.tick()
        self.assertIs(self.ns['select_combat_target']([(current, 1), (newcomer, 1)], set()), current)

    def test_higher_priority_caster_can_replace_target(self):
        self.ns['sv']['use_smart_target'] = 1
        current, caster = self.mob(2), self.mob(3, 1, body=10)
        self.ns['select_combat_target']([(current, 1)], set())
        self.assertIs(self.ns['select_combat_target']([(current, 1), (caster, 1)], set()), caster)

    def test_changeling_and_backstab_priorities_are_preserved(self):
        current, changeling = self.mob(2), self.mob(3, 1)
        self.ns['select_combat_target']([(current, 1)], set())
        self.assertIs(self.ns['select_combat_target']([(current, 1), (changeling, 1)], {3}), changeling)
        self.ns['backstab_locked_target'] = lambda mobs: current
        self.assertIs(self.ns['select_combat_target']([(current, 1), (changeling, 1)], {3}), current)

    def test_dead_or_out_of_range_target_is_replaced(self):
        first, second = self.mob(2), self.mob(3)
        self.ns['select_combat_target']([(first, 1)], set())
        first.Hits = 0
        self.assertIs(self.ns['select_combat_target']([(first, 1), (second, 2)], set()), second)
        self.assertEqual(self.ns['select_combat_target']([(second, 20), (self.mob(4), 1)], set()).Serial, 4)

    def test_unknown_hp_target_can_still_be_engaged(self):
        mob = self.mob()
        mob.Hits, mob.HitsMax = 0, 0
        self.assertIs(self.ns['select_combat_target']([(mob, 1)], set()), mob)

    def test_stalled_target_releases_but_damage_keeps_lock(self):
        first, second = self.mob(2, 4), self.mob(3, 3)
        self.ns['select_combat_target']([(first, 4)], set())
        self.tick(7000)
        first.Hits = 99
        self.assertIs(self.ns['select_combat_target']([(first, 4), (second, 3)], set()), first)
        self.tick(7000)
        self.assertIs(self.ns['select_combat_target']([(first, 4), (second, 3)], set()), first)
        self.tick(1000)
        self.assertIs(self.ns['select_combat_target']([(first, 4), (second, 3)], set()), second)


    def test_manual_request_supersedes_automatic_swap(self):
        self.item(18)
        self.item(19)
        self.ns['_slayer_equip']({'serial': 18}, True)
        self.shared['attack_equip_request'] = json.dumps({'serial': 19, 'is_weapon': True})
        self.ns['advance_equipment']()
        self.tick(600)
        self.ns['advance_equipment']()
        self.assertIn(('equip', 19), self.calls)
        self.assertNotIn(('equip', 18), self.calls)

    def test_ninjitsu_cannot_clear_ability_selected_earlier_in_tick(self):
        self.ns['_flow']['ability_used'] = True
        self.player.HasSpecial = True
        self.ns['arm_ninjitsu_attack'](('Death Strike', 30))
        self.assertNotIn('clear', self.calls)

    def test_emergency_curse_preempts_owned_honor_cursor(self):
        self.ns['start_cursor']('honor', self.mob(), lambda: None)
        self.cursor = True
        self.buffs.add('Bload Oath (curse)')
        self.ns.update(_pending_apple=None, _cached_castpause=0,
                       Spells=Obj(CastChivalry=lambda *args: self.calls.append(('cast', args))),
                       calc_castspeed_chiv_sw=lambda ms: ms)
        self.ns['sv'].update(use_pot_apple=0, use_removecurse=1)
        self.ns['checkbloodoath']()
        self.assertIsNone(self.ns['_flow']['cursor'])
        self.assertLess(self.calls.index('cancel'), next(i for i, call in enumerate(self.calls)
                                                       if call[0] == 'cast'))
        self.assertIn(('cast', ('Remove Curse', 1, False)), self.calls)

    def setup_loop(self, victims, active=1):
        self.shared['activeattack'] = active
        self.ns.update(_victims_cache=victims, _changelings_cache=[],
                       _IDLE_PAUSE_EXTRA=250)
        self.ns['sv'].update(nearbyrange=1, use_df=0, use_cw=0,
                            use_thunderstorm=0, use_distancemarker=0,
                            use_honor=0, activeattack=active)
        self.timers.update({name: self.now + 10000 for name in
                           ('sv_refresh', 'mobscan', 'weaponcheck', 'checks', 'dress')})
        for name in ('advance_equipment', 'reequip_last_weapon', 'track_weapon_special_state',
                     'track_backstab_execution', 'binding_bracelet', 'trappedcrate',
                     'checkbloodoath', 'auto_potion', 'evasion', 'checkhits', 'curseweapon',
                     'divinefury_lowstam', 'combat_buffs', 'attuneweapon', 'immolatingweapon',
                     'counterattack', 'castmirrorimage', 'holylight', 'playingtheodds',
                     'castsummonfey', 'checkwhitetigerform', 'removepoison', 'removecurse',
                     'closewounds', 'prearm_weaponspecial', 'slayer_swap_tick',
                     'release_one_mirror_image', 'checkweight', 'drop_heirloom_chests',
                     'move_artifacts_to_lootbag'):
            self.ns[name] = lambda *args, name=name: self.calls.append(name)
        self.ns['continue_hidden_backstab'] = lambda: False
        self.ns['fighting'] = lambda mob, *args: self.calls.append('fighting')
        self.ns['Misc'].Pause = lambda ms: self.calls.append(('pause', ms))

    def test_loop_runs_emergencies_then_combat_then_background(self):
        self.setup_loop([self.mob()])
        self.ns['run_tick']()
        self.assertLess(self.calls.index('checkbloodoath'), self.calls.index('fighting'))
        self.assertNotIn('combat_buffs', self.calls)
        for name in ('checkweight', 'drop_heirloom_chests', 'move_artifacts_to_lootbag'):
            self.assertNotIn(name, self.calls)
        self.assertNotIn('closewounds', self.calls)
        self.assertNotIn('removecurse', self.calls)

    def test_attack_off_does_not_heal_with_hostile_in_six_tiles(self):
        self.setup_loop([self.mob(distance=4)], active=0)
        self.ns['run_tick']()
        for name in ('fighting', 'closewounds', 'removecurse', 'removepoison'):
            self.assertNotIn(name, self.calls)

    def test_hidden_cycle_services_emergencies_without_background_waits(self):
        self.setup_loop([self.mob()])
        self.ns['continue_hidden_backstab'] = lambda: True
        self.ns['run_tick']()
        self.assertIn('checkbloodoath', self.calls)
        self.assertIn('auto_potion', self.calls)
        self.assertNotIn('checkweight', self.calls)

    def test_main_loop_calls_have_no_operational_sleeps_or_cursor_waits(self):
        tree = ast.parse((ROOT / 'AttackScript_MikeWalker.py').read_text())
        for fn in (n for n in tree.body if isinstance(n, ast.FunctionDef)):
            for call in (n for n in ast.walk(fn) if isinstance(n, ast.Call)
                         and isinstance(n.func, ast.Attribute)):
                if call.func.attr == 'Pause':
                    self.assertEqual(fn.name, 'run_tick')
                self.assertNotEqual(call.func.attr, 'WaitForTarget')
                if call.func.attr in ('WaitForProps', 'WaitForContext'):
                    self.assertEqual(ast.literal_eval(call.args[1]), 0)

    def test_shield_left_behind_is_not_treated_as_weapon(self):
        shield = self.item(20, 0x1B76)
        self.hands['LeftHand'] = shield
        self.ns['_last_other_hand_serial'] = shield.Serial
        self.assertIsNone(self.ns['_current_weapon']())
        self.assertFalse(self.ns['weapon_ready']())



if __name__ == '__main__':
    unittest.main()
