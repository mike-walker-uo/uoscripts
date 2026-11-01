import ast
from pathlib import Path
from types import SimpleNamespace as Obj
import unittest

ROOT = Path(__file__).resolve().parents[1]


def load_gump(name):
    folder = 'UltimateDexxerAttackScript' if name.startswith('AttackScript_') else 'UltimateMageAttackScript'
    tree = ast.parse((ROOT / folder / name).read_text(encoding='utf-8'))
    ns = {"PROFILE_PATH": "profile.json", "DRESS_NAME_ENTRY": 100, "DF_STAM_ENTRY": 101}
    funcs = [node for node in tree.body if isinstance(node, ast.FunctionDef)]
    exec(compile(ast.Module(body=funcs, type_ignores=[]), name, 'exec'), ns)
    for node in tree.body:
        if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name):
            if node.targets[0].id in ('sections',):
                exec(compile(ast.Module(body=[node], type_ignores=[]), name, 'exec'), ns)
    return ns


class TabTests(unittest.TestCase):
    def setUp(self):
        self.values = {}
        self.rendered = []
        self.buttons = []
        self.gd = Obj(gumpDefinition='', gumpStrings='', buttonid=0)
        self.misc = Obj(ReadSharedValue=lambda key: self.values.get(key, 0),
                        SetSharedValue=lambda key, val: self.values.update({key: val}))
        self.gumps = Obj(CreateGump=lambda **kw: self.gd, AddPage=lambda *a: None,
                         AddBackground=lambda *a: None, AddAlphaRegion=lambda *a: None,
                         AddLabel=lambda *a: None, AddImageTiled=lambda *a: None,
                         AddButton=lambda *a: self.buttons.append(a[5]),
                         SendGump=lambda *a: None, WaitForGump=lambda *a: None,
                         CloseGump=lambda *a: None, GetGumpData=lambda *a: self.gd)

    def test_mage_tabs_render_every_section_once_and_dispatch(self):
        ns = load_gump('MageAttackScript_MikeWalker_GUMP.py')
        ns.update(Misc=self.misc, Gumps=self.gumps, Player=Obj(Serial=1), setX=0, setY=0)
        ns['refresh_slayer_section'] = lambda: ns['sections'].update({'2: Slayer Books': {}})
        ns['buildSection'] = lambda gd, title, sy, *args: (self.rendered.append(title) if gd else None) or sy + 20
        expected = set(ns['sections']) | {'2: Slayer Books'}
        all_rendered = []
        for index, tab in enumerate(('main', 'heal', 'spells', 'summons', 'skills', 'slayer')):
            self.gd.buttonid = 900001 + index
            ns['buttoncheck'](1)
            self.assertEqual(self.values['mage_gump_tab'], tab)
            self.rendered.clear()
            ns['sendgump']()
            self.assertTrue(self.rendered)
            all_rendered.extend(self.rendered)
        self.assertEqual(set(all_rendered), expected)
        self.assertEqual(len(all_rendered), len(expected))

    def test_dexxer_tabs_render_all_settings_and_keep_slayer(self):
        ns = load_gump('AttackScript_MikeWalker_GUMP.py')
        ns.update(Misc=self.misc, Gumps=self.gumps, Player=Obj(Serial=1),
                  TAB_SETTINGS=900001, TAB_SLAYER=900002, _active_tab='settings',
                  calc_section_height=lambda *args: 20,
                  add_gump_shell=lambda *args: None,
                  buildSection=lambda gd, title, sy, *args: self.rendered.append(title) or sy + 20)
        all_rendered = []
        for button, name in ((900001, 'settings'), (900003, 'fight'),
                             (900004, 'magic'), (900005, 'pots')):
            self.gd.buttonid = button
            ns['buttoncheck'](1)
            self.assertEqual(ns['_active_tab'], name)
            self.rendered.clear()
            ns['build_settings_gump']()
            all_rendered.extend(self.rendered)
        self.assertEqual(set(all_rendered), set(ns['sections']))
        self.assertEqual(len(all_rendered), len(ns['sections']))
        self.gd.buttonid = 900002
        ns['buttoncheck'](1)
        self.assertEqual(ns['_active_tab'], 'slayer')


if __name__ == '__main__':
    unittest.main()
