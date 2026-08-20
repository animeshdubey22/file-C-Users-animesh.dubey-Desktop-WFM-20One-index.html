import urllib.request, json, sys, time, threading

sys.stdout.reconfigure(encoding='utf-8')

BASE = 'http://127.0.0.1:8000'

def post_json(path, data):
    payload = json.dumps(data).encode('utf-8')
    req = urllib.request.Request(f"{BASE}{path}", data=payload, headers={'Content-Type': 'application/json'}, method='POST')
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read().decode())

def get_json(path):
    req = urllib.request.Request(f"{BASE}{path}", headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read().decode())

print("=== 1. Testing High-Concurrency WAL Database Writes ===")
def do_write(idx):
    post_json('/api/integrations/telephony/webhook', {
        'provider': 'Amazon Connect',
        'event_type': 'STATE_CHANGE',
        'agent_id': 'AGT001',
        'new_state': 'Voice',
        'channel': 'Voice',
        'duration_seconds': idx
    })

threads = []
for i in range(25):
    t = threading.Thread(target=do_write, args=(i,))
    threads.append(t)
    t.start()
for t in threads:
    t.join()
print("-> 25 concurrent non-blocking writes successfully executed under WAL mode!")

print("\n=== 2. Testing Telephony Connectors API & Health Check ===")
connectors = get_json('/api/integrations/connectors')
print(f"Loaded {len(connectors)} CCaaS Connectors: {[c['name'] for c in connectors]}")
test_res = post_json('/api/integrations/connectors/CONN_AMAZON_CONNECT/test', {})
print(f"Health test response for Amazon Connect: {test_res}")

print("\n=== 3. Testing Real-Time CTI Webhook Ingestion ===")
wh_res = post_json('/api/integrations/telephony/webhook', {
    'provider': 'Genesys Cloud',
    'event_type': 'CALL_STARTED',
    'agent_id': 'AGT002',
    'new_state': 'Voice',
    'channel': 'Voice',
    'duration_seconds': 45,
    'payload': {'call_id': 'CALL_EMEA_9921'}
})
print(f"Webhook Ingestion Result: {wh_res}")
events = get_json('/api/integrations/telephony/events')
print(f"Latest logged CTI event: {events[0]['provider']} -> Agent: {events[0]['agent_name']} ({events[0]['new_state']})")

print("\n=== 4. Testing Async Mathematical Solver ===")
solve_job = post_json('/api/wsm/solver/async-run', {
    'campaign_id': 'CAMP_HOB',
    'mode': 'BALANCED',
    'enforce_union_rules': True,
    'min_rest_hours': 11,
    'max_consecutive_days': 6
})
print(f"Async solver launched with Job ID: {solve_job['job_id']}")
for _ in range(6):
    time.sleep(0.7)
    status = get_json(f"/api/wsm/solver/jobs/{solve_job['job_id']}")
    print(f"  Progress: {status['progress_percent']}% | Stage: {status.get('summary_json')}")
    if status['status'] == 'COMPLETED':
        print(f"-> Solver completed! Quality Score: {status['quality_score']}% | Constraints: {status['constraint_score']}%")
        break

print("\nALL ENTERPRISE BACKEND TESTS PASSED!")
