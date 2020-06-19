from flask import render_template
import sqlite3
import requests
from flask import Flask
from flask import request,redirect,url_for,session,flash
from wtforms import TextField
app = Flask(__name__)
app.secret_key = "ACb12F3niJhklTg56ZDbdKbWnMKOdi"

#--------------------------------------------------------------
#                       FUNCTIONS
#--------------------------------------------------------------

# Function to check if role of a visitor is to be assigned
def isVisitor():
    if session.get('role') == None:
        session["role"]       = "visitor"
        session['modified']   = True

#--------------------------------------------------------------
#                       ROUTES
#--------------------------------------------------------------

# Route to get index page
@app.route('/', methods = ['GET'])
def hel():
    isVisitor()
    if not(session.get('username')==None):
        messages            = session['username']
    else:
        messages            = ""
    user = {'username': messages}
    return redirect(url_for('index',user=user))

# Route to get registration page
@app.route('/reg', methods = ['GET'])
def add():
    isVisitor()
    if session['role'] == 'visitor' or session['role'] == 'donor':
        return render_template('register.html')
    else:
        return redirect(url_for('index'))

# Route to add registration details
@app.route('/addrec', methods = ['POST'])
def addrec():
    isVisitor()
    try:
        if session['role'] == 'visitor':
            session['role']     = "visitor"
            session['modified'] = True
            nm      = request.form['nm']
            addr    = request.form['add']
            city    = request.form['city']
            pin     = request.form['pin']
            bg      = request.form['bg']
            email   = request.form['email']
            passs   = request.form['pass']
            with sqlite3.connect("database.db") as con:
                cur = con.cursor()
                cur.execute("INSERT INTO users (name,addr,city,pin,bg,email,pass) VALUES (?,?,?,?,?,?,?)",(nm,addr,city,pin,bg,email,passs) )
                con.commit()
        elif session['role'] == 'donor':
            nm      = request.form['nm']
            addr    = request.form['add']
            city    = request.form['city']
            pin     = request.form['pin']
            bg      = request.form['bg']
            email   = session["username"]
            passs   = request.form['pass']
            with sqlite3.connect("database.db") as con:
                cur = con.cursor()
                cur.execute("UPDATE users set name = ? ,addr = ?, city = ?, pin =?, bg = ?, email = ?, pass = ? WHERE email = ?",(nm,addr,city,pin,bg,email,passs,email) )
                con.commit()
        else:
            pass
    except KeyError as e:
        print(e)
        return redirect(url_for('index'))                                                                                       
    except Exception as e:
        print(e)
        con.rollback()
    finally:
        flash('done')
        con.close()
        return redirect(url_for('index'))
        
# Route to play with index page
@app.route('/index', methods = ['POST','GET'])
def index():
    isVisitor()
    if not(session.get('username')==None):
        messages            = session['username']
    else:
        messages            = ""
    user        = {'username': messages}
    con         = sqlite3.connect('database.db')
    con.row_factory = sqlite3.Row
    cur         = con.cursor()

    if request.method == 'POST':
        val         = request.form['search']
        formType    = request.form['type']    
        if formType == 'blood':
            cur.execute("select * from users where bg=?",(val,))
            search  = cur.fetchall()
            cur.execute("select * from users ")
            rows    = cur.fetchall()
            con.close()
            return render_template('index.html', title='Home', user=user,rows=rows,search=search)
        if formType == 'donorname':
            cur.execute("select * from users where name=?",(val,))
            search  = cur.fetchall()
            cur.execute("select * from users ")
            rows    = cur.fetchall()
            con.close()
            return render_template('index.html', title='Home', user=user,rows=rows,search=search)

    if request.method=='GET':
        cur.execute("select * from users ")
        rows = cur.fetchall()
        con.close()
        return render_template('index.html', title='Home', user=user, rows=rows)

# NOT USED
@app.route('/list')
def list():
   con = sqlite3.connect('database.db')
   con.row_factory = sqlite3.Row
   cur = con.cursor()
   cur.execute("select * from users")
   rows = cur.fetchall()
   return render_template("list.html",rows = rows)

# NOT USED
@app.route('/drop')
def dr():
    con = sqlite3.connect('database.db')
    con.execute("DROP TABLE request")
    return "dropped successfully"

