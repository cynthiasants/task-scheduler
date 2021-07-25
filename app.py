import random, string, os
from flask import *
from flask_mysqldb import MySQL
from functools import wraps


#wraps
def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'login' in session:
            return f(*args, **kwargs)
        else:
            flash("You need to login first")
            return redirect(url_for('sign'))
    return wrap


app = Flask(__name__)
app.config['SECRET_KEY'] = "".join([random.choice(string.ascii_letters) for _ in range(32)])
app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_PORT"] = 3306
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = ""
app.config["MYSQL_DB"] = "gx_scheduler"
app.config["MYSQL_CURSORCLASS"] = "DictCursor"

db = MySQL(app)

#fungsi membuat nama random
def makeString(l = 10):
    return ''.join(random.choice(string.ascii_letters) for _ in range(l))

#koneksi dan crud
def cursor():
    conn = db.connection
    return conn.cursor()

def cud(query, val:tuple = (), getlastid=0):
    with cursor() as cur:
        if val:
            cur.execute(query, val)
        else:
            cur.execute(query)
        db.connection.commit()
    if getlastid:
        return cur.lastrowid
    return cur.rowcount

def select(query, val:tuple = (), fa = 1):
    with cursor() as cur:
        if val:
            cur.execute(query, val)
        else:
            cur.execute(query)
        data = cur.fetchall() if fa else cur.fetchone()
    return data


#dashboard
@app.route("/")
@login_required
def index():
    return render_template("base.html", page = "dashboard")

@app.route("/calendar")
@login_required
def calendar():
    colors = ["#00c7f2", "#fc3d39", "#53d769"]
    query = "SELECT * FROM tasks WHERE id_user = %s"
    data = select(query, (session['id_user'], ))
    out = []
    if data:
        for i, cal in enumerate(data):
            out.append({
                "id": 1,
                "name": cal['judul_task'],
                "startdate": str(cal['date_end'].date()),
                "enddate": str(cal['date_end'].date()),
                "starttime": "00:00:00",
                "endtime": str(cal['date_end'].time()),
                "color": colors[i % len(colors)],
                "url": ""
            })
        return jsonify({"status" : "success", "data" : {"monthly" : out}})

#tasks
@app.route("/tasks")
@login_required
def tasks():
    return render_template("base.html", page = "tasks", data = {"makul" : select("SELECT * FROM makul WHERE id_user = %s", (session['id_user'], )), "platform" : select("SELECT * FROM platform WHERE id_user = %s", (session['id_user'],)), "tasks" : select("SELECT a.id_task, a.judul_task, a.date_end, b.nama_makul, c.nama_platform FROM tasks a JOIN makul b ON a.id_makul = b.id_makul JOIN platform c ON a.id_platform = c.id_platform WHERE a.id_user = %s AND a.status = 0", (session['id_user'],)), "edit" : 0})

@app.route("/tasks/create", methods = ['POST'])
@login_required
def createTask():
    if request.method == 'POST':
        try:
            foto = request.files['foto_tugas']
            query = "INSERT INTO tasks(judul_task, desc_task, date_start, date_end, id_makul, id_platform, image, time_to_send, id_user) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s)"
            if not os.path.isdir(f'static/img/tugas/{session["username"]}'):
                os.makedirs(f'static/img/tugas/{session["username"]}')
            fn = f'static/img/tugas/{session["username"]}/{makeString()}.jpg'
            foto.save(fn)
            cud(query, (request.form['judul_tugas'], request.form['desc_tugas'], request.form['start_date'], request.form['end_date'], request.form['makul'], request.form['platform'], fn, request.form['schedule_date'], session['id_user']), 1)
        except:
            query = "INSERT INTO tasks(judul_task, desc_task, date_start, date_end, id_makul, id_platform, time_to_send, id_user) VALUES(%s, %s, %s, %s, %s, %s, %s, %s)"
            cud(query, (request.form['judul_tugas'], request.form['desc_tugas'], request.form['start_date'], request.form['end_date'], request.form['makul'], request.form['platform'], request.form['schedule_date'], session['id_user']), 1)
    return redirect(url_for('tasks'))

