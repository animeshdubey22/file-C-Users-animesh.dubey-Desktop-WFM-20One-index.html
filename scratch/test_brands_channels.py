import urllib.request, json

# 1. Test GET brands for CAMP_HOB
with urllib.request.urlopen('http://127.0.0.1:8000/api/wsm/campaigns/CAMP_HOB/brands') as r:
    brands = json.loads(r.read().decode())
    print('Brands for CAMP_HOB:', [b['name'] for b in brands])

# 2. Test POST brand
payload = json.dumps({'campaign_id': 'CAMP_HOB', 'name': 'Luxury Decor Collection', 'code': 'LUX'}).encode('utf-8')
req = urllib.request.Request('http://127.0.0.1:8000/api/wsm/campaigns/CAMP_HOB/brands', data=payload, headers={'Content-Type': 'application/json'}, method='POST')
with urllib.request.urlopen(req) as r:
    brand_res = json.loads(r.read().decode())
    print('Create brand response:', brand_res)

# 3. Test GET channels for CAMP_HOB
with urllib.request.urlopen('http://127.0.0.1:8000/api/wsm/campaigns/CAMP_HOB/channels') as r:
    channels = json.loads(r.read().decode())
    print('Channels for CAMP_HOB:', [f"{c['name']} ({c['channel']})" for c in channels])

# 4. Test POST channel
payload2 = json.dumps({
    'campaign_id': 'CAMP_HOB',
    'brand_id': brand_res['id'],
    'name': 'VIP Concierge Voice',
    'channel': 'Voice',
    'target_sla_seconds': 15,
    'target_sla_percent': 90,
    'target_aht': 320,
    'target_occupancy': 80
}).encode('utf-8')
req2 = urllib.request.Request('http://127.0.0.1:8000/api/wsm/campaigns/CAMP_HOB/channels', data=payload2, headers={'Content-Type': 'application/json'}, method='POST')
with urllib.request.urlopen(req2) as r:
    print('Create channel response:', r.read().decode())
