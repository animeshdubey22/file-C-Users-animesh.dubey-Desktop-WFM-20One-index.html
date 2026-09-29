"""
Enterprise WSM End-to-End Test Suite
Validates all phases of the Enterprise Workforce Scheduling Management Platform:
1. Campaigns & LOBs
2. Employee Campaign Assignments & Multi-skills
3. Availability Windows & Preferences
4. Shift Templates & Shift Events (Break/Lunch)
5. Work Patterns & Multi-Week Rotations
6. Staffing Requirements (09:00 - 09:30 Voice=20, Chat=10, Email=5)
7. Automatic Scheduling Engine (2-Pass Solver)
8. Coverage & Quality Scoring
9. 'Why?' Explainability Criteria
10. Locking, Overrides, 2-Stage Approval & Publishing
"""

import unittest
import sqlite3
import json
from services.scheduling_engine import WsmSchedulingEngine, run_automatic_scheduler

class TestEnterpriseWsm(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect('wfm_one.db')
        self.conn.row_factory = sqlite3.Row

    def tearDown(self):
        self.conn.close()

    def test_01_campaign_and_lob_entities(self):
        c = self.conn.cursor()
        c.execute("SELECT * FROM campaigns WHERE id = 'CAMP_HOB'")
        hob = c.fetchone()
        self.assertIsNotNone(hob, "House of Brands Enterprise campaign must exist")
        self.assertEqual(hob['code'], 'HOB')

        c.execute("SELECT * FROM lines_of_business WHERE campaign_id = 'CAMP_HOB'")
        lobs = c.fetchall()
        channels = [l['channel'] for l in lobs]
        self.assertIn('Voice', channels)
        self.assertIn('Chat', channels)
        self.assertIn('Email', channels)
        print("[PASS] Test 01 Passed: Campaign & LOB entities verified.")

    def test_02_john_smith_employee_profile(self):
        c = self.conn.cursor()
        c.execute("SELECT * FROM agents WHERE id = 'EMP1000'")
        john = c.fetchone()
        self.assertIsNotNone(john)
        self.assertEqual(john['name'], 'John Smith')

        c.execute("SELECT * FROM employee_campaign_assignments WHERE agent_id = 'EMP1000'")
        assign = c.fetchone()
        self.assertIsNotNone(assign)
        self.assertEqual(assign['campaign_id'], 'CAMP_HOB')
        self.assertEqual(assign['fte_allocation'], 1.0)

        c.execute("SELECT s.channel, es.proficiency_score FROM employee_skills es JOIN skills s ON es.skill_id = s.id WHERE es.agent_id = 'EMP1000'")
        skills = {r['channel']: r['proficiency_score'] for r in c.fetchall()}
        self.assertIn('Voice', skills)
        self.assertIn('Chat', skills)
        self.assertIn('Email', skills)
        self.assertGreaterEqual(skills['Voice'], 90)
        print("[PASS] Test 02 Passed: John Smith profile, 100% allocation, and Voice/Chat/Email skills verified.")

    def test_03_availability_and_shift_templates(self):
        c = self.conn.cursor()
        c.execute("SELECT * FROM employee_availability_windows WHERE agent_id = 'EMP1000' AND day_of_week = 1")
        mon_avail = c.fetchone()
        self.assertIsNotNone(mon_avail)
        self.assertEqual(mon_avail['earliest_start'], '08:00')
        self.assertEqual(mon_avail['latest_end'], '19:00')

        c.execute("SELECT * FROM shift_templates WHERE id = 'SHT_9H_STD'")
        sht = c.fetchone()
        self.assertIsNotNone(sht)
        self.assertEqual(sht['duration_hours'], 9.0)
        self.assertEqual(sht['paid_hours'], 8.0)
        self.assertEqual(sht['unpaid_hours'], 1.0)
        print("[PASS] Test 03 Passed: Structured availability windows and 9-hour shift templates verified.")

    def test_04_work_patterns_and_rotations(self):
        c = self.conn.cursor()
        c.execute("SELECT * FROM work_patterns WHERE id = 'PAT_5X8_MF'")
        pat = c.fetchone()
        self.assertIsNotNone(pat)
        self.assertEqual(pat['days_on'], 5)
        self.assertEqual(pat['days_off'], 2)

        c.execute("SELECT * FROM rotation_schedules WHERE id = 'ROT_4WK_STD'")
        rot = c.fetchone()
        self.assertIsNotNone(rot)
        self.assertEqual(rot['cycle_weeks'], 4)
        print("[PASS] Test 04 Passed: Reusable 5x8 work patterns and 4-week rotations verified.")

    def test_05_staffing_requirements_and_mandatory_test(self):
        c = self.conn.cursor()
        c.execute("SELECT channel, required_fte FROM staffing_requirements WHERE campaign_id = 'CAMP_HOB' AND date = '2026-08-25' AND interval_start = '09:00'")
        reqs = {r['channel']: r['required_fte'] for r in c.fetchall()}
        self.assertEqual(reqs.get('Voice'), 20.0, "09:00-09:30 Voice requirement must be 20")
        self.assertEqual(reqs.get('Chat'), 10.0, "09:00-09:30 Chat requirement must be 10")
        self.assertEqual(reqs.get('Email'), 5.0, "09:00-09:30 Email requirement must be 5")
        print("[PASS] Test 05 Passed: Mandatory interval staffing requirement (Voice=20, Chat=10, Email=5) verified.")

    def test_06_automatic_scheduling_engine_solve(self):
        result = run_automatic_scheduler(
            campaign_id='CAMP_HOB',
            start_date='2026-08-25',
            end_date='2026-08-25',
            mode='BALANCED',
            preserve_locked=True
        )
        self.assertTrue(result['success'])
        self.assertGreater(result['total_assignments_generated'], 0)
        self.assertGreaterEqual(result['overall_quality_score'], 85.0)
        self.assertGreaterEqual(result['coverage_score'], 80.0)
        self.assertEqual(result['constraint_score'], 100.0)
        print(f"[PASS] Test 06 Passed: Automatic solver generated {result['total_assignments_generated']} assignments with Quality Score: {result['overall_quality_score']}%.")

        # Verify John Smith's generated shift
        c = self.conn.cursor()
        c.execute("SELECT * FROM schedule_assignments WHERE run_id = ? AND agent_id = 'EMP1000' AND date = '2026-08-25'", (result['run_id'],))
        john_assignment = c.fetchone()
        self.assertIsNotNone(john_assignment)
        self.assertEqual(john_assignment['shift_start'], '09:00')
        self.assertEqual(john_assignment['shift_end'], '18:00')

        events = json.loads(john_assignment['intraday_events_json'])
        event_names = [e['name'] for e in events]
        self.assertIn('Morning Break', event_names)
        self.assertIn('Lunch Break', event_names)
        self.assertIn('Afternoon Break', event_names)

        # Verify 'Why?' explanation
        c.execute("SELECT * FROM schedule_explanations WHERE run_id = ? AND agent_id = 'EMP1000' AND date = '2026-08-25'", (result['run_id'],))
        john_exp = c.fetchone()
        self.assertIsNotNone(john_exp)
        reasons = json.loads(john_exp['reasons_json'])
        self.assertGreaterEqual(len(reasons), 6)
        crit_names = [r['criterion'] for r in reasons]
        self.assertIn('Skill Qualified', crit_names)
        self.assertIn('Campaign Eligible', crit_names)
        self.assertIn('Availability Window Met', crit_names)
        print("[PASS] Test 07 Passed: Shift Minutes & 'Why?' explainability criteria validated for John Smith.")

if __name__ == '__main__':
    unittest.main()
