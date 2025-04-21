from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import date
from functools import wraps
from sqlalchemy import or_
import io
import pandas as pd
import traceback

app = Flask(__name__)
app.secret_key = 'secretkey123'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tpo.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)

# ==================== MODELS ====================
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(10), nullable=False)

class StudentProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    name = db.Column(db.String(100))
    dob = db.Column(db.String(20))
    gender = db.Column(db.String(10))
    year_drop = db.Column(db.String(10))
    marks_10 = db.Column(db.Float)
    marks_12 = db.Column(db.Float)
    cgpa = db.Column(db.Float)
    backlog = db.Column(db.String(10))
    percentage = db.Column(db.Float)
    is_placed = db.Column(db.Boolean, default=False)

class Company(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    min_cgpa = db.Column(db.Float)
    backlog_allowed = db.Column(db.String(10))
    gender = db.Column(db.String(10))
    description = db.Column(db.Text)
    visit_date = db.Column(db.Date)

class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student_profile.id'))
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'))
    __table_args__ = (db.UniqueConstraint('student_id', 'company_id', name='unique_application'),)

# ==================== HELPERS ====================
def get_logged_in_student():
    if 'user_id' in session:
        return StudentProfile.query.filter_by(user_id=session['user_id']).first()
    return None

def login_required(role=None):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session or (role and session.get('role') != role):
                flash('Please log in to access this page.', 'warning')
                return redirect(url_for('login'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# ==================== ROUTES ====================
@app.route('/')
def home():
    return render_template('landing.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']
        hashed_password = generate_password_hash(password)

        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'danger')
            return redirect(url_for('signup'))

        db.session.add(User(username=username, password=hashed_password, role=role))
        db.session.commit()
        flash('Signup successful. Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']

        try:
            user = User.query.filter_by(username=username, role=role).first()
            if user and check_password_hash(user.password, password):
                session['user_id'] = user.id
                session['role'] = user.role
                flash('Login successful', 'success')
                return redirect(url_for('student_dashboard' if role == 'student' else 'tpo_dashboard'))
            else:
                flash('Invalid credentials', 'danger')
        except Exception as e:
            traceback.print_exc()
            flash('Server error during login', 'danger')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))

@app.route('/student_dashboard', methods=['GET', 'POST'])
@login_required(role='student')
def student_dashboard():
    student = get_logged_in_student()

    if request.method == 'POST':
        if not student:
            student = StudentProfile(user_id=session['user_id'])
            db.session.add(student)

        try:
            student.name = request.form['name']
            student.dob = request.form['dob']
            student.gender = request.form['gender']
            student.year_drop = request.form['year_drop']
            student.marks_10 = float(request.form['marks_10'])
            student.marks_12 = float(request.form['marks_12'])
            student.cgpa = float(request.form['cgpa'])
            student.backlog = request.form['backlog']
            student.percentage = round((student.cgpa / 10) * 100, 2)
        except Exception as e:
            flash('Invalid input. Please enter valid numbers.', 'danger')
            return redirect(url_for('student_dashboard'))

        db.session.commit()
        flash('Profile updated.', 'success')
        return redirect(url_for('student_dashboard'))

    applied_ids = [a.company_id for a in Application.query.filter_by(student_id=student.id).all()] if student else []
    applied_companies = Company.query.filter(Company.id.in_(applied_ids)).all()
    all_companies = Company.query.all()
    upcoming_companies = Company.query.filter(Company.visit_date >= date.today()).all()

    eligible_companies = [
        c for c in upcoming_companies
        if student and student.cgpa >= c.min_cgpa
        and (c.backlog_allowed == 'Yes' or student.backlog == 'No')
        and (c.gender == 'All' or c.gender == student.gender)
        and c.id not in applied_ids
    ]

    return render_template(
        'student_dashboard.html',
        student=student,
        applied_companies=applied_companies,
        eligible_companies=eligible_companies,
        all_companies=all_companies,
        upcoming_companies=upcoming_companies
    )

