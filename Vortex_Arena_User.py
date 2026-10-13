from flask import Flask, request, session, redirect, url_for
from urllib.parse import quote
from vortex_shared import *
app=Flask(__name__); app.secret_key=SECRET_KEY; init_db()

def page(title,body,active='Home'): return base(title,body,active)
@app.route('/')
def home():
    if 'user_id' not in session:return redirect('/login')
    with db() as c:
        user=c.execute('SELECT * FROM users WHERE id=?',(session['user_id'],)).fetchone()
        regs=c.execute('SELECT r.*,t.title,t.game,t.start_time,t.status,t.live_url FROM registrations r JOIN tournaments t ON t.id=r.tournament_id WHERE r.user_id=? ORDER BY r.id DESC LIMIT 3',(user['id'],)).fetchall()
        ts=c.execute("SELECT * FROM tournaments WHERE status!='Completed' ORDER BY id DESC LIMIT 3").fetchall()
        live_count=c.execute("SELECT COUNT(*) n FROM tournaments WHERE status='Live'").fetchone()['n']
    registered=len(user_regs(user['id']))
    body=f'''<section class="card" style="background:radial-gradient(circle at 95% 5%,#4920a766,transparent 42%),linear-gradient(125deg,#091c3d,#030b1c);padding:18px">
      <div class="row between"><div><div class="muted">WELCOME BACK, PLAYER</div><h1 class="title" style="margin-top:7px">{html.escape(user['username'])}</h1><div class="sub" style="margin:5px 0 0">Play · Compete · Win</div></div><span class="tag">PLAYER</span></div>
      <div class="grid" style="margin-top:16px"><div><div class="muted">My Registrations</div><div class="big">{registered}</div></div><div><div class="muted">Entry Fee</div><div class="big">₹5</div></div></div>
      <p style="margin:16px 0 0"><a class="btn" href="/tournaments">Explore Tournaments →</a></p>
      <a class="btn green" style="display:block;text-align:center;margin-top:10px" href="{html.escape(YOUTUBE_CHANNEL,quote=True)}" target="_blank" rel="noopener">▶ YouTube Live / Channel</a>
      <div class="muted" style="margin-top:7px">Follow Vortex Arena streams and match updates</div>
    </section>
    <div class="row between"><h3>Quick Access</h3><a href="/settings">My Profile</a></div>
    <div class="grid" style="grid-template-columns:repeat(2,minmax(0,1fr));margin-bottom:16px">
      <a class="game" style="text-decoration:none" href="/games"><strong>🎮 Games</strong><span class="muted">Explore available games</span></a>
      <a class="game" style="text-decoration:none" href="/tournaments"><strong>🏆 Tournaments</strong><span class="muted">Join and reserve a slot</span></a>
      <a class="game" style="text-decoration:none" href="/my-matches"><strong>♜ My Matches</strong><span class="muted">Slots and room details</span></a>
      <a class="game" style="text-decoration:none" href="/live"><strong>◉ Live Matches</strong><span class="muted">Watch matches live ({live_count})</span></a>
      <a class="game" style="text-decoration:none" href="/results"><strong>▤ Results</strong><span class="muted">Tournament results</span></a>
      <a class="game" style="text-decoration:none" href="/settings"><strong>⚙ Settings</strong><span class="muted">Account and preferences</span></a>
    </div>
    <div class="row between"><h3>Upcoming Tournaments</h3><a href="/tournaments">View all</a></div>'''
    if ts:
        for t in ts:
            with db() as c: count=slot_count(c,t['id'])
            body+=f'''<section class="card"><div class="row between"><div><div class="muted">{html.escape(t['game'])}</div><h3 style="margin-top:5px">{html.escape(t['title'])}</h3><div class="muted">{html.escape(t['start_time'] or 'Time to be announced')} · Entry ₹{t['entry_fee']}</div></div><span class="pill">{max(0,48-count*4)} seats left</span></div><p><a class="btn" href="/join/{t['id']}">View & Register</a></p></section>'''
    else:
        body+='<div class="notice">No upcoming tournaments right now. Please check again soon.</div>'
    body+='<h3 style="margin-top:18px">Your Recent Matches</h3>'
    if regs:
        for r in regs: body+=f'''<section class="card"><div class="row between"><strong>{html.escape(r['title'])}</strong><span class="pill">{html.escape(r['registration_status'])}</span></div><div class="muted">{html.escape(r['game'])} · Slot {r['slot_no']} · {html.escape(r['start_time'] or 'Time pending')}</div><p><a class="btn secondary" href="/my-matches">View match details</a></p></section>'''
    else: body+='<div class="notice">You have not registered for a tournament yet. Open Tournaments to get started.</div>'
    return page('Home',body,'Home')

