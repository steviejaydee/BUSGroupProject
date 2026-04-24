from flask import send_from_directory, render_template, request, redirect, url_for, session, flash, current_app
from flask_mail import Message
from app import app, mail
from app.forms import TriageForm, EditUserForm
from datetime import timedelta, datetime
import json
import os
import socket

# Configuration
QUEUE_FILE = 'pending_triage.json'
mydomains = ("@bham.ac.uk", "@student.bham.ac.uk")


Timeout = timedelta(days=365)
app.permanent_session_lifetime = Timeout

def is_online():
    """Checks if the server has an active internet connection."""
    try:

        socket.create_connection(("8.8.8.8", 53), timeout=2)
        return True
    except OSError:
        return False

def init_db():
    """Initializes the user database with dummy data if it doesn't exist."""
    if not os.path.exists('users.json'):
        dummy_users = [
            {"first_name": "Alice", "email": "axb3759@bham.ac.uk", "password": "password123", "role": "student"},
            {"first_name": "Bob", "email": "bxs7290@bham.ac.uk", "password": "securepass", "role": "student"},
            {"first_name": "Charlie", "email": "cxp1296@bham.ac.uk", "password": "bham2026", "role": "student"},
            {"first_name": "Stevie", "email": "sxd1008@student.bham.ac.uk", "password": "somethingwitty", "role": "student"},
            {"first_name": "admin", "email": "admin@bham.ac.uk", "password": "admin", "role": "admin"}
        ]
        with open('users.json', 'w') as f:
            json.dump(dummy_users, f, indent=4)

def send_triage_email(data):
    """Sends the triage form data via email."""
    msg = Message(
        subject=f"Triage Request: {data['name']}",
        sender=session.get('email', 'noreply@bham.ac.uk'),
        recipients=["sxd1008@student.bham.ac.uk"] 
    )
    msg.body = f"Problem: {data['problem']}\nType: {data['type']}\nAdditional: {data['addon']}"
    mail.send(msg)

def sync_pending_forms():
    """Attempts to send forms that were queued while offline."""
    if not os.path.exists(QUEUE_FILE) or not is_online():
        return

    with open(QUEUE_FILE, 'r') as f:
        try:
            pending = json.load(f)
        except json.JSONDecodeError:
            pending = []

    successful = 0
    remaining = []
    for item in pending:
        try:
            send_triage_email(item)
            successful += 1
        except Exception:
            remaining.append(item)

    with open(QUEUE_FILE, 'w') as f:
        json.dump(remaining, f, indent=4)
        
    if successful > 0:
        flash(f"Success! {successful} saved form(s) have been sent.")
    if remaining:
        flash(f"Notice: {len(remaining)} form(s) are still queued due to connection issues.")

def validtime():
    """Validates session timeout logic."""
    if 'email' not in session or 'lastchecked' not in session:
        return False
    try:
        lastchecked = datetime.fromisoformat(session['lastchecked'])
        if datetime.now() - lastchecked > Timeout:
            session.clear()
            return False
        session['lastchecked'] = datetime.now().isoformat()
        return True
    except (ValueError, KeyError):
        return False

@app.route('/')
def index():
    if 'first_name' not in session:
        flash('Please log in')
        return redirect(url_for('login'))
    
    # Check session validity
    if not validtime():
        flash('Your session has expired. Please log in again.')
        return redirect(url_for('login'))

    # Sync any pending triage forms if we are online
    sync_pending_forms()
    
    return render_template('index.html', first_name=session['first_name'])

@app.route('/login', methods=['GET', 'POST'])
def login():
    # If already logged in and session is valid, go to index
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

        # Check user database
        user = None
        with open('users.json', 'r') as f:
            users_db = json.load(f)
            for u in users_db:
                if u['email'] == email and u['password'] == password:
                    user = u
                    break
        
        if user:
            session.permanent = True
            session['email'] = user['email']
            session['first_name'] = first_name or user['first_name']
            session['lastchecked'] = datetime.now().isoformat()

            # Admin redirect
            if user['role'] == 'admin' or user['first_name'] == 'admin':
                return redirect(url_for('admin'))

            return redirect(url_for('index'))
        else:
            flash('Invalid sign in, please try again.')
            
    return render_template('login.html')