@app.route('/tpo')
@login_required(role='tpo')
def tpo_dashboard():
    query = StudentProfile.query
    cgpa_min = request.args.get('cgpa_min', type=float)
    cgpa_max = request.args.get('cgpa_max', type=float)
    backlog = request.args.get('backlog')

    if cgpa_min is not None:
        query = query.filter(StudentProfile.cgpa >= cgpa_min)
    if cgpa_max is not None:
        query = query.filter(StudentProfile.cgpa <= cgpa_max)
    if backlog in ['Yes', 'No']:
        query = query.filter_by(backlog=backlog)

    students = query.all()
    return render_template('tpo_dashboard.html', students=students)


@app.route('/apply/<int:company_id>', methods=['POST'])
@login_required(role='student')
def apply_company(company_id):
    student = get_logged_in_student()
    if not student:
        flash('Student profile not found.', 'danger')
        return redirect(url_for('student_dashboard'))

    try:
        db.session.add(Application(student_id=student.id, company_id=company_id))
        db.session.commit()
        flash('Applied successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Already applied or error occurred.', 'warning')
    return redirect(url_for('student_dashboard'))

@app.route('/eligible_students')
@login_required(role='tpo')
def eligible_students():
    companies = Company.query.all()
    eligible_data = []

    for company in companies:
        eligible_students = StudentProfile.query.filter(
            StudentProfile.cgpa >= company.min_cgpa,
            (StudentProfile.backlog == 'No') | (company.backlog_allowed == 'Yes'),
                       or_(company.gender == 'All', StudentProfile.gender == company.gender)
        ).all()
        eligible_data.append((company, eligible_students))

    return render_template('eligible_students.html', eligible_data=eligible_data)

@app.route('/students_placed')
@login_required(role='tpo')
def students_placed():
    placed_students = StudentProfile.query.filter_by(is_placed=True).all()
    return render_template('students_placed.html', students=placed_students)

@app.route('/export')
@login_required(role='tpo')
def export_excel():
    query = StudentProfile.query
    cgpa_min = request.args.get('cgpa_min', type=float)
    cgpa_max = request.args.get('cgpa_max', type=float)
    backlog = request.args.get('backlog')

    if cgpa_min is not None:
        query = query.filter(StudentProfile.cgpa >= cgpa_min)
    if cgpa_max is not None:
        query = query.filter(StudentProfile.cgpa <= cgpa_max)
    if backlog in ['Yes', 'No']:
        query = query.filter_by(backlog=backlog)

    students = query.all()

    data = []
    for s in students:
        user = User.query.get(s.user_id)
        data.append({
            'Username': user.username,
            'Name': s.name,
            'DOB': s.dob,
            'Gender': s.gender,
            '10th Marks': s.marks_10,
            '12th Marks': s.marks_12,
            'CGPA': s.cgpa,
            'Percentage': s.percentage,
            'Backlog': s.backlog,
            'Year Drop': s.year_drop,
            'Placed': 'Yes' if s.is_placed else 'No'
        })

    df = pd.DataFrame(data)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:

        df.to_excel(writer, index=False, sheet_name='Students')
    output.seek(0)
    return send_file(output, download_name='filtered_students.xlsx', as_attachment=True)

@app.route('/view_criteria')
@login_required(role='tpo')
def view_criteria():
    companies = Company.query.order_by(Company.visit_date.desc()).all()
    return render_template('view_criteria.html', companies=companies)



@app.route('/masters_students')
@login_required(role='tpo')
def masters_students ():
    companies = Company.query.order_by(Company.visit_date.desc()).all()
    return render_template('masters_students.html', companies=companies)

@app.errorhandler(500)
def handle_exception(e):
    return "An error occurred (500)", 500

@app.route('/add_company', methods=['GET', 'POST'])
@login_required(role='tpo')
def add_company():
    if request.method == 'POST':
        company_name = request.form['name']
        min_cgpa = float(request.form['min_cgpa'])
        backlog_allowed = request.form['backlog_allowed']
        gender = request.form['gender']
        description = request.form['description']
        visit_date = date.fromisoformat(request.form['visit_date'])

        new_company = Company(
            name=company_name,
            min_cgpa=min_cgpa,
            backlog_allowed=backlog_allowed,
            gender=gender,
            description=description,
            visit_date=visit_date
        )
        db.session.add(new_company)
        db.session.commit()
        flash('Company added successfully!', 'success')
        return redirect(url_for('tpo_dashboard'))

    return render_template('add_company.html')


if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # recreate the new schema
    app.run(debug=True)

# ==================== MAIN ====================
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
