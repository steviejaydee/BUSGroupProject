from flask import Flask, render_template, request, redirect, url_for, session, flash
from app import app
from datetime import timedelta
from datetime import datetime
import json
import os

mydomains = ("@bham.ac.uk","@student.bham.ac.uk")
Timeout = timedelta(seconds=10)
app.permanent_session_lifetime = Timeout #TEMP TEST

def init_db():
    #creates json for user database if it does not yet exist
    if not os.path.exists('users.json'):
        dummy_users = [
            {"first_name": "Alice", "email": "axb3759@bham.ac.uk", "password": "password123"},
            {"first_name": "Bob", "email": "bxs7290@bham.ac.uk", "password": "securepass"},
            {"first_name": "Charlie", "email": "cxp1296@bham.ac.uk", "password": "bham2026"}
        ]
        with open('users.json', 'w') as f:
            json.dump(dummy_users, f, indent  = 4)

@app.route('/')
def index():
    init_db()
    #Check user is logged in
    if not validtime():
        flash('Your session has expired. Please log in again.')
        return redirect(url_for('login'))
    flash(f"You have successfully logged in. Your session will be remembered for 1 year.")
    return render_template('index.html', first_name = session.get('first_name', 'Student'))

def validtime():
    if 'email' not in session or 'lastchecked' not in session:
        return False
    lastchecked = datetime.fromisoformat(session['lastchecked'])
    if datetime.now() - lastchecked > Timeout:
        session.clear()
        return False
    session['lastchecked'] = datetime.now().isoformat()
    return True

@app.route('/login', methods = ['GET', 'POST'])
def login():
    #Sees if user is logged in (directed to homepage  if so)
    if 'email' in session and validtime():
        return redirect(url_for('index'))
    if request.method == 'POST':
        first_name = request.form.get('first_name')
        email = request.form.get('email')
        password = request.form.get('password')

        if not any(email.endswith(domain) for domain in mydomains):
            flash('Use an address ending in (@bham.ac.uk or @student.bham.ac.uk)')
            return redirect(url_for('login'))

        #Check user database to see if user email and password already exist.
        user = None
        with open('users.json', 'r') as f:
            users_db = json.load(f)
            for u in users_db:
                if u['email'] == email and  u['password'] == password:
                    user = u
                    break
        if user:
            session.permanent = True
            session['email'] = user['email']
            session['first_name'] = user['first_name']
            session['lastchecked'] = datetime.now().isoformat() # updates the check
            return redirect(url_for('index'))
        #guessing you wanted the else in the post block - los pollos
        else:
            flash('Invalid sign in, please try again (maybe check your email is correct).')
    return render_template('login.html')
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/triage')
def triage():
    pass

@app.route('/meditation')
def meditation():
    pass

@app.route('/resources')
def resources():
    pass

@app.route('/emergency')
def emergency():
    pass

