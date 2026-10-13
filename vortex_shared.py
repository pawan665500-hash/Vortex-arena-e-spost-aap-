import os, sqlite3, hashlib, secrets, hmac, html
from flask import session, redirect, url_for, request, render_template_string
BASE_DIR=os.path.dirname(os.path.abspath(__file__))
DB_PATH=os.path.join(BASE_DIR,'vortex_arena.db')
SECRET_KEY=os.environ.get('VORTEX_SECRET_KEY','change-this-secret-before-deploying')
ADMIN_PASSWORD=os.environ.get('VORTEX_ADMIN_PASSWORD','change-me-now')
try:
    from vortex_config import UPI_ID as _CONFIG_UPI_ID, SECRET_KEY as _CONFIG_SECRET_KEY, ADMIN_PASSWORD as _CONFIG_ADMIN_PASSWORD
except Exception:
    _CONFIG_UPI_ID='your-upi-id@bank'; _CONFIG_SECRET_KEY='change-this-secret-before-deploying'; _CONFIG_ADMIN_PASSWORD='change-me-now'
UPI_ID=os.environ.get('VORTEX_UPI_ID',_CONFIG_UPI_ID)
SECRET_KEY=os.environ.get('VORTEX_SECRET_KEY',_CONFIG_SECRET_KEY)
ADMIN_PASSWORD=os.environ.get('VORTEX_ADMIN_PASSWORD',_CONFIG_ADMIN_PASSWORD)
YOUTUBE_CHANNEL=os.environ.get('VORTEX_YOUTUBE_URL','https://youtube.com/@smaltanime_00')
GAMES=['Free Fire','BGMI','Roblox','Minecraft','Other Games']

def db():
    c=sqlite3.connect(DB_PATH,timeout=15); c.row_factory=sqlite3.Row; return c

def pw_hash(pw, salt=None):
    salt=salt or secrets.token_hex(16)
    digest=hashlib.pbkdf2_hmac('sha256',pw.encode(),bytes.fromhex(salt),240000).hex()
    return salt+'$'+digest

def pw_ok(pw, stored):
    try:
        salt,digest=stored.split('$',1)
        return hmac.compare_digest(hashlib.pbkdf2_hmac('sha256',pw.encode(),bytes.fromhex(salt),240000).hex(),digest)
    except Exception: return False

def init_db():
    with db() as c:
        c.executescript('''
        CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, username TEXT UNIQUE NOT NULL, email TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL, created_at TEXT DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS tournaments(id INTEGER PRIMARY KEY, game TEXT NOT NULL, title TEXT NOT NULL, entry_fee INTEGER NOT NULL DEFAULT 5, room_id TEXT DEFAULT '', room_password TEXT DEFAULT '', custom_room_id TEXT DEFAULT '', start_time TEXT DEFAULT '', live_url TEXT DEFAULT '', status TEXT NOT NULL DEFAULT 'Upcoming', created_at TEXT DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS registrations(id INTEGER PRIMARY KEY, tournament_id INTEGER NOT NULL, user_id INTEGER NOT NULL, team_name TEXT NOT NULL, game_uid TEXT NOT NULL, slot_no INTEGER NOT NULL, payment_status TEXT NOT NULL DEFAULT 'Pending', registration_status TEXT NOT NULL DEFAULT 'Pending', created_at TEXT DEFAULT CURRENT_TIMESTAMP, UNIQUE(tournament_id,user_id), UNIQUE(tournament_id,slot_no,user_id), FOREIGN KEY(tournament_id) REFERENCES tournaments(id), FOREIGN KEY(user_id) REFERENCES users(id));
        ''')
        n=c.execute('SELECT COUNT(*) n FROM tournaments').fetchone()['n']
        if n==0:
            c.execute("INSERT INTO tournaments(game,title,entry_fee,start_time,status) VALUES(?,?,?,?,?)",('Free Fire','Free Fire Squad Battle',5,'Today, 7:00 PM','Upcoming'))

