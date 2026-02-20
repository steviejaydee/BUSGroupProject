from flask import Flask, render_template, request, redirect, url_for, session, flash
from app import app
from datetime import timedelta

app.permanent_session_lifetime = timedelta(days = 365)

@app.route('/')
def index():
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

        #Making sure email ends with the correct domain for UoB (it also makes sure everything is filled in but the form requires this anyways, may not be essential?):
        if first_name and email and email.endswith('@student.bham.ac.uk') and password:
            #Establish a permanent session (persists between session) so user is logged out automatically after a year:
            session.permanent = True
            session['email'] = email
            session ['first_name'] = first_name
            return redirect(url_for('index'))
    else:
        flash('Invalid sign in, please try again (maybe check your email is correct).')
    return render_template('login.html')
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))