@app.route("/tasks/edit")
@app.route("/tasks/edit/<id>", methods = ["GET", "POST"])
@login_required
def editTask(id:int = None):
    if request.method == 'GET':
        return render_template("base.html", page = "tasks", data = {"makul" : select("SELECT * FROM makul WHERE id_user = %s", (session['id_user'],)), "platform" : select("SELECT * FROM platform WHERE id_user = %s", (session['id_user'],)), "tasks" : select("SELECT a.id_task, a.judul_task, a.date_end, b.nama_makul, c.nama_platform FROM tasks a JOIN makul b ON a.id_makul = b.id_makul JOIN platform c ON a.id_platform = c.id_platform WHERE a.id_user = %s", (session['id_user'],)), "edit" : select("SELECT * FROM tasks WHERE id_task = %s AND id_user = %s", (id, session['id_user']), 0)})
    else:
        cek = select("SELECT * FROM tasks WHERE id_task = %s AND id_user = %s", (id, session['id_user']))
        if cek:
            try:
                foto = request.files['foto_tugas']
                query = "UPDATE tasks SET judul_task = %s, desc_task = %s, date_start = %s, date_end = %s, id_makul = %s, id_platform = %s, image = %s, time_to_send = %s WHERE id_task = %s AND id_user = %s"
                fn = f'static/img/tugas/{session["username"]}/{makeString()}.jpg'
                foto.save(fn)
                cud(query, (request.form['judul_tugas'], request.form['desc_tugas'], request.form['start_date'], request.form['end_date'], request.form['makul'], request.form['platform'], fn, request.form['schedule_date'], id, session['id_user']), 1)
            except:
                query = "UPDATE tasks SET judul_task = %s, desc_task = %s, date_start = %s, date_end = %s, id_makul = %s, id_platform = %s, time_to_send = %s  WHERE id_task = %s AND id_user = %s"
                cud(query, (request.form['judul_tugas'], request.form['desc_tugas'], request.form['start_date'], request.form['end_date'], request.form['makul'], request.form['platform'], request.form['schedule_date'], id, session['id_user']), 1)
            return redirect(url_for('tasks'))

@app.route("/tasks/delete")
@app.route("/tasks/delete/<id>", methods = ["POST"])
@login_required
def deleteTask(id:int = None):
    if request.method == "GET":
        return jsonify({"status" : 405, "msg" : "Method not allowed"})
    else:
        if id:
            data = select("SELECT * FROM tasks WHERE id_task = %s AND id_user = %s", (id, session['id_user']), 0)
            if data:
                if cud("DELETE FROM tasks WHERE id_task = %s", (id, )):
                    return jsonify({"status" : "success", "msg" : f"Berhasil menghapus tugas {data['judul_task']}"})
                return jsonify({"status" : "error", "msg" : "Gagal menghapus tugas"})
            return jsonify({"status" : "error", "msg" : "Tugas tidak ditemukan"})
        return jsonify({"status" : "error", "msg" : "Masukkan ID"})

@app.route("/tasks/done")
@app.route("/tasks/done/<id>", methods = ["POST"])
@login_required
def doneTask(id:int = None):
    if id:
        data = select("SELECT * FROM tasks WHERE id_task = %s AND id_user = %s AND status = 0", (id, session['id_user']), 0)
        if data:
            if cud("UPDATE tasks SET status = 1 WHERE id_task = %s", (id, )):
                return jsonify({"status" : "success", "msg" : f"Berhasil menyelesaikan tugas {data['judul_task']}"})
            return jsonify({"status" : "error", "msg" : "Gagal menyelesaikan tugas / tugas sudah selesai"})
        return jsonify({"status" : "error", "msg" : "Tugas tidak ditemukan"})
    return jsonify({"status" : "error", "msg" : "Masukkan ID"})


#makul
@app.route("/makul")
@login_required
def makul():
    return render_template("base.html", page = "makul", data = select("SELECT * FROM makul WHERE id_user = %s", (session['id_user'], )), val = None)

@app.route("/makul/create", methods = ["POST"])
@login_required
def createMakul():
    namaMakul = request.form['nama_makul']
    cud("INSERT INTO makul(nama_makul, id_user) VALUES(%s, %s)", (namaMakul, session['id_user']))
    return redirect(url_for("makul"))

@app.route("/makul/edit")
@app.route("/makul/edit/<id>", methods = ["GET", "POST"])
@login_required
def editMakul(id = None):
    if request.method == "GET":
        if id:
            data = select("SELECT * FROM makul WHERE id_makul = %s AND id_user = %s", (id, session['id_user']), 0)
            if data:
                return render_template("base.html", page = "makul", data = select("SELECT * FROM makul WHERE id_user = %s", (session['id_user'], )), val = data)
        return redirect(url_for("makul"))
    else:
        namaMakul = request.form['nama_makul']
        cud("UPDATE makul SET nama_makul = %s WHERE id_makul = %s AND id_user = %s", (namaMakul, id, session['id_user']))
        return redirect(url_for("makul"))

