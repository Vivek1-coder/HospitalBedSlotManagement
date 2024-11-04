from flask import Flask,redirect,render_template,request,flash,session
from flask_sqlalchemy import SQLAlchemy
from flask.helpers import url_for
from flask_login import UserMixin
from flask_login import login_required, logout_user,login_user,login_manager,LoginManager,current_user
from werkzeug.security import generate_password_hash,check_password_hash
from sqlalchemy import text
from sqlalchemy.orm import Session
import json
from flask_mail import Mail

# mydatabase connection 
local_server=True
app=Flask(__name__)
app.secret_key="vivekyadav"

with open('config.json','r') as c:
    params = json.load(c)["params"]

app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT='465',
    MAIL_USE_SSL=True,
    MAIL_USERNAME=params['gmail-user'],
    MAIL_PASSWORD=params['gmail-password']
)
mail = Mail(app)

# this is for getting the unique user access
login_manager=LoginManager(app)
login_manager.login_view="login"

# app.config["SQLALCHEMY_DATABASE_URI"] = 'mysql://username:password@localhost/databasename'
app.config["SQLALCHEMY_DATABASE_URI"] = 'mysql://root:@localhost/covid'
db = SQLAlchemy(app)




@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id)) or Hospitaluser.query.get(int(user_id))


class Test(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(50))

class User(UserMixin,db.Model):
    id = db.Column(db.Integer,primary_key=True)
    srfid = db.Column(db.String(20),unique=True)
    email = db.Column(db.String(100))
    dob = db.Column(db.String(1000))

class Hospitaluser(UserMixin,db.Model):
    id = db.Column(db.Integer,primary_key=True)
    hcode = db.Column(db.String(20))
    email = db.Column(db.String(100))
    password = db.Column(db.String(1000))

