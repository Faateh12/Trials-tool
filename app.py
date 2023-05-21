from datetime import datetime

from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user


app = Flask(__name__, template_folder="Templates")

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:Faateh123@localhost:5432/trials_test'
app.config['SECRET_KEY'] = 'secret!'
app.config['SQLALCHEMY_ECHO'] = True
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

class Trials(db.Model):
    __tablename__ = 'trials'
    trial_id = db.Column(db.String(50), primary_key=True)
    date = db.Column(db.String(50))
    company = db.Column(db.String(255))
    model_number = db.Column(db.String(50))

class notes(db.Model):
    __tablename__ = 'notes'
    id = db.Column(db.Integer, primary_key=True)
    note = db.Column(db.String(5000))
    ticket_id = db.Column(db.String(100))
    timestamp = db.Column(db.String(100))
    user = db.Column(db.String(100))

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    username = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(100))

with app.app_context():
    # Create the tables
    db.create_all()


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def generate_next_trial_id():
    current_year = datetime.now().year
    latest_ticket = Trials.query.order_by(Trials.trial_id.desc()).first()
    if latest_ticket:
        latest_year = int(latest_ticket.trial_id.split("-")[2])
        if current_year == latest_year:
            counter = int(latest_ticket.trial_id.split("-")[3])
            counter += 1
            counter = str(counter).zfill(3)
            return f"MAT-TRI-{current_year}-{counter}"
    return f"MAT-TRI-{current_year}-000"


# @app.route('/', methods=['GET', 'POST'])
# def home():
#     return render_template("home.html")


@app.route('/', methods=['GET', 'POST'])
def dashboard():
    return render_template("dash.html")

@app.route('/trials', methods=['GET', 'POST'])
def trials():
    rows = Trials.query.all()
    return render_template("trials.html", rows=rows)

@app.route('/new-trial', methods=['GET', 'POST'])
def new_trial():
    return render_template("new-trial.html")



if __name__ == '__main__':
    app.run(debug=True)


