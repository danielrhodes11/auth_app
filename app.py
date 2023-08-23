from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_debugtoolbar import DebugToolbarExtension
from models import connect_db, db, User
from forms import UserForm

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
        return redirect('/secret')
    else:
        return render_template("register.html", form=form)


  







