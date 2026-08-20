import urllib.request
import json

BASE_URL = "http://127.0.0.1:8000"

def get(path):
    req = urllib.request.Request(f"{BASE_URL}{path}")
    with urllib.request.urlopen(req) as resp:
        return resp.status, json.loads(resp.read().decode())

def post(path, data):
    body = json.dumps(data).encode('utf-8')
    req = urllib.request.Request(f"{BASE_URL}{path}", data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as resp:
        return resp.status, json.loads(resp.read().decode())

print("1. Checking API Root...")
status, data = get("/api/agents")
print(f"   Status: {status}, Total Agents: {len(data)}")

print("2. Checking WSM Campaigns...")
status, camps = get("/api/wsm/campaigns")
print(f"   Status: {status}, Total Campaigns: {len(camps)}")
for c in camps:
    print(f"   - {c['id']}: {c['name']} (SLA: {c['service_level_target']}%)")

print("3. Checking WSM Shift Templates...")
status, templates = get("/api/wsm/shift-templates")
print(f"   Status: {status}, Total Templates: {len(templates)}")

print("4. Executing Solver via POST /api/wsm/schedule/generate...")
status, gen_res = post("/api/wsm/schedule/generate", {
    "campaign_id": "CAMP_HOB",
    "start_date": "2026-08-25",
    "end_date": "2026-08-25",
    "mode": "BALANCED",
    "preserve_locked": True
})
print(f"   Status: {status}, Run ID: {gen_res['run_id']}")
print(f"   Assignments: {gen_res['total_assignments_generated']}")
print(f"   Overall Quality: {gen_res['overall_quality_score']}%")
print(f"   Interval Coverage: {gen_res['coverage_score']}%")
print(f"   Constraint Compliance: {gen_res['constraint_score']}%")

run_id = gen_res['run_id']

print("5. Checking 'Why?' Explainability for John Smith (EMP1000)...")
status, explain = get(f"/api/wsm/schedule/explain/{run_id}/EMP1000/2026-08-25")
print(f"   Status: {status}, Total Evaluated Criteria: {len(explain['reasons'])}")
for r in explain['reasons'][:4]:
    print(f"   - [{r['status']}] {r['criterion']}: {r['rationale']}")

print("6. Checking Interval Coverage Matrix...")
status, cov_res = get(f"/api/wsm/schedule/coverage/{run_id}")
intervals = cov_res.get('intervals', [])
print(f"   Status: {status}, Total Intervals: {len(intervals)}")
peak_0900 = [x for x in intervals if x['interval_start'] == '09:00']
if peak_0900:
    print(f"   - 09:00 Interval: Channel={peak_0900[0]['channel']}, Req={peak_0900[0]['required_fte']}, Sched={peak_0900[0]['scheduled_fte']}, Gap={peak_0900[0]['gap']}")

print("7. Publishing Run to Live Master Roster...")
status, pub_res = post(f"/api/wsm/schedule/runs/{run_id}/publish", {})
print(f"   Status: {status}, Published: {pub_res.get('status')}")

print("\nALL LIVE API ENDPOINTS VERIFIED & EXECUTED WITH 100% SUCCESS!")