@app.route('/register',methods=['GET','POST'])
def register():
    msg=''
    if request.method=='POST':
        name=request.form.get('username','').strip(); email=request.form.get('email','').strip().lower(); pw=request.form.get('password','')
        if len(name)<3 or '@' not in email or len(pw)<8: msg='<div class="notice error">Enter a username (3+ characters), valid email and password (8+ characters).</div>'
        else:
            try:
                with db() as c:c.execute('INSERT INTO users(username,email,password_hash) VALUES(?,?,?)',(name,email,pw_hash(pw)))
                return redirect('/login?registered=1')
            except sqlite3.IntegrityError: msg='<div class="notice error">Username or email already exists.</div>'
    body=f'''<h1 class="title">Create Account</h1><div class="sub">Register to enter tournaments</div>{msg}<form method="post" class="card"><label>Username</label><input name="username" required minlength="3" autocomplete="username"><label>Email</label><input type="email" name="email" required autocomplete="email"><label>Password</label><input type="password" name="password" required minlength="8" autocomplete="new-password"><button class="btn" type="submit">Create Account</button><p class="muted">Already registered? <a href="/login">Login</a></p></form>'''
    return page('Register',body,'Setting')

@app.route('/login',methods=['GET','POST'])
def login():
    msg='<div class="notice ok">Account created. Please log in.</div>' if request.args.get('registered') else ''
    if request.method=='POST':
        email=request.form.get('email','').strip().lower(); pw=request.form.get('password','')
        with db() as c:u=c.execute('SELECT * FROM users WHERE email=?',(email,)).fetchone()
        if u and pw_ok(pw,u['password_hash']):session.clear();session['user_id']=u['id'];session['username']=u['username'];return redirect('/')
        msg='<div class="notice error">Incorrect email or password.</div>'
    return page('Login',f'''<h1 class="title">Player Login</h1><div class="sub">Welcome back to Vortex Arena</div>{msg}<form method="post" class="card"><label>Email</label><input type="email" name="email" required autocomplete="email"><label>Password</label><input type="password" name="password" required autocomplete="current-password"><button class="btn" type="submit">Login</button><p class="muted">New player? <a href="/register">Create account</a></p></form>''','Setting')

@app.route('/logout')
def logout(): session.clear(); return redirect('/login')
@app.route('/games')
@app.route('/tournaments')
def games():
    if 'user_id' not in session:return redirect('/login')
    chosen=request.args.get('game',''); q=request.args.get('q','').strip()
    ts=tournament_rows(); body='<h1 class="title">All Games</h1><div class="sub">Play · Compete · Win</div><form method="get"><input name="q" placeholder="Search games or tournaments" value="'+html.escape(q)+'"><button class="btn" type="submit">Search</button></form><div class="row" style="flex-wrap:wrap;margin:10px 0 16px">'
    for g in GAMES: body+=f'<a class="btn secondary" href="/games?game={quote(g)}">{html.escape(g)}</a>'
    body+='</div>'
    matches=[t for t in ts if (not chosen or t['game']==chosen) and (not q or q.lower() in (t['game']+' '+t['title']).lower())]
    if not matches: body+='<div class="notice">No tournaments found for this search.</div>'
    for t in matches:
        with db() as c: count=slot_count(c,t['id'])
        body+=f'''<section class="card"><div class="row between"><div><h3>{html.escape(t['game'])}</h3><div>{html.escape(t['title'])}</div><div class="muted">{html.escape(t['start_time'] or 'Time to be announced')} · ₹{t['entry_fee']} entry</div></div><span class="pill">{count*4}/48 players</span></div><p><a class="btn" href="/join/{t['id']}">Register Team</a></p></section>'''
    return page('Tournaments' if request.path=='/tournaments' else 'Games',body,'Tournaments' if request.path=='/tournaments' else 'Games')

