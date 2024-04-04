from flask import Flask, render_template, redirect, jsonify, session, flash
from flask_debugtoolbar import DebugToolbarExtension
from models import db, connect_db, User, Feedback
from sqlalchemy import text
from forms import RegisterForm, LoginForm, FeedbackForm

app = Flask(__name__)
app.debug = True

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///login_app_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
app.config['SQLALCHEMY_ECHO'] = False
app.config['SECRET_KEY'] = 'isasecret'
debug = DebugToolbarExtension(app)

connect_db(app)

# USER ROUTES
@app.route('/')
def home_page():
    return render_template('users/index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """ Register user: produce form & handle form submission"""
    form = RegisterForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        email = form.email.data
        first_name = form.first_name.data
        last_name = form.last_name.data

        user = User.register(username, password, email, first_name, last_name)

        db.session.add(user)
        db.session.commit()

        session['username'] = user.username
        
        flash('Successfully registered and logged in!')
        return redirect(f'/users/{user.username}')
    
    return render_template('users/register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Produce login form or handle login."""

    form = LoginForm()

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        user = User.authenticate(username, password)

        if user:
            session['username'] = user.username
            return redirect(f'/users/{user.username}')

        else:
            form.username.errors = ['Invalid Login Information']
 
    return render_template('users/login.html', form=form)


@app.route('/logout')
def logout():
    session.pop('username')
    flash('You have been logged out!')

    return redirect('/login')


@app.route('/users/<username>')
def show_user_info(username):
    """User information page for logged in users only."""

    if 'username' in session and session['username'] == username:
        user = User.query.filter_by(username=username).first_or_404()
        feedback = Feedback.query.filter(Feedback.username == username).all()
        form = FeedbackForm()

        return render_template('users/show.html', user=user, feedback=feedback, form=form)
    else:  
        return redirect('/login')

@app.route('/users/<username>/delete', methods = ['POST'])
def delete_user(username):
    if 'username' in session and session['username'] == username:
        user = User.query.get(username)
        db.session.delete(user)
        db.session.commit()
        session.pop('username')

        flash('Your account has been deleted!')
        return redirect('/login')
    
    else:
        flash('Error! User does not exist!')
        return redirect('/users/<username>')




# FEEDBACK ROUTES
@app.route('/users/<username>/feedback/add', methods = ['GET', 'POST'])
def add_feedback(username):

    if 'username' in session and session['username'] == username:
        form = FeedbackForm()
        if form.validate_on_submit():
            title = form.title.data
            content = form.content.data
            
            feedback = Feedback(title=title, content=content, username=username)
            db.session.add(feedback)
            db.session.commit()

            return redirect(f'/users/{feedback.username}')
        return render_template('feedbacks/new.html', form=form, username=username)
    
    else:
        return redirect('/login')

@app.route('/feedback/<int:feedback_id>/update', methods = ['GET', 'POST'])
def update_feedback(feedback_id):
    feedback = Feedback.query.get_or_404(feedback_id)
    if 'username' in session and session['username'] == feedback.username:
        form = FeedbackForm(obj=feedback)
        if form.validate_on_submit():
            feedback.title = form.title.data
            feedback.content = form.content.data
            
            db.session.add(feedback)
            db.session.commit()

            return redirect(f'/users/{feedback.username}')
        return render_template('feedbacks/update.html', form=form, feedbacke=feedback)
    
    else:
        return redirect('/login')

@app.route('/feedback/<int:feedback_id>/delete', methods = ['POST'])
def delete_feedback(feedback_id):
    feedback = Feedback.query.get_or_404(feedback_id)
    if 'username' in session and session['username'] == feedback.username:
        db.session.delete(feedback)
        db.session.commit()

        flash('Feedback has been deleted!')
        return redirect(f'/users/{feedback.username}')
    
    else:
        flash('You must be logged in!')
        return redirect('/login')
