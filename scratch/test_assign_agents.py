import urllib.request, json

# Test adding agent EMP1000 to CAMP_CCG
payload = json.dumps({'agent_ids': ['EMP1000', 'EMP1001', 'EMP1002']}).encode('utf-8')
req = urllib.request.Request('http://127.0.0.1:8000/api/wsm/campaigns/CAMP_CCG/agents',
    data=payload, headers={'Content-Type': 'application/json'}, method='POST')

try:
    with urllib.request.urlopen(req) as r:
        print('Assign response:', r.read().decode())
except Exception as e:
    print('Assign failed:', e)

# Test listing agents for CAMP_CCG
try:
    with urllib.request.urlopen('http://127.0.0.1:8000/api/wsm/campaigns/CAMP_CCG/agents') as r:
        print('Agents in CAMP_CCG:', r.read().decode())
except Exception as e:
    print('List agents failed:', e)
