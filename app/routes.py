from flask import Flask, render_template, request, redirect, url_for, session, flash
from app import app
from datetime import timedelta
import json
import os


app.permanent_session_lifetime = timedelta(days = 365)
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
    if 'email' not in session:
        return redirect(url_for('login'))
    return render_template('index.html', first_name = session.get('first_name', 'Student'))

@app.route('/login', methods = ['GET', 'POST'])
def login():
    #Sees if user is logged in (directed to homepage  if so)
    if 'email' in session:
        return redirect(url_for('index'))
    if request.method == 'POST':
        first_name = request.form.get('first_name')
        email = request.form.get('email')
        password = request.form.get('password')

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
            return redirect(url_for('index'))
    else:
        flash('Invalid sign in, please try again (maybe check your email is correct).')
    return render_template('login.html')
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))
