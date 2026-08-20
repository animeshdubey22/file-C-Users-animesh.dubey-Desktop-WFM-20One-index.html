import sqlite3

conn = sqlite3.connect('wfm_one.db')
c = conn.cursor()

# 1. Create campaign_brands table
c.execute("""
    CREATE TABLE IF NOT EXISTS campaign_brands (
        id TEXT PRIMARY KEY,
        campaign_id TEXT NOT NULL,
        name TEXT NOT NULL,
        code TEXT,
        description TEXT,
        status TEXT DEFAULT 'Active',
        created_at TEXT DEFAULT (datetime('now')),
        FOREIGN KEY (campaign_id) REFERENCES campaigns(id)
    )
""")

# 2. Check if brand_id exists on lines_of_business
c.execute("PRAGMA table_info(lines_of_business)")
lob_cols = [r[1] for r in c.fetchall()]
if 'brand_id' not in lob_cols:
    c.execute("ALTER TABLE lines_of_business ADD COLUMN brand_id TEXT")
    print("Added brand_id to lines_of_business")

# 3. Seed default brands for campaigns if empty
c.execute("SELECT COUNT(*) FROM campaign_brands")
count = c.fetchone()[0]
if count == 0:
    seed_brands = [
        ('BRD_RUGS_USA', 'CAMP_HOB', 'Rugs USA', 'RUGS', 'Direct to consumer rugs and home decor'),
        ('BRD_NULOOM', 'CAMP_HOB', 'NuLoom', 'NULM', 'Modern contemporary home flooring'),
        ('BRD_ANNE_SELKE', 'CAMP_HOB', 'Anne Selke', 'ASLK', 'Luxury textiles and premium decor'),
        ('BRD_RUGS_USA_MAIN', 'CAMP_RUGS_USA', 'Rugs USA', 'RUGS', 'Flagship Brand'),
        ('BRD_NULOOM_MAIN', 'CAMP_NULOOM', 'NuLoom', 'NULM', 'Flagship Brand'),
        ('BRD_ANNE_SELKE_MAIN', 'CAMP_ANNE_SELKE', 'Anne Selke', 'ASLK', 'Flagship Brand'),
        ('BRD_GLOBAL_CARE', 'CAMP_CCG', 'Customer Care Global', 'CCG', 'Global Enterprise Support')
    ]
    for b in seed_brands:
        c.execute("""
            INSERT OR REPLACE INTO campaign_brands (id, campaign_id, name, code, description, status)
            VALUES (?, ?, ?, ?, ?, 'Active')
        """, b)
    print(f"Seeded {len(seed_brands)} default campaign brands")

conn.commit()

# Print status
c.execute("SELECT id, campaign_id, name FROM campaign_brands")
print("\nCampaign Brands:")
for r in c.fetchall():
    print(" ", r)

c.execute("SELECT id, campaign_id, name, channel FROM lines_of_business")
print("\nLines of Business / Channels:")
for r in c.fetchall():
    print(" ", r)

conn.close()