@app.route('/join/<int:tid>',methods=['GET','POST'])
def join(tid):
    if 'user_id' not in session:return redirect('/login')
    with db() as c:t=c.execute('SELECT * FROM tournaments WHERE id=?',(tid,)).fetchone()
    if not t:return page('Tournament','<div class="notice">Tournament not found.</div>','Games')
    msg=''
    if request.method=='POST':
        team=request.form.get('team_name','').strip(); uid=request.form.get('game_uid','').strip()
        if not team or not uid: msg='<div class="notice error">Team name and game UID are required.</div>'
        else:
            try:
                with db() as c:
                    existing=c.execute('SELECT id FROM registrations WHERE tournament_id=? AND user_id=?',(tid,session['user_id'])).fetchone()
                    if existing:return redirect('/payment/'+str(existing['id']))
                    if slot_count(c,tid)>=12: msg='<div class="notice error">All 12 slots are full for this tournament.</div>'
                    else:
                        slot=next_slot(c,tid)
                        cur=c.execute('INSERT INTO registrations(tournament_id,user_id,team_name,game_uid,slot_no) VALUES(?,?,?,?,?)',(tid,session['user_id'],team,uid,slot))
                        return redirect('/payment/'+str(cur.lastrowid))
            except sqlite3.IntegrityError: msg='<div class="notice error">You are already registered for this tournament.</div>'
    body=f'''<h1 class="title">Team Registration</h1><div class="sub">{html.escape(t['title'])}</div>{msg}<form method="post" class="card"><div class="notice">Game: <b>{html.escape(t['game'])}</b><br>Entry fee: <b>₹{t['entry_fee']}</b><br>Maximum: 48 players · 12 squad slots</div><label>Team Name</label><input name="team_name" required maxlength="40" placeholder="Enter team name"><label>{html.escape(t['game'])} UID / Player ID</label><input name="game_uid" required maxlength="60" placeholder="Enter game UID"><button class="btn" type="submit">Next — Payment</button></form>'''
    return page('Team Registration',body,'Games')

@app.route('/payment/<int:rid>',methods=['GET','POST'])
def payment(rid):
    if 'user_id' not in session:return redirect('/login')
    with db() as c:r=c.execute('SELECT r.*,t.title,t.entry_fee,t.game FROM registrations r JOIN tournaments t ON t.id=r.tournament_id WHERE r.id=? AND r.user_id=?',(rid,session['user_id'])).fetchone()
    if not r:return redirect('/my-matches')
    upi=f'upi://pay?pa={quote(UPI_ID)}&pn={quote("Vortex Arena")}&am={r["entry_fee"]}&cu=INR&tn={quote("Tournament registration "+str(rid))}'
    msg=''
    if request.method=='POST':
        with db() as c:c.execute("UPDATE registrations SET payment_status='Submitted',registration_status='Pending' WHERE id=? AND user_id=? AND payment_status='Pending'",(rid,session['user_id']))
        msg='<div class="notice ok">Payment marked as submitted. Admin confirmation is still required.</div>'
        with db() as c:r=c.execute('SELECT r.*,t.title,t.entry_fee,t.game FROM registrations r JOIN tournaments t ON t.id=r.tournament_id WHERE r.id=?',(rid,)).fetchone()
    body=f'''<h1 class="title">Registration Payment</h1><div class="sub">{html.escape(r['title'])}</div>{msg}<section class="card"><div class="muted">AMOUNT DUE</div><div class="big">₹{r['entry_fee']}</div><p>Team: <b>{html.escape(r['team_name'])}</b></p><p>Reserved slot: <b>{r['slot_no']}</b></p><div class="notice">Tap below to open a UPI app. Complete the payment there, then return and submit the payment for admin verification.</div><a class="btn green" style="display:block;text-align:center" href="{html.escape(upi,quote=True)}">Pay ₹{r['entry_fee']} with UPI</a><p class="muted">UPI ID configured: {html.escape(UPI_ID)}</p><form method="post"><button class="btn" type="submit">I Have Paid — Submit for Review</button></form><p class="muted">Status: {html.escape(r['payment_status'])} · Registration: {html.escape(r['registration_status'])}</p></section>'''
    return page('Payment',body,'Games')

