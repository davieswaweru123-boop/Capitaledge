from flask import Flask,render_template,request,redirect,url_for,session,send_from_directory,flash
from werkzeug.security import generate_password_hash,check_password_hash
import sqlite3,os
from pathlib import Path
BASE=Path(__file__).parent; DB=BASE/'capitaledge.db'; DOWNLOADS=BASE/'downloads'
app=Flask(__name__); app.secret_key=os.environ.get('SECRET_KEY','change-me')
def db():
 c=sqlite3.connect(DB); c.row_factory=sqlite3.Row; return c
def init():
 c=db(); c.executescript('''CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT,email TEXT UNIQUE,password TEXT,role TEXT DEFAULT 'user');CREATE TABLE IF NOT EXISTS products(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT,description TEXT,price REAL,filename TEXT);CREATE TABLE IF NOT EXISTS purchases(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER,product_id INTEGER,status TEXT,created_at DATETIME DEFAULT CURRENT_TIMESTAMP);''')
 if not c.execute("SELECT id FROM users WHERE email='admin@capitaledge.com'").fetchone(): c.execute('INSERT INTO users(name,email,password,role) VALUES(?,?,?,?)',('CapitalEdge Admin','admin@capitaledge.com',generate_password_hash('Admin123!'),'admin'))
 if c.execute('SELECT COUNT(*) n FROM products').fetchone()['n']==0:
  c.execute('INSERT INTO products(name,description,price,filename) VALUES(?,?,?,?)',('CapitalEdge Starter Bot','Demo licensed bot package.',19,'starter-bot.txt')); c.execute('INSERT INTO products(name,description,price,filename) VALUES(?,?,?,?)',('CapitalEdge Pro Toolkit','Trading tools and premium resources.',49,'pro-toolkit.txt'))
 c.commit(); c.close(); DOWNLOADS.mkdir(exist_ok=True); (DOWNLOADS/'starter-bot.txt').write_text('CAPITALEDGE DEMO BOT\nReplace with your licensed product.'); (DOWNLOADS/'pro-toolkit.txt').write_text('CAPITALEDGE PRO TOOLKIT\nReplace with your licensed toolkit.')
init()
def user():
 if 'uid' not in session:return None
 c=db(); u=c.execute('SELECT * FROM users WHERE id=?',(session['uid'],)).fetchone(); c.close(); return u
@app.context_processor
def ctx(): return {'user':user()}
@app.route('/')
def home():
 c=db(); p=c.execute('SELECT * FROM products').fetchall(); c.close(); return render_template('home.html',products=p)
@app.route('/register',methods=['GET','POST'])
def register():
 if request.method=='POST':
  n,e,p=request.form['name'],request.form['email'].lower(),request.form['password']; c=db()
  try: cur=c.execute('INSERT INTO users(name,email,password) VALUES(?,?,?)',(n,e,generate_password_hash(p))); c.commit(); session['uid']=cur.lastrowid
  except sqlite3.IntegrityError: flash('Email already registered.'); c.close(); return redirect(url_for('register'))
  c.close(); return redirect(url_for('dashboard'))
 return render_template('auth.html',mode='register')
@app.route('/login',methods=['GET','POST'])
def login():
 if request.method=='POST':
  c=db(); u=c.execute('SELECT * FROM users WHERE email=?',(request.form['email'].lower(),)).fetchone(); c.close()
  if u and check_password_hash(u['password'],request.form['password']): session['uid']=u['id']; return redirect(url_for('admin' if u['role']=='admin' else 'dashboard'))
  flash('Invalid login.')
 return render_template('auth.html',mode='login')
@app.route('/logout')
def logout(): session.clear(); return redirect('/')
@app.route('/dashboard')
def dashboard():
 u=user()
 if not u:return redirect('/login')
 c=db(); p=c.execute('SELECT p.*,x.name,x.filename FROM purchases p JOIN products x ON x.id=p.product_id WHERE p.user_id=? AND p.status="paid"',(u['id'],)).fetchall(); c.close(); return render_template('dashboard.html',purchases=p)
@app.route('/buy/<int:pid>',methods=['POST'])
def buy(pid):
 u=user()
 if not u:return redirect('/login')
 c=db(); c.execute('INSERT INTO purchases(user_id,product_id,status) VALUES(?,?,?)',(u['id'],pid,'paid')); c.commit(); c.close(); flash('Demo purchase completed. Connect a real payment gateway before accepting money.'); return redirect('/dashboard')
@app.route('/download/<path:name>')
def download(name):
 u=user()
 if not u:return redirect('/login')
 c=db(); ok=c.execute('SELECT 1 FROM purchases p JOIN products x ON x.id=p.product_id WHERE p.user_id=? AND p.status="paid" AND x.filename=?',(u['id'],name)).fetchone(); c.close()
 if not ok:return 'Purchase required',403
 return send_from_directory(DOWNLOADS,name,as_attachment=True)
@app.route('/admin')
def admin():
 u=user()
 if not u or u['role']!='admin':return 'Admin access required',403
 c=db(); users=c.execute('SELECT id,name,email,role FROM users ORDER BY id DESC').fetchall(); products=c.execute('SELECT * FROM products').fetchall(); purchases=c.execute('SELECT p.*,u.email,x.name FROM purchases p JOIN users u ON u.id=p.user_id JOIN products x ON x.id=p.product_id ORDER BY p.id DESC').fetchall(); c.close(); return render_template('admin.html',users=users,products=products,purchases=purchases)
@app.route('/admin/product',methods=['POST'])
def add_product():
 u=user()
 if not u or u['role']!='admin':return 'Admin access required',403
 c=db(); c.execute('INSERT INTO products(name,description,price,filename) VALUES(?,?,?,?)',(request.form['name'],request.form['description'],float(request.form['price']),request.form['filename'])); c.commit(); c.close(); return redirect('/admin')
if __name__=='__main__':init();app.run(host='0.0.0.0',port=5000,debug=True)
