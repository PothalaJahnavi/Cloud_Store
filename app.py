from flask import Flask,request,redirect,render_template,url_for,session
from flask_sqlalchemy import SQLAlchemy
import bcrypt 
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app=Flask(__name__)
app.config['SECRET_KEY'] = 'mysecretkey'
app.config["SQLALCHEMY_DATABASE_URI"]="sqlite:///cloud.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db=SQLAlchemy(app)
app.app_context().push()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    email = db.Column(db.String,unique=True,nullable=False)
    password=db.Column(db.String,nullable=False)
    mynotes=db.relationship('Notes',backref="user")

    def set_password(self, password):
        self.password= generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)
    
    def __repr__(self)->str:
        return f"{self.email}-{self.id}"
    
class Notes(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title=db.Column(db.String,nullable=False)
    desc=db.Column(db.String,nullable=False)
    date=db.Column(db.Date,nullable=False)
    user_id=db.Column(db.Integer,db.ForeignKey('user.id'))

    def __repr__(self)->str:
        return f"{self.title}-{self.desc}-{self.date}"

@app.route("/")
def home():
    return render_template("home.html")


@app.route("/register",methods=["GET","POST"])
def register():
    message=''
    if request.method == 'POST':
        name = request.form['name']
        email=request.form['email']
        password = request.form['password']
        cfrmpassword=request.form['cfrmpassword']
        if User.query.filter_by(email=email).first() is not None:
            message = 'Email already taken'
            return render_template('register.html', message=message)
        else:
            if password==cfrmpassword:
                user = User(name=name,email=email)
                user.set_password(password)
                db.session.add(user)
                db.session.commit()
                session['email']=user.email
                session['user_id']=user.id
                return redirect(url_for('login'))
            else:
                message="password and confirm password should match"
                return render_template("register.html",message=message)
    return render_template("register.html")
       


@app.route("/login",methods=["GET","POST"])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        print(user)
        if user is not None and user.check_password(password):
            session['email']=user.email
            session['user_id']=user.id
            return redirect('/notes')
        else:
            error = 'Invalid username or password'
            return render_template('login.html', error=error)
    return render_template("login.html")




@app.route("/notes")
def notes():
    today=datetime.now().date()
    user_id = session.get('user_id')
    if user_id:
        all_notes=Notes.query.filter_by(user_id=user_id).all()
        return render_template("notes.html",notes=all_notes,today=today)
    else:
        return redirect("/login")

@app.route("/addNotes",methods=['GET','POST'])
def addNotes():
    if request.method=='POST':
        title=request.form["title"]
        desc=request.form["desc"]
        date=request.form["date"]
        user_id = session.get('user_id')
        today=datetime.now().date()
        cmpdate=datetime.strptime(date, '%Y-%m-%d').date()
        print(today)
        print(cmpdate)
        if cmpdate < today:
            message="Please Enter a date on or after today"
            return render_template("add.html",message=message)
        new_note=Notes(
        title=title,
        desc=desc,
        date=cmpdate,
        user_id=user_id)
        print(date)
        db.session.add(new_note)
        db.session.commit()
        return redirect("/notes")
    return render_template("add.html")
    
@app.route("/delete/<int:id>")
def delete(id):
    note=Notes.query.get_or_404(id)
    db.session.delete(note)
    db.session.commit()
    return render_template("notes.html",message="Note Deleted successfully")



@app.route("/edit/<int:id>",methods=['GET','POST'])
def edit(id):
    note=db.get_or_404(Notes,id)
    if request.method=='POST':
        myNote = Notes.query.get(id)
        title = request.form['title']
        desc = request.form['desc']
        date=request.form['date']
        myNote.title = title
        myNote.desc = desc
        myNote.date=datetime.strptime(date, '%Y-%m-%d').date()
        db.session.commit()
        return redirect("/notes")
    return render_template("edit.html",note=note)

@app.route("/logout")
def logout():
    session.pop('user_id', None)
    session.pop('email', None)
    return redirect('/login')    



if __name__=='__main__':
    app.run(debug=False,host='0.0.0.0')
