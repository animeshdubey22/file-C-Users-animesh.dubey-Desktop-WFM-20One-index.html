import urllib.request, json

payload = json.dumps({
    'name': 'Customer Care Global',
    'code': 'CCG',
    'description': 'Global Customer Care',
    'timezone': 'IST',
    'currency': 'INR',
    'service_level_target': 80,
    'aht_target': 280,
    'occupancy_target': 85,
    'shrinkage_target': 13.5,
    'default_interval': 30,
    'operating_days': ['Mon','Tue','Wed','Thu','Fri','Sat'],
    'hoop_start': '08:00',
    'hoop_end': '22:00',
    'base_hourly_rate': 650.0,
    'ot_multiplier': 1.5,
    'weekend_multiplier': 1.25
}).encode('utf-8')

req = urllib.request.Request('http://127.0.0.1:8000/api/wsm/campaigns',
    data=payload, headers={'Content-Type': 'application/json'}, method='POST')

with urllib.request.urlopen(req) as r:
    print('Campaign creation response:', r.read().decode())

with urllib.request.urlopen('http://127.0.0.1:8000/api/wsm/campaigns') as r:
    data = json.loads(r.read().decode())
    print(f'Total campaigns in DB: {len(data)}')
    for c in data:
        print(f"  - {c['id']}: {c['name']} ({c.get('currency')} {c.get('base_hourly_rate')}/hr) Days: {c.get('operating_days')}")
