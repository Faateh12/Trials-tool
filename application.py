import json
import os
from datetime import datetime

from flask import Flask, render_template, request, jsonify, flash, redirect, make_response, url_for, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from bs4 import BeautifulSoup
from flask_mail import Mail, Message
import boto3
import jwt


application = Flask(__name__, template_folder="Templates")

# AWS production uri
application.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://Faateh:Faateh123@trials-db.cwvdgyt4btit.us-east-1.rds.amazonaws.com:5432/test_db'

# development uri
#application.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:Faateh123@localhost:5432/trials_test'
application.config['SECRET_KEY'] = 'secret!'
application.config['SQLALCHEMY_ECHO'] = True
application.config['MAIL_SERVER'] = 'smtp.gmail.com'
application.config['MAIL_PORT'] = 587
application.config['MAIL_USE_TLS'] = True
application.config['MAIL_USERNAME'] = 'matsingtools@gmail.com'
application.config['MAIL_PASSWORD'] = 'lvfnjwubxveklhjc'
application.config['MAIL_DEFAULT_SENDER'] = 'matsingtools@gmail.com'
db = SQLAlchemy(application)
login_manager = LoginManager(application)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'
s3 = boto3.client('s3', region_name='us-east-1')
mail = Mail(application)

class Trials(db.Model):
    __tablename__ = 'trials'
    trial_id = db.Column(db.String(50), primary_key=True)
    trial_year = db.Column(db.String(50))
    country = db.Column(db.String(50))
    operator = db.Column(db.String(255))
    rep_company = db.Column(db.String(255))
    venue = db.Column(db.String(255))
    status = db.Column(db.String(255))
    start_date = db.Column(db.String(50))
    end_date = db.Column(db.String(50))
    result = db.Column(db.String(500))
    antenna_status = db.Column(db.String(255))
    notes = db.Column(db.String(1000))
    last_updated = db.Column(db.String(500))
    antenna_readiness_eta = db.Column(db.String(255))
    antenna_shipment_eta = db.Column(db.String(255))
    aos_status = db.Column(db.String(500))
    model_qty = db.Column(db.String(5000))
    shipped_model_serial = db.Column(db.String(500))
    po_received_date = db.Column(db.String(500))
    trial_agreement_signed_date = db.Column(db.String(500))
    stage = db.Column(db.String(500))
    try_buy = db.Column(db.String(500))
    antenna_location = db.Column(db.String(500))
    form_completion_date = db.Column(db.String(500))
    add_date = db.Column(db.String(500))
    target_integration_date = db.Column(db.String(500))

class notes(db.Model):
    __tablename__ = 'notes'
    id = db.Column(db.Integer, primary_key=True)
    note = db.Column(db.String(5000))
    trial_id = db.Column(db.String(100))
    timestamp = db.Column(db.String(100))
    user = db.Column(db.String(100))
    filename = db.Column(db.String(500))
    s3_url = db.Column(db.String(500))

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    username = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(100))



@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def verify_and_decode_token(token):
    try:
        payload = jwt.decode(token, 'secret_key', algorithms=['HS256'])
        return payload
    except jwt.InvalidTokenError:
        return None

def send_error_email(error, is_local=False):
    if is_local:
        recipients = ['faateh.work@gmail.com']
        subject = 'Error on Trials tool local host'
    else:
        recipients = ['faateh.work@gmail.com']
        subject = 'Error on Trials tool'

    msg = Message(subject, recipients=recipients)
    msg.html = render_template('error_email.html', error=error)

    mail.send(msg)

@application.errorhandler(500)
def internal_server_error(error):
    is_local = request.host == '127.0.0.1:5000'
    send_error_email(error, is_local)
    return render_template('500.html'), 500

@application.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out!', 'success')
    return redirect(url_for('login'))

def generate_next_trial_id():
    current_year = datetime.now().year
    last_two_digits = current_year % 100
    latest_ticket = Trials.query.order_by(Trials.trial_id.desc()).first()

    if latest_ticket:
        latest_year = int(latest_ticket.trial_id.split("-")[2])
        counter = int(latest_ticket.trial_id.split("-")[3])

        if latest_year == last_two_digits:
            counter += 1
        else:
            counter = 1
    else:
        counter = 1

    counter = str(counter).zfill(3)
    return f"MAT-TRI-{last_two_digits}-{counter}"



