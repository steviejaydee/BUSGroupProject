from flask import send_from_directory, render_template, request, redirect, url_for, session, flash, current_app
from app import app
from app.forms import TriageForm, EditUserForm
from app.email import send_email
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
            {"first_name": "Alice", "email": "axb3759@bham.ac.uk", "password": "password123", "role":"student"},
            {"first_name": "Bob", "email": "bxs7290@bham.ac.uk", "password": "securepass", "role":"student"},
            {"first_name": "Charlie", "email": "cxp1296@bham.ac.uk", "password": "bham2026", "role":"student"},
            {"first_name": "admin", "email":"admin@bham.ac.uk", "password": "admin", "role":"admin"}
        ]
        with open('users.json', 'w') as f:
            json.dump(dummy_users, f, indent  = 4)

@app.route('/')
def index():
    try:
        print(session['first_name'])
    except KeyError:
        flash('Please log in')
        return redirect(url_for('login'))

    #Check user is logged in
    #if not validtime():
        #flash('Your session has expired. Please log in again.')
        #return redirect(url_for('login'))
    #flash(f"You have successfully logged in. Your session will be remembered for 1 year.")

    return render_template('index.html', first_name = session['first_name'])

# def validtime():
# #     if 'email' not in session or 'lastchecked' not in session:
# #         return False
# #     lastchecked = datetime.fromisoformat(session['lastchecked'])
# #     if datetime.now() - lastchecked > Timeout:
# #         session.clear()
# #         return False
# #     session['lastchecked'] = datetime.now().isoformat()
#     return True

@app.route('/login', methods = ['GET', 'POST'])
def login():

    #Sees if user is logged in (directed to homepage  if so)
    # if 'email' in session and validtime():
    #    return redirect(url_for('index'))

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

            # admin check
            if user['first_name'] == 'admin':
                return redirect(url_for('admin'))

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
        flash('You are not logged in')
        return redirect(url_for('login'))

    session.clear()
    return redirect(url_for('login'))

@app.route('/triage', methods=["GET", "POST"])
def triage():
    try:
        SFN = session['first_name']
        print(SFN)
    except KeyError:
        flash('Please log in to access support form')
        return redirect(url_for('login'))
    form = TriageForm()
    if form.validate_on_submit():
        name = form.name.data
        dob = form.dob.data
        problem = form.problem.data
        therapy_type = form.type.data
        addon = form.addon.data
        send_email(
            subject = "Mental Health Support",
            sender = app.config["ADMINS"][0],
            recipients = [session['email'], "mhw@contacts.bham.ac.uk"],
            text_body = render_template(
                "triage_email.txt",
                name = name,
                dob = dob,
                problem = problem,
                therapy_type = therapy_type,
                addon = addon
            ),
            html_body = render_template(
                "triage_email.html",
                name = name,
                dob = dob,
                problem = problem,
                therapy_type = therapy_type,
                addon = addon
            )
        )

        flash(f"Form submitted successfully")
        return redirect(url_for("index"))
    return render_template("triage.html", form = form, GuestCheck = SFN)

@app.route('/meditation', methods=["GET", "POST"])
def meditation():
    try:
        print(session['first_name'])
    except KeyError:
        flash('Please log in to access meditation')
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

@app.route('/emergency')
def emergency():
    return render_template("emergency.html")

@app.route('/download/<filename>', methods=["GET", "POST"])
def download(file_path, filename):
    try:
        print(session['first_name'])
    except KeyError:
        flash('Please log in to download')
        return redirect(url_for('login'))

    return send_from_directory(file_path,
                               filename, 
                               as_attachment=True)

@app.route('/guest', methods = ["GET","POST"])
def guest():
    session.permanent = True
    session['email'] = 'guest'
    session['first_name'] = 'Guest'
    session['lastchecked'] = datetime.now().isoformat()
    return redirect(url_for('index'))
init_db()

@app.route('/admin', methods = ["GET","POST"])
def admin():
    # are they logged in?
    try:
        print(session['first_name'])
    except KeyError:
        flash('Please log in')
        return redirect(url_for('login'))

    # are they admin?
    if not session['first_name'] == 'admin':
        return redirect(url_for('index'))

    with open('users.json', 'r') as file:
        data = json.load(file)
    return render_template('admin.html', data=data)

@app.route('/edit_user/<int:row_id>', methods = ["GET","POST"])
def edit_user(row_id):
    # fix row number
    row_id -= 1
    # load form to edit on
    form = EditUserForm()

    # are they logged in?
    try:
        print(session['first_name'])
    except KeyError:
        flash('Please log in, edit_user')
        return redirect(url_for('login'))

    # are they admin?
    if not session['first_name'] == 'admin':
        return redirect(url_for('index'))

    with open('users.json', 'r') as file:
        data = json.load(file)

    if form.validate_on_submit():
        # if left empty then None, if changed then not
        first_name = form.first_name.data if form.first_name.data else None
        email = form.email.data if form.email.data else None
        password = form.password.data if form.password.data else None
        role = form.role.data if form.role.data else None

        # to iterate over
        changes_list = [first_name,email,password,role]

        # to keep track of where in our list
        i = 0
        for each in changes_list:
            # if empty, then skips over
            if each:
                match i:
                    case 0:
                        data[row_id]['first_name'] = each
                    case 1:
                        data[row_id]['email'] = each
                    case 2:
                        data[row_id]['password'] = each
                    case 3:
                        data[row_id]['role'] = each
            i+=1

        print(f'changes {data[row_id]}')
        # Write the data to the file
        with open('users.json', 'w') as file:
            # indent=4 makes the file human-readable (pretty-printed)
            json.dump(data, file, indent=4)

        return redirect(url_for('admin'))

    print('This is the ID: ',data[row_id])
    return render_template('edit_user.html', user_data=data[row_id], form=form)

@app.route('/delete_user/<int:row_id>', methods = ["GET","POST"])
def delete_user(row_id):
    # fix row number
    row_id -= 1

    # are they logged in?
    try:
        print(session['first_name'])
    except KeyError:
        flash('Please log in')
        return redirect(url_for('login'))

    # are they admin?
    if not session['first_name'] == 'admin':
        return redirect(url_for('index'))


    with open('users.json', 'r') as file:
        data = json.load(file)

    del data[row_id]
    print(data)

    # Write the data to the file
    with open('users.json', 'w') as file:
        # indent=4 makes the file human-readable (pretty-printed)
        json.dump(data, file, indent=4)

    return redirect(url_for('admin'))