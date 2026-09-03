import sqlite3, json
c = sqlite3.connect('prospector.db')
c.row_factory = sqlite3.Row
slug = 'clinica-prado-odontologia-rio-claro'
lead = c.execute("SELECT * FROM leads WHERE slug=?", (slug,)).fetchone()
print("=== LEAD FULL ===")
print(json.dumps(dict(lead), ensure_ascii=False, indent=2, default=str))
print("=== OUTREACH HISTORY ===")
rows = [dict(r) for r in c.execute("SELECT * FROM outreach_history WHERE slug=?", (slug,))]
print(json.dumps(rows, ensure_ascii=False, indent=2, default=str))
print("=== TABLES ===")
tabs = [r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'")]
print(tabs)
