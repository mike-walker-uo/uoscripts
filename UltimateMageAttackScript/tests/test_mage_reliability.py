import ast
import json
import os
from pathlib import Path
import sys
import tempfile
import threading
import types
from types import SimpleNamespace as Obj
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'MageAttackScript_MikeWalker.py'
GUMP = ROOT / 'MageAttackScript_MikeWalker_GUMP.py'


def load_functions(source=SCRIPT):
    tree = ast.parse(source.read_text(encoding='utf-8'))
    ns = {}
    exec(compile(ast.Module(
        body=[node for node in tree.body if isinstance(node, ast.FunctionDef)],
        type_ignores=[]), str(source), 'exec'), ns)
    return ns


class FakeClock:
    def __init__(self):
        self.now = 0.0

    def time(self):
        return self.now


class MageReliabilityTests(unittest.TestCase):
    def setUp(self):
        self.ns = load_functions()
        self.clock = FakeClock()
        self.timers = {}
        self.calls = []
        self.cursor = False
        self.inventory_lock = threading.RLock()
        self.ns.update(
            time=self.clock,
            _mage_inventory_until=0.0,
            _artifact_scan_queue=[], _artifact_move_queue=[],
            _heirloom_candidate_queue=[], _heirloom_drop_queue=[],
            _heirloom_drop_state=None, _pending_mage_potion=None,
            _mirror_release_candidates=[], _last_mage_pet_target=0,
            _mage_combat=False,
            Monitor=Obj(Enter=lambda obj: self.inventory_lock.acquire(),
                        Exit=lambda obj: self.inventory_lock.release()),
            Timer=Obj(
                Timers=self.timers,
                Remaining=lambda name: int((self.timers.get(name, self.clock.now) - self.clock.now) * 1000),
                Create=lambda name, ms: self.timers.update(
                    {name: self.clock.now + ms / 1000.0}),
                Check=lambda name: self.timers.get(name, 0) > self.clock.now),
            Target=Obj(
                HasTarget=lambda: self.cursor,
                Cancel=self.cancel_cursor,
                TargetExecute=self.target_execute,
                TargetExecuteRelative=self.target_execute_relative),
            Misc=Obj(Pause=lambda ms: None, ReadSharedValue=lambda name: 0),
            Mobiles=Obj(FindBySerial=lambda serial: None),
            Player=Obj(Paralized=False, Poisoned=False, Hits=100, HitsMax=100),
            Spells=Obj(Interrupt=lambda: self.calls.append('interrupt')),
            sv={'use_messages': 0},
            serverdelay=150,
            cast_lock_deadline=None,
            nether_pending_deadline=None,
            nether_followup_pending=False,
            pending_target_cursor=None,
            pending_pet_gor_serial=0,
            pending_pet_gor_started=0.0,
            pending_cast_cooldown=None,
            busy_failure_count=0,
            busy_failure_since=None,
            last_cast_recovery=-100.0,
            last_cast_failure_check=0.0,
            last_cast_failure_signatures=set(),
            target_wait_extended_until=0.0,
            last_target_wait_failure=0.0,
            last_target_wait_failure_kind=None,
            last_offensive_target_state=None,
            los_rejected_positions={},
            _timer_create=lambda name, ms: self.timers.update(
                {name: self.clock.now + ms / 1000.0}),
            calc_castpause=lambda: 300,
            hostile_within_two=lambda: False)

    def cancel_cursor(self):
        self.calls.append('cancel')
        self.cursor = False

    def target_execute(self, *args):
        self.calls.append(('target', args))
        self.cursor = False

    def target_execute_relative(self, *args):
        self.calls.append(('relative', args))
        self.cursor = False

    def test_reactive_armor_retries_if_buff_never_appears(self):
        buffs = set()
        self.ns['sv']['use_reactivearmor'] = 1
        self.ns['Player'].Mana = 100
        self.ns['Player'].BuffsExist = lambda name: name in buffs
        self.ns['Spells'].CastMagery = lambda spell: self.calls.append(spell)
        self.ns['mana_cost'] = lambda cost: cost
        self.ns['calc_castspeed'] = lambda ms: ms

        self.ns['keep_reactive_armor']()
        self.clock.now = 2.0
        self.ns['keep_reactive_armor']()
        self.assertEqual(self.calls, ['Reactive Armor'])
        self.clock.now = 4.1
        self.ns['keep_reactive_armor']()
        self.assertEqual(self.calls, ['Reactive Armor', 'Reactive Armor'])
        buffs.add('Reactive Armor')
        self.clock.now = 9.0
        self.ns['keep_reactive_armor']()
        self.assertEqual(self.calls, ['Reactive Armor', 'Reactive Armor'])

    def test_artifact_moves_are_paced_and_skip_destination_contents(self):
        backpack = Obj(Serial=1, Container=0, Deleted=False)
        bag = Obj(Serial=2, Container=1, Deleted=False, Contains=[])
        nested = Obj(Serial=3, Container=1, Deleted=False, Name='bag', Contains=[])
        first = Obj(Serial=4, Container=3, Deleted=False, Name="Soul Seeker", Contains=[])
        second = Obj(Serial=5, Container=1, Deleted=False, Name="Aegis of Grace", Contains=[])
        already = Obj(Serial=6, Container=2, Deleted=False, Name="Soul Seeker", Contains=[])
        backpack.Contains = [bag, nested, second]
        nested.Contains = [first]
        bag.Contains = [already]
        objects = {i.Serial: i for i in (backpack, bag, nested, first, second, already)}
        self.ns['Player'].Backpack = backpack
        self.ns['Player'].HeadMessage = lambda *args: None
        self.ns['Items'] = Obj(FindBySerial=objects.get,
                               Move=lambda item, dest, amount: self.calls.append((item.Serial, dest)),
                               WaitForProps=lambda *args: None)
        self.ns.update(sv={'use_move_artis': 1, 'lootbag_serial': 2, 'use_messages': 0},
                       _artifact_name_cache={}, _artifact_scan_queue=[], _artifact_move_queue=[],
                       ARTIFACT_NAMES={'soul seeker', 'aegis of grace'})
        for _ in range(5):
            self.ns['move_artifacts_to_lootbag']()
        self.assertEqual(self.calls, [(4, 2)])
        self.clock.now = 0.61
        self.ns['move_artifacts_to_lootbag']()
        self.assertEqual(self.calls, [(4, 2), (5, 2)])
        self.assertNotIn(6, self.ns['_artifact_name_cache'])

    def test_artifact_scan_does_not_restart_while_queue_is_pending(self):
        bag = Obj(Serial=2, Container=1, Deleted=False)
        item = Obj(Serial=3, Container=1, Deleted=False, Name='ordinary')
        self.ns['Player'].Backpack = Obj(Serial=1)
        self.ns['Items'] = Obj(FindBySerial={2: bag, 3: item}.get)
        self.ns.update(sv={'use_move_artis': 1, 'lootbag_serial': 2, 'use_messages': 0},
                       _artifact_name_cache={}, _artifact_scan_queue=[3, 3], _artifact_move_queue=[],
                       ARTIFACT_NAMES=set(),
                       backpack_items_except=lambda *args: self.fail('scan restarted'))
        self.ns['move_artifacts_to_lootbag']()
        self.assertEqual(self.ns['_artifact_scan_queue'], [3])

    def test_artifact_gump_persists_bag_and_handles_cancellation(self):
        ns = load_functions(GUMP)
        values = {'use_move_artis': 0, 'lootbag_serial': 0}
        saves = []
        ns.update(Misc=Obj(ReadSharedValue=lambda key: values.get(key, 0),
                           SetSharedValue=lambda key, value: values.update({key: value})),
                  select_artifact_lootbag=lambda: 0,
                  mark_settings_changed=lambda: None,
                  save_settings=lambda: saves.append(dict(values)),
                  sections={'global': {'artifacts': {'sharedvalue': 'use_move_artis'}}})
        ns['toggle_artifact_lootbag']('use_move_artis')
        self.assertEqual(saves, [])
        ns['select_artifact_lootbag'] = lambda: 42
        ns['toggle_artifact_lootbag']('use_move_artis')
        self.assertEqual(saves[-1], {'use_move_artis': 1, 'lootbag_serial': 42})
        self.assertIn('lootbag_serial', ns['get_all_sv_keys']())
        ns['toggle_artifact_lootbag']('use_move_artis')
        self.assertEqual(saves[-1]['use_move_artis'], 0)

    def test_protection_penalty_is_applied_after_each_fc_cap(self):
        protected = [True]
        self.ns['Player'].BuffsExist = lambda buff: protected[0] and buff == 'Protection'
        self.ns['serverdelay'] = 150
        for gear_fc, expected_fc in ((0, -2), (2, 0), (4, 0), (6, 0)):
            self.ns['_cached_fc'] = gear_fc
            self.assertEqual(self.ns['calc_castspeed'](2000),
                             2000 - expected_fc * 250 + 400)
        for gear_fc, expected_fc in ((0, -2), (2, 0), (4, 2), (6, 2)):
            self.ns['_cached_fc'] = gear_fc
            self.assertEqual(self.ns['calc_castspeed_sw'](2000),
                             2000 - expected_fc * 250 + 400)
        protected[0] = False
        self.assertEqual(self.ns['calc_castspeed'](2000), 1900)
        self.assertEqual(self.ns['calc_castspeed_sw'](2000), 1400)

    def test_honor_selects_nearest_full_health_mob(self):
        damaged = Obj(Serial=1, Hits=50, HitsMax=100)
        full = Obj(Serial=2, Hits=100, HitsMax=100)
        further = Obj(Serial=3, Hits=100, HitsMax=100)
        self.ns['sv']['honordistance'] = 10
        self.assertIs(self.ns['honor_candidate']([(damaged, 1), (further, 5), (full, 3)]), full)
        self.ns['sv']['honordistance'] = 2
        self.assertIsNone(self.ns['honor_candidate']([(damaged, 1), (full, 3)]))

    def test_heal_potion_confirms_before_cooldown_and_retries(self):
        potion = Obj(Serial=9, Amount=2, Deleted=False)
        used = []
        self.ns.update(sv={'use_mage_heal_potion': 1, 'mage_heal_potion_pct': 20},
                       Items=Obj(FindByID=lambda *args: potion, FindBySerial=lambda n: potion,
                                 UseItem=lambda item: used.append(item.Serial)))
        self.ns['Player'].Hits = 10
        self.ns['Player'].HitsMax = 100
        self.ns['Player'].Backpack = Obj(Serial=1)
        self.assertTrue(self.ns['manage_mage_potions']())
        self.assertFalse(self.ns['Timer'].Check('mage_potion_cooldown'))
        self.clock.now = 3.1
        self.assertTrue(self.ns['manage_mage_potions']())
        potion.Amount = 1
        self.ns['manage_mage_potions']()
        self.assertTrue(self.ns['Timer'].Check('mage_potion_cooldown'))
        self.assertEqual(used, [9, 9])

    def test_pet_sync_tracks_only_confirmed_cursor_target(self):
        target = Obj(Serial=7, Deleted=False, Hits=100, HitsMax=100)
        self.ns.update(sv={'use_mage_pet_sync': 1, 'activeattack': 1, 'attackrange': 12},
                       Mobiles=Obj(FindBySerial=lambda serial: target),
                       external_target_reserved=lambda: False)
        self.ns['Player'].Followers = 1
        self.ns['Player'].BuffsExist = lambda name: False
        self.ns['Player'].DistanceTo = lambda mob: 3
        self.ns['Player'].ChatSay = lambda text: self.calls.append(text)
        self.assertTrue(self.ns['sync_mage_pets'](target))
        self.assertEqual(self.ns['_last_mage_pet_target'], 0)
        self.cursor = True
        self.assertTrue(self.ns['execute_pending_target']())
        self.assertEqual(self.ns['_last_mage_pet_target'], 7)
        self.assertFalse(self.ns['sync_mage_pets'](target))

    def test_heirloom_drop_checks_name_and_confirms_move(self):
        decoy = Obj(Serial=2, ItemID=0x2811, Hue=0, Name='ordinary chest', Container=99, Deleted=False)
        chest = Obj(Serial=3, ItemID=0x2811, Hue=0, Name='Chest of Heirlooms', Container=99, Deleted=False)
        self.ns.update(sv={'use_drop_heirlooms': 1, 'use_messages': 0},
                       HEIRLOOM_CHEST_ID=0x2811, HEIRLOOM_CHEST_HUE=0,
                       HEIRLOOM_CHEST_NAME='chest of heirlooms', HEIRLOOM_DROP_OFFSETS=((0, 0),),
                       _artifact_name_cache={},
                       Items=Obj(FindBySerial={2: decoy, 3: chest}.get,
                                 MoveOnGround=lambda item, *args: self.calls.append(item.Serial)),
                       backpack_items_except=lambda *args: [decoy, chest],
                       item_is_in_backpack=lambda item: item is not None and item.Container == 99)
        self.ns['Player'].Backpack = Obj(Serial=99)
        self.ns['Player'].Position = Obj(X=1, Y=2, Z=0)
        self.ns['Player'].HeadMessage = lambda *args: None
        self.assertFalse(self.ns['drop_heirloom_chests']())
        self.assertTrue(self.ns['drop_heirloom_chests']())
        self.assertEqual(self.calls, [3])
        chest.Container = 0
        self.clock.now = 0.61
        self.ns['drop_heirloom_chests']()
        self.assertIsNone(self.ns['_heirloom_drop_state'])

    def test_mirror_release_uses_release_context_only(self):
        mirror = Obj(Serial=2, Deleted=False, Name='Hero', MobileID=1)
        self.ns.update(sv={'use_mage_release_mirror': 1, 'attackrange': 12, 'use_messages': 0},
                       Player=Obj(Serial=1, Name='Hero', MobileID=1, Followers=4),
                       Mobiles=Obj(Filter=lambda: Obj(), ApplyFilter=lambda f: [mirror],
                                   FindBySerial=lambda serial: mirror),
                       Misc=Obj(WaitForContext=lambda serial, ms: [Obj(Entry='Release', Response=7)],
                                ContextReply=lambda serial, response: self.calls.append((serial, response))))
        self.ns['release_one_mirror_image'](False)
        self.assertEqual(self.calls, [])
        self.ns['release_one_mirror_image'](True)
        self.assertEqual(self.calls, [(2, 7)])

    def test_ignore_buttons_persist_and_toggle_specific_serial(self):
        ns = load_functions(GUMP)
        values = {'mage_ignored_serials': '[]'}
        saved = []
        ns.update(Misc=Obj(ReadSharedValue=lambda key: values.get(key),
                           SetSharedValue=lambda key, val: values.update({key: val})),
                  Mobiles=Obj(FindBySerial=lambda serial: Obj(Serial=serial, Name='mob')),
                  Player=Obj(Serial=1, HeadMessage=lambda *args: None),
                  prompt_target=lambda message: 42, json=json,
                  mark_settings_changed=lambda: None,
                  save_settings=lambda: saved.append(values['mage_ignored_serials']))
        ns['ignore_mage_target']()
        self.assertEqual(json.loads(saved[-1]), [42])
        ns['unignore_mage_target']()
        self.assertEqual(json.loads(saved[-1]), [])

    def test_watchdog_tracks_each_cast_lifecycle(self):
        recovered = []
        self.ns['recover_cast_state'] = recovered.append
        self.ns['Timer'].Check = lambda name: name == 'spells'

        for now in (0.0, 1.0, 2.0):
            self.clock.now = now
            self.ns['set_spell_timer'](1000)
            self.ns['cast_state_watchdog']()
        self.clock.now = 4.9
        self.ns['cast_state_watchdog']()
        self.assertEqual(recovered, [])

        self.clock.now = 5.01
        self.ns['cast_state_watchdog']()
        self.assertEqual(recovered, ['spell lock'])

    def test_spell_wait_uses_calculated_cast_time_and_bounded_lag(self):
        self.ns.update(calc_castspeed=lambda ms: ms - 300,
                       calc_castspeed_sw=lambda ms: ms - 600,
                       serverdelay=200)
        self.assertEqual(self.ns['spell_target_wait_ms'](2000), 2300)
        self.assertEqual(self.ns['spell_target_wait_ms'](2000, True), 2000)
        self.ns['target_wait_extended_until'] = 10.0
        self.assertEqual(self.ns['spell_target_wait_ms'](2000), 2550)

    def test_busy_failure_exits_wait_without_targeting(self):
        failures = iter(['busy'])
        self.ns.update(
            _razor_wait_for_target=lambda ms, noshow: False,
            consume_cast_failure=lambda: next(failures),
            apply_cast_failure=lambda failure: failure == 'busy')
        self.assertFalse(self.ns['wait_for_target_responsive'](2000, True))
        self.assertEqual([call for call in self.calls if isinstance(call, tuple)], [])
        self.assertEqual(self.ns['last_target_wait_failure_kind'], 'busy')

    def test_action_wait_is_ignored_until_cursor_arrives(self):
        failures = iter(['action_wait'])

        def wait(_ms, _noshow):
            if self.calls:
                self.cursor = True
                return True
            self.calls.append('waited')
            return False

        self.ns.update(_razor_wait_for_target=wait,
                       consume_cast_failure=lambda: next(failures),
                       apply_cast_failure=lambda failure: False)
        self.assertTrue(self.ns['wait_for_target_responsive'](2000, True))
        self.assertEqual(self.ns['last_target_wait_failure_kind'], None)

    def test_failed_wait_never_targets_but_late_owned_cursor_does(self):
        target = Obj(Serial=42)
        self.ns.update(
            spell_target_wait_ms=lambda *args: 1000,
            wait_for_target_responsive=lambda *args: False,
            last_target_wait_failure_kind='busy')
        self.assertFalse(self.ns['wait_for_spell_target'](0.0, 1000, 'mobile', target))
        self.assertIsNone(self.ns['pending_target_cursor'])
        self.assertFalse(any(isinstance(call, tuple) for call in self.calls))

        self.ns['last_target_wait_failure_kind'] = 'timeout'
        self.assertFalse(self.ns['wait_for_spell_target'](0.0, 1000, 'mobile', target))
        self.assertIsNotNone(self.ns['pending_target_cursor'])
        self.assertTrue(self.ns['resolve_orphan_target_cursor']())
        self.assertFalse(any(isinstance(call, tuple) for call in self.calls))

        self.clock.now = 0.5
        self.cursor = True
        self.assertTrue(self.ns['resolve_orphan_target_cursor']())
        self.assertIsNone(self.ns['pending_target_cursor'])
        self.assertIn(('target', (42,)), self.calls)

    def test_unconsumable_cursor_is_cancelled_at_owned_deadline(self):
        self.cursor = True
        self.ns['pending_target_cursor'] = {
            'kind': 'ground', 'target': (1, 2, 3), 'deadline': 1.0,
            'started': 0.0}
        self.ns['Target'].TargetExecute = lambda *args: self.calls.append(('stuck', args))

        self.assertTrue(self.ns['resolve_orphan_target_cursor']())
        self.assertIsNotNone(self.ns['pending_target_cursor'])
        self.clock.now = 1.0
        self.assertTrue(self.ns['resolve_orphan_target_cursor']())
        self.assertIsNone(self.ns['pending_target_cursor'])
        self.assertFalse(self.cursor)
        self.assertEqual(self.calls[-1], 'cancel')

    def test_hostile_cancellation_is_not_reported_as_success(self):
        self.cursor = True
        self.ns['pending_target_cursor'] = {
            'kind': 'hostile', 'target': 7, 'deadline': 1.0, 'started': 0.0}

        def reject(_preferred):
            self.cursor = False
            return None

        self.ns['target_current_visible_hostile'] = reject
        self.assertFalse(self.ns['execute_pending_target']())
        self.assertIsNotNone(self.ns['pending_target_cursor'])

    def test_late_colossus_cursor_runs_success_confirmation(self):
        self.cursor = True
        self.ns.update(
            pending_target_cursor={
                'kind': 'colossus', 'target': (10, 11, 0),
                'deadline': 1.0, 'started': 0.0},
            _colossus_tile_idx=3,
            guardme_pending=False)
        self.assertTrue(self.ns['resolve_orphan_target_cursor']())
        self.assertEqual(self.ns['_colossus_tile_idx'], 0)
        self.assertTrue(self.ns['guardme_pending'])
        self.assertAlmostEqual(self.timers['colossus_confirmation'], 2.0)
        self.assertAlmostEqual(self.timers['guardme_delay'], 2.0)

    def test_nether_pending_and_dead_target_are_bounded(self):
        self.ns['set_nether_pending_timer'](9000)
        self.assertAlmostEqual(self.timers['netherblast_pending'], 5.1)
        self.assertAlmostEqual(self.ns['nether_pending_deadline'], 5.1)

        self.ns['spell_target_wait_ms'] = lambda *args: 9000
        data, wait_ms = self.ns['_pending_target_data'](
            0.0, 2000, 'nether', (77, 4, 5, 6), max_pending_ms=5100)
        self.assertEqual(wait_ms, 5100)
        self.assertEqual(data['deadline'], 5.1)
        self.ns['place_nether_blast_target'](77, 4, 5, 6)
        self.assertIn(('target', (4, 5, 6)), self.calls)

    def summon_settings(self):
        return {
            'use_risingcolossus': 1,
            'use_summonelemental': 0, 'elemental_threshold': 0,
            'use_summon_daemon': 0, 'daemon_threshold': 0,
            'use_energy_vortex': 0, 'energy_vortex_threshold': 0,
            'use_blade_spirit': 0, 'blade_spirit_threshold': 0,
            'use_summon_creature': 0, 'creature_threshold': 0,
            'use_summonfey': 0, 'use_summonfiend': 0, 'fey_threshold': 0,
            'use_messages': 0,
        }

    def configure_summons(self, free_slots=3):
        self.ns.update(
            sv=self.summon_settings(),
            _COLOSSUS_SLOTS=3,
            _RC_OFFSETS=((1, 0),),
            _colossus_tile_idx=0,
            guardme_fey=0, guardme_fiend=0, guardme_pending=False,
            Player=Obj(
                Followers=5 - free_slots, FollowersMax=5, Mana=100,
                Paralized=False, Mount=None, Serial=1,
                Position=Obj(X=10, Y=20, Z=0),
                HeadMessage=lambda *args: None),
            skill_value=lambda name: 100,
            mana_cost=lambda base: base,
            has_arcane_empowerment=lambda: False,
            wait_for_spell_target=lambda *args: True,
            journal_entries_since=lambda start: [],
            did_fizzle=lambda start: False,
            Spells=Obj(CastMysticism=lambda name: self.calls.append(('cast', name))))

    def test_summon_requires_three_slots_and_safe_empowerment(self):
        self.configure_summons(free_slots=2)
        self.assertFalse(self.ns['summon_demand']())

        self.configure_summons(free_slots=3)
        self.ns['arcane_empowerment'] = lambda: self.calls.append('empower') or True
        self.assertTrue(self.ns['manage_summons'](False))
        self.assertEqual(self.calls, ['empower'])

        self.assertTrue(self.ns['manage_summons'](True))
        self.assertIn(('cast', 'Rising Colossus'), self.calls)

    def test_fey_fiend_and_colossus_issue_guard_after_summoning(self):
        for kind in ('fey', 'fiend', 'colossus'):
            with self.subTest(kind=kind):
                self.setUp()
                self.configure_summons(free_slots=3)
                self.ns['sv'].update(use_risingcolossus=int(kind == 'colossus'),
                                     use_summonfey=int(kind == 'fey'),
                                     use_summonfiend=int(kind == 'fiend'),
                                     fey_threshold=3, use_summon_counter=0,
                                     summon_require_empowerment=0)
                self.ns['calc_castspeed_sw'] = lambda ms: ms
                self.ns['Player'].ChatSay = lambda text: self.calls.append(('say', text))
                self.ns['Spells'].CastSpellweaving = lambda name: self.calls.append(('cast', name))
                self.assertTrue(self.ns['manage_summons'](True))
                self.assertTrue(self.ns['guardme_pending'])
                self.ns['say_guardme_if_pending']()
                self.assertNotIn(('say', 'all guard me'), self.calls)
                self.ns['Player'].Followers = 3
                self.clock.now = 10
                self.ns['say_guardme_if_pending']()
                self.assertEqual(self.calls.count(('say', 'all guard me')), 1)
                self.ns['say_guardme_if_pending']()
                self.assertEqual(self.calls.count(('say', 'all guard me')), 1)

    def test_summon_empowerment_requirement_can_be_disabled(self):
        self.configure_summons(free_slots=3)
        self.ns['sv']['summon_require_empowerment'] = 1
        self.ns['arcane_empowerment'] = lambda: False
        self.assertTrue(self.ns['manage_summons'](False))
        self.assertNotIn(('cast', 'Rising Colossus'), self.calls)
        self.ns['sv']['summon_require_empowerment'] = 0
        self.assertTrue(self.ns['manage_summons'](False))
        self.assertIn(('cast', 'Rising Colossus'), self.calls)

    def test_natures_fury_summon_checks_slots_mana_and_retry(self):
        self.configure_summons(free_slots=1)
        self.ns['sv'].update(use_risingcolossus=0, use_natures_fury=1,
                             summon_require_empowerment=0)
        self.ns['Spells'].CastSpellweaving = lambda name: self.calls.append(('cast', name))
        self.assertFalse(self.ns['summon_demand'](False))
        self.assertFalse(self.ns['manage_summons'](False))
        self.assertEqual(self.calls, [])
        self.ns['Player'].Mana = 23
        self.assertFalse(self.ns['manage_summons'](True))
        self.ns['Player'].Mana = 24
        self.assertTrue(self.ns['manage_summons'](True))
        self.assertEqual(self.calls, [('cast', 'Natures Fury')])
        self.clock.now = 1.0
        self.assertFalse(self.ns['summon_demand'](True))
        self.ns['Player'].Followers = self.ns['Player'].FollowersMax
        self.clock.now = 4.0
        self.assertFalse(self.ns['summon_demand'](True))
        self.ns['Player'].Followers -= 1
        self.assertTrue(self.ns['summon_demand'](True))
        self.assertFalse(self.ns['summon_demand'](False))
        self.ns['sv']['use_natures_fury'] = 0
        self.assertFalse(self.ns['summon_demand'](True))

    def test_mirror_image_checks_danger_slots_skill_mana_and_mount(self):
        self.configure_summons(free_slots=1)
        self.ns['sv'].update(use_risingcolossus=0, use_mirror_image=1,
                             summon_require_empowerment=0)
        skills = {'Ninjitsu': 20}
        self.ns['skill_value'] = lambda name: skills.get(name, 100)
        self.ns['calc_castspeed'] = lambda value: value
        self.ns['Spells'].CastNinjitsu = lambda name: self.calls.append(('cast', name))
        self.assertFalse(self.ns['manage_summons'](False))
        self.ns['Player'].Mount = Obj()
        self.assertFalse(self.ns['manage_summons'](True))
        self.ns['Player'].Mount = None
        skills['Ninjitsu'] = 19
        self.assertFalse(self.ns['manage_summons'](True))
        skills['Ninjitsu'] = 20
        self.ns['Player'].Mana = 9
        self.assertFalse(self.ns['manage_summons'](True))
        self.ns['Player'].Mana = 100
        self.ns['Player'].Followers = self.ns['Player'].FollowersMax
        self.assertFalse(self.ns['manage_summons'](True))
        self.ns['Player'].Followers -= 1
        self.assertTrue(self.ns['manage_summons'](True))
        self.assertEqual(self.calls, [('cast', 'Mirror Image')])
        self.clock.now = 2.0
        self.assertFalse(self.ns['manage_summons'](True))
        self.clock.now = 5.1
        self.assertTrue(self.ns['manage_summons'](True))
        self.assertEqual(self.calls.count(('cast', 'Mirror Image')), 2)

    def test_animate_dead_requires_corpse_and_tracks_target(self):
        self.configure_summons(free_slots=0)
        self.ns['sv'].update(use_risingcolossus=0, use_animate_dead=1,
                             summon_require_empowerment=0)
        self.ns.update(_animate_dead_corpses=[], _animate_dead_seen={})
        self.ns['Player'].DistanceTo = lambda serial: {101: 10, 102: 11}[serial]
        corpses = {}
        scans = []
        self.ns['Items'] = Obj(Filter=lambda: Obj(),
                               ApplyFilter=lambda fil: scans.append(fil) or list(corpses.values()),
                               FindBySerial=lambda serial: corpses.get(serial))
        self.ns['Spells'].CastNecro = lambda name: self.calls.append(('cast', name))
        def target_cast(start, delay, kind, target, *args):
            self.ns['pending_target_cursor'] = {'kind': kind, 'target': target}
            self.cursor = True
            return self.ns['execute_pending_target']()
        self.ns['wait_for_spell_target'] = target_cast
        self.assertFalse(self.ns['manage_summons'](True))
        self.assertEqual(scans[0].RangeMax, 10)
        self.assertEqual(scans[0].IsCorpse, 1)
        self.clock.now = 1.1
        corpses[102] = Obj(Serial=102, ItemID=0x2006, Deleted=False,
                           Visible=True, OnGround=True, IsCorpse=True)
        self.assertFalse(self.ns['manage_summons'](True))
        self.clock.now = 2.2
        corpses[101] = Obj(Serial=101, ItemID=0x2006, Deleted=False,
                           Visible=True, OnGround=True, IsCorpse=True)
        self.assertFalse(self.ns['manage_summons'](False))
        self.assertNotIn(('cast', 'Animate Dead'), self.calls)
        self.assertTrue(self.ns['manage_summons'](True))
        self.assertIn(('cast', 'Animate Dead'), self.calls)
        self.assertIn(('target', (101,)), self.calls)
        self.assertIn(101, self.ns['_animate_dead_seen'])
        self.clock.now = 13
        self.assertFalse(self.ns['manage_summons'](True))
        self.assertEqual(self.calls.count(('cast', 'Animate Dead')), 1)

    def test_animate_dead_late_cursor_revalidates_corpse(self):
        self.configure_summons()
        self.ns['sv']['use_animate_dead'] = 1
        corpse = Obj(Serial=101, ItemID=0x2006, Deleted=False,
                     Visible=True, OnGround=True, IsCorpse=True)
        self.ns.update(_animate_dead_seen={},
                       Items=Obj(FindBySerial=lambda serial: corpse),
                       pending_target_cursor={'kind': 'animate_dead', 'target': 101})
        self.ns['Player'].DistanceTo = lambda serial: 11
        self.cursor = True
        self.assertFalse(self.ns['execute_pending_target']())
        self.assertIn('cancel', self.calls)
        self.assertNotIn(101, self.ns['_animate_dead_seen'])
        self.calls.clear()
        self.ns['Player'].DistanceTo = lambda serial: 10
        self.ns['pending_target_cursor'] = {'kind': 'animate_dead', 'target': 101}
        self.cursor = True
        self.assertTrue(self.ns['execute_pending_target']())
        self.assertIn(('target', (101,)), self.calls)
        self.assertIn(101, self.ns['_animate_dead_seen'])

    def test_animate_dead_disabled_or_low_mana_does_not_scan(self):
        self.configure_summons(free_slots=0)
        self.ns['sv']['use_risingcolossus'] = 0
        self.ns['_animate_dead_corpses'] = []
        self.ns['_animate_dead_seen'] = {}
        self.ns['Items'] = Obj(Filter=lambda: self.fail('should not scan'))
        self.assertFalse(self.ns['manage_summons'](False))
        self.ns['sv']['use_animate_dead'] = 1
        self.ns['Player'].Mana = 22
        self.assertFalse(self.ns['manage_summons'](True))

    def test_animated_weapon_respects_slots_and_cast_confirmation(self):
        self.configure_summons(free_slots=2)
        self.ns['sv'].update(use_risingcolossus=0, use_animated_weapon=1)
        skills = {'Magery': 100, 'Mysticism': 100, 'Spellweaving': 100}
        self.ns['skill_value'] = lambda name: skills[name]
        self.assertTrue(self.ns['summon_demand']())
        skills['Spellweaving'] = 99
        self.assertFalse(self.ns['summon_demand']())
        self.ns['Player'].Followers = 1
        self.assertTrue(self.ns['summon_demand']())
        self.assertTrue(self.ns['manage_summons'](True))
        self.assertIn(('cast', 'Animated Weapon'), self.calls)
        self.clock.now = 1.0
        self.assertTrue(self.ns['manage_summons'](True))
        self.assertEqual(self.calls.count(('cast', 'Animated Weapon')), 1)
        skills['Mysticism'] = 32
        self.assertFalse(self.ns['summon_demand']())

    def test_colossus_journal_race_suppresses_duplicate_cast(self):
        self.configure_summons(free_slots=3)
        self.ns['journal_entries_since'] = lambda start: None
        self.assertTrue(self.ns['manage_summons'](True))
        self.assertEqual(self.calls.count(('cast', 'Rising Colossus')), 1)
        self.clock.now = 1.0
        self.assertTrue(self.ns['manage_summons'](True))
        self.assertEqual(self.calls.count(('cast', 'Rising Colossus')), 1)

    def test_low_hp_healing_falls_back_by_actual_eligibility(self):
        skills = {'Mysticism': 0, 'Magery': 100}
        self.ns.update(
            sv={'use_heal': 1, 'use_cleansingwinds': 1, 'use_messages': 0,
                'heal_threshold': 80},
            Player=Obj(Hits=40, HitsMax=100, Mana=100, Paralized=False,
                       Poisoned=False, Serial=1),
            skill_value=lambda name: skills[name],
            mana_cost=lambda base: base,
            wait_for_spell_target=lambda *args: True,
            did_fizzle=lambda start: False,
            Spells=Obj(
                CastMysticism=lambda name: self.calls.append(name),
                CastMagery=lambda name: self.calls.append(name)))
        self.assertTrue(self.ns['auto_heal']())
        self.assertEqual(self.calls, ['Greater Heal'])

        self.calls.clear()
        self.timers.clear()
        skills['Magery'] = 0
        self.assertFalse(self.ns['auto_heal']())
        self.assertEqual(self.calls, [])
        skills['Magery'] = 0.1
        self.assertTrue(self.ns['auto_heal']())
        self.assertEqual(self.calls, ['Heal'])

    def test_no_magery_uses_cleansing_winds_at_threshold(self):
        skills = {'Mysticism': 100, 'Magery': 0}
        self.ns.update(
            sv={'use_heal': 1, 'use_cure': 1, 'use_cleansingwinds': 1, 'use_messages': 0,
                'heal_threshold': 90},
            Player=Obj(Hits=80, HitsMax=100, Mana=100, Paralized=False,
                       Poisoned=False, Serial=1),
            skill_value=lambda name: skills[name], mana_cost=lambda base: base,
            wait_for_spell_target=lambda *args: True,
            did_fizzle=lambda start: False,
            Spells=Obj(CastMysticism=lambda name: self.calls.append(name),
                       CastMagery=lambda name: self.calls.append(name)))
        self.assertTrue(self.ns['auto_heal']())
        self.assertEqual(self.calls, ['Cleansing Winds'])
        self.calls.clear()
        self.timers.clear()
        self.ns['Player'].Poisoned = True
        self.assertTrue(self.ns['auto_cure']())
        self.assertEqual(self.calls, ['Cleansing Winds'])
        self.calls.clear()
        self.timers.clear()
        self.ns['sv']['use_cleansingwinds'] = 0
        self.assertFalse(self.ns['auto_cure']())
        self.assertEqual(self.calls, [])

    def test_spirit_speak_healing_is_optional_and_independent(self):
        self.ns.update(
            sv={'use_heal': 0, 'use_spirit_speak_heal': 1,
                'use_messages': 0, 'heal_threshold': 90},
            Player=Obj(Hits=80, HitsMax=100, Mana=0, Paralized=False,
                       Poisoned=False, UseSkill=lambda skill: self.calls.append(skill)))
        self.assertTrue(self.ns['auto_heal']())
        self.assertEqual(self.calls, ['Spirit Speak'])
        self.assertTrue(self.ns['auto_heal']())
        self.clock.now = 1.3
        self.assertFalse(self.ns['auto_heal']())
        self.clock.now = 5.1
        self.ns['Player'].Poisoned = True
        self.assertFalse(self.ns['auto_heal']())
        self.ns['Player'].Poisoned = False
        self.ns['Player'].Hits = 100
        self.assertFalse(self.ns['auto_heal']())
        self.ns['Player'].Hits = 80
        self.cursor = True
        self.assertFalse(self.ns['auto_heal']())
        self.cursor = False
        self.ns['sv']['use_spirit_speak_heal'] = 0
        self.assertFalse(self.ns['auto_heal']())
        self.assertEqual(self.calls, ['Spirit Speak'])

    def test_spirit_speak_completes_before_cleansing_winds_if_needed(self):
        self.ns.update(
            sv={'use_heal': 0, 'use_spirit_speak_heal': 1,
                'use_cleansingwinds': 1, 'use_messages': 0, 'heal_threshold': 90},
            Player=Obj(Hits=70, HitsMax=100, Mana=100, Paralized=False,
                       Poisoned=False, Serial=1,
                       UseSkill=lambda name: self.calls.append(name)),
            skill_value=lambda name: 100, mana_cost=lambda base: base,
            wait_for_spell_target=lambda *args: True, did_fizzle=lambda start: False,
            Spells=Obj(CastMysticism=lambda name: self.calls.append(name),
                       CastMagery=lambda name: self.calls.append(name)))
        self.assertTrue(self.ns['auto_heal']())
        self.clock.now = 1.0
        self.assertTrue(self.ns['auto_heal']())
        self.assertEqual(self.calls, ['Spirit Speak'])
        self.clock.now = 1.3
        self.assertTrue(self.ns['auto_heal']())
        self.assertEqual(self.calls, ['Spirit Speak', 'Cleansing Winds'])
        self.calls.clear()
        self.timers.clear()
        self.ns['Timer'].Create('spirit_speak_heal', 5000)
        self.ns['Player'].Mana = 10
        self.assertFalse(self.ns['auto_heal']())
        self.assertEqual(self.calls, [])

    def test_spirit_speak_healed_above_threshold_skips_cleansing_winds(self):
        self.ns.update(
            sv={'use_heal': 1, 'use_spirit_speak_heal': 1,
                'use_cleansingwinds': 1, 'use_messages': 0, 'heal_threshold': 90},
            Player=Obj(Hits=85, HitsMax=100, Mana=100, Paralized=False,
                       Poisoned=False, UseSkill=lambda name: self.calls.append(name)))
        self.assertTrue(self.ns['auto_heal']())
        self.ns['Player'].Hits = 95
        self.clock.now = 1.3
        self.assertFalse(self.ns['auto_heal']())
        self.assertEqual(self.calls, ['Spirit Speak'])

    def test_apple_consumption_is_confirmed_before_cooldown(self):
        apple = Obj(Serial=12, Amount=2, Deleted=False)
        self.ns.update(_pending_mage_apple=None,
                       sv={'use_enchanted_apple': 1, 'use_messages': 0},
                       Player=Obj(Backpack=Obj(Serial=1),
                                  BuffsExist=lambda name: name == 'Bload Oath (curse)'),
                       Items=Obj(FindByID=lambda *args: apple,
                                 FindBySerial=lambda serial: apple,
                                 UseItem=lambda item: self.calls.append(item.Serial)))
        self.assertTrue(self.ns['manage_enchanted_apple']())
        self.assertEqual(self.calls, [12])
        self.assertFalse(self.ns['manage_enchanted_apple']())
        self.assertNotIn('mage_apple_cooldown', self.timers)
        apple.Amount = 1
        self.assertFalse(self.ns['manage_enchanted_apple']())
        self.assertTrue(self.ns['Timer'].Check('mage_apple_cooldown'))

    def test_apple_rejection_retries_and_disabled_never_uses(self):
        apple = Obj(Serial=12, Amount=2, Deleted=False)
        self.ns.update(_pending_mage_apple=None,
                       sv={'use_enchanted_apple': 1, 'use_messages': 0},
                       Player=Obj(Backpack=Obj(Serial=1), BuffsExist=lambda name: True),
                       Items=Obj(FindByID=lambda *args: apple,
                                 FindBySerial=lambda serial: apple,
                                 UseItem=lambda item: self.calls.append(item.Serial)))
        self.assertTrue(self.ns['manage_enchanted_apple']())
        self.clock.now = 1.1
        self.assertFalse(self.ns['manage_enchanted_apple']())
        self.assertNotIn('mage_apple_cooldown', self.timers)
        self.clock.now = 3.1
        self.assertTrue(self.ns['manage_enchanted_apple']())
        self.ns['sv']['use_enchanted_apple'] = 0
        self.clock.now = 6.2
        self.assertFalse(self.ns['manage_enchanted_apple']())
        self.assertEqual(self.calls, [12, 12])

    def test_orange_petals_use_exact_hue_and_follow_buff(self):
        petal = Obj(Serial=21, Amount=2)
        active = {'value': False}
        def find_item(*args):
            self.calls.append(('find', args))
            return petal
        self.ns.update(sv={'use_orange_petals': 1, 'use_messages': 0},
                       Player=Obj(Backpack=Obj(Serial=1),
                                  BuffsExist=lambda name: active['value']),
                       Items=Obj(FindByID=find_item,
                                 UseItem=lambda item: self.calls.append(('use', item.Serial))))
        self.assertTrue(self.ns['manage_orange_petals']())
        self.assertEqual(self.calls[0][1][:2], (0x1021, 0x002B))
        self.assertFalse(self.ns['manage_orange_petals']())
        self.clock.now = 3.1
        active['value'] = True
        self.assertFalse(self.ns['manage_orange_petals']())
        active['value'] = False
        self.cursor = True
        self.assertFalse(self.ns['manage_orange_petals']())
        self.cursor = False
        self.assertTrue(self.ns['manage_orange_petals']())
        self.ns['sv']['use_orange_petals'] = 0
        self.clock.now = 7
        self.assertFalse(self.ns['manage_orange_petals']())

    def test_emergency_cure_priority_respects_skills(self):
        skills = {'Magery': 100, 'Mysticism': 100}
        self.ns.update(
            sv={'use_cure': 1, 'use_cleansingwinds': 1, 'use_messages': 0},
            Player=Obj(Hits=40, HitsMax=100, Mana=100, Paralized=False,
                       Poisoned=True, Serial=1),
            skill_value=lambda name: skills[name],
            mana_cost=lambda base: base,
            wait_for_spell_target=lambda *args: True,
            did_fizzle=lambda start: False,
            Spells=Obj(
                CastMysticism=lambda name: self.calls.append(name),
                CastMagery=lambda name: self.calls.append(name)))
        self.assertTrue(self.ns['auto_cure']())
        self.assertEqual(self.calls, ['Cure'])

        self.calls.clear()
        self.timers.clear()
        skills['Magery'] = 0
        self.assertTrue(self.ns['auto_cure']())
        self.assertEqual(self.calls, ['Cleansing Winds'])

    def test_cleansing_winds_blocked_in_all_care_paths(self):
        pet = Obj(Poisoned=True, Hits=20, HitsMax=100, Name='pet', Serial=3)
        self.ns.update(
            sv={'use_heal': 1, 'use_cure': 1, 'use_cleansingwinds': 1,
                'use_messages': 0, 'heal_threshold': 90,
                'use_auto_heal_pet': 1, 'use_auto_cure_pet': 1,
                'pet_heal_option': 3, 'pet_hp_threshold': 90},
            Player=Obj(Hits=40, HitsMax=100, Mana=100, Paralized=False,
                       Poisoned=False, Serial=1, Pets=[pet],
                       BuffsExist=lambda name: True),
            skill_value=lambda name: {'Mysticism': 100, 'Magery': 0}[name],
            mana_cost=lambda base: base,
            hostile_within_two=lambda: True,
            Spells=Obj(CastMysticism=lambda name: self.calls.append(name)))
        self.assertFalse(self.ns['auto_heal']())
        self.ns['Player'].Poisoned = True
        self.assertFalse(self.ns['auto_cure']())
        self.ns['Player'].Poisoned = False
        self.assertFalse(self.ns['cleansing_winds']())
        self.ns['heal_pets']()
        self.ns['cure_pets']()
        self.assertEqual(self.calls, [])

    def test_close_hostile_filter_uses_two_tiles(self):
        helper = load_functions()['hostile_within_two']
        class FakeList:
            def __getitem__(self, key):
                return list
        f = Obj()
        nearby = []
        helper.__globals__.update(Mobiles=Obj(Filter=lambda: f,
                                             ApplyFilter=lambda fil: nearby),
                                  List=FakeList(), Byte=int, sv={})
        self.assertFalse(helper())
        self.assertEqual(f.RangeMax, 2)
        self.assertFalse(f.CheckIgnoreObject)
        nearby.append(Obj())
        self.assertTrue(helper())

    def test_strangle_tracks_actual_mob_until_near_end(self):
        first, second = Obj(Serial=10), Obj(Serial=20)
        self.ns.update(
            sv={key: 0 for key in ('use_messages', 'use_command_undead',
                'use_conduit', 'use_evil_omen', 'use_curse', 'use_corpse_skin',
                'use_strangle', 'use_mind_rot', 'use_poison', 'use_paralyze',
                'use_sleep', 'use_mass_sleep', 'use_mana_vampire')},
            Player=Obj(Paralized=False, Poisoned=False, Mana=100),
            debuff_expiry={}, last_debuff_target=0, nuke_cascade_until=0,
            get_mob_tier=lambda mob: 'boss', low_mana=lambda: False,
            skill_value=lambda name: 100, mana_cost=lambda base: base,
            Mobiles=Obj(FindBySerial=lambda serial: first if serial == 10 else second),
            target_current_visible_hostile=lambda preferred: preferred,
            Spells=Obj(CastNecro=lambda name: self.calls.append(name)),
            did_fizzle=lambda start: False)
        self.ns['sv']['use_strangle'] = 1
        def target_cast(start, delay, kind, target, *args):
            self.ns['pending_target_cursor'] = {'kind': kind, 'target': target.Serial}
            self.cursor = True
            return self.ns['execute_pending_target']()
        self.ns['wait_for_spell_target'] = target_cast
        self.assertEqual(self.ns['strangle_duration_ms'](), 32000)
        self.assertTrue(self.ns['apply_debuffs'](first))
        self.clock.now = 1
        self.assertFalse(self.ns['apply_debuffs'](first))
        self.assertTrue(self.ns['apply_debuffs'](second))
        self.clock.now = 31
        self.assertFalse(self.ns['apply_debuffs'](first))
        self.clock.now = 32
        self.assertTrue(self.ns['apply_debuffs'](first))
        self.assertEqual(self.calls, ['Strangle', 'Strangle', 'Strangle'])

    def test_late_strangle_cursor_tracks_actual_target(self):
        self.ns.update(debuff_expiry={}, skill_value=lambda name: 100,
                       pending_target_cursor={'kind': 'strangle', 'target': 10},
                       Mobiles=Obj(FindBySerial=lambda serial: Obj(Serial=serial)),
                       target_current_visible_hostile=lambda preferred: Obj(Serial=20))
        self.cursor = True
        self.assertTrue(self.ns['execute_pending_target']())
        self.assertIn((20, 'debuff_strangle'), self.ns['debuff_expiry'])
        self.assertNotIn((10, 'debuff_strangle'), self.ns['debuff_expiry'])

    def test_book_scans_only_for_enabled_auto_swap(self):
        reads = {'slayer_swap_request': 123}
        scans = []
        equips = []
        self.ns.update(
            sv={'use_slayer_autoswap': 0, 'use_messages': 0},
            _slayer_books_dirty=True,
            _default_book=None,
            Player=Obj(Paralized=False),
            Misc=Obj(
                ReadSharedValue=lambda key: reads.get(key, 0),
                SetSharedValue=lambda key, value: reads.update({key: value})),
            refresh_slayer_books=lambda: scans.append(self.clock.now),
            _equip_book=equips.append,
            _target_slayer_group=lambda target: None)
        self.ns['process_slayer_swap'](None)
        self.assertEqual(equips, [123])
        self.assertEqual(scans, [])

        self.ns['sv']['use_slayer_autoswap'] = 1
        self.ns['process_slayer_swap'](Obj(Serial=1))
        self.ns['process_slayer_swap'](Obj(Serial=1))
        self.assertEqual(scans, [0.0])
        self.clock.now = 31.0
        self.ns['process_slayer_swap'](Obj(Serial=1))
        self.assertEqual(scans, [0.0, 31.0])

    def test_rare_spawn_alerts_report_combat_block(self):
        searches = []
        self.ns.update(
            sv={'use_checkforlegendaries': 1},
            Journal=Obj(Search=lambda text: searches.append(text) or
                        text == 'a curious creature apparates nearby'),
            Player=Obj(HeadMessage=lambda *args: None),
            longalarm=lambda: self.calls.append('alarm'))
        self.assertTrue(self.ns['legendarycheck']())
        self.assertEqual(self.calls, ['alarm'])
        self.assertIn('you sense a legendary', searches)


    def test_unaffordable_colossus_does_not_reserve_combat(self):
        self.configure_summons()
        self.ns['Player'].Mana = 10
        self.assertFalse(self.ns['manage_summons'](True))
        self.assertEqual(self.calls, [])
        self.ns['Player'].Mana = 50
        self.assertTrue(self.ns['manage_summons'](True))
        self.assertIn(('cast', 'Rising Colossus'), self.calls)

    def test_colossus_confirmation_still_prevents_duplicate_casts(self):
        self.configure_summons()
        self.ns['Timer'].Create('colossus_confirmation', 2000)
        self.ns['Player'].Mana = 10
        self.assertTrue(self.ns['manage_summons'](True))
        self.assertEqual(self.calls, [])

    def test_target_switch_keeps_curse_cooldown_and_expiry(self):
        self.ns.update(
            sv={key: 0 for key in (
                'use_messages', 'use_command_undead', 'use_conduit',
                'use_evil_omen', 'use_corpse_skin', 'use_strangle',
                'use_mind_rot', 'use_poison', 'use_paralyze', 'use_sleep',
                'use_mass_sleep', 'use_mana_vampire')},
            Player=Obj(Paralized=False, Poisoned=False, Mana=100),
            last_debuff_target=0, debuff_expiry={},
            DEBUFF_BADGES={'debuff_curse': 'CU'},
            get_mob_tier=lambda mob: 'boss', low_mana=lambda: False,
            skill_value=lambda name: 120, mana_cost=lambda base: base,
            Spells=Obj(CastMagery=lambda name: self.calls.append(name)),
            wait_for_spell_target=lambda *args: True,
            did_fizzle=lambda start: False)
        self.ns['sv']['use_curse'] = 1
        for serial in (1, 2, 1):
            for _ in range(2):
                self.ns['apply_debuffs'](Obj(Serial=serial))
                self.clock.now += 1
        self.assertEqual(self.calls, ['Curse', 'Curse'])
        self.assertTrue(self.ns['debuff_status_line']().startswith('CU:'))
        self.clock.now = 60
        self.assertTrue(self.ns['apply_debuffs'](Obj(Serial=1)))
        self.assertEqual(self.calls, ['Curse', 'Curse', 'Curse'])
        self.assertNotIn((2, 'debuff_curse'), self.ns['debuff_expiry'])

    def configure_combat(self, victims, start_name='all_victims'):
        tree = ast.parse(SCRIPT.read_text(encoding='utf-8'))
        main = next(node for node in tree.body if isinstance(node, ast.While))
        start = next(i for i, node in enumerate(main.body)
                     if isinstance(node, ast.Assign)
                     and any(isinstance(t, ast.Name) and t.id == start_name
                             for t in node.targets))
        tick = ast.For(target=ast.Name(id='_tick', ctx=ast.Store()),
                       iter=ast.Tuple(elts=[ast.Constant(value=0)], ctx=ast.Load()),
                       body=main.body[start:], orelse=[])
        self.combat_tick = compile(ast.fix_missing_locations(ast.Module(
            body=[tick], type_ignores=[])), str(SCRIPT), 'exec')
        self.victims = victims
        self.ns.update(
            nether_followup_pending=False,
            _pending_mage_apple=None,
            sv={'attackrange': 12, 'activeattack': 1,
                'attack_blue_changelings': 0, 'use_distancemarker': 0,
                'use_honor': 0, 'honordistance': 10, 'use_messages': 0,
                'use_nether_blast': 0, 'mass_threshold': 4, 'multi_threshold': 2},
            Player=Obj(Paralized=False, Poisoned=False, Hits=100, HitsMax=100,
                       DistanceTo=lambda mob: 4, BuffsExist=lambda name: True),
            Mobiles=Obj(FindBySerial=lambda serial: next(
                (m for m in self.victims if m.Serial == serial), None)),
            mobs_list=lambda rng: self.calls.append('scan') or self.victims,
            mobs_in_line_of_sight=lambda mobs, rng: list(mobs),
            manage_summons=lambda danger: False,
            refresh_gear_cache=lambda: None,
            nether_blast_ready_for=lambda *args: False,
            is_under_attack=lambda: False,
            _nb_marker_count=0,
            manage_reaper=lambda nearest: False,
            process_slayer_swap=lambda target: None,
            status_overlay=lambda target: None,
            apply_bard=lambda *args: False,
            apply_debuffs=lambda *args: False,
            cast_single_target=lambda target: self.calls.append(('attack', target.Serial)))
        for name in (
                'keep_magic_reflect', 'keep_reactive_armor', 'keep_protection',
                'keep_bless', 'attune_weapon', 'gift_of_life', 'gift_of_renewal',
                'keep_mana_shield', 'keep_mystic_weapon', 'arcane_empowerment',
                'keep_reaper_form', 'keep_wraith_form', 'keep_lich_form',
                'keep_vampiric_embrace', 'keep_stone_form', 'bard_resilience',
                'bard_perseverance', 'bard_inspire', 'bard_invigorate',
                'pet_gift_of_life', 'pet_gift_of_renewal', 'bless_pets'):
            self.ns[name] = lambda name=name: self.calls.append(name)

    def test_artifact_mover_runs_only_when_safe_and_without_cursor(self):
        self.configure_combat([Obj(Serial=1)])
        self.ns['move_artifacts_to_lootbag'] = lambda: self.calls.append('move')
        exec(self.combat_tick, self.ns)
        self.assertNotIn('move', self.calls)
        self.victims = []
        self.cursor = True
        exec(self.combat_tick, self.ns)
        self.assertNotIn('move', self.calls)
        self.cursor = False
        exec(self.combat_tick, self.ns)
        self.assertIn('move', self.calls)

    def test_honor_targets_full_health_candidate_in_combat(self):
        damaged = Obj(Serial=1, Hits=40, HitsMax=100)
        healthy = Obj(Serial=2, Hits=100, HitsMax=100)
        self.configure_combat([damaged, healthy])
        self.ns['sv']['use_honor'] = 1
        self.ns['Player'].DistanceTo = lambda mob: 2 if mob.Serial == 1 else 4
        self.ns['Player'].BuffsExist = lambda name: False
        self.ns['Player'].InvokeVirtue = lambda name: self.calls.append('honor')
        self.ns['wait_for_target_responsive'] = lambda *args: True
        self.ns['execute_target_confirmed'] = lambda serial: self.calls.append(('honor_target', serial)) or True
        exec(self.combat_tick, self.ns)
        self.assertIn(('honor_target', 2), self.calls)
        self.assertNotIn(('honor_target', 1), self.calls)

    def test_combat_defers_routine_buffs_and_scans_once(self):
        self.configure_combat([Obj(Serial=1)])
        exec(self.combat_tick, self.ns)
        self.assertEqual(self.calls, ['scan', ('attack', 1)])

    def test_urgent_defensive_buff_still_owns_combat_tick(self):
        self.configure_combat([Obj(Serial=1)])
        self.ns['is_under_attack'] = lambda: True

        def reflect():
            self.calls.append('reflect')
            self.ns['set_spell_timer'](1000)

        self.ns['keep_magic_reflect'] = reflect
        exec(self.combat_tick, self.ns)
        self.assertIn('reflect', self.calls)
        self.assertNotIn('arcane_empowerment', self.calls)
        self.assertNotIn(('attack', 1), self.calls)

    def test_low_health_skips_defensive_buffs_and_summons(self):
        self.configure_combat([Obj(Serial=1)])
        self.ns['Player'].Hits = 10
        self.ns['is_under_attack'] = lambda: True
        self.ns['manage_summons'] = lambda danger: self.calls.append('summon') or True
        self.ns['manage_reaper'] = lambda target: self.calls.append('reaper') or True
        exec(self.combat_tick, self.ns)
        self.assertNotIn('summon', self.calls)
        self.assertNotIn('reaper', self.calls)
        self.assertNotIn('keep_reactive_armor', self.calls)
        self.assertNotIn('keep_magic_reflect', self.calls)
        self.assertIn(('attack', 1), self.calls)

    def test_low_health_or_poison_skips_idle_buffs(self):
        self.configure_combat([])
        self.ns['Player'].Hits = 10
        exec(self.combat_tick, self.ns)
        self.assertNotIn('keep_reactive_armor', self.calls)
        self.assertNotIn('arcane_empowerment', self.calls)
        self.calls.clear()
        self.ns['Player'].Hits = 100
        self.ns['Player'].Poisoned = True
        exec(self.combat_tick, self.ns)
        self.assertNotIn('keep_reactive_armor', self.calls)
        self.assertNotIn('arcane_empowerment', self.calls)

    def test_honor_wait_restarts_before_attack_and_refreshes_next_tick(self):
        self.configure_combat([Obj(Serial=1, Hits=100, HitsMax=100)])
        self.ns['sv']['use_honor'] = 1
        self.ns['Player'].BuffsExist = lambda name: False
        self.ns['Player'].InvokeVirtue = lambda name: self.calls.append('honor')
        self.ns['wait_for_target_responsive'] = lambda *args: True
        self.ns['target_current_visible_hostile'] = lambda target: target
        exec(self.combat_tick, self.ns)
        self.assertEqual(self.calls, ['scan', 'honor'])
        self.victims = [Obj(Serial=2)]
        self.ns['sv']['use_honor'] = 0
        exec(self.combat_tick, self.ns)
        self.assertEqual(self.calls[-2:], ['scan', ('attack', 2)])

    def test_reaper_attempt_owns_tick_even_without_spell_timer(self):
        self.configure_combat([Obj(Serial=1)])
        self.ns['manage_reaper'] = lambda target: True
        exec(self.combat_tick, self.ns)
        self.assertEqual(self.calls, ['scan'])

    def test_spell_cursor_still_uses_fresh_visible_hostiles(self):
        old, current = Obj(Serial=1), Obj(Serial=2)
        self.cursor = True
        self.ns.update(
            sv={'attackrange': 12, 'attack_blue_changelings': 0},
            mobs_list=lambda rng: self.calls.append('fresh scan') or [current],
            mobs_in_line_of_sight=lambda mobs, rng: mobs,
            Player=Obj(DistanceTo=lambda mob: 4),
            remember_offensive_target=lambda target: None)
        self.assertIs(self.ns['target_current_visible_hostile'](old), current)
        self.assertIn('fresh scan', self.calls)
        self.assertIn(('target', (2,)), self.calls)

    def test_cure_attempt_still_blocks_offensive_casts(self):
        self.configure_combat([Obj(Serial=1)], start_name='care_attempted')
        self.ns.update(
            auto_heal=lambda: False,
            auto_cure=lambda: self.calls.append('cure') or True,
            rare_pet_alert_active=False)
        self.ns['Timer'].Create('maintenance', 10000)
        self.ns['Timer'].Create('legendarycheck', 10000)
        exec(self.combat_tick, self.ns)
        self.assertEqual(self.calls, ['cure'])

    def test_idle_still_refreshes_routine_buffs(self):
        self.configure_combat([])
        exec(self.combat_tick, self.ns)
        self.assertIn('arcane_empowerment', self.calls)
        self.assertIn('keep_bless', self.calls)
        self.assertEqual(self.calls.count('scan'), 1)

    def advance_clock(self, ms):
        self.clock.now += ms / 1000.0

    def test_closed_mobile_cursor_does_not_add_fixed_pause(self):
        self.cursor = True
        self.ns['Misc'].Pause = self.advance_clock
        self.assertTrue(self.ns['execute_target_confirmed'](Obj(Serial=7)))
        self.assertEqual(self.clock.now, 0)

    def test_mobile_cursor_retry_waits_only_while_cursor_is_open(self):
        self.cursor = True
        live = Obj(Serial=7)
        self.ns['Misc'].Pause = self.advance_clock
        self.ns['Mobiles'].FindBySerial = lambda serial: live

        def target(value):
            self.calls.append(value)
            if value is live:
                self.cursor = False

        self.ns['Target'].TargetExecute = target
        self.assertTrue(self.ns['execute_target_confirmed'](7))
        self.assertEqual(self.calls, [7, live])
        self.assertAlmostEqual(self.clock.now, 0.1)

    def test_owned_spell_targets_do_not_wait_after_cursor_closes(self):
        self.ns['Misc'].Pause = self.advance_clock
        for kind, target in (
                ('mobile', 7), ('nether', (7, 1, 2, 3)),
                ('ground', (1, 2, 3)), ('colossus', (1, 2, 3)),
                ('relative', (7, -2))):
            with self.subTest(kind=kind):
                self.cursor = True
                self.ns['pending_target_cursor'] = {'kind': kind, 'target': target}
                self.assertTrue(self.ns['execute_pending_target']())
                self.assertIsNone(self.ns['pending_target_cursor'])
                self.assertEqual(self.clock.now, 0)

    def test_nether_validation_overlaps_full_recovery_window(self):
        for recovery_ms, failure in ((250, None), (900, None),
                                     (250, 'busy'), (250, 'interrupted')):
            with self.subTest(recovery_ms=recovery_ms, failure=failure):
                self.clock.now = 10
                self.timers.clear()
                target = Obj(Serial=1, Hits=100, Position=Obj(X=3, Y=0, Z=0))
                self.configure_combat([target])
                self.ns['sv']['use_nether_blast'] = 1
                self.ns['Player'].Mana = 100
                self.ns['Player'].Position = Obj(X=0, Y=0, Z=0)
                self.ns.update(
                    real_skill_value=lambda name: 120,
                    mana_cost=lambda base: base,
                    calc_castpause=lambda: recovery_ms,
                    calc_castspeed=lambda ms: ms,
                    wait_for_target_responsive=lambda *args: True,
                    cast_failure_since=lambda start: (
                        failure if self.clock.now >= 10.2 else None))
                self.ns['Misc'].Pause = self.advance_clock

                def cast(name):
                    self.cursor = True

                self.ns['Spells'].CastMastery = cast
                exec(self.combat_tick, self.ns)
                if failure == 'busy':
                    self.assertAlmostEqual(self.timers['spells'], 10.5)
                    self.assertAlmostEqual(self.timers['netherblast'], 11.25)
                elif failure == 'interrupted':
                    self.assertAlmostEqual(self.timers['spells'], 10.251)
                    self.assertAlmostEqual(self.timers['netherblast'], 10.251)
                else:
                    self.assertAlmostEqual(self.timers['spells'], 10 + recovery_ms / 1000.0)
                    self.assertAlmostEqual(self.timers['netherblast'], 15.1)
                self.assertAlmostEqual(self.clock.now, 10.35)
                self.assertEqual(self.ns['nether_followup_pending'], failure is None)

    def test_recovery_preserves_server_minimum_and_fcr_delay(self):
        ns = load_functions()
        ns.update(_cached_castpause=0, serverdelay=150)
        self.assertEqual(ns['calc_castpause'](), 250)
        ns['_cached_castpause'] = 900
        self.assertEqual(ns['calc_castpause'](), 900)
        ns.update(_cached_castpause=100, serverdelay=350)
        self.assertEqual(ns['calc_castpause'](), 350)

    def test_instrument_search_only_runs_for_enabled_bard_skills(self):
        self.ns.update(
            sv={key: 0 for key in (
                'use_area_peace', 'use_discordance', 'use_peace',
                'use_provocation', 'use_tribulation', 'use_despair')},
            Player=Obj(Paralized=False, Poisoned=False),
            get_instrument=lambda: self.calls.append('instrument search'))
        self.assertFalse(self.ns['apply_bard'](Obj(Serial=1), [], []))
        self.assertEqual(self.calls, [])
        self.ns['sv']['use_discordance'] = 1
        self.assertFalse(self.ns['apply_bard'](Obj(Serial=1), [], []))
        self.assertEqual(self.calls, ['instrument search'])


    def configure_attack_spells(self):
        self.ns['sv'].update({key: 0 for key in (
            'use_messages', 'use_wordofdeath', 'use_explosion_combo',
            'use_death_ray', 'use_resist_aware', 'use_low_mana_mode',
            'use_flamestrike', 'use_energybolt', 'use_eaglestrike',
            'use_bombard', 'use_mindblast', 'use_lightning', 'use_fireball',
            'use_harm', 'use_nether_bolt', 'use_magicarrow')})
        self.ns['Player'].Poisoned = False
        self.ns['Player'].Mana = 100
        self.ns['Player'].ManaMax = 200
        self.ns['Player'].Position = Obj(X=0, Y=0, Z=0)
        self.ns['Player'].BuffsExist = lambda name: False
        self.ns['Player'].DistanceTo = lambda target: 3
        self.ns.update(
            skill_value=lambda name: 120,
            real_skill_value=lambda name: 120,
            mana_cost=lambda base: base,
            get_mob_real_hp=lambda target: (1000, 5000),
            get_mob_tier=lambda target: 'boss',
            get_weakres=lambda target: None,
            nuke_cascade_active=lambda: False,
            wait_for_spell_target=lambda *args, **kwargs: True,
            did_fizzle=lambda start: False,
            cast_failure_since=lambda start: None,
            Spells=Obj(
                CastMastery=lambda name: self.calls.append(('cast', name)),
                CastSpellweaving=lambda name: self.calls.append(('cast', name)),
                CastMagery=lambda name: self.calls.append(('cast', name)),
                CastMysticism=lambda name: self.calls.append(('cast', name))))

    def test_word_of_death_uses_hp_ratio_before_combo_or_death_ray(self):
        self.configure_attack_spells()
        self.ns['sv'].update(use_wordofdeath=1, use_explosion_combo=1, use_death_ray=1)
        self.ns['cast_explosion_combo'] = lambda target: self.calls.append('combo') or True
        waits = []
        self.ns['wait_for_spell_target'] = lambda *args: waits.append(args[1]) or True
        for hits, maximum in ((7, 25), (28, 100), (280, 1000)):
            with self.subTest(maximum=maximum):
                self.clock.now += 1
                self.calls.clear()
                attempted = self.ns['cast_single_target'](Obj(Hits=hits, HitsMax=maximum))
                self.assertEqual(self.calls, [('cast', 'Word of Death')])
                self.assertTrue(attempted)
        self.assertEqual(waits, [3500, 3500, 3500])

    def test_word_of_death_preserves_health_mana_skill_and_cast_guards(self):
        self.configure_attack_spells()
        self.ns['sv']['use_wordofdeath'] = 1
        target = Obj(Hits=20, HitsMax=100)
        for reason in ('mana', 'skill', 'healthy', 'dead', 'unknown bar',
                       'small mob', 'poisoned', 'paralyzed', 'casting', 'disabled', 'range'):
            with self.subTest(reason=reason):
                self.configure_attack_spells()
                self.ns['sv']['use_wordofdeath'] = 1
                self.ns['Player'].Paralized = False
                self.timers.clear()
                target.Hits, target.HitsMax = 20, 100
                if reason == 'mana':
                    self.ns['Player'].Mana = 49
                elif reason == 'skill':
                    self.ns['skill_value'] = lambda name: 82
                elif reason == 'healthy':
                    target.Hits = 30
                elif reason == 'dead':
                    target.Hits = 0
                elif reason == 'unknown bar':
                    target.HitsMax = 0
                elif reason == 'small mob':
                    self.ns['get_mob_real_hp'] = lambda target: (20, 500)
                elif reason == 'poisoned':
                    self.ns['Player'].Poisoned = True
                elif reason == 'paralyzed':
                    self.ns['Player'].Paralized = True
                elif reason == 'casting':
                    self.ns['set_spell_timer'](1000)
                elif reason == 'disabled':
                    self.ns['sv']['use_wordofdeath'] = 0
                elif reason == 'range':
                    self.ns['Player'].DistanceTo = lambda target: 11
                self.assertFalse(self.ns['cast_word_of_death'](target))
                self.assertEqual(self.calls, [])

    def test_word_of_death_preempts_ready_nether_blast_in_a_pack(self):
        target = Obj(Serial=1, Hits=7, HitsMax=25, Position=Obj(X=3, Y=0, Z=0))
        self.configure_combat([target, Obj(Serial=2)])
        self.configure_attack_spells()
        self.ns['sv'].update(use_wordofdeath=1, use_nether_blast=1)
        self.ns['nether_blast_ready_for'] = lambda *args: True
        self.ns['apply_bard'] = lambda *args: self.calls.append('bard') or True
        exec(self.combat_tick, self.ns)
        self.assertIn(('cast', 'Word of Death'), self.calls)
        self.assertNotIn(('cast', 'Nether Blast'), self.calls)
        self.assertNotIn('bard', self.calls)

    def test_nether_followup_gets_a_turn_before_another_blast_or_debuff(self):
        single_attack = self.ns['cast_single_target']
        target = Obj(Serial=1, Hits=80, HitsMax=100, Position=Obj(X=3, Y=0, Z=0))
        self.configure_combat([target])
        self.configure_attack_spells()
        self.ns['cast_single_target'] = single_attack
        self.ns['sv'].update(use_eaglestrike=1, use_nether_blast=1)
        self.ns['nether_followup_pending'] = True
        self.ns['nether_blast_ready_for'] = lambda *args: True
        self.ns['apply_bard'] = lambda *args: self.calls.append('bard') or True
        exec(self.combat_tick, self.ns)
        self.assertIn(('cast', 'Eagle Strike'), self.calls)
        self.assertNotIn(('cast', 'Nether Blast'), self.calls)
        self.assertNotIn('bard', self.calls)
        self.assertFalse(self.ns['nether_followup_pending'])
        self.clock.now += 1
        exec(self.combat_tick, self.ns)
        self.assertEqual(self.calls.count(('cast', 'Eagle Strike')), 1)
        self.assertEqual(self.calls.count(('cast', 'Nether Blast')), 1)
        self.assertTrue(self.ns['nether_followup_pending'])

    def test_no_eligible_single_followup_does_not_block_nether_blast(self):
        single_attack = self.ns['cast_single_target']
        target = Obj(Serial=1, Hits=80, HitsMax=100, Position=Obj(X=3, Y=0, Z=0))
        self.configure_combat([target])
        self.configure_attack_spells()
        self.ns['cast_single_target'] = single_attack
        self.ns['sv']['use_nether_blast'] = 1
        self.ns['nether_followup_pending'] = True
        self.ns['nether_blast_ready_for'] = lambda *args: True
        exec(self.combat_tick, self.ns)
        self.assertIn(('cast', 'Nether Blast'), self.calls)
        self.assertTrue(self.ns['nether_followup_pending'])

    def test_cure_preserves_pending_nether_followup(self):
        self.configure_combat([Obj(Serial=1)], start_name='care_attempted')
        self.ns.update(
            auto_heal=lambda: False,
            auto_cure=lambda: self.calls.append('cure') or True,
            rare_pet_alert_active=False,
            nether_followup_pending=True)
        self.ns['Timer'].Create('maintenance', 10000)
        self.ns['Timer'].Create('legendarycheck', 10000)
        exec(self.combat_tick, self.ns)
        self.assertEqual(self.calls, ['cure'])
        self.assertTrue(self.ns['nether_followup_pending'])

    def test_low_mana_still_allows_eagle_strike_followup(self):
        self.configure_attack_spells()
        self.ns['sv'].update(use_low_mana_mode=1, use_energybolt=1,
                             use_eaglestrike=1, use_bombard=1)
        self.ns['Player'].Mana = 24
        self.assertTrue(self.ns['cast_single_target'](Obj(Hits=80, HitsMax=100)))
        self.assertEqual(self.calls, [('cast', 'Eagle Strike')])


    def test_word_of_death_normalizes_large_health_bars(self):
        self.configure_attack_spells()
        self.ns['sv']['use_wordofdeath'] = 1
        self.ns['cast_single_target'](Obj(Hits=28, HitsMax=100))
        self.assertEqual(self.calls, [('cast', 'Word of Death')])

    def test_late_nether_cursor_also_reserves_single_target_followup(self):
        self.cursor = True
        self.ns['pending_target_cursor'] = {
            'kind': 'nether', 'target': (7, 1, 2, 3),
            'started': 0, 'deadline': 1}
        self.assertTrue(self.ns['resolve_orphan_target_cursor']())
        self.assertTrue(self.ns['nether_followup_pending'])
        self.assertIsNone(self.ns['pending_target_cursor'])

    def test_failed_single_target_followup_does_not_cast_blast_in_same_tick(self):
        single_attack = self.ns['cast_single_target']
        target = Obj(Serial=1, Hits=80, HitsMax=100, Position=Obj(X=3, Y=0, Z=0))
        self.configure_combat([target])
        self.configure_attack_spells()
        self.ns['cast_single_target'] = single_attack
        self.ns['sv'].update(use_eaglestrike=1, use_nether_blast=1)
        self.ns['nether_followup_pending'] = True
        self.ns['nether_blast_ready_for'] = lambda *args: True

        def timeout(*args):
            self.ns['set_spell_timer'](250)
            return False

        self.ns['wait_for_spell_target'] = timeout
        exec(self.combat_tick, self.ns)
        self.assertIn(('cast', 'Eagle Strike'), self.calls)
        self.assertNotIn(('cast', 'Nether Blast'), self.calls)


    def configure_pending_nether(self, cooldown_owner=True):
        self.ns['pending_target_cursor'] = {
            'kind': 'nether', 'target': (7, 1, 2, 3),
            'started': self.clock.now, 'deadline': self.clock.now + 5.1}
        self.ns['pending_cast_cooldown'] = 'netherblast' if cooldown_owner else None
        self.ns['Timer'].Create('netherblast', 5100)
        self.ns['set_nether_pending_timer'](5100)

    def test_late_nether_fizzle_releases_timeout_reservation_for_retry(self):
        self.configure_attack_spells()
        self.ns['sv']['use_nether_blast'] = 1
        self.configure_pending_nether(cooldown_owner=False)
        self.clock.now = 2.8
        self.ns['consume_cast_failure'] = lambda: 'interrupted'
        self.ns['release_failed_cast_from_journal']()
        self.assertIsNone(self.ns['pending_target_cursor'])
        self.clock.now += 0.01
        self.assertFalse(self.ns['resolve_orphan_target_cursor']())
        target = Obj(Position=Obj(X=3, Y=0, Z=0))
        self.assertTrue(self.ns['nether_blast_ready_for'](target, 1))

    def test_late_failure_after_nether_target_rolls_back_full_cooldown(self):
        self.ns['create_rollback_cooldown']('netherblast', 5100)
        self.ns['nether_followup_pending'] = True
        self.ns['set_spell_timer'](900)
        self.clock.now = 0.3
        self.ns['consume_cast_failure'] = lambda: 'interrupted'
        self.ns['release_failed_cast_from_journal']()
        self.clock.now += 0.01
        self.assertFalse(self.ns['Timer'].Check('netherblast'))
        self.assertFalse(self.ns['Timer'].Check('spells'))
        self.assertFalse(self.ns['nether_followup_pending'])
        self.assertIsNone(self.ns['pending_cast_cooldown'])

    def test_nether_failures_release_owned_cursor_with_reason_specific_backoff(self):
        for failure, retry_ms in (('interrupted', 1), ('invalid_target', 250),
                                  ('unseen_target', 250), ('busy', 1000),
                                  ('spell_cooldown', 1000)):
            with self.subTest(failure=failure):
                self.clock.now = 10
                self.configure_pending_nether()
                self.cursor = True
                self.ns['apply_cast_failure'](failure, True)
                self.assertIsNone(self.ns['pending_target_cursor'])
                self.assertIsNone(self.ns['pending_cast_cooldown'])
                self.assertFalse(self.cursor)
                self.assertAlmostEqual(self.timers['netherblast'], 10 + retry_ms / 1000.0)
                self.assertAlmostEqual(self.timers['netherblast_pending'], 10.001)

    def test_action_wait_does_not_release_nether_ownership_or_cooldown(self):
        self.configure_pending_nether()
        pending = self.ns['pending_target_cursor']
        self.ns['apply_cast_failure']('action_wait', True)
        self.assertIs(self.ns['pending_target_cursor'], pending)
        self.assertEqual(self.ns['pending_cast_cooldown'], 'netherblast')
        self.assertAlmostEqual(self.timers['netherblast'], 5.1)

    def test_nether_timeout_keeps_late_cursor_and_success_cooldown(self):
        self.configure_pending_nether()
        self.ns.update(
            spell_target_wait_ms=lambda *args: 200,
            consume_cast_failure=lambda: None)

        def wait(ms, noshow):
            self.clock.now += ms / 1000.0
            return False

        self.ns['_razor_wait_for_target'] = wait
        self.assertFalse(self.ns['wait_for_spell_target'](
            0, 2000, 'nether', (7, 1, 2, 3), max_pending_ms=5100))
        self.assertEqual(self.ns['last_target_wait_failure_kind'], 'timeout')
        self.assertIsNotNone(self.ns['pending_target_cursor'])
        self.clock.now = 0.5
        self.cursor = True
        self.assertTrue(self.ns['resolve_orphan_target_cursor']())
        self.assertTrue(self.ns['nether_followup_pending'])
        self.assertEqual(self.ns['pending_cast_cooldown'], 'netherblast')
        self.assertAlmostEqual(self.timers['netherblast'], 5.1)
        self.assertIn(('target', (1, 2, 3)), self.calls)

    def test_nether_expiry_blocked_and_dead_target_messages_are_classified(self):
        for message, expected in (
                ('You cannot use this ability until the last one has expired.', 'spell_cooldown'),
                ('That location is blocked.', 'invalid_target'),
                ('The path is blocked.', 'invalid_target'),
                ('Your target is dead.', 'invalid_target'),
                ('The target has died.', 'invalid_target'),
                ('You are already casting a spell.', 'busy'),
                ('Your concentration is disturbed, thus ruining thy spell.', 'interrupted'),
                ('You are frozen and cannot move.', None)):
            with self.subTest(message=message):
                self.assertEqual(self.ns['classify_cast_failure_entries'](
                    [Obj(Text=message)]), expected)

    def test_next_spell_failure_does_not_reset_successful_nether_cooldown(self):
        self.ns['create_rollback_cooldown']('netherblast', 5100)
        self.ns.update(
            spell_target_wait_ms=lambda *args: 1000,
            _razor_wait_for_target=lambda *args: False,
            consume_cast_failure=lambda: 'interrupted')
        self.assertFalse(self.ns['wait_for_spell_target'](0, 1250, 'self', 1))
        self.assertAlmostEqual(self.timers['netherblast'], 5.1)
        self.assertIsNone(self.ns['pending_cast_cooldown'])

    def test_late_nether_cursor_tracks_its_own_later_rejection(self):
        self.configure_pending_nether(cooldown_owner=False)
        self.cursor = True
        self.assertTrue(self.ns['resolve_orphan_target_cursor']())
        self.assertEqual(self.ns['pending_cast_cooldown'], 'netherblast')
        self.clock.now = 0.1
        self.ns['consume_cast_failure'] = lambda: 'invalid_target'
        self.ns['release_failed_cast_from_journal']()
        self.assertAlmostEqual(self.timers['netherblast'], 0.35)
        self.assertFalse(self.ns['nether_followup_pending'])


    def companion_helper(self):
        if not (ROOT.parent / 'UO Scripts/check_vampiricembrace.py').is_file():
            self.skipTest('Optional equipment helper is not installed')
        ns = load_functions(ROOT.parent / 'UO Scripts/check_vampiricembrace.py')
        ns.update(Timer=self.ns['Timer'], Monitor=self.ns['Monitor'],
                  Misc=self.ns['Misc'], Target=self.ns['Target'])
        return ns

    def test_mage_and_helper_claim_same_existing_inventory_signal(self):
        helper = self.companion_helper()
        self.assertTrue(self.ns['begin_mage_actions']())
        self.assertFalse(helper['begin_helper_action']())
        self.clock.now = 6.1  # Stopping mage cannot leave an indefinite lease.
        self.assertTrue(helper['begin_helper_action']())
        self.assertFalse(self.ns['begin_mage_actions']())
        self.clock.now += 0.8
        self.assertTrue(self.ns['begin_mage_actions']())

    def test_cast_recovery_keeps_inventory_busy_then_releases_it(self):
        helper = self.companion_helper()
        self.assertTrue(self.ns['begin_mage_actions']())
        self.ns['set_spell_timer'](300)
        self.ns['pause_mage_loop'](0)
        self.assertLessEqual(self.timers['attack_inventory_busy'], 0.301)
        self.clock.now = 0.29
        self.assertFalse(helper['begin_helper_action']())
        self.clock.now = 0.31
        self.assertTrue(helper['begin_helper_action']())

    def test_idle_mage_releases_inventory_without_erasing_other_script_lease(self):
        self.assertTrue(self.ns['begin_mage_actions']())
        self.ns['pause_mage_loop'](0)
        self.clock.now = 0.01
        helper = self.companion_helper()
        self.assertTrue(helper['begin_helper_action']())
        expiry = self.timers['attack_inventory_busy']
        self.ns['pause_mage_loop'](0)
        self.assertEqual(self.timers['attack_inventory_busy'], expiry)
        self.assertFalse(self.ns['begin_mage_actions']())

    def test_late_spell_cursor_keeps_inventory_protected_until_deadline(self):
        self.assertTrue(self.ns['begin_mage_actions']())
        self.ns['pending_target_cursor'] = {
            'kind': 'nether', 'target': (7, 1, 2, 3), 'deadline': 5.1}
        self.ns['set_spell_timer'](250)
        self.ns['pause_mage_loop'](0)
        self.clock.now = 4
        self.assertFalse(self.companion_helper()['begin_helper_action']())
        self.assertGreaterEqual(self.timers['attack_inventory_busy'], 5.1)

    def test_mage_respects_gump_and_external_cursor_reservations(self):
        for kind in ('gump', 'external'):
            with self.subTest(kind=kind):
                self.timers.clear()
                self.ns['Misc'].ReadSharedValue = lambda name: int(kind == 'gump')
                if kind == 'external':
                    self.ns['Timer'].Create('attack_external_target_busy', 1000)
                self.cursor = True
                self.assertFalse(self.ns['begin_mage_actions']())
                self.assertTrue(self.ns['resolve_orphan_target_cursor']())
                self.ns['pending_target_cursor'] = {
                    'kind': 'ground', 'target': (1, 2, 3), 'deadline': 1}
                self.assertFalse(self.ns['execute_pending_target']())
                self.assertTrue(self.cursor)
                self.assertEqual(self.calls, [])

    def test_combat_signal_is_published_and_expires_after_stop(self):
        self.ns['sv']['activeattack'] = 1
        self.ns['publish_mage_combat']([Obj(Serial=7)])
        self.assertTrue(self.ns['Timer'].Check('attack_combat_busy'))
        self.assertTrue(self.ns['begin_mage_actions']())
        self.assertGreaterEqual(self.timers['attack_combat_busy'], 6)
        self.clock.now = 6.1
        self.assertFalse(self.ns['Timer'].Check('attack_combat_busy'))
        self.ns['publish_mage_combat']([])
        self.clock.now += 0.01
        self.assertFalse(self.ns['Timer'].Check('attack_combat_busy'))

    def test_target_wait_renews_inventory_lease_during_long_cast(self):
        helper = self.companion_helper()
        self.assertTrue(self.ns['begin_mage_actions']())
        self.ns['consume_cast_failure'] = lambda: None

        def wait(ms, noshow):
            self.assertFalse(helper['helper_actions_allowed']())
            self.clock.now += ms / 1000.0
            self.cursor = self.clock.now >= 6.5
            return self.cursor

        self.ns['_razor_wait_for_target'] = wait
        self.assertTrue(self.ns['wait_for_target_responsive'](7000, True))
        self.assertGreater(self.timers['attack_inventory_busy'], self.clock.now + 5)

    def test_helper_item_and_equipment_work_yields_to_existing_signals(self):
        helper = self.companion_helper()
        for name in ('attack_combat_busy', 'attack_inventory_busy',
                     'attack_external_target_busy'):
            with self.subTest(name=name):
                self.timers.clear()
                self.ns['Timer'].Create(name, 1000)
                helper['check_bandages']()  # No item reads/uses without safe access.
                helper['GetLayerItem']()
                helper['check_arrows']()
                self.assertFalse(helper['begin_helper_action']())
        self.timers.clear()
        self.ns['Misc'].ReadSharedValue = lambda name: 1
        helper['check_bandages']()
        helper['GetLayerItem']()
        helper['check_arrows']()
        self.assertFalse(helper['begin_helper_action']())

    def test_bandage_belt_claim_prevents_mage_from_starting_during_item_use(self):
        helper = self.companion_helper()

        def use(item):
            self.assertTrue(self.ns['Timer'].Check('attack_inventory_busy'))
            self.assertFalse(self.ns['begin_mage_actions']())
            self.calls.append('belt')

        helper.update(
            Player=Obj(Backpack=Obj(Serial=1), HeadMessage=lambda *args: None),
            Items=Obj(ContainerCount=lambda *args: 0,
                      FindByName=lambda *args: Obj(Serial=2), UseItem=use))
        helper['check_bandages']()
        self.assertEqual(self.calls, ['belt'])

    def test_helper_dress_keeps_lease_until_agent_finishes(self):
        helper = self.companion_helper()
        running = [False]
        helper.update(
            layers=['Head'], changelist='test',
            Player=Obj(GetItemOnLayer=lambda layer: None),
            Dress=Obj(ChangeList=lambda name: None,
                      DressStatus=lambda: running[0],
                      DressFStart=lambda: running.__setitem__(0, True),
                      DressFStop=lambda: running.__setitem__(0, False)))

        def pause(ms):
            self.assertFalse(self.ns['begin_mage_actions']())
            self.clock.now += ms / 1000.0
            if self.clock.now >= 2:
                running[0] = False

        self.ns['Misc'].Pause = pause
        helper['GetLayerItem']()
        self.assertFalse(running[0])
        self.assertFalse(self.ns['begin_mage_actions']())
        self.clock.now += 0.8
        self.assertTrue(self.ns['begin_mage_actions']())

    def test_stopped_helper_dress_stops_agent_and_lease_expires(self):
        helper = self.companion_helper()
        running = [False]
        helper.update(
            layers=['Head'], changelist='test',
            Player=Obj(GetItemOnLayer=lambda layer: None),
            Dress=Obj(ChangeList=lambda name: None,
                      DressStatus=lambda: running[0],
                      DressFStart=lambda: running.__setitem__(0, True),
                      DressFStop=lambda: running.__setitem__(0, False)))

        def stop(ms):
            raise RuntimeError('helper stopped')

        self.ns['Misc'].Pause = stop
        with self.assertRaisesRegex(RuntimeError, 'helper stopped'):
            helper['GetLayerItem']()
        self.assertFalse(running[0])
        self.clock.now = 0.8
        self.assertTrue(self.ns['begin_mage_actions']())

    def test_simultaneous_mage_and_helper_claim_has_one_winner(self):
        helper = self.companion_helper()
        for _ in range(20):
            self.timers.clear()
            self.ns['_mage_inventory_until'] = 0
            ready = threading.Barrier(2)
            results = []

            def claim(action):
                ready.wait(timeout=2)
                results.append(action())

            workers = [threading.Thread(target=claim, args=(action,)) for action in
                       (self.ns['begin_mage_actions'], helper['begin_helper_action'])]
            for worker in workers:
                worker.start()
            for worker in workers:
                worker.join(timeout=2)
                self.assertFalse(worker.is_alive())
            self.assertEqual(sorted(results), [False, True])


    def test_urgent_mage_care_stops_long_helper_dress(self):
        helper = self.companion_helper()
        running = [False]
        helper.update(
            layers=['Head'], changelist='test',
            Player=Obj(GetItemOnLayer=lambda layer: None),
            Dress=Obj(ChangeList=lambda name: None,
                      DressStatus=lambda: running[0],
                      DressFStart=lambda: running.__setitem__(0, True),
                      DressFStop=lambda: running.__setitem__(0, False)))

        def poison_during_dress(ms):
            self.ns['Player'].Poisoned = True
            self.assertFalse(self.ns['begin_mage_actions']())
            self.clock.now += ms / 1000.0

        self.ns['Misc'].Pause = poison_during_dress
        helper['GetLayerItem']()
        self.assertFalse(running[0])
        self.assertAlmostEqual(self.clock.now, 0.1)
        self.clock.now += 0.8
        self.assertTrue(self.ns['begin_mage_actions']())



