"""Exercise the real Blood Oath handler without starting Razor Enhanced."""
import ast
from pathlib import Path
from types import SimpleNamespace
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / 'AttackScript_MikeWalker.py'


class BloodOathTests(unittest.TestCase):
    def setUp(self):
        self.now = 0
        self.timers = {}
        self.oath = True
        self.apple = SimpleNamespace(Serial=123, Amount=5, Deleted=False)
        self.use_calls = 0
        self.curse_calls = 0
        self.messages = []
        self.consume = False
        self.clear_oath = False
        self.settings = {'use_pot_apple': 1, 'use_messages': 0,
                         'use_removecurse': 1}
        self.player = SimpleNamespace(
            BuffsExist=lambda name: self.oath if name == 'Bload Oath (curse)' else False,
            HeadMessage=lambda hue, message: self.messages.append(message),
            WarMode=False, Paralized=False, Serial=1)
        self.namespace = {
            'Player': self.player,
            'Timer': SimpleNamespace(
                Check=lambda name: self.timers.get(name, 0) > self.now,
                Create=lambda name, delay: self.timers.update({name: self.now + delay})),
            'Items': SimpleNamespace(UseItem=self.use_apple,
                                    FindBySerial=lambda serial: self.apple),
            'Misc': SimpleNamespace(Pause=self.pause),
            'Spells': SimpleNamespace(CastChivalry=self.remove_curse),
            'sv': self.settings,
            'find_enchanted_apple': lambda: self.apple,
            'calc_castspeed_chiv_sw': lambda value: value,
            '_cached_castpause': 0,
            '_pending_apple': None,
        }
        tree = ast.parse(SCRIPT.read_text(encoding='utf-8'))
        functions = [node for node in tree.body if isinstance(node, ast.FunctionDef)
                     and node.name in ('checkbloodoath', 'blood_oath_apple_warning')]
        exec(compile(ast.Module(body=functions, type_ignores=[]), str(SCRIPT), 'exec'),
             self.namespace)
        self.check = self.namespace['checkbloodoath']

    def pause(self, milliseconds):
        self.now += milliseconds

    def use_apple(self, apple):
        self.use_calls += 1
        if self.consume:
            apple.Amount -= 1
            if apple.Amount == 0:
                self.apple = None
        if self.clear_oath:
            self.oath = False

    def remove_curse(self, *args):
        self.curse_calls += 1

    def test_rejected_use_retries_after_short_delay(self):
        self.check()
        self.assertNotIn('pot_apple', self.timers)
        self.assertEqual(self.apple.Amount, 5)
        self.assertEqual(self.curse_calls, 1)
        self.check()
        self.assertEqual(self.use_calls, 1)
        self.pause(3000)
        self.check()
        self.assertEqual(self.use_calls, 2)

    def test_consumed_apple_starts_full_cooldown_even_if_cure_fails(self):
        self.consume = True
        self.check()
        self.assertEqual(self.apple.Amount, 4)
        self.check()
        self.assertEqual(self.timers['pot_apple'] - self.now, 60000)
        self.assertEqual(self.curse_calls, 1)
        self.pause(2000)
        self.check()
        self.assertEqual(self.use_calls, 1)

    def test_last_apple_consumed(self):
        self.apple.Amount = 1
        self.consume = True
        self.check()
        self.assertIsNone(self.apple)
        self.check()
        self.assertIn('pot_apple', self.timers)

    def test_successful_cure_does_not_cast_remove_curse(self):
        self.consume = self.clear_oath = True
        self.check()
        self.check()
        self.assertIn('pot_apple', self.timers)
        self.assertEqual(self.curse_calls, 0)

    def test_external_cure_without_consumption_does_not_start_cooldown(self):
        self.clear_oath = True
        self.check()
        self.assertNotIn('pot_apple', self.timers)
        self.assertEqual(self.curse_calls, 0)

    def test_moved_multi_item_stack_is_not_false_consumption(self):
        self.check()
        self.apple = None
        self.pause(1000)
        self.check()
        self.assertNotIn('pot_apple', self.timers)

    def test_no_apple_for_other_curses(self):
        self.oath = False
        self.check()
        self.assertEqual(self.use_calls, 0)
        self.assertEqual(self.curse_calls, 0)

    def test_disabled_apples_fall_back_to_remove_curse(self):
        self.settings['use_pot_apple'] = 0
        self.check()
        self.assertEqual(self.use_calls, 0)
        self.assertEqual(self.curse_calls, 1)

    def test_missing_apples_fall_back_to_remove_curse(self):
        self.apple = None
        self.check()
        self.assertEqual(self.use_calls, 0)
        self.assertEqual(self.curse_calls, 1)

    def test_full_cooldown_falls_back_to_remove_curse(self):
        self.timers['pot_apple'] = 60000
        self.check()
        self.assertEqual(self.use_calls, 0)
        self.assertEqual(self.curse_calls, 1)


if __name__ == '__main__':
    unittest.main()
