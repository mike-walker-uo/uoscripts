"""Keep ownership until automated cursors are consumed or safely abandoned."""
import unittest
import test_combat_flow as fixtures


class CursorLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.world = fixtures.CombatFlowTests(methodName='runTest')
        self.world.setUp()
        self.ns = self.world.ns
        self.target = self.world.mob()

    def honor(self):
        self.assertTrue(self.ns['start_cursor']('honor', self.target, lambda: None))

    def test_invalid_target_before_cursor_arrives_keeps_pending_request(self):
        for reason in ('damaged', 'deleted', 'out_of_range'):
            with self.subTest(reason=reason):
                self.setUp()
                self.honor()
                if reason == 'damaged':
                    self.target.Hits = 99
                elif reason == 'deleted':
                    self.target.Deleted = True
                else:
                    self.target.distance = 15
                self.world.tick(200)
                self.ns['service_cursor']()
                self.assertIsNotNone(self.ns['_flow']['cursor'])
                self.assertEqual(self.world.shared['attack_cursor_owner'], 'honor')
                self.world.cursor = True
                self.world.tick(200)
                self.ns['service_cursor']()
                self.assertEqual(self.world.calls, ['cancel'])
                self.assertIsNone(self.ns['_flow']['cursor'])

    def test_late_cursor_after_request_timeout_is_cancelled(self):
        self.honor()
        self.world.tick(1100)
        self.ns['service_cursor']()
        self.assertIsNotNone(self.ns['_flow']['cursor'])
        self.world.cursor = True
        self.world.tick(200)
        self.ns['service_cursor']()
        self.assertEqual(self.world.calls, ['cancel'])
        self.assertIsNone(self.ns['_flow']['cursor'])

    def test_no_response_releases_reservation_without_cancelling_future_manual_cursor(self):
        self.honor()
        self.world.tick(5000)
        self.ns['service_cursor']()
        self.assertIsNone(self.ns['_flow']['cursor'])
        self.assertEqual(self.world.shared['attack_cursor_owner'], '')
        self.world.cursor = True
        self.world.tick()
        self.ns['service_cursor']()
        self.assertTrue(self.world.cursor)
        self.assertEqual(self.world.calls, [])

    def test_rejected_target_execution_does_not_mark_pet_command_complete(self):
        self.assertTrue(self.ns['start_cursor']('pet', self.target, lambda: None))
        self.world.cursor = True
        self.ns['Target'].TargetExecute = lambda serial: self.world.calls.append(('attempt', serial))
        self.world.tick(200)
        self.ns['service_cursor']()
        self.assertIsNotNone(self.ns['_flow']['cursor'])
        self.assertEqual(self.ns['_last_pet_target_serial'], 0)
        self.world.tick(800)
        self.ns['service_cursor']()
        self.assertEqual(self.world.calls, [('attempt', self.target.Serial), 'cancel'])

    def test_retry_can_finish_pet_command_after_cursor_is_consumed(self):
        self.assertTrue(self.ns['start_cursor']('pet', self.target, lambda: None))
        self.world.cursor = True
        self.ns['Target'].TargetExecute = lambda serial: None
        self.world.tick(200)
        self.ns['service_cursor']()
        self.ns['Target'].TargetExecute = self.world.target
        self.world.tick(200)
        self.ns['service_cursor']()
        self.assertIsNone(self.ns['_flow']['cursor'])
        self.assertEqual(self.ns['_last_pet_target_serial'], self.target.Serial)

    def test_bandage_interruption_preserves_bandage_and_cancels_late_own_cursor(self):
        self.honor()
        beneficial = [True]
        self.world.cursor = True
        self.ns['Target'].HasTarget = lambda flag=None: self.world.cursor and (flag is None or beneficial[0])
        self.world.tick(200)
        self.ns['service_cursor']()
        self.assertTrue(self.world.cursor)
        self.assertEqual(self.world.calls, [])
        beneficial[0] = False  # Bandage completed; delayed Honor cursor arrives.
        self.world.tick(200)
        self.ns['service_cursor']()
        self.assertEqual(self.world.calls, ['cancel'])

    def test_beneficial_cursor_remains_open_when_ownership_deadline_expires(self):
        self.honor()
        self.world.cursor = True
        self.ns['Target'].HasTarget = lambda flag=None: self.world.cursor
        self.world.tick(5000)
        self.ns['service_cursor']()
        self.assertTrue(self.world.cursor)
        self.assertIsNone(self.ns['_flow']['cursor'])
        self.assertEqual(self.world.calls, [])

    def test_manual_gump_cursor_is_never_consumed_or_cancelled(self):
        self.honor()
        self.world.cursor = True
        self.world.shared['attack_gump_targeting'] = 1
        self.world.tick(5000)
        self.ns['service_cursor']()
        self.assertTrue(self.world.cursor)
        self.assertIsNone(self.ns['_flow']['cursor'])
        self.assertEqual(self.world.calls, [])

    def test_invalid_request_stays_cancelled_even_if_target_heals_again(self):
        self.honor()
        self.target.Hits = 99
        self.world.tick(200)
        self.ns['service_cursor']()
        self.target.Hits = 100
        self.world.cursor = True
        self.world.tick(200)
        self.ns['service_cursor']()
        self.assertEqual(self.world.calls, ['cancel'])

    def cursor_flag(self, flag):
        self.world.cursor = True
        self.ns['Target'].HasTarget = lambda requested=None: self.world.cursor and (requested is None or requested == flag)

    def test_watchdog_cancels_unowned_cursors_after_three_seconds(self):
        for flag in ('Beneficial', 'Harmful', 'Neutral'):
            with self.subTest(flag=flag):
                self.setUp()
                self.cursor_flag(flag)
                self.ns['clear_stuck_cursor']()
                self.world.tick(2999)
                self.ns['clear_stuck_cursor']()
                self.assertTrue(self.world.cursor)
                self.world.tick(1)
                self.ns['clear_stuck_cursor']()
                self.assertFalse(self.world.cursor)
                self.assertEqual(self.world.calls, ['cancel'])
                self.assertTrue(self.ns['_flow']['cursor_used'])

    def test_watchdog_resets_when_cursor_clears(self):
        self.cursor_flag('Beneficial')
        self.ns['clear_stuck_cursor']()
        self.world.tick(2000)
        self.world.cursor = False
        self.ns['clear_stuck_cursor']()
        self.world.tick(1000)
        self.world.cursor = True
        self.ns['clear_stuck_cursor']()
        self.world.tick(2999)
        self.ns['clear_stuck_cursor']()
        self.assertTrue(self.world.cursor)
        self.world.tick(1)
        self.ns['clear_stuck_cursor']()
        self.assertFalse(self.world.cursor)

    def test_watchdog_resets_when_cursor_type_changes(self):
        self.cursor_flag('Neutral')
        self.ns['clear_stuck_cursor']()
        self.world.tick(2500)
        self.cursor_flag('Beneficial')
        self.ns['clear_stuck_cursor']()
        self.world.tick(500)
        self.ns['clear_stuck_cursor']()
        self.assertTrue(self.world.cursor)
        self.world.tick(2500)
        self.ns['clear_stuck_cursor']()
        self.assertFalse(self.world.cursor)

    def test_watchdog_protects_manual_gump_prompts(self):
        self.cursor_flag('Neutral')
        self.ns['clear_stuck_cursor']()
        self.world.shared['attack_gump_targeting'] = 1
        self.world.tick(4000)
        self.ns['clear_stuck_cursor']()
        self.assertTrue(self.world.cursor)
        self.world.shared['attack_gump_targeting'] = 0
        self.ns['clear_stuck_cursor']()
        self.assertTrue(self.world.cursor)
        self.world.tick(3000)
        self.ns['clear_stuck_cursor']()
        self.assertFalse(self.world.cursor)

    def test_watchdog_respects_external_target_reservation(self):
        self.cursor_flag('Neutral')
        self.ns['Timer'].Create('attack_external_target_busy', 5000)
        self.ns['clear_stuck_cursor']()
        self.world.tick(4000)
        self.ns['clear_stuck_cursor']()
        self.assertTrue(self.world.cursor)
        self.world.tick(1000)
        self.ns['clear_stuck_cursor']()
        self.assertTrue(self.world.cursor)
        self.world.tick(3000)
        self.ns['clear_stuck_cursor']()
        self.assertFalse(self.world.cursor)

    def test_watchdog_does_not_run_with_attack_off(self):
        self.cursor_flag('Beneficial')
        self.ns['sv']['activeattack'] = 0
        self.ns['clear_stuck_cursor']()
        self.world.tick(4000)
        self.ns['clear_stuck_cursor']()
        self.assertTrue(self.world.cursor)
        self.assertEqual(self.world.calls, [])

    def test_watchdog_clears_pending_job_after_bandage_cursor_sticks(self):
        self.honor()
        self.cursor_flag('Beneficial')
        self.ns['clear_stuck_cursor']()
        self.ns['service_cursor']()
        self.world.tick(3000)
        self.ns['clear_stuck_cursor']()
        self.assertFalse(self.world.cursor)
        self.assertIsNone(self.ns['_flow']['cursor'])
        self.assertEqual(self.world.shared['attack_cursor_owner'], '')
        self.assertFalse(self.ns['start_cursor']('honor', self.target, lambda: self.fail()))


if __name__ == '__main__':
    unittest.main()