# Route to perform login
@app.route('/login', methods = ['POST', 'GET'])
def login():
    isVisitor()
    if request.method == 'GET':
        return render_template('/login.html')
    if request.method == 'POST':
        email       = request.form['email']
        password    = request.form['pass']
        if email == 'admin@bloodbank.com' and password == 'admin':
            session['username']     = email
            session['admin']        = True
            session['role']         = "admin"
            session['modified']     = True
            return redirect(url_for('index'))
        elif email == "doctorRajeev@sundarhospital.com" and password == "doctor":
            session['username']     = email
            session['role']         = "doctor"
            session['doctor']       = True
            session['modified']     = True
            return redirect(url_for('index'))
        else:
            con = sqlite3.connect('database.db')
            con.row_factory = sqlite3.Row
            cur = con.cursor()
            cur.execute("select email,pass from users where email=?",(email,))
            rows = cur.fetchall()
            for row in rows:
                db_email                = row['email']
                db_password             = row['pass']
                if email == db_email and password == db_password:
                    session['username']     = db_email
                    session['logged_in']    = True
                    session['role']         = "donor"
                    session['modified']     = True
                    return redirect(url_for('index'))
                else:
                    return render_template('/login.html')
            return render_template('/login.html')
    else:
        return render_template('/')

# Route to perform logout
@app.route('/logout', methods = ['GET'])
def logout():
    isVisitor()
    try:
        session.pop('username', None)
        session.pop('logged_in', None)
        if session['role'] == "admin":
            session.pop('admin', None)
        elif session['role'] == 'doctor':
            session.pop('doctor', None)
        session['role']      = "visitor"
        session['modified']  = True
    except KeyError as e:
        print("I got a KeyError - reason " +str(e))
    return redirect(url_for('login'))

# Route to get dahboard
@app.route('/dashboard', methods = ['GET'])
def dashboard():
    isVisitor()
    try:
        if not(session['role'] == 'admin' or session['role'] == 'doctor'):
            return redirect(url_for('index'))
    except Exception as e:
        print(e)
        return redirect(url_for('index'))
    
    totalblood=0
    con             = sqlite3.connect('database.db')
    con.row_factory = sqlite3.Row
    cur             = con.cursor()
    cur.execute("select * from blood")
    rows            = cur.fetchall()
    for row in rows:
        totalblood  += int(row['qty'])
        cur.execute("select * from users")
        users       = cur.fetchall()

    Apositive   = 0
    Opositive   = 0
    Bpositive   = 0
    Anegative   = 0
    Onegative   = 0
    Bnegative   = 0
    ABpositive  = 0
    ABnegative  = 0

    cur.execute("select * from blood where type=?",('A+',))
    bloodType   = cur.fetchall()
    for a in bloodType:
           Apositive += int(a['qty'])

    cur.execute("select * from blood where type=?",('A-',))
    bloodType   = cur.fetchall()
    for a in bloodType:
        Anegative += int(a['qty'])

    cur.execute("select * from blood where type=?",('O+',))
    bloodType   = cur.fetchall()
    for a in bloodType:
        Opositive += int(a['qty'])

    cur.execute("select * from blood where type=?",('O-',))
    bloodType   = cur.fetchall()
    for a in bloodType:
        Onegative += int(a['qty'])

    cur.execute("select * from blood where type=?",('B+',))
    bloodType   = cur.fetchall()
    for a in bloodType:
        Bpositive += int(a['qty'])

    cur.execute("select * from blood where type=?",('B-',))
    bloodType   = cur.fetchall()
    for a in bloodType:
        Bnegative += int(a['qty'])

    cur.execute("select * from blood where type=?",('AB+',))
    bloodType   = cur.fetchall()
    for a in bloodType:
        ABpositive += int(a['qty'])

    cur.execute("select * from blood where type=?",('AB-',))
    bloodType   = cur.fetchall()
    for a in bloodType:
        ABnegative += int(a['qty'])
    
    bloodtypestotal = {'apos': Apositive,'aneg':Anegative,'opos':Opositive,'oneg':Onegative,'bpos':Bpositive,'bneg':Bnegative,'abpos':ABpositive,'abneg':ABnegative}
    return render_template("requestdonors.html",rows = rows,totalblood = totalblood,users=users,bloodtypestotal=bloodtypestotal)

# Route to get Add Donor page
@app.route('/bloodbank', methods=['GET'])
def bl():
    isVisitor()
    try:
        if not(session['role'] == 'doctor' or session['role'] == 'admin'):
            return redirect(url_for('index'))
        else:
            return render_template('/adddonor.html')
    except Exception as e:
        print(e)
        return redirect(url_for('index'))
    
