from flask import Flask, render_template, request, redirect, flash, session
from flask_debugtoolbar import DebugToolbarExtension
from models import connect_db, db, User
from forms import UserForm, LoginForm

app = Flask(__name__)


app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql:///auth_app"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = True
app.config["SECRET_KEY"] = "abc123"
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False

toolbar = DebugToolbarExtension(app)

connect_db(app)


@app.route("/")
def base():
    """redirects to register page"""

    return redirect("/register")

@app.route("/register", methods=["GET", "POST"])
def register():
    """register user"""
    
    form = UserForm()
    
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        email = form.email.data
        first_name = form.first_name.data
        last_name = form.last_name.data
            
        user = User.register(username, password, email, first_name, last_name)
        db.session.add(user)
        db.session.commit()
        session["username"] = user.username
        flash("Welcome! Successfully Created Your Account!", "success")
        return redirect('/users/<username>')
    else:
        return render_template("register.html", form=form)
    
@app.route("/login", methods=["GET", "POST"])
def login():
    """login user"""
    
    form = LoginForm()
    
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        
        user = User.authenticate(username, password)
        
        if user:
            session["username"] = user.username
            flash("Welcome Back!", "success")
            return redirect("/users/<username>")
        else:
            form.username.errors = ["Invalid username/password."]
            return render_template("login.html", form=form)
    else:
        return render_template("login.html", form=form)
    
@app.route("/users/<username>")
def show_user(username):
    """Shows user info"""
    
    if "username" not in session:
        flash("Please login first!", "danger")
        return redirect("/login")
    else:
        username = session["username"]
        user = User.query.filter_by(username=username).first()
        return render_template("user.html", user=user)


    
    
@app.route("/logout")
def logout():
    """logout user"""
    
    session.pop("username")
    flash("Goodbye!", "info")
    return redirect("/")

    
@app.route("/secret")
def secret():
    """secret page for logged in users"""
    
    if "username" not in session:
        flash("Please login first!", "danger")
        return redirect("/login")
    else:
        return render_template("secret.html")



  