@application.route('/', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        logout_user()
        print("logged in")
        return redirect(url_for('login'))
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        # print(user.id)
        if user and user.password == password:
            login_user(user)
            return redirect(url_for('user_home'))
        else:
            print("error")
            flash('Login unsuccessful. Please check your username and password.', 'danger')
    token = request.args.get('token')  # Assuming the token is passed as a query parameter

    if token:
        payload = verify_and_decode_token(token)
        if payload:
            user_email = payload['user_email']
            user = User.query.filter_by(email=user_email).first()
            if user:
                login_user(user)
                return redirect(url_for('user_home'))
            else:
                # Handle case when the user does not exist
                # Redirect or return an error response as needed
                error = "User does not exist"
                return error
        else:
            # Handle case when the token is invalid or expired
            # Redirect or return an error response as needed
            error = "Invalid or expired token"
            return error
    # return render_template("home.html")
    response = make_response(render_template("login.html"))
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return response

@application.route("/register", methods=['GET', 'POST'])
def register():
    if request.method == "POST":
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm = request.form['confirm']
        if " " in username:
            username_parts = username.split(" ")
            username = username_parts[0]
        if password == confirm:
            user = User(
                username=username,
                email=email,
                password=password
            )
            db.session.add(user)
            db.session.commit()
            flash('You have successfully created an account!')
            return redirect(url_for('login'))
        else:
            flash('Registration unsuccessful. Passwords Do Not Match!', 'danger')
    return render_template("register.html")




@application.route('/user-home', methods=['GET', 'POST'])
@login_required
def user_home():
    current = current_user._get_current_object()
    return render_template("home.html", user=current)

@application.route('/trials', methods=['GET', 'POST'])
def trials():
    rows = Trials.query.all()
    return render_template("trials.html", rows=rows)

@application.route('/new-trial', methods=['GET', 'POST'])
def new_trial():
    if request.method == "POST":
        operator = request.form.get("operator")
        country = request.form.get("country")
        rep_company = request.form.get("rep-company")
        venue = request.form.get("venue")
        selected_date = request.form.get("date")
        parsed_date = datetime.strptime(selected_date, "%Y-%m-%d")
        formatted_date = parsed_date.strftime("%m/%d/%Y")
        trial = Trials(
            trial_id=generate_next_trial_id(),
            trial_year=datetime.now().year,
            country=country,
            operator=operator,
            rep_company=rep_company,
            venue=venue,
            start_date=formatted_date
        )
        db.session.add(trial)
        db.session.commit()
        print("sucessfully added new trial")
    return render_template("new-trial.html")

@application.route("/trial-activity/<id>", methods=['GET', 'POST'])
# @login_required
def trial_activity(id):
    current = current_user._get_current_object()
    results = notes.query.filter_by(trial_id=id).order_by(notes.id.desc()).all()
    return render_template("trial-activity.html", notes=results, trial_number=id, user=current)

@application.route("/save-activity", methods=['GET', 'POST'])
# @login_required
def save_activity():
    current = current_user._get_current_object()
    if request.method == "POST":
        note_data = request.get_json()
        print(note_data)
        note_text = note_data.get('note')
        trial_id = note_data.get('trial-id')
        timestamp = note_data.get('timestamp')
        note = notes(
            note=note_text,
            trial_id=trial_id,
            timestamp=timestamp,
            user=current.username
        )
        db.session.add(note)
        db.session.commit()
    return jsonify({'status': 'success'})


@application.route("/update-trial", methods=['GET', 'POST'])
# @login_required
def update_ticket():
    if request.method == "POST":
        data = request.json
        #print(data)
        ticket_id = data.get('id')
        field = data.get('field')
        value = data.get('value')
        soup = BeautifulSoup(value, 'html.parser')
        cleaned_value = soup.get_text()
        #print(cleaned_value)
        ticket = Trials.query.get(ticket_id)
        setattr(ticket, field, value)
        db.session.commit()
    return jsonify({'status': 'success'})

@application.route('/upload-file', methods=['GET', 'POST'])
@login_required
def upload_file():
    if request.method == "POST":
        trial_id = request.form.get('trial-id')
        timestamp = request.form.get('date')
        file = request.files['file']
        current = current_user._get_current_object()
        note = notes(
            trial_id=trial_id,
            timestamp=timestamp,
            user=current.username,
            s3_url=f'https://trials-tool-bucket.s3.amazonaws.com/{file.filename}',
            filename=file.filename
        )
        db.session.add(note)
        db.session.commit()
        extension = os.path.splitext(file.filename)[1].lower()
        print(extension)
        if extension == ".jpg" or extension == ".png" or extension == ".jpeg":
            content_type = "image/png"
        elif extension == ".pdf":
            content_type = "application/pdf"
        else:
            content_type = None
        if content_type:
            print(content_type)
            s3.put_object(
                Bucket='trials-tool-bucket',
                Key=file.filename,
                Body=file,
                ACL='public-read',
                ContentType=content_type,
                ContentDisposition='inline'
            )
        else:
            s3.put_object(
                Bucket='trials-tool-bucket',
                Key=file.filename,
                Body=file,
                ACL='public-read'
            )
    response = {"status": "success", "message": "Activity file upload"}
    json_response = json.dumps(response)
    return json_response







if __name__ == '__main__':
    application.run(debug=True)


