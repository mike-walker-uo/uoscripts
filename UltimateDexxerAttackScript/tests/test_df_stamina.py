"""Exercise stamina Divine Fury settings and GUMP without Razor Enhanced."""
import ast
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace as Obj
import unittest

ROOT = Path(__file__).resolve().parents[1]


def load_script(filename, namespace):
    tree = ast.parse((ROOT / filename).read_text())
    functions = [n for n in tree.body if isinstance(n, ast.FunctionDef)]
    exec(compile(ast.Module(body=functions, type_ignores=[]), filename, 'exec'), namespace)
    for node in tree.body:
        if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name):
            name = node.targets[0].id
            if name in ('SETTINGS_KEYS', 'DF_STAM_ENTRY', 'DRESS_NAME_ENTRY',
                        'TAB_SETTINGS', 'TAB_SLAYER', 'sections', '_section_indices'):
                exec(compile(ast.Module(body=[node], type_ignores=[]), filename, 'exec'), namespace)
    return tree


class DivineFuryStaminaTests(unittest.TestCase):
    def setUp(self):
        self.settings = {'use_df_lowstam': 0, 'df_stam_threshold': 180, 'use_df': 0}
        self.casts = []
        self.timers = {}
        self.messages = []
        self.player = Obj(Stam=100, Mana=30, Paralized=False,
                          BuffsExist=lambda name: False,
                          GetSkillValue=lambda name: 120,
                          HeadMessage=lambda *args: self.messages.append(args))
        self.misc = Obj(ReadSharedValue=lambda key: self.settings.get(key, 0),
                        SetSharedValue=self.settings.__setitem__)
        self.attack = dict(Player=self.player, Misc=self.misc, sv={}, lmc=0,
                           Spells=Obj(CastChivalry=self.casts.append),
                           Timer=Obj(Check=lambda key: key in self.timers,
                                     Create=self.timers.__setitem__),
                           _cached_castpause=0)
        self.tree = load_script('AttackScript_MikeWalker.py', self.attack)
        self.attack['calc_castspeed_chiv_sw'] = lambda ms: ms
        self.gump = dict(Player=self.player, Misc=self.misc, json=json, os=os)
        load_script('AttackScript_MikeWalker_GUMP.py', self.gump)

    def test_default_and_disabled_check_never_cast(self):
        for node in self.tree.body:
            if (isinstance(node, ast.Expr) and isinstance(node.value, ast.Call)
                    and isinstance(node.value.func, ast.Attribute)
                    and node.value.func.attr == 'SetSharedValue'
                    and isinstance(node.value.args[0], ast.Constant)
                    and node.value.args[0].value in ('use_df_lowstam', 'df_stam_threshold')):
                exec(compile(ast.Module(body=[node], type_ignores=[]), 'defaults', 'exec'), self.attack)
        self.assertEqual(self.settings['use_df_lowstam'], 0)
        self.assertEqual(self.settings['df_stam_threshold'], 180)
        self.attack['refresh_sv']()
        self.attack['divinefury_lowstam']()
        self.assertEqual(self.casts, [])

    def test_enabled_uses_custom_threshold_and_cast_guards(self):
        self.settings.update(use_df_lowstam=1, df_stam_threshold=100)
        for stamina, buff, busy, mana, paralized, expected in (
                (100, False, False, 30, False, []),
                (101, False, False, 30, False, []),
                (99, True, False, 30, False, []),
                (99, False, True, 30, False, []),
                (99, False, False, 14, False, []),
                (99, False, False, 30, True, []),
                (99, False, False, 30, False, ['Divine Fury'])):
            with self.subTest(stamina=stamina, buff=buff, busy=busy, mana=mana, paralized=paralized):
                self.casts.clear()
                self.timers.clear()
                if busy:
                    self.timers['spells'] = 1000
                self.player.Stam, self.player.Mana, self.player.Paralized = stamina, mana, paralized
                self.player.BuffsExist = lambda name: buff
                self.attack['refresh_sv']()
                self.attack['divinefury_lowstam']()
                self.assertEqual(self.casts, expected)
                if expected:
                    self.assertEqual(self.timers['spells'], 1000)

    def test_invalid_threshold_preserves_previous_setting(self):
        self.gump['save_settings'] = lambda: self.fail('Invalid input must not save')
        for text in ('', 'abc', '1.5', '0', '-1'):
            with self.subTest(text=text):
                self.gump['Gumps'] = Obj(GetTextByID=lambda *args: text)
                self.gump['save_df_stam_threshold'](Obj())
                self.assertEqual(self.settings['df_stam_threshold'], 180)
        self.assertEqual(len(self.messages), 5)

    def test_gump_dispatch_layout_and_character_persistence(self):
        calls = []
        gd = Obj(buttonid=0)
        self.gump['Gumps'] = Obj(
            AddButton=lambda *args: calls.append(('button', args)),
            AddLabel=lambda *args: None, AddTooltip=lambda *args: None,
            AddTextEntry=lambda *args: calls.append(('entry', args)),
            GetTextByID=lambda *args: ' 125 ', WaitForGump=lambda *args: None,
            CloseGump=lambda *args: None, GetGumpData=lambda *args: gd)
        actions = self.gump['sections']['3: Attacks']
        section = self.gump['_section_indices']['3: Attacks']
        height = self.gump['buildSection'](Obj(), '3: Attacks', 0, actions, 0)
        self.assertEqual(height, self.gump['calc_section_height']('3: Attacks', actions))
        entries = [args for kind, args in calls if kind == 'entry']
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0][-2:], (self.gump['DF_STAM_ENTRY'], '180'))
        with TemporaryDirectory() as directory:
            settings_file = os.path.join(directory, 'character.json')
            self.gump.update(SETTINGS_FILE=settings_file, _active_tab='settings')
            for key in ('DF Stam Threshold', 'DF Low Stam'):
                gd.buttonid = section * 1000 + list(actions).index(key) + 1
                self.gump['buttoncheck'](1)
            self.assertEqual(self.settings['df_stam_threshold'], 125)
            self.assertEqual(self.settings['use_df_lowstam'], 1)
            self.assertEqual(self.settings['use_df'], 0)
            with open(settings_file) as f:
                saved = json.load(f)
            self.assertEqual(saved['df_stam_threshold'], 125)
            self.assertEqual(saved['use_df_lowstam'], 1)
            self.settings.update(df_stam_threshold=180, use_df_lowstam=0)
            self.attack.update(SETTINGS_FILE=settings_file, LEGACY_SETTINGS_FILE='',
                               json=json, os=os, ignored_mob_names=set(),
                               ignored_mob_serials=set(), ignored_summon_names=set())
            self.assertTrue(self.attack['load_settings']())
            self.assertEqual(self.settings['df_stam_threshold'], 125)
            self.assertEqual(self.settings['use_df_lowstam'], 1)
            self.gump['buttoncheck'](1)
            self.assertEqual(self.settings['use_df_lowstam'], 0)


if __name__ == '__main__':
    unittest.main()
