
# 📚 TPO Portal — Placement Management System

A web-based Training and Placement Portal built with **Flask** and **SQLite**, designed for students and TPOs to manage placement activities such as company listings, student profiles, applications, and eligibility tracking.

---

## 🧰 Tech Stack

- **Python** with Flask
- **SQLite** (via SQLAlchemy)
- HTML + CSS (via Jinja templates)
- **Pandas + XlsxWriter** (for Excel export)
- User authentication (hashed passwords)

---

## 🔧 Features

### 👨‍🎓 Student
- Signup/Login as a student
- Create/update personal and academic profile
- View list of eligible companies
- Apply to companies (1-click apply)
- Track applied companies

### 🧑‍💼 TPO/Admin
- Signup/Login as TPO
- View all student profiles (with filters)
- View eligible students per company
- Export student data as Excel
- Track placed students
- View company criteria & details

---

## 🗂 Project Structure

```
├── app.py                 # Main Flask application
├── templates/             # HTML templates
├── static/                # CSS, JS, etc.
├── tpo.db                 # SQLite Database
├── requirements.txt       # Python dependencies
└── README.md              # You're here!
```

---

## 💾 Setup Instructions

### 1. Clone the repo

```bash
git clone https://github.com/yourusername/tpo-portal.git
cd tpo-portal
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Initialize the database

```bash
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

### 4. Run the app

```bash
python app.py
```

App will be live at `http://127.0.0.1:5000`

---

## 📤 Export Feature (TPO Only)

- Filters (CGPA range, backlog)
- Export student list to Excel (`.xlsx`)
- Uses Pandas + XlsxWriter

---

## 🛠 Troubleshooting

### Error: `no such column: student_profile.is_placed`

> You likely added a new field in the model.

✅ Fix:
```bash
flask db migrate -m "Added is_placed column"
flask db upgrade
```

---

## 🔐 Security

- Passwords stored securely (hashed using Werkzeug)
- Role-based access control (`student` or `tpo`)

---

## 📦 requirements.txt

```
Flask==2.2.5
Flask-Login==0.6.2
Flask-Migrate==4.0.5
Flask-SQLAlchemy==3.1.1
SQLAlchemy==2.0.23
Werkzeug==2.3.7
pandas==2.1.4
openpyxl==3.1.2
XlsxWriter==3.1.9
```



## 🧠 Future Improvements

- Company login & result upload
- Resume uploads
- Email notifications
- Dashboard analytics for TPO

---

## 👏 Contributing

Pull requests are welcome! For major changes, please open an issue first to discuss. 
contact at vaishno1702@gmail.com
