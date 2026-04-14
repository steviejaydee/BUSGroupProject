from flask import send_from_directory, render_template, request, redirect, url_for, session, flash, current_app
from flask_mail import Message
from app import app, mail
from app.forms import TriageForm
from datetime import timedelta
from datetime import datetime
import json
import os
import socket
#When testing email functionality, make sure to make a separate terminal and enter the following:
#   pip install aiosmtpd
#   python -m aiosmtpd -n -l 127.0.0.1:8025 --debug

QUEUE_FILE = 'pending_triage.json'
mydomains = ("@bham.ac.uk","@student.bham.ac.uk")
Timeout = timedelta(days=365)
app.permanent_session_lifetime = Timeout
def is_online():
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=2)
        return True
    except OSError:
        return False
def init_db():
    #creates json for user database if it does not yet exist
    if not os.path.exists('users.json'):
        dummy_users = [
            {"first_name": "Alice", "email": "axb3759@bham.ac.uk", "password": "password123", "role":"student"},
            {"first_name": "Bob", "email": "bxs7290@bham.ac.uk", "password": "securepass", "role":"student"},
            {"first_name": "Charlie", "email": "cxp1296@bham.ac.uk", "password": "bham2026", "role":"student"},
            {"first_name": "Stevie", "email": "sxd1008@student.bham.ac.uk", "password": "somethingwitty", "role": "student"},
            {"first_name": "admin", "email":"admin@bham.ac.uk", "password": "admin", "role":"admin"}
        ]
        with open('users.json', 'w') as f:
            json.dump(dummy_users, f, indent  = 4)



def send_triage_email(data):
    msg = Message(
        subject=f"Triage Request: {data['name']}",
        sender=f'{session['email']}',
        recipients=["sxd1008@student.bham.ac.uk"] #Using stevie's uni email as a placeholder.
    )
    msg.body = f"Problem: {data['problem']}\nType: {data['type']}\nAdditional: {data['addon']}"
    mail.send(msg)

def sync_pending_forms():
    if not os.path.exists(QUEUE_FILE) or not is_online():
        print('nope')
        return

    with open(QUEUE_FILE, 'r') as f:
        pending = json.load(f)
    successful = 0
    remaining = []
    for item in pending:
        try:
            send_triage_email(item)
            successful += 1
            print('sent')
        except Exception:
            remaining.append(item)

    with open(QUEUE_FILE, 'w') as f:
        json.dump(remaining, f, indent=4)
    if successful > 0:
        flash(f"Success! {successful} saved form(s) have been sent.")
    if remaining:
        flash(f"Notice: {len(remaining)} form(s) are still queued due to connection issues.")

@app.route('/')
def index():
    try:
        print(session['first_name'])
    except KeyError:
        flash('Please log in')
        return redirect(url_for('login'))


    if not validtime():
        flash('Your session has expired. Please log in again.')
        return redirect(url_for('login'))
    sync_pending_forms()
    return render_template('index.html', first_name = session['first_name'])

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
       sync_pending_forms()
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
                if u['email'] == email and  u['password'] == password: # this finds the user our database
                    user = u
                    break
        if user:
            session.permanent = True
            session['email'] = user['email']
            session['first_name'] = first_name
            session['lastchecked'] = datetime.now().isoformat() # updates the check
            #sync_pending_forms()
            return redirect(url_for('index'))
        #guessing you wanted the else in the post block - los pollos
        else:
            flash('Invalid sign in, please try again.')
    return render_template('login.html')

@app.route('/logout')
def logout():
    try:
        print(session['first_name'])
    except KeyError:
        flash('Please log in')
        return redirect(url_for('login'))

    session.clear()
    return redirect(url_for('login'))

@app.route('/triage', methods=["GET", "POST"])
def triage():
    try:
        print(session['first_name'])
    except KeyError:
        flash('Please log in')
        return redirect(url_for('login'))
    form = TriageForm()
    if form.validate_on_submit():
        dob_str = form.dob.data.strftime('%Y-%m-%d') if form.dob.data else ""
        data = {
            "name": form.name.data,
            "dob": dob_str,
            "problem": form.problem.data,
            "type": form.type.data,
            "addon": form.addon.data
        }
        if is_online():
            try:
                send_triage_email(data)
                flash('Form submitted succesfully.')
            except Exception:
                save_to_queue(data)
                flash('Mail service currently unavailiable. Please try again later.')
            return redirect(url_for('index'))
        else:
            save_to_queue(data)
            flash('No connection detected, your form will send later when there is a stable connection.')
            return redirect(url_for('index'))
    if request.method == 'POST':
        print(f"Form Errors: {form.errors}")
    return render_template('triage.html', form=form)

def save_to_queue(data):
    queue = []
    if os.path.exists(QUEUE_FILE):
        with open(QUEUE_FILE, 'r') as f:
            queue = json.load(f)
    queue.append(data)
    with open(QUEUE_FILE, 'w') as f:
        json.dump(queue, f, indent=4)
@app.route('/meditation', methods=["GET", "POST"])
def meditation():
    try:
        print(session['first_name'])
    except KeyError:
        flash('Please log in')
        return redirect(url_for('login'))

    meditations_filepath = os.path.join(current_app.root_path, "static", "meditations")
    soundscapes_filepath = os.path.join(current_app.root_path, "static", "soundscapes")
    meditations = os.listdir(meditations_filepath)
    soundscapes = os.listdir(soundscapes_filepath)
    return render_template("meditation.html", 
                           meditations = meditations, 
                           soundscapes = soundscapes, 
                           meditations_filepath = meditations_filepath, 
                           soundscapes_filepath = soundscapes_filepath)

@app.route('/resources')
def resources():
    try:
        print(session['first_name'])
    except KeyError:
        flash('Please log in')
        return redirect(url_for('login'))
    return render_template("resources.html")

@app.route('/emergency')
def emergency():
    try:
        print(session['first_name'])
    except KeyError:
        flash('Please log in')
        return redirect(url_for('login'))

    return render_template("emergency.html")

@app.route('/download/<filename>', methods=["GET", "POST"])
def download(file_path, filename):
    try:
        print(session['first_name'])
    except KeyError:
        flash('Please log in')
        return redirect(url_for('login'))

    return send_from_directory(file_path,
                               filename, 
                               as_attachment=True)


init_db()