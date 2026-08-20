import sqlite3, json

conn = sqlite3.connect('wfm_one.db')
c = conn.cursor()

# Clean test campaign
c.execute("DELETE FROM campaigns WHERE id='CAMP_TEST'")
conn.commit()
print("Cleaned test campaign")

# Show campaigns table columns
c.execute("PRAGMA table_info(campaigns)")
cols = [r[1] for r in c.fetchall()]
print("Campaigns columns:", cols)

# Check if operating_days_json column exists
has_op_days = 'operating_days_json' in cols
has_hoop_start = 'hoop_start' in cols
has_base_rate = 'base_hourly_rate' in cols
print(f"  operating_days_json: {has_op_days}")
print(f"  hoop_start: {has_hoop_start}")
print(f"  base_hourly_rate: {has_base_rate}")

# List existing campaigns
c.execute("SELECT id, name, status FROM campaigns ORDER BY name")
camps = c.fetchall()
print(f"\nExisting campaigns ({len(camps)}):")
for camp in camps:
    print(f"  {camp[0]} | {camp[1]} | {camp[2]}")

conn.close()