class Hospitaldata(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    hcode = db.Column(db.String(200),unique=True)
    hname = db.Column(db.String(200))
    normalbed = db.Column(db.Integer)
    hicubed = db.Column(db.Integer)
    icubed = db.Column(db.Integer)
    vbed = db.Column(db.Integer)
    
class Trig(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    hcode = db.Column(db.String(200))
    normalbed = db.Column(db.Integer)
    hicubed = db.Column(db.Integer)
    icubed = db.Column(db.Integer)
    vbed = db.Column(db.Integer)
    querys = db.Column(db.String(50))
    date = db.Column(db.String(50))
    
class Bookingpatient(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    srfid = db.Column(db.String(50),unique=True)
    bedtype = db.Column(db.String(50))
    hcode = db.Column(db.String(50))
    spo2 = db.Column(db.Integer)
    pname = db.Column(db.String(50))
    pphone = db.Column(db.String(50))
    paddress = db.Column(db.String(100))
    
    


@app.route("/")
def home():
    return render_template("index.html")

# @app.route("/usersignup")
# def usersignup():
#     return render_template("usersignup.html")


# @app.route("/userlogin")
# def userlogin():
#     return render_template("userlogin.html")

@app.route("/trigers")
def trigers():
    query=Trig.query.all() 
    return render_template("trigers.html",query=query)


@app.route('/signup', methods=['POST', 'GET'])
def signup():
    if request.method == "POST":
        srfid = request.form.get('srf')
        email = request.form.get('email')
        dob = request.form.get('dob')
        
        # Generate hashed password
        encpassword = generate_password_hash(dob)
        user = User.query.filter_by(srfid=srfid).first()
        if user : 
            flash("Srif id has already been taken","warning")
            return render_template("usersignup.html")
        # Safely execute insert query with parameterized SQL
        with Session(db.engine) as session:
            query = text("INSERT INTO `user` (`srfid`, `email`, `dob`) VALUES (:srfid, :email, :dob)")
            session.execute(query, {"srfid": srfid, "email": email, "dob": encpassword})
            session.commit()  # Commit the transaction to save changes
        
        flash("SignIn success Please login","success")
        return render_template("userlogin.html")
        

    return render_template("usersignup.html")


@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == "POST":
        srfid = request.form.get('srf')
        dob = request.form.get('dob')
        user=User.query.filter_by(srfid=srfid).first()

        if user and check_password_hash(user.dob,dob):
            login_user(user)
            flash("Login success","info")
            return redirect("/slotbooking")
        else : 
            flash("Invalid Credentials","danger")
            return render_template("userlogin.html")
        
    return render_template("userlogin.html")


@app.route('/admin', methods=['POST', 'GET'])
def admin():
    if request.method == "POST":
        username = request.form.get('username')
        password = request.form.get('password')
        if(username == params['user'] and password == params['password']):
            session['user'] = username
            flash("Login successful","info")
            return render_template("addHosUser.html")
        else:
            flash("Invalid Credentials","danger")
            return render_template("admin.html")

    return render_template("admin.html")


@app.route('/addHospitalUser', methods=['POST', 'GET'])
def addHospitalUser():
    if 'user' in session and session['user'] == params['user']:
        if request.method == "POST":
            hcode = request.form.get('hcode')
            email = request.form.get('email')
            password = request.form.get('password')
            hcode = hcode.upper()
            # Generate hashed password
            encpassword = generate_password_hash(password)
            user = Hospitaluser.query.filter_by(email=email).first()
            if user:
                flash("Email already exists", "warning")
                return render_template("admin.html")

            # Renaming `session` to avoid conflict with Flask `session`
            with Session(db.engine) as db_session:
                query = text("INSERT INTO `hospitaluser` (`hcode`, `email`, `password`) VALUES (:hcode, :email, :password)")
                db_session.execute(query, {"hcode": hcode, "email": email, "password": encpassword})
                db_session.commit()  # Commit the transaction to save changes

            flash("Data Inserted", "success")
            return render_template("addHosUser.html")
    else:
        flash("login and try again", "warning")
        return redirect('/admin')
    

@app.route('/hospitallogin', methods=['POST', 'GET'])
def hospitallogin():
    if request.method == "POST":
        email = request.form.get('email')
        password = request.form.get('password')
        user= Hospitaluser.query.filter_by(email=email).first()

        if user and check_password_hash(user.password,password):
            login_user(user)
            flash("Login success","info")
            return redirect('/addhospitalinfo')
        else : 
            flash("Invalid Credentials","danger")
            return render_template("hospitallogin.html")
        
    return render_template("hospitallogin.html")



@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Logout Successful","warning")
    return redirect('/')

@app.route('/logoutadmin')
def logoutadmin():
    session.pop('user')
    flash("Admin Logged out","warning")
    return redirect('/admin')

# login_manager.login_view="hospitallogin"

@app.route("/addhospitalinfo",methods=['POST','GET'])
def addhospitalinfo():
    email=current_user.email
    posts=Hospitaluser.query.filter_by(email=email).first()
    code=posts.hcode
    postsdata=Hospitaldata.query.filter_by(hcode=code).first()

    if request.method=="POST":
        hcode=request.form.get('hcode')
        hname=request.form.get('hname')
        nbed=request.form.get('normalbed')
        hbed=request.form.get('hicubeds')
        ibed=request.form.get('icubeds')
        vbed=request.form.get('ventbeds')
        hcode=hcode.upper()
        huser=Hospitaluser.query.filter_by(hcode=hcode).first()
        hduser=Hospitaldata.query.filter_by(hcode=hcode).first()
        if hduser:
            flash("Data is already Present you can update it..","primary")
            return render_template("hospitaldata.html")
        if huser:            
            # db.engine.execute(f"INSERT INTO `hospitaldata` (`hcode`,`hname`,`normalbed`,`hicubed`,`icubed`,`vbed`) VALUES ('{hcode}','{hname}','{nbed}','{hbed}','{ibed}','{vbed}')")
            query=Hospitaldata(hcode=hcode,hname=hname,normalbed=nbed,hicubed=hbed,icubed=ibed,vbed=vbed)
            db.session.add(query)
            db.session.commit()
            flash("Data Is Added","primary")
            return redirect('/addhospitalinfo')
            

        else:
            flash("Hospital Code not Exist","warning")
            return redirect('/addhospitalinfo')

    return render_template("hospitaldata.html",postsdata=postsdata or {})
    # return render_template("hospitaldata.html",postsdata=postsdata)

@app.route("/hedit/<string:id>",methods=['POST','GET'])
@login_required
def hedit(id):
    if request.method=="POST":
        hcode=request.form.get('hcode').upper()
        hname=request.form.get('hname')
        nbed=request.form.get('normalbed')
        hbed=request.form.get('hicubeds')
        ibed=request.form.get('icubeds')
        vbed=request.form.get('ventbeds')
        post = Hospitaldata.query.get(id)
        query = text("UPDATE hospitaldata SET hcode=:hcode, hname=:hname, normalbed=:nbed, hicubed=:hbed, icubed=:ibed, vbed=:vbed WHERE id=:id")
        db.session.execute(query,{"hcode": hcode, "hname": hname, "nbed": nbed, "hbed": hbed, "ibed": ibed, "vbed": vbed, "id": id})
        db.session.commit()  # Commit the updates to the database
        flash("Slot Updated", "danger")
        return redirect('/addhospitalinfo') 
    posts=Hospitaldata.query.filter_by(id = id).first()
    return render_template("hedit.html",posts=posts)

@app.route("/hdelete/<string:id>",methods=['POST','GET'])
@login_required
def hdelete(id):
    post = Hospitaldata.query.get_or_404(id)
    
    # Delete the record
    db.session.delete(post)
    db.session.commit()
    # Flash a message and redirect
    flash("Hospital data deleted successfully", "danger")
    return redirect('/addhospitalinfo')
   
@app.route("/pdetails",methods=['GET'])
@login_required
def pdetails():
    code=current_user.srfid
    print(code)
    data=Bookingpatient.query.filter_by(srfid=code).first()
    return render_template("details.html",data=data)



@app.route("/test")
@login_required  # Ensure only logged-in users can access this route
def test():
    # Check if the user is authenticated before accessing `email`
    if current_user.is_authenticated:
        ema = current_user.email
        print(ema)
    else:
        flash("Please log in to access this page.", "warning")
        return redirect('/hospitallogin')  # Redirect to login if not authenticated

    try:
        a = Test.query.all()
        print(a)
        return f'My Database is connected mai {a[1]}'
    except Exception as e:
        print(e)
        return "My Database is not Connected"


@app.route("/slotbooking", methods=['POST', 'GET'])
@login_required
def slotbooking():
    query1 = Hospitaldata.query.all()
    query = Hospitaldata.query.all()

    if request.method == "POST":
        srfid = request.form.get('srfid')
        bedtype = request.form.get('bedtype')
        hcode = request.form.get('hcode')
        spo2 = request.form.get('spo2')
        pname = request.form.get('pname')
        pphone = request.form.get('pphone')
        paddress = request.form.get('paddress')  

        check2 = Hospitaldata.query.filter_by(hcode=hcode).first()
        checkpatient = Bookingpatient.query.filter_by(srfid=srfid).first()

        if checkpatient:
            flash("This SRF ID is already registered.", "warning")
            return render_template("booking.html", query=query, query1=query1)
        
        if not check2:
            flash("Hospital Code does not exist.", "warning")
            return render_template("booking.html", query=query, query1=query1)

        dbb = Hospitaldata.query.filter_by(hcode=hcode).first()
        
        if dbb:
            if bedtype == "NormalBed" and dbb.normalbed > 0:
                dbb.normalbed -= 1
            elif bedtype == "HICUBed" and dbb.hicubed > 0:
                dbb.hicubed -= 1
            elif bedtype == "ICUBed" and dbb.icubed > 0:
                dbb.icubed -= 1
            elif bedtype == "VENTILATORBed" and dbb.vbed > 0:
                dbb.vbed -= 1
            else:
                flash("Selected bed type is not available.", "danger")
                return render_template("booking.html", query=query, query1=query1)

            db.session.commit()

            # Add booking data if seat is available
            res = Bookingpatient(srfid=srfid, bedtype=bedtype, hcode=hcode, spo2=spo2, pname=pname, pphone=pphone, paddress=paddress)
            db.session.add(res)
            db.session.commit()
            flash("Slot is booked. Kindly visit the hospital for further procedure.", "success")
            return render_template("booking.html", query=query, query1=query1)
        else:
            flash("Please provide a valid hospital code.", "info")
            return render_template("booking.html", query=query, query1=query1)

    return render_template("booking.html", query=query, query1=query1)





app.run(debug=True)