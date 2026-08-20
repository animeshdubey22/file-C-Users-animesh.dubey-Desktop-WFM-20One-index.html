import sqlite3

conn = sqlite3.connect('wfm_one.db')
c = conn.cursor()

def add_col_if_missing(table, col, col_type):
    c.execute(f"PRAGMA table_info({table})")
    cols = [r[1] for r in c.fetchall()]
    if col not in cols:
        print(f"Adding column {col} to {table}...")
        c.execute(f"ALTER TABLE {table} ADD COLUMN {col} {col_type}")

# Enhance campaigns table
add_col_if_missing('campaigns', 'operating_days_json', "TEXT DEFAULT '[\"Mon\",\"Tue\",\"Wed\",\"Thu\",\"Fri\"]'")
add_col_if_missing('campaigns', 'hoop_start', "TEXT DEFAULT '08:00'")
add_col_if_missing('campaigns', 'hoop_end', "TEXT DEFAULT '20:00'")
add_col_if_missing('campaigns', 'base_hourly_rate', "REAL DEFAULT 25.0")
add_col_if_missing('campaigns', 'ot_multiplier', "REAL DEFAULT 1.5")
add_col_if_missing('campaigns', 'weekend_multiplier', "REAL DEFAULT 1.25")

# Enhance activities table
add_col_if_missing('activities', 'activity_type', "TEXT DEFAULT 'PRIMARY'")
add_col_if_missing('activities', 'default_duration_minutes', "INTEGER DEFAULT 60")
add_col_if_missing('activities', 'min_duration_minutes', "INTEGER DEFAULT 5")
add_col_if_missing('activities', 'max_duration_minutes', "INTEGER DEFAULT 120")

# Enhance shift_templates table
add_col_if_missing('shift_templates', 'primary_activity', "TEXT DEFAULT 'Phone'")
add_col_if_missing('shift_templates', 'events_json', "TEXT DEFAULT '[]'")

# Enhance work_patterns table
add_col_if_missing('work_patterns', 'default_shift_template_id', "TEXT")
add_col_if_missing('work_patterns', 'operating_days_json', "TEXT DEFAULT '[\"Mon\",\"Tue\",\"Wed\",\"Thu\",\"Fri\"]'")

# Seed standard activities if missing
standard_activities = [
    ('ACT_PHONE', 'Phone / Voice', 'VOICE', 'VOICE', 1, 1, '#10b981', '9h', 'Primary inbound phone channel', 'PRIMARY', 540, 540, 660),
    ('ACT_CHAT', 'Chat Support', 'CHAT', 'CHAT', 1, 1, '#06b6d4', '9h', 'Primary live chat channel', 'PRIMARY', 540, 540, 660),
    ('ACT_EMAIL', 'E-mail Support', 'EMAIL', 'EMAIL', 1, 1, '#f59e0b', '9h', 'Primary email tickets channel', 'PRIMARY', 540, 540, 660),
    ('ACT_BACKOFFICE', 'Back-office', 'NON_VOICE', 'BACKOFFICE', 1, 1, '#8b5cf6', '9h', 'Primary back-office admin tasks', 'PRIMARY', 540, 540, 660),
    ('ACT_TL', 'Team Leader', 'LEADERSHIP', 'TL', 1, 1, '#ec4899', '9h', 'Team leader floor supervision', 'PRIMARY', 540, 540, 660),
    ('ACT_BRK15', 'Short Break (15m)', 'BREAK', 'BREAK_15', 1, 1, '#38bdf8', '15m', 'Rest break', 'EVENT', 15, 5, 30),
    ('ACT_LUNCH60', 'Lunch Break (1h)', 'MEAL', 'LUNCH_60', 0, 1, '#fb923c', '60m', 'Meal lunch break', 'EVENT', 60, 30, 90),
    ('ACT_COACH30', '1-on-1 Coaching (30m)', 'COACHING', 'COACH_30', 1, 1, '#a855f7', '30m', 'Performance coaching', 'EVENT', 30, 15, 60),
    ('ACT_MEET60', 'Team Meeting (1h)', 'MEETING', 'MEET_60', 1, 1, '#6366f1', '60m', 'Team sync meeting', 'EVENT', 60, 15, 120),
    ('ACT_TRAIN60', 'Training Session (1h)', 'TRAINING', 'TRAIN_60', 1, 1, '#a78bfa', '60m', 'Skill upskilling training', 'EVENT', 60, 30, 120),
]

for act in standard_activities:
    c.execute("""
        INSERT OR REPLACE INTO activities (id, name, category, code, is_paid, is_planned, color_hex, default_duration, description, activity_type, default_duration_minutes, min_duration_minutes, max_duration_minutes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, act)

conn.commit()
conn.close()
print("Schema enhanced and seeded successfully!")