@app.route('/my-matches')
def my_matches():
    if 'user_id' not in session:return redirect('/login')
    regs=user_regs(session['user_id']);body='<h1 class="title">My Matches</h1><div class="sub">Slots, room details and live links</div>'
    if not regs:body+='<div class="notice">No registrations yet. <a href="/games">Find a tournament</a>.</div>'
    for r in regs:
        body+=f'<section class="card"><h3>{html.escape(r["title"])}</h3><div class="muted">{html.escape(r["game"])} · {html.escape(r["start_time"] or "Time pending")}</div><p>Team: {html.escape(r["team_name"])}<br>Slot: <b>{r["slot_no"]}</b> of 12<br>Payment: <b>{html.escape(r["payment_status"])}</b><br>Registration: <b>{html.escape(r["registration_status"])}</b></p>'
        if r['registration_status']=='Confirmed':body+=f'<div class="notice">Room ID: {html.escape(r["room_id"] or "Not announced")}<br>Custom Room ID: {html.escape(r["custom_room_id"] or "Not announced")}<br>Password: {html.escape(r["room_password"] or "Not announced")}</div>'
        if r['live_url']:body+=f'<p><a class="btn" href="{html.escape(r["live_url"],quote=True)}" target="_blank" rel="noopener">Watch YouTube Live</a></p>'
        body+='</section>'
    return page('My Matches',body,'Match')
@app.route('/matches')
def matches(): return my_matches()
@app.route('/live')
@app.route('/results')
@app.route('/settings')
def misc():
    if 'user_id' not in session:return redirect('/login')
    path=request.path
    if path=='/live':
        ts=[t for t in tournament_rows() if t['status']=='Live'];body='<h1 class="title">Live Matches</h1><div class="sub">Watch ongoing tournaments</div>'
        for t in ts:body+=f'<section class="card"><h3>{html.escape(t["title"])}</h3><div class="muted">{html.escape(t["game"])}</div><p><a class="btn" href="{html.escape(t["live_url"] or YOUTUBE_CHANNEL,quote=True)}" target="_blank" rel="noopener">Watch Live</a></p></section>'
        if not ts:body+='<div class="notice">No matches are live right now. You can still open the Vortex Arena YouTube channel for streams and updates.</div>'
        body+=f'<section class="card"><h3>Vortex Arena on YouTube</h3><div class="muted">Channel: Smalt Anime</div><p><a class="btn green" href="{html.escape(YOUTUBE_CHANNEL,quote=True)}" target="_blank" rel="noopener">▶ Open YouTube Live / Channel</a></p></section>'
        return page('Live',body,'Live')
    if path=='/results': return page('Results','<h1 class="title">Results</h1><div class="sub">Tournament results</div><div class="notice">Results will appear here when the admin publishes them.</div>','Result')
    return page('Settings',f'<h1 class="title">Settings</h1><div class="sub">Account and preferences</div><section class="card"><h3>{html.escape(session.get("username","Player"))}</h3><p><a class="btn secondary" href="/my-matches">My Registrations</a></p><a class="btn danger" href="/logout">Logout</a></section>','Setting')

if __name__=='__main__':
    print('Vortex Arena User Panel: http://127.0.0.1:8082')
    app.run(host='127.0.0.1',port=int(os.environ.get('VORTEX_USER_PORT','8082')),debug=False)
