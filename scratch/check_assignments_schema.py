import sqlite3

conn = sqlite3.connect('wfm_one.db')
c = conn.cursor()
c.execute('PRAGMA table_info(employee_campaign_assignments)')
for col in c.fetchall():
    print(col)

c.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='employee_campaign_assignments'")
print("\nCREATE SQL:\n", c.fetchone()[0])

c.execute("SELECT * FROM employee_campaign_assignments LIMIT 5")
print("\nSample Rows:")
for r in c.fetchall():
    print(r)

conn.close()
