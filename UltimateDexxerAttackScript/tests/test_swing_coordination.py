"""Cross-script target agreement and uninterrupted melee ability handling."""
from pathlib import Path
from types import SimpleNamespace as Obj
import unittest
import ast

import test_combat_flow as fixtures

ROOT = Path(__file__).resolve().parents[1]


class SwingCoordinationTests(unittest.TestCase):
    def setUp(self):
        self.world = fixtures.CombatFlowTests(methodName='runTest')
        self.world.setUp()
        self.ns = self.world.ns
        self.calls = self.world.calls
        self.player = self.world.player
        self.player.Mount = False
        weapon = self.world.item()
        self.world.hands['RightHand'] = weapon
        self.ns.update(equippedweapon=weapon, weapon_set='axe', _pending_apple=None,
                       get_weaponabilitiesmanacost=lambda mana: mana,
                       weapons={'axe': Obj(weaponspecial_primary='Double Strike',
                                           weaponspecial_secondary='Whirlwind')})
        self.ns['sv'].update(disable_weaponspecials=0, use_weaponspecialprimary=1,
                             use_weaponspecialsecondary=1, use_pot_apple=0, use_removecurse=0)

    def oath(self, acknowledge=True):
        self.world.buffs.add('Bload Oath (curse)')
        def arm():
            self.calls.append('secondary')
            if acknowledge:
                self.player.HasSpecial = True
        def clear():
            self.calls.append('clear')
            self.player.HasSpecial = False
        self.player.WeaponSecondarySA = arm
        self.player.WeaponClearSA = clear
        return self.world.mob()

    def fight(self, target, count=3):
        self.ns['fighting'](target, [], [], [], count)

    def controller(self):
        if not (ROOT / 'Kirins/kirins_new_controller.py').is_file():
            self.skipTest('Optional Ki-Rin controller is not installed')
        ns = dict(Player=self.player, Timer=self.ns['Timer'], Misc=self.ns['Misc'],
                  time=Obj(time=lambda: self.world.now / 1000.0),
                  wait_active=False, combat_target_serial=0, combat_failures=0,
                  combat_last_hits=None, combat_last_progress_at=0,
                  mount_pet_serial=0, PET_LEASH_BLOCKED='pet_leash_blocked', COMBAT_SWITCH_ADVANTAGE=3,
                  COMBAT_ADJACENT_STALE_SECONDS=12, MOB_FAILURES_BEFORE_IGNORE=4)
        tree = ast.parse((ROOT / 'Kirins/kirins_new_controller.py').read_text())
        nodes = [n for n in tree.body if isinstance(n, ast.FunctionDef)
                 and n.name in ('combat_tick', 'set_attack')]
        exec(compile(ast.Module(body=nodes, type_ignores=[]), 'controller', 'exec'), ns)
        ns.update(set_state=lambda state: None, session_log=lambda *args: None,
                  world_event_active=lambda: False,
                  route_chunk=lambda x, y: self.calls.append(('route', x, y)) or (True, True))
        return ns

    def test_readied_whirlwind_survives_subsequent_ticks(self):
        target = self.oath()
        self.fight(target)
        for _ in range(6):
            self.world.tick(100)
            self.ns['publish_combat_activity']([(self.world.mob(n), 1) for n in (2, 3, 4)])
            self.ns['checkbloodoath']()
            self.ns['prearm_weaponspecial']()
            self.fight(target)
        self.assertEqual(self.calls.count('secondary'), 1)
        self.assertNotIn('clear', self.calls)
        self.assertTrue(self.player.WarMode)
        self.assertEqual(self.calls.count(('attack', target.Serial)), 1)

    def test_pending_server_ack_does_not_rearm_or_start_normal_attack(self):
        target = self.oath(acknowledge=False)
        self.fight(target)
        self.world.tick(100)
        self.fight(target)
        self.assertEqual(self.calls, ['secondary'])
        self.player.HasSpecial = True
        self.world.tick(100)
        self.fight(target)
        self.assertEqual(self.calls.count('secondary'), 1)
        self.assertIn(('attack', target.Serial), self.calls)

    def test_consumed_whirlwind_can_rearm_on_next_swing(self):
        target = self.oath()
        self.fight(target)
        self.player.HasSpecial = False
        self.world.tick(1250)
        self.fight(target)
        self.assertEqual(self.calls.count('secondary'), 2)
        self.assertNotIn('clear', self.calls)

    def test_unknown_readied_ability_is_replaced_once(self):
        target = self.oath()
        self.player.HasSpecial = True
        self.fight(target)
        self.world.tick(100)
        self.fight(target)
        self.assertEqual(self.calls.count('clear'), 1)
        self.assertEqual(self.calls.count('secondary'), 1)

    def test_oath_with_two_enemies_stops_attacks_and_clears_ability(self):
        target = self.oath()
        self.fight(target)
        self.calls.clear()
        self.world.tick(100)
        self.fight(target, count=2)
        self.assertFalse(self.player.WarMode)
        self.assertEqual(self.calls, ['clear'])
        self.assertIsNone(self.ns['_flow']['special_slot'])

    def test_all_paths_obey_ability_debounce_and_preserve_armed_special(self):
        self.assertTrue(self.ns['arm_weapon_special']('secondary'))
        self.world.tick(100)
        self.assertFalse(self.ns['arm_weapon_special']('secondary'))
        self.world.tick(800)
        self.player.HasSpecial = True
        self.assertFalse(self.ns['arm_weapon_special']('primary'))
        self.assertEqual(self.calls, ['secondary'])

    def test_repeated_attack_requests_are_throttled_but_target_changes_are_immediate(self):
        first, second = self.world.mob(2), self.world.mob(3)
        self.ns['engage_target'](first)
        for _ in range(4):
            self.world.tick(100)
            self.ns['engage_target'](first)
        self.assertEqual(self.calls, [('attack', 2)])
        self.ns['engage_target'](second)
        self.assertEqual(self.calls[-1], ('attack', 3))
        self.player.WarMode = False
        self.ns['engage_target'](second)
        self.assertEqual(self.calls.count(('attack', 3)), 2)

    def test_requested_spells_cast_in_melee_but_healing_still_defers(self):
        self.ns['_flow']['melee'] = True
        for spell in ('Enemy Of One', 'Consecrate Weapon', 'Divine Fury', 'Curse Weapon',
                      'Attune Weapon', 'Immolating Weapon', 'Counter Attack', 'Playing The Odds',
                      'Holy Light', 'Thunderstorm', 'Summon Fey'):
            with self.subTest(spell=spell):
                self.assertTrue(self.ns['cast_action'](lambda name: self.calls.append(name), spell))
                self.world.tick(250)
        for spell in ('Cleanse by fire', 'Close Wounds', 'Remove Curse'):
            with self.subTest(spell=spell):
                self.assertFalse(self.ns['cast_action'](lambda *args: self.fail(), spell))

    def test_defense_moves_and_opted_in_stamina_rescue_remain_available(self):
        self.ns['_flow']['melee'] = True
        self.assertTrue(self.ns['cast_action'](lambda spell: self.calls.append(spell), 'Confidence'))
        self.world.tick(250)
        self.ns['sv'].update(use_df_lowstam=1, df_stam_threshold=180)
        self.player.Stam = 179
        self.assertTrue(self.ns['cast_action'](lambda spell: self.calls.append(spell), 'Divine Fury'))
        self.assertEqual(self.calls, ['Confidence', 'Divine Fury'])

    def test_dress_yields_during_combat(self):
        self.ns['publish_combat_activity']([(self.world.mob(), 1)])
        self.ns['sv']['use_dresslist'] = 1
        self.ns['Dress'] = Obj(ChangeList=lambda *args: self.fail(), DressFStart=lambda: self.fail())
        self.ns['dresslist']()
        self.assertTrue(self.ns['Timer'].Check('attack_combat_busy'))
        self.assertIsNone(self.ns['_flow']['equipment'])

    def test_automatic_slayer_swaps_are_queued_with_adjacent_mob(self):
        for is_weapon in (True, False):
            with self.subTest(is_weapon=is_weapon):
                self.setUp()
                item = self.world.item(18)
                entry = {'serial': item.Serial, 'name': 'Slayer'}
                self.ns.update(_last_slayer_target_group=None,
                               _slayer_weapon_by_group={'undead': entry},
                               _slayer_talisman_by_group={'undead': entry},
                               load_slayer_sets=lambda: None,
                               slayer_group_for_mob=lambda mob: 'undead')
                self.ns['sv'].update(use_slayer_swap=int(is_weapon),
                                     use_slayer_talisman=int(not is_weapon))
                mob = self.world.mob(distance=1)
                self.ns['publish_combat_activity']([(mob, 1)])
                self.ns['slayer_swap_tick'](mob)
                job = self.ns['_flow']['equipment']
                self.assertEqual(job['serial'], item.Serial)
                self.assertEqual(job['is_weapon'], is_weapon)
                self.assertTrue(self.ns['Timer'].Check('slayerswap'))
                self.ns['advance_equipment']()
                self.world.tick(600)
                self.ns['advance_equipment']()
                self.assertIn(('equip', item.Serial), self.calls)

    def test_combat_busy_signal_expires_after_script_stops(self):
        self.ns['publish_combat_activity']([(self.world.mob(), 1)])
        self.assertTrue(self.ns['Timer'].Check('attack_combat_busy'))
        self.world.tick(1500)
        self.assertFalse(self.ns['Timer'].Check('attack_combat_busy'))

    def test_controller_can_follow_published_target_without_overriding_attack_selection(self):
        controller = self.controller()
        first, second = self.world.mob(2, 3), self.world.mob(3, 5)
        first.Position, second.Position = Obj(X=3, Y=0), Obj(X=5, Y=0)
        self.ns['publish_attack_target'](second)
        controller['combat_tick']([first, second], [], [])
        self.assertEqual(controller['combat_target_serial'], second.Serial)
        self.assertIn(('route', 5, 0), self.calls)
        chosen = self.ns['select_combat_target']([(first, 3), (second, 5)], set())
        self.assertIs(chosen, first)
        controller['set_attack'](False)
        self.world.tick(1)
        self.assertFalse(self.ns['Timer'].Check('attack_controller_target'))
        self.assertEqual(self.world.shared['attack_controller_target'], 0)

    def test_controller_request_never_bypasses_attack_filters(self):
        allowed = self.world.mob(2)
        self.world.shared['attack_controller_target'] = 3
        self.ns['Timer'].Create('attack_controller_target', 1000)
        self.assertIs(self.ns['select_combat_target']([(allowed, 1)], set()), allowed)

    def test_bandage_cursor_is_not_consumed_or_cancelled_as_honor(self):
        self.ns['start_cursor']('honor', self.world.mob(), lambda: None)
        self.world.cursor = True
        self.ns['Target'].HasTarget = lambda flag=None: True
        self.ns['service_cursor']()
        self.assertEqual(self.calls, [])
        self.assertIsNotNone(self.ns['_flow']['cursor'])
        self.assertTrue(self.world.cursor)
        self.world.tick(5000)
        self.ns['service_cursor']()
        self.assertIsNone(self.ns['_flow']['cursor'])
        self.assertTrue(self.world.cursor)

    def test_lore_reservation_blocks_automatic_cursors_and_spells(self):
        self.ns['Timer'].Create('attack_external_target_busy', 1000)
        self.assertFalse(self.ns['start_cursor']('honor', self.world.mob(), lambda: self.fail()))
        self.assertFalse(self.ns['cast_action'](lambda *args: self.fail(), 'Confidence'))

    @unittest.skipUnless((ROOT / 'Kirins/kirins_new_tracker.py').is_file() and
                         (ROOT.parent / 'UO Scripts/check_vampiricembrace.py').is_file(),
                         'Optional tracker and equipment helper are not installed')
    def test_tracker_and_dress_helper_obey_combat_signal(self):
        tracker = dict(Timer=self.ns['Timer'], Misc=self.ns['Misc'], Target=self.ns['Target'])
        fixtures.load_functions(ROOT / 'Kirins/kirins_new_tracker.py', tracker)
        self.ns['Timer'].Create('attack_combat_busy', 1000)
        self.assertFalse(tracker['tracking_actions_allowed']())
        self.assertIsNone(tracker['scan_tracking_gump']())
        self.assertFalse(tracker['cache_tracking_gumps']())
        self.world.tick(1000)
        self.assertTrue(tracker['tracking_actions_allowed']())
        helper = dict(Timer=self.ns['Timer'])
        fixtures.load_functions(ROOT.parent / 'UO Scripts/check_vampiricembrace.py', helper)
        self.ns['Timer'].Create('attack_inventory_busy', 1000)
        helper['GetLayerItem']()  # No Dress calls or slot reads while combat owns equipment.
        helper['check_bagsofsending']()
        helper['check_arrows']()

    def test_dead_cached_mob_does_not_enable_blood_oath_whirlwind(self):
        self.world.setup_loop([self.world.mob(2), self.world.mob(3), self.world.mob(4, hp=0)])
        self.world.buffs.add('Bload Oath (curse)')
        self.ns['sv'].update(disable_weaponspecials=0, use_weaponspecialprimary=1,
                             use_weaponspecialsecondary=1)
        self.ns['run_tick']()
        self.assertFalse(self.ns['_flow']['blood_oath_whirlwind'])

    def test_incoming_oath_stops_unverified_special_before_replacing_it(self):
        target = self.oath()
        self.player.HasSpecial = True
        self.ns['publish_combat_activity']([(self.world.mob(n), 1) for n in (2, 3, 4)])
        self.assertFalse(self.ns['_flow']['blood_oath_whirlwind'])
        self.ns['checkbloodoath']()
        self.assertFalse(self.player.WarMode)
        self.fight(target)
        self.assertTrue(self.player.WarMode)
        self.assertEqual(self.calls.count('clear'), 1)
        self.assertEqual(self.calls.count('secondary'), 1)

    def test_idle_combat_clears_busy_and_selected_target_with_valid_intervals(self):
        self.ns['publish_combat_activity']([(self.world.mob(), 1)])
        self.ns['publish_attack_target'](self.world.mob())
        self.ns['publish_combat_activity']([])
        self.assertEqual(self.world.shared['attack_selected_target'], 0)
        self.world.tick(1)
        self.assertFalse(self.ns['Timer'].Check('attack_combat_busy'))
        self.assertFalse(self.ns['Timer'].Check('attack_selected_target'))

    @unittest.skipUnless((ROOT / 'Kirins/kirins_new_tracker.py').is_file(),
                         'Optional Ki-Rin tracker is not installed')
    def test_animal_lore_releases_reservation_on_success_timeout_and_error(self):
        for outcome in ('success', 'timeout', 'error'):
            with self.subTest(outcome=outcome):
                self.world.tick(3000)
                tracker = dict(Timer=self.ns['Timer'], Misc=self.ns['Misc'],
                               Target=self.ns['Target'], Player=self.player,
                               rare_to_lore_serial=2, lored_rare_serials=set(),
                               ANIMAL_LORE_RANGE=8, ANIMAL_LORE_RETRY_MS=3000,
                               ANIMAL_LORE_TARGET_WAIT_MS=2000,
                               tracker_log=lambda *args: None,
                               Mobiles=Obj(FindBySerial=lambda serial: self.world.mob(serial),
                                           Message=lambda *args: None))
                fixtures.load_functions(ROOT / 'Kirins/kirins_new_tracker.py', tracker)
                def use_skill(name):
                    if outcome == 'error':
                        raise RuntimeError('Skill failed')
                self.player.UseSkill = use_skill
                self.ns['Target'].WaitForTarget = lambda *args: outcome != 'timeout'
                if outcome == 'error':
                    with self.assertRaisesRegex(RuntimeError, 'Skill failed'):
                        tracker['try_lore_rare']()
                else:
                    tracker['try_lore_rare']()
                self.assertEqual(self.world.shared['attack_cursor_owner'], '')
                self.world.tick(1)
                self.assertFalse(self.ns['Timer'].Check('attack_external_target_busy'))
                self.assertEqual(tracker['lored_rare_serials'],
                                 {2} if outcome == 'success' else set())

    def test_adjacent_enemy_replaces_distant_target_without_waiting_for_stall(self):
        for smart in (0, 1):
            with self.subTest(smart=smart):
                self.ns['sv']['use_smart_target'] = smart
                distant, adjacent = self.world.mob(2, 6), self.world.mob(3, 1)
                self.ns['select_combat_target']([(distant, 6)], set())
                self.world.tick(200)
                distant.Hits = 99  # Damage must not renew a lock over a melee enemy.
                distant.distance = 5
                chosen = self.ns['select_combat_target']([(distant, 5), (adjacent, 1)], set())
                self.assertIs(chosen, adjacent)
                self.ns['engage_target'](chosen)
                self.assertEqual(self.calls[-1], ('attack', adjacent.Serial))

    def test_distant_smart_priority_caster_cannot_displace_melee_enemy(self):
        self.ns['sv']['use_smart_target'] = 1
        adjacent, caster = self.world.mob(2, 1), self.world.mob(3, 4, body=10)
        self.assertIs(self.ns['select_combat_target']([(adjacent, 1), (caster, 4)], set()), adjacent)

    def test_distant_changeling_cannot_displace_melee_enemy(self):
        adjacent, changeling = self.world.mob(2, 1), self.world.mob(3, 4)
        self.assertIs(self.ns['select_combat_target']([(adjacent, 1), (changeling, 4)], {3}), adjacent)

    def test_distant_controller_target_yields_to_melee_and_controller_follows(self):
        adjacent, distant = self.world.mob(2, 1), self.world.mob(3, 6)
        adjacent.Position, distant.Position = Obj(X=1, Y=0), Obj(X=6, Y=0)
        self.world.shared['attack_controller_target'] = distant.Serial
        self.ns['Timer'].Create('attack_controller_target', 5000)
        chosen = self.ns['select_combat_target']([(adjacent, 1), (distant, 6)], set())
        self.assertIs(chosen, adjacent)
        self.ns['publish_attack_target'](chosen)
        controller = self.controller()
        controller['combat_tick']([distant, adjacent], [], [])
        self.assertEqual(controller['combat_target_serial'], adjacent.Serial)
        self.assertEqual(self.world.shared['attack_controller_target'], adjacent.Serial)

    def test_ranged_build_keeps_existing_target_with_adjacent_enemy(self):
        self.ns['_is_ranged_build'] = True
        distant, adjacent = self.world.mob(2, 6), self.world.mob(3, 1)
        self.ns['select_combat_target']([(distant, 6)], set())
        self.world.tick(200)
        self.assertIs(self.ns['select_combat_target']([(distant, 6), (adjacent, 1)], set()), distant)


if __name__ == '__main__':
    unittest.main()
