"""Weapon swap gaps must not activate unarmed or stale weapon abilities."""
import ast
from pathlib import Path
from types import SimpleNamespace as Obj
import unittest

SOURCE = Path(__file__).resolve().parents[1] / 'AttackScript_MikeWalker.py'


class WeaponSwapTests(unittest.TestCase):
    def setUp(self):
        self.calls = []
        self.sword = Obj(Serial=17, ItemID=0xF61)
        self.bow = Obj(Serial=18, ItemID=0x27A5)
        self.current = self.sword
        self.player = Obj(
            GetItemOnLayer=lambda layer: self.current if layer == 'FirstValid' else None,
            HasSpecial=False, Mana=100, Paralized=False,
            BuffsExist=lambda name: False, SpellIsEnabled=lambda name: False,
            HeadMessage=lambda *args: self.calls.append(('message', args)),
            WeaponPrimarySA=lambda: self.calls.append('primary'),
            WeaponSecondarySA=lambda: self.calls.append('secondary'),
            WeaponClearSA=lambda: self.calls.append('clear'),
            Attack=lambda *args: self.calls.append('attack'),
            LowerManaCost=40, SumAttribute=lambda name: 100,
            FasterCasting=2, FasterCastRecovery=6)
        self.ns = dict(
            Player=self.player, Timer=Obj(Check=lambda name: False,
                                         Create=lambda *args: self.calls.append(('timer', args))),
            equippedweapon=self.sword, weapon_set='sword',
            _weapon_key_by_item_id={self.sword.ItemID: 'sword', self.bow.ItemID: 'bow'},
            weapons={'default': Obj(ItemID=None),
                     'sword': Obj(singleenemyspecial='primary'),
                     'bow': Obj(singleenemyspecial='secondary')},
            serverdelay=100, sv={'activeattack': 1, 'disable_weaponspecials': 0,
                                'use_weaponspecialprimary': 1, 'use_weaponspecialsecondary': 1},
            WEAPON_SPECIAL_ARM_DEBOUNCE_MS=250)
        tree = ast.parse(SOURCE.read_text())
        exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n, ast.FunctionDef)],
                                type_ignores=[]), str(SOURCE), 'exec'), self.ns)
        self.ns.update(selected_ninjitsu_attack=lambda: None,
                       backstab_loop_enabled=lambda: False,
                       get_weaponabilitiesmanacost=lambda mana: mana)

    def test_empty_check_preserves_profile_without_warning(self):
        self.current = None
        self.ns['checkweapon']()
        self.assertEqual(self.ns['weapon_set'], 'sword')
        self.assertIsNone(self.ns['equippedweapon'])
        self.assertIsNone(self.ns['weapons']['default'].ItemID)
        self.assertEqual(self.calls, [])

    def test_unarmed_gap_blocks_all_weapon_special_paths(self):
        self.current = None
        for name, args in (('prearm_weaponspecial', ()),
                           ('fighting', (None, [], [], [], 0)),
                           ('arm_shadow_strike', ()),
                           ('arm_filler_special', ([],))):
            with self.subTest(name=name):
                self.ns[name](*args)
                self.assertEqual(self.calls, [])
        self.player.HasSpecial = True
        self.ns['prearm_weaponspecial']()
        self.assertEqual(self.calls, ['clear'])

    def test_swap_refreshes_new_slot_before_periodic_check(self):
        self.current = self.bow
        self.ns['prearm_weaponspecial']()
        self.assertEqual(self.ns['weapon_set'], 'bow')
        self.assertIs(self.ns['equippedweapon'], self.bow)
        self.assertEqual(self.calls[0], 'secondary')
        self.assertNotIn('primary', self.calls)

    def test_recovery_after_empty_check_uses_new_weapon(self):
        self.current = None
        self.ns['checkweapon']()
        self.ns['prearm_weaponspecial']()
        self.current = self.bow
        self.ns['prearm_weaponspecial']()
        self.assertEqual(self.calls[0], 'secondary')
        self.assertEqual(self.ns['weapon_set'], 'bow')

    def test_equipped_unknown_weapon_still_uses_default(self):
        self.current = Obj(Serial=19, ItemID=0x9999)
        self.ns['checkweapon']()
        self.assertEqual(self.ns['weapon_set'], 'default')
        self.assertEqual(self.ns['weapons']['default'].ItemID, 0x9999)
        self.assertTrue(self.ns['weapon_ready']())


if __name__ == '__main__':
    unittest.main()