@app.route('/guest', methods=["GET", "POST"])
def guest():
    session.permanent = True
    session['email'] = 'guest'
    session['first_name'] = 'Guest'
    session['lastchecked'] = datetime.now().isoformat()
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/triage', methods=["GET", "POST"])
def triage():
    if 'first_name' not in session:
        flash('Please log in to access the support form')
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
                flash('Form submitted successfully.')
            except Exception:
                save_to_queue(data)
                flash('Mail service currently unavailable. Form saved to queue.')
        else:
            save_to_queue(data)
            flash('No connection detected. Your form will be sent when you are online.')
            
        return redirect(url_for('index'))
        
    return render_template('triage.html', form=form, GuestCheck=session.get('first_name'))

def save_to_queue(data):
    """Saves form data to a local JSON file if it cannot be sent."""
    queue = []
    if os.path.exists(QUEUE_FILE):
        with open(QUEUE_FILE, 'r') as f:
            try:
                queue = json.load(f)
            except json.JSONDecodeError:
                queue = []
    queue.append(data)
    with open(QUEUE_FILE, 'w') as f:
        json.dump(queue, f, indent=4)

@app.route('/meditation')
def meditation():
    try:
        print(session['first_name'])
    except KeyError:
        flash('Please log in to access meditation')
        return redirect(url_for('login'))

    meditations_filepath = os.path.join(current_app.root_path, "downloads")
    meditations = os.listdir(meditations_filepath)
    return render_template("meditation.html",
                           meditations = meditations)

@app.route('/resources')
def resources():
    if 'first_name' not in session:
        flash('Please log in')
        return redirect(url_for('login'))
    return render_template("resources.html")

@app.route('/emergency')
def emergency():
    return render_template("emergency.html")

@app.route('/download/<filename>', methods=["GET", "POST"])
def download(file_path, filename):
    if 'first_name' not in session:
        flash('Please log in to download')
        return redirect(url_for('login'))

    return send_from_directory(file_path, filename, as_attachment=True)

# --- Admin Routes ---

@app.route('/admin')
def admin():
    if 'first_name' not in session:
        flash('Please log in')
        return redirect(url_for('login'))

    if session.get('first_name') != 'admin':
        return redirect(url_for('index'))

    with open('users.json', 'r') as file:
        data = json.load(file)
    return render_template('admin.html', data=data)

@app.route('/edit_user/<int:row_id>', methods=["GET", "POST"])
def edit_user(row_id):
    index_to_edit = row_id - 1
    form = EditUserForm()

    if session.get('first_name') != 'admin':
        return redirect(url_for('index'))

    with open('users.json', 'r') as file:
        data = json.load(file)

    if form.validate_on_submit():
        # Update fields if data was provided in the form
        if form.first_name.data: data[index_to_edit]['first_name'] = form.first_name.data
        if form.email.data:      data[index_to_edit]['email'] = form.email.data
        if form.password.data:   data[index_to_edit]['password'] = form.password.data
        if form.role.data:       data[index_to_edit]['role'] = form.role.data

        with open('users.json', 'w') as file:
            json.dump(data, file, indent=4)

        flash(f"User {data[index_to_edit]['email']} updated.")
        return redirect(url_for('admin'))

    return render_template('edit_user.html', user_data=data[index_to_edit], form=form)

@app.route('/delete_user/<int:row_id>')
def delete_user(row_id):
    index_to_delete = row_id - 1

    if session.get('first_name') != 'admin':
        return redirect(url_for('index'))

    with open('users.json', 'r') as file:
        data = json.load(file)

    if 0 <= index_to_delete < len(data):
        deleted_user = data.pop(index_to_delete)
        with open('users.json', 'w') as file:
            json.dump(data, file, indent=4)
        flash(f"User {deleted_user['email']} deleted.")

    return redirect(url_for('admin'))

# Initialize database on startup
init_db()