# Route to add blood
@app.route('/addb', methods=['POST'])
def addb():
    isVisitor()
    try:
        if not(session['role'] == 'admin' or session['role'] == 'doctor'):
            return redirect(url_for('index'))
        else:
            if request.method == 'POST':
                addedEntry = False
                try:
                    bloodType   = request.form['blood_group']
                    donorname   = request.form['donorname']
                    donorsex    = request.form['gender']
                    qty         = request.form['qty']
                    dweight     = request.form['dweight']
                    email       = request.form['email']
                    phone       = request.form['phone']
                    with sqlite3.connect("database.db") as con:
                        con.row_factory = sqlite3.Row
                        cur = con.cursor()
                        cur.execute("select * from users where email=?",(email,))
                        rows = cur.fetchall()
                        if rows == []:
                            addedEntry = False
                        else:
                            for row in rows:
                                db_email    = row['email']
                                db_name     = row['name']
                                db_bg       = row['bg']
                            if db_email == email and db_bg == bloodType and db_name == donorname:
                                cur.execute("INSERT INTO blood (type,donorname,donorsex,qty,dweight,donoremail,phone) VALUES (?,?,?,?,?,?,?)",(bloodType,donorname,donorsex,qty,dweight,email,phone) )
                                con.commit()
                                addedEntry = True
                            else:
                                addedEntry = False
                except Exception as e:
                    print(e)
                    con.rollback()
                finally:
                    if addedEntry:
                        flash("Added new entry!")
                    else:
                        flash("Wrong email!")
                    con.close()
                    return redirect(url_for('dashboard'))
            else:
                return render_template("rest.html",msg="")
    except Exception as e:
        print(e)
        return redirect(url_for('index'))

# Route to edit donor blood information
@app.route("/editdonor/<id>", methods=['GET', 'POST'])
def editdonor(id):
    isVisitor()
    try:
        if not(session['role'] == 'doctor' or session['role'] == 'admin'):
            return redirect(url_for('index'))
        else:
            if request.method == 'GET':
                con             = sqlite3.connect('database.db')
                con.row_factory = sqlite3.Row
                cur             = con.cursor()
                cur.execute("select * from blood where id=?",(id,))
                rows            = cur.fetchall()
                return render_template("editdonor.html",rows = rows)
            if request.method == 'POST':
                try:
                    bloodType   = request.form['blood_group']
                    donorname   = request.form['donorname']
                    donorsex    = request.form['gender']
                    qty         = request.form['qty']
                    dweight     = request.form['dweight']
                    email       = request.form['email']
                    phone       = request.form['phone']
                    with sqlite3.connect("database.db") as con:
                        cur = con.cursor()
                        cur.execute("UPDATE blood SET type = ?, donorname = ?, donorsex = ?, qty = ?,dweight = ?, donoremail = ?,phone = ? WHERE id = ?",(bloodType,donorname,donorsex,qty,dweight,email,phone,id) )
                        con.commit()
                except Exception as e:
                    print(e)
                    con.rollback()
                finally:
                    flash('saved successfully')
                    con.close()
                    return redirect(url_for('dashboard'))
    except Exception as e:
        print(e)
        return redirect(url_for('index'))
                    
# Route to view and edit profile
@app.route("/myprofile/<email>", methods=('GET', 'POST'))
def myprofile(email):
    isVisitor()
    try:
        if not(session['role'] == 'donor'):
            return redirect(url_for('index'))
        else:
            if request.method == 'GET':
                con             = sqlite3.connect('database.db')
                con.row_factory = sqlite3.Row
                cur             = con.cursor()
                cur.execute("select * from users where email=?",(email,))
                rows            = cur.fetchall()
                return render_template("myprofile.html",rows = rows)
        
            if request.method == 'POST':
                try:
                    name    = request.form['name']
                    addr    = request.form['addr']
                    city    = request.form['city']
                    pin     = request.form['pin']
                    bg      = request.form['bg']
                    emailid = request.form['email']
                    with sqlite3.connect("database.db") as con:
                        cur = con.cursor()
                        cur.execute("UPDATE users SET name = ?, addr = ?, city = ?, pin = ?,bg = ?, email = ? WHERE email = ?",(name,addr,city,pin,bg,emailid,email) )
                        con.commit()
                except Exception as e:
                    print(e)
                    con.rollback()
                finally:
                    flash('profile saved')
                    con.close()
                    return redirect(url_for('index'))
    except Exception as e:
        print(e)
        return redirect(url_for('index'))

