import urllib.request, json, sys

sys.stdout.reconfigure(encoding='utf-8')

def query_bot(msg):
    payload = json.dumps({'message': msg, 'role': 'WFM Admin', 'campaign_id': 'CAMP_HOB'}).encode('utf-8')
    req = urllib.request.Request('http://127.0.0.1:8000/api/bot/chat', data=payload, headers={'Content-Type': 'application/json'}, method='POST')
    with urllib.request.urlopen(req) as r:
        res = json.loads(r.read().decode())
        print(f"\n--- Q: '{msg}' ---")
        print(f"Title: {res.get('title')}")
        print(f"Reply Preview: {res.get('reply')[:140]}...")

query_bot("How do I create a new campaign?")
query_bot("How do I assign agents to a campaign?")
query_bot("Explain primary shift activities and breaks")
query_bot("How do work pattern templates work?")
query_bot("What are our active campaign stats?")