class AtomicProfileTests(unittest.TestCase):
    def assert_failed_write_retains_profile(self, source, ironpython=False):
        ns = load_functions(source)
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, 'profile.json')
            with open(path, 'w') as stream:
                stream.write('{"old": true}')

            real_os = os
            fake_os = Obj(
                path=real_os.path,
                fsync=real_os.fsync,
                remove=real_os.remove,
                rename=real_os.rename)
            modules = {}
            if ironpython:
                class File:
                    @staticmethod
                    def Replace(*_args):
                        raise OSError('replace failed')

                system = types.ModuleType('System')
                system_io = types.ModuleType('System.IO')
                system_io.File = File
                system.IO = system_io
                modules = {'System': system, 'System.IO': system_io}
            else:
                fake_os.replace = lambda *_args: (_ for _ in ()).throw(
                    OSError('replace failed'))

            previous = {name: sys.modules.get(name) for name in modules}
            sys.modules.update(modules)
            ns.update(os=fake_os, json=json)
            try:
                with self.assertRaises(OSError):
                    ns['atomic_write_json'](path, {'new': True})
            finally:
                for name, old in previous.items():
                    if old is None:
                        sys.modules.pop(name, None)
                    else:
                        sys.modules[name] = old

            with open(path) as stream:
                self.assertEqual(stream.read(), '{"old": true}')
            self.assertFalse(os.path.exists(path + '.tmp'))

    def test_gump_failed_replace_retains_old_profile(self):
        self.assert_failed_write_retains_profile(GUMP)

    def test_ironpython_fallback_failed_replace_retains_old_profile(self):
        self.assert_failed_write_retains_profile(SCRIPT, ironpython=True)


if __name__ == '__main__':
    unittest.main()