# Route to request for blood - > NOT USED
@app.route('/contactforblood/<emailid>', methods=['GET', 'POST'])
def contactforblood(emailid):
    isVisitor()
    if request.method == 'GET':
        conn        = sqlite3.connect('database.db')
        fromemail   = session['username']
        name        = request.form['nm']
        addr        = request.form['add']
        conn.execute("INSERT INTO request (toemail,formemail,toname,toaddr) VALUES (?,?,?,?)",(emailid,fromemail,name,addr) )
        conn.commit()
        conn.close()
        flash('request sent')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        conn        = sqlite3.connect('database.db')
        fromemail   = session['username']
        name        = request.form['nm']
        addr        = request.form['add']
        conn.execute("INSERT INTO request (toemail,formemail,toname,toaddr) VALUES (?,?,?,?)",(emailid,fromemail,name,addr) )
        conn.commit()
        conn.close()
        flash('request sent')
        return redirect(url_for('index'))

# Route to get notifications
@app.route('/notifications',methods=['GET'])
def notifications():
    isVisitor()
    try:
        if not(session['role'] == 'donor'):
            return redirect(url_for('index'))
        else:
            conn = sqlite3.connect('database.db')
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cor = conn.cursor()
            cur.execute('select * from request where toemail=?',(session['username'],))
            cor.execute('select * from request where toemail=?',(session['username'],))
            row = cor.fetchone()
            rows = cur.fetchall()
            conn.close()
            if row==None:
                return render_template('notifications.html')
            else:
                return render_template('notifications.html',rows=rows)
    except Exception as e:
        print(e)
        return redirect(url_for('index'))
            
# Route to delete a user
@app.route('/deleteuser/<useremail>', methods=['GET'])
def deleteuser(useremail):
    isVisitor()
    try:
        if not(session['role'] == 'admin'):
            return redirect(url_for('index'))
        else:
            conn = sqlite3.connect('database.db')
            cur = conn.cursor()
            cur.execute('delete from users Where email=?',(useremail,))
            flash('deleted user:' + useremail)
            conn.commit()
            conn.close()
            return redirect(url_for('dashboard'))
    except Exception as e:
        print(e)
        return redirect(url_for('index'))

# Route to delete blood entry
@app.route('/deletebloodentry/<id>', methods=['GET'])
def deletebloodentry(id):
    isVisitor()
    try:
        if not(session['role'] == 'doctor' or session['role'] == 'admin'):
            return redirect(url_for('index'))
        else:
            conn = sqlite3.connect('database.db')
            cur = conn.cursor()
            cur.execute('delete from blood Where id=?',(id,))
            flash('deleted entry:'+id)
            conn.commit()
            conn.close()
            return redirect(url_for('dashboard'))
    except:
        return redirect(url_for('index'))

# Route to delete a own account
@app.route('/deleteme/<useremail>', methods=['GET'])
def deleteme(useremail):
    isVisitor()
    try:
        if not(session['role'] == 'donor'):
            return redirect(url_for('index'))
        else:
            if useremail == session['username']:
                conn = sqlite3.connect('database.db')
                cur = conn.cursor()
                cur.execute('delete from users Where email=?',(useremail,))
                flash('deleted user:' + useremail)
                conn.commit()
                conn.close()
                session.pop('username', None)
                session.pop('logged_in',None)
                return redirect(url_for('index'))
            else:
                return redirect(url_for('index'))
    except Exception as e:
        print(e)
        return redirect(url_for('index'))

# Route to delete notification
@app.route('/deletenoti/<id>', methods=['GET'])
def deletenoti(id):
    isVisitor()
    try:
        if not(session['role'] == 'donor'):
            return redirect(url_for('index'))
        else:
            conn = sqlite3.connect('database.db')
            cur = conn.cursor()
        cur.execute('delete from request Where id=?',(id,))
        flash('deleted notification:'+id)
        conn.commit()
        conn.close()
        return redirect(url_for('notifications'))
    except:
        return redirect(url_for('index'))

if __name__ == '__main__':
    conn = sqlite3.connect('database.db')
    conn.execute('CREATE TABLE IF NOT EXISTS users (name TEXT, addr TEXT, city TEXT, pin TEXT, bg TEXT,email TEXT UNIQUE, pass TEXT)')
    conn.execute('CREATE TABLE IF NOT EXISTS blood (id INTEGER PRIMARY KEY AUTOINCREMENT, type TEXT, donorname TEXT, donorsex TEXT, qty TEXT, dweight TEXT, donoremail TEXT, phone TEXT)')
    conn.execute('CREATE TABLE IF NOT EXISTS request (id INTEGER PRIMARY KEY AUTOINCREMENT, toemail TEXT, formemail TEXT, toname TEXT, toaddr TEXT)')
    conn.execute('CREATE TABLE IF NOT EXISTS request (id INTEGER PRIMARY KEY AUTOINCREMENT, toemail TEXT, formemail TEXT, toname TEXT, toaddr TEXT)')
    conn.close()
    app.run(debug=True)
    