def base(title, body, active=''):
    return render_template_string('''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no"><title>{{title}} | Vortex Arena</title><style>
    :root{color-scheme:dark;--bg:#020817;--panel:#07162e;--line:#173d83;--blue:#0788ff;--purple:#6725ff;--muted:#8fb5ed;--text:#f4f7ff}*{box-sizing:border-box}html,body{margin:0;height:100%;font-family:Arial,Helvetica,sans-serif;background:var(--bg);color:var(--text);overflow:hidden}body{background:radial-gradient(ellipse at 50% -20%,#112d69 0,transparent 55%),var(--bg)}.app{height:100vh;height:100dvh;max-width:760px;margin:auto;display:flex;flex-direction:column;border-left:1px solid #123777;border-right:1px solid #123777;min-height:0;overflow:hidden}.top{flex-shrink:0;height:66px;border-bottom:1px solid var(--blue);display:flex;align-items:center;gap:12px;padding:10px 16px;background:#020b1beF}.logo{font-weight:900;font-size:18px;letter-spacing:1px}.logo span{display:block;color:#8f7bff;font-size:9px;letter-spacing:4px;margin-top:2px}.v{font-size:30px;color:#65c7ff;font-weight:900}.main{flex:1 1 auto;min-height:0;overflow-y:auto;overflow-x:hidden;overscroll-behavior:contain;-webkit-overflow-scrolling:touch;padding:16px;padding-bottom:28px;scrollbar-width:thin;scrollbar-color:#2355a8 #061027}.bottom{position:relative;z-index:5;flex:0 0 68px;height:68px;display:flex;justify-content:space-around;align-items:stretch;border-top:1px solid #1755b9;background:#020a1b;box-shadow:0 -5px 20px #00143c;padding-bottom:env(safe-area-inset-bottom)}.bottom a{flex:1;min-width:0;text-align:center;text-decoration:none;color:#8daeea;font-size:10px;padding:9px 1px;white-space:nowrap;display:flex;flex-direction:column;align-items:center;justify-content:center}.bottom a b{display:block;font-size:18px;line-height:20px;margin-bottom:3px;color:inherit;font-weight:600}.bottom a.active{color:#fff;background:linear-gradient(0deg,#4d17ff44,transparent);border-bottom:2px solid #743cff}.title{font-size:23px;font-weight:800;margin:0 0 5px}.sub{color:#63b8ff;font-size:13px;margin-bottom:16px}.card{background:linear-gradient(125deg,#081a36,#030c1e);border:1px solid var(--line);border-radius:13px;padding:14px;margin-bottom:12px;box-shadow:0 0 12px #00153a55}.row{display:flex;align-items:center;gap:10px}.between{justify-content:space-between}.muted{color:var(--muted);font-size:12px}.tag{display:inline-block;border:1px solid #4e35d9;border-radius:20px;padding:5px 10px;color:#c6baff;font-size:11px}.btn,button{display:inline-block;border:0;border-radius:9px;padding:11px 15px;background:linear-gradient(110deg,#6324ff,#087dff);color:white;font-weight:700;text-decoration:none;font-size:13px;cursor:pointer}.btn.secondary{background:#10264a;border:1px solid #2854a0}.btn.danger{background:#7b1d3c}.btn.green{background:linear-gradient(110deg,#0084db,#00b99c)}input,select{width:100%;background:#020b1b;color:white;border:1px solid #214b91;border-radius:9px;padding:12px;margin:6px 0 12px;font-size:14px}label{font-size:12px;color:#a7c9ff}h3{font-size:16px;margin:0 0 8px}table{width:100%;border-collapse:collapse;font-size:12px}th,td{text-align:left;padding:10px 6px;border-bottom:1px solid #15325f}th{color:#7fbaff}a{color:#8dc6ff}.notice{padding:11px;border:1px solid #24549c;border-radius:9px;color:#b7d4ff;background:#061632;margin-bottom:12px;font-size:13px}.pill{font-size:10px;padding:4px 7px;border-radius:6px;background:#172d50;color:#c7ddff}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}.grid .card{margin:0}.big{font-size:22px;font-weight:800}.error{color:#ff8a9a}.ok{color:#6ef2be}.game{border:1px solid #224c91;border-radius:10px;padding:12px;background:#07172f;margin-bottom:9px}.game strong{display:block;margin-bottom:5px}@media(min-width:760px){.main{padding:26px 30px}.top{height:78px}.bottom{height:74px}.main>.grid{grid-template-columns:repeat(3,minmax(0,1fr))}}@media(max-width:380px){.bottom{height:62px}.bottom a{font-size:8px}.bottom a b{font-size:15px}.main{padding:11px;padding-bottom:18px}.title{font-size:21px}}
    </style></head><body><div class="app"><header class="top"><div class="v">V</div><div class="logo">VORTEX ARENA<span>ESPORTS</span></div><div style="margin-left:auto;color:#80b7ff;font-size:11px">PLAY · COMPETE · WIN</div></header><main class="main">{{body|safe}}</main><nav class="bottom">{% for item in nav %}<a class="{{'active' if item[0]==active else ''}}" href="{{item[1]}}"><b>{{item[2]}}</b>{{item[0]}}</a>{% endfor %}</nav></div></body></html>''',title=title,body=body,active=active,nav=[('Home','/','⌂'),('Games','/games','🎮'),('Tournaments','/tournaments','🏆'),('Matches','/my-matches','♜'),('Live','/live','◉'),('Results','/results','▤'),('Settings','/settings','⚙')])

def require_user():
    if 'user_id' not in session: return redirect('/login')
    return None

def tournament_rows():
    with db() as c: return c.execute('SELECT * FROM tournaments ORDER BY id DESC').fetchall()

def user_regs(uid):
    with db() as c: return c.execute('SELECT r.*,t.title,t.game,t.start_time,t.room_id,t.room_password,t.custom_room_id,t.live_url,t.status AS tournament_status FROM registrations r JOIN tournaments t ON t.id=r.tournament_id WHERE r.user_id=? ORDER BY r.id DESC',(uid,)).fetchall()

def next_slot(c, tid):
    used={r['slot_no'] for r in c.execute('SELECT slot_no FROM registrations WHERE tournament_id=?',(tid,)).fetchall()}
    available=[n for n in range(1,13) if n not in used]
    if not available:return None
    return secrets.choice(available)

def slot_count(c, tid): return c.execute('SELECT COUNT(*) n FROM registrations WHERE tournament_id=?',(tid,)).fetchone()['n']

def admin_ok(): return bool(session.get('is_admin'))
