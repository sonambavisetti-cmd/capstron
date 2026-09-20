import sqlite3
p = r'C:\Users\SonamBavisetti\Desktop\Capstone\capstoneRepo\dev.db'
conn = sqlite3.connect(p)
cur = conn.cursor()
cur.execute("SELECT name, type FROM sqlite_master WHERE type IN ('table','index')")
rows = cur.fetchall()
print('Objects in dev.db:')
for r in rows:
    print(r)
conn.close()