@app.route("/makul/delete")
@app.route("/makul/delete/<id>", methods = ["POST"])
@login_required
def deleteMakul(id = None):
    if request.method == "GET":
        return jsonify({"status" : 405, "msg" : "Method not allowed"})
    else:
        if id:
            data = select("SELECT * FROM makul WHERE id_makul = %s AND id_user = %s", (id, session['id_user']), 0)
            if data:
                if cud("DELETE FROM makul WHERE id_makul = %s AND id_user = %s", (id, session['id_user'])):
                    return jsonify({"status" : "success", "msg" : f"Berhasil menghapus makul {data['nama_makul']}"})
                return jsonify({"status" : "error", "msg" : "Gagal menghapus makul"})
            return jsonify({"status" : "error", "msg" : "Makul tidak ditemukan"})
        return jsonify({"status" : "error", "msg" : "Masukkan ID"})

#platform
@app.route("/platform")
@login_required
def platform():
    return render_template("base.html", page = "platform", data = select("SELECT * FROM platform WHERE id_user = %s", (session['id_user'],)), val = None)
@app.route("/platform/create", methods = ["POST"])
@login_required
def createPlatform():
    namaPlatform = request.form['nama_platform']
    cud("INSERT INTO platform(nama_platform, id_user) VALUES(%s, %s)", (namaPlatform, session['id_user']))
    return redirect(url_for("platform"))

@app.route("/platform/edit")
@app.route("/platform/edit/<id>", methods = ["GET", "POST"])
@login_required
def editPlatform(id = None):
    if request.method == "GET":
        if id:
            data = select("SELECT * FROM platform WHERE id_platform = %s AND id_user = %s", (id, session['id_user']), 0)
            if data:
                return render_template("base.html", page = "platform", data = select("SELECT * FROM platform WHERE id_user = %s", (session['id_user'],)), val = data)
        return redirect(url_for("platform"))
    else:
        namaPlatform = request.form['nama_platform']
        cud("UPDATE platform SET nama_platform = %s WHERE id_platform = %s", (namaPlatform, id))
        return redirect(url_for("platform"))
@app.route("/platform/delete")
@app.route("/platform/delete/<id>", methods = ["POST"])
@login_required
def deletePlatform(id =  None):
    if request.method == "GET":
        return jsonify({"status" : 405, "msg" : "Method not allowed"})
    else:
        if id:
            data = select("SELECT * FROM platform WHERE id_platform = %s AND id_user = %s", (id, session['id_user']), 0)
            if data:
                if cud("DELETE FROM platform WHERE id_platform = %s", (id, )):
                    return jsonify({"status" : "success", "msg" : f"Berhasil menghapus platform {data['nama_platform']}"})
                return jsonify({"status" : "error", "msg" : "Gagal menghapus platform"})
            return jsonify({"status" : "error", "msg" : "Platform tidak ditemukan"})
        return jsonify({"status" : "error", "msg" : "Masukkan ID"})

@app.route("/sign")
def sign():
    return render_template('login.html')

@app.route("/sign/action/login", methods = ['POST'])
def login():
    query = "SELECT * FROM users WHERE username = %s AND password = %s"
    data = select(query, (request.form['user'], request.form['pass']), fa=0)
    if data:
        session['username'] = data['username']
        session['id_user'] = data['id_user']
        session['login'] = True
        return redirect(url_for('index'))
    return redirect(url_for('sign'))
    

@app.route("/sign/action/register", methods = ['POST'])
def register():
    query = "INSERT INTO users(username,password, email, wa) VALUES(%s, %s, %s, %s)"
    idu = cud(query, (request.form['user'], request.form['pass'], request.form['email'], request.form['wa']), 1)
    if idu:
        session['username'] = request.form['user']
        session['id_user'] = idu
        session['login'] = True
        return redirect(url_for('index'))
    return redirect(url_for('sign'))

@app.route("/sign/logout")
@login_required
def logout():
    session.pop('username', None)
    session.pop('id_user', None)
    session.pop('login', None)
    return redirect(url_for('sign'))


app.run(port=1119, debug=1)
