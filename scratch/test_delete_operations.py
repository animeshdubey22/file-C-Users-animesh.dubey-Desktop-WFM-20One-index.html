import urllib.request, json

# 1. Test remove agent EMP1000 from CAMP_CCG
req = urllib.request.Request('http://127.0.0.1:8000/api/wsm/campaigns/CAMP_CCG/agents/EMP1000', method='DELETE')
with urllib.request.urlopen(req) as r:
    print('Remove agent EMP1000 response:', r.read().decode())

# 2. Check agents list for CAMP_CCG
with urllib.request.urlopen('http://127.0.0.1:8000/api/wsm/campaigns/CAMP_CCG/agents') as r:
    agents = json.loads(r.read().decode())
    print(f'Remaining agents in CAMP_CCG ({len(agents)}): {[a["name"] for a in agents]}')

# 3. Create a temporary test campaign to delete
create_payload = json.dumps({
    'name': 'Temporary Delete Test',
    'code': 'TMPDEL',
    'operating_days': ['Mon','Tue']
}).encode('utf-8')
req = urllib.request.Request('http://127.0.0.1:8000/api/wsm/campaigns',
    data=create_payload, headers={'Content-Type': 'application/json'}, method='POST')
with urllib.request.urlopen(req) as r:
    print('Created temp campaign:', r.read().decode())

# 4. Delete the temp campaign
req = urllib.request.Request('http://127.0.0.1:8000/api/wsm/campaigns/CAMP_TMPDEL', method='DELETE')
with urllib.request.urlopen(req) as r:
    print('Deleted temp campaign response:', r.read().decode())

# 5. Verify campaigns list does NOT contain CAMP_TMPDEL
with urllib.request.urlopen('http://127.0.0.1:8000/api/wsm/campaigns') as r:
    camps = json.loads(r.read().decode())
    ids = [c['id'] for c in camps]
    print('CAMP_TMPDEL in list?:', 'CAMP_TMPDEL' in ids)
    print(f'Active campaigns ({len(camps)}): {ids}')
