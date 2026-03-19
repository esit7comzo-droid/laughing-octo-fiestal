from flask import Flask, request, redirect, session, render_template_string, jsonify
import sqlite3
import uuid

app = Flask(__name__)
app.secret_key = 'secretkey'

# DB 초기화
def init_db():
    conn = sqlite3.connect('nas.db')
    c = conn.cursor()
    c.execute('''
    CREATE TABLE IF NOT EXISTS files (
        id TEXT,
        filename TEXT,
        content BLOB
    )
    ''')
    conn.commit()
    conn.close()

init_db()

# 로그인 페이지
LOGIN_HTML = """
<!DOCTYPE html>
<html>
<head>
<style>
body {background:#111;color:white;font-family:Arial;}
.box {width:300px;margin:auto;margin-top:100px;}
input,button {width:100%;padding:10px;margin:5px;border-radius:10px;border:none;}
button {background:#0f0;}
</style>
</head>
<body>
<div class="box">
<h2>LOGIN</h2>
<form method="POST">
<input name="id" placeholder="ID">
<input name="pw" type="password" placeholder="Password">
<button>Login</button>
</form>
</div>
</body>
</html>
"""

# NAS 페이지
DASH_HTML = """
<!DOCTYPE html>
<html>
<head>
<style>
body {background:#000;color:#0f0;font-family:monospace;}
.box {width:80%;margin:auto;margin-top:50px;}
input,button {padding:10px;margin:5px;border-radius:10px;border:none;}
</style>
</head>
<body>
<div class="box">
<h2>NAS PANEL</h2>

<form method="POST" enctype="multipart/form-data" action="/upload">
<input type="file" name="file">
<button>Upload</button>
</form>

<h3>FILES</h3>
<ul>
{% for f in files %}
<li>{{f[1]}} - <a href="/share/{{f[0]}}">공유링크</a></li>
{% endfor %}
</ul>

</div>
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['id'] == 'admin' and request.form['pw'] == '@':
            session['login'] = True
            return redirect('/nas')
    return render_template_string(LOGIN_HTML)

@app.route('/nas')
def nas():
    if not session.get('login'):
        return redirect('/')
    conn = sqlite3.connect('nas.db')
    c = conn.cursor()
    c.execute("SELECT * FROM files")
    files = c.fetchall()
    conn.close()
    return render_template_string(DASH_HTML, files=files)

@app.route('/upload', methods=['POST'])
def upload():
    if not session.get('login'):
        return redirect('/')
    f = request.files['file']
    data = f.read()
    fid = str(uuid.uuid4())

    conn = sqlite3.connect('nas.db')
    c = conn.cursor()
    c.execute("INSERT INTO files VALUES (?, ?, ?)", (fid, f.filename, data))
    conn.commit()
    conn.close()

    return redirect('/nas')

@app.route('/share/<fid>')
def share(fid):
    conn = sqlite3.connect('nas.db')
    c = conn.cursor()
    c.execute("SELECT filename, content FROM files WHERE id=?", (fid,))
    file = c.fetchone()
    conn.close()

    if not file:
        return "Not found"

    return jsonify({
        "filename": file[0],
        "size": len(file[1])
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
