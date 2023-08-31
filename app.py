from flask import Flask, render_template, request, redirect, flash, session, url_for
from flask_debugtoolbar import DebugToolbarExtension
from models import connect_db, db, User, Feedback, Token
from forms import UserForm, LoginForm, FeedbackForm
import secrets
from flask_mail import Mail, Message
from sqlalchemy.exc import IntegrityError


app = Flask(__name__)


app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql:///auth_app"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = True
app.config["SECRET_KEY"] = "abc123"
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_DEFAULT_SENDER'] = 'danielrhodes47@gmail.com'
app.config['MAIL_USERNAME'] = 'danielrhodes47@gmail.com'
app.config['MAIL_PASSWORD'] = 'zexwizeccdaixqje'


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

    mail = Mail(app)

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        email = form.email.data
        first_name = form.first_name.data
        last_name = form.last_name.data

        user = User.register(username, password, email,
                             first_name, last_name)
        validation_token = Token(
            token=secrets.token_urlsafe(16), username=username)
        db.session.add(user)
        db.session.add(validation_token)
        db.session.commit()

        verification_url = url_for(
            "validate_token", username=username, token=validation_token.token, _external=True)

        msg = Message(
            "Welcome to my app! Please confirm you're human.", recipients=[email])
        msg.html = render_template(
            "validation_email.html", verification_url=verification_url)
        mail.send(msg)

        return render_template("verify_email.html", username=username)
    else:
        return render_template("register.html", form=form)


@app.route("/validate_token/<username>/<token>")
def validate_token(username, token):
    """Validate user's email token"""

    token_record = Token.query.filter_by(token=token).first()
    if not token_record or token_record.username != username:
        flash("Invalid token!", "danger")
        return redirect("/login")

    user = User.query.filter_by(username=username).first()
    if user:
        user.email_verified = True
        db.session.commit()

    db.session.delete(token_record)
    db.session.commit()

    flash("Email verified! You can now log in.", "success")

    return redirect("/login")


@app.route("/login", methods=["GET", "POST"])
def login():
    """login user"""

    form = LoginForm()

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        user = User.authenticate(username, password)

        if user:
            if user.email_verified:
                session["username"] = user.username
                flash(f"Welcome back, {user.username}!", "success")
                return redirect(f"/users/{user.username}")
            else:
                flash("Please verify your email before logging in.", "danger")
                return redirect("/login")
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
        feedbacks = Feedback.query.filter_by(username=username).all()
        return render_template("user.html", user=user, feedbacks=feedbacks)


@app.route("/users/<username>/delete", methods=["POST"])
def delete_user(username):
    """Deletes user"""

    if "username" not in session:
        flash("Please login first!", "danger")
        return redirect("/login")
    else:
        username = session["username"]
        feedback = Feedback.query.filter_by(username=username).all()
        for fb in feedback:
            db.session.delete(fb)
        user = User.query.filter_by(username=username).first()

        # Delete associated tokens for the user
        tokens = Token.query.filter_by(username=username).all()
        for token in tokens:
            db.session.delete(token)

        db.session.delete(user)
        db.session.commit()
        session.pop("username")
        flash("User Deleted!", "info")
        return redirect("/")


@app.route(f"/users/<username>/feedback/add", methods=["GET", "POST"])
def add_feedback(username):
    """Adds feedback"""

    if "username" not in session:
        flash("Please login first!", "danger")
        return redirect("/login")
    else:
        form = FeedbackForm()

        if form.validate_on_submit():
            title = form.title.data
            content = form.content.data
            username = session["username"]

            feedback = Feedback(
                title=title, content=content, username=username)
            db.session.add(feedback)
            db.session.commit()
            flash("Feedback Added!", "success")
            return redirect(f"/users/{username}")
        else:
            return render_template("feedback.html", form=form)


@app.route("/feedback/<int:feedback_id>/update", methods=["GET", "POST"])
def update_feedback(feedback_id):
    """Updates feedback"""

    if "username" not in session:
        flash("Please login first!", "danger")
        return redirect("/login")
    else:
        feedback = Feedback.query.get_or_404(feedback_id)
        form = FeedbackForm(obj=feedback)

        if form.validate_on_submit():
            feedback.title = form.title.data
            feedback.content = form.content.data
            db.session.commit()
            flash("Feedback Updated!", "success")
            return redirect(f"/users/{feedback.username}")
        else:
            return render_template("update_feedback.html", form=form, feedback=feedback)


@app.route("/feedback/<int:feedback_id>/delete", methods=["POST"])
def delete_feedback(feedback_id):
    """Deletes feedback"""

    if "username" not in session:
        flash("Please login first!", "danger")
        return redirect("/login")
    else:
        feedback = Feedback.query.get_or_404(feedback_id)
        db.session.delete(feedback)
        db.session.commit()
        flash("Feedback Deleted!", "info")
        return redirect(f"/users/{feedback.username}")


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
