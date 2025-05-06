from flask import Flask, render_template, request, redirect, flash, url_for , session, jsonify
from datetime import datetime
import csv
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Constants
OFFICE_START_TIME = datetime.strptime("10:00", "%H:%M")
EMPLOYEE_FILE = "employees.csv"
ATTENDANCE_FILE = "attendance.csv"

# Initialize CSVs
if not os.path.exists(EMPLOYEE_FILE):
    with open(EMPLOYEE_FILE, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Employee ID", "Name", "Department"])

if not os.path.exists(ATTENDANCE_FILE):
    with open(ATTENDANCE_FILE, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Employee ID", "Name", "Date", "Time", "Status"])

# Routes

# Dummy credentials for login
USER_CREDENTIALS = {
    "admin": {"password": "admin123", "role": "admin"},
    "employee": {"password": "employee123", "role": "employee"}
}

# Routes
@app.route('/', methods=['GET', 'POST'])
def login():
    if 'user' in session:
        role = session['role']
        return redirect(url_for(f"{role}_dashboard"))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']

        if username in USER_CREDENTIALS:
            if USER_CREDENTIALS[username]['password'] == password and USER_CREDENTIALS[username]['role'] == role:
                session['user'] = username
                session['role'] = role
                flash("Login successful!", "success")
                return redirect(url_for(f"{role}_dashboard"))
            else:
                flash("Invalid credentials or role.", "error")
        else:
            flash("Invalid username.", "error")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    session.pop('role', None)
    flash("Logged out successfully.", "info")
    return redirect(url_for('login'))

@app.route('/admin_dashboard')
def admin_dashboard():
    if 'user' not in session or session.get('role') != 'admin':
        flash("Unauthorized access. Admins only.", "error")
        return redirect(url_for('login'))
    return render_template('admin_dashboard.html')  # Admin-specific functionality like adding employees

@app.route('/employee_dashboard')
def employee_dashboard():
    if 'user' not in session or session.get('role') != 'employee':
        flash("Unauthorized access. Employees only.", "error")
        return redirect(url_for('login'))
    return render_template('employee_dashboard.html')


@app.route('/add_employee', methods=['GET', 'POST'])
def add_employee():
    if request.method == 'POST':
        emp_id = request.form['emp_id']
        name = request.form['name']
        dept = request.form['dept']

        if emp_id and name and dept:
            with open(EMPLOYEE_FILE, 'r') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    if row["Employee ID"] == emp_id:
                        flash("Employee ID already exists.", "error")
                        return redirect(url_for('add_employee'))

            with open(EMPLOYEE_FILE, 'a', newline='') as file:
                writer = csv.writer(file)
                writer.writerow([emp_id, name, dept])
            flash(f"Employee {name} added successfully.", "success")
            return redirect(url_for('add_employee'))
        else:
            flash("Please fill all fields.", "error")
    return render_template('add_employee.html')


@app.route('/clock_in', methods=['POST'])
def clock_in():
    emp_id = request.form['emp_id']
    found = False

    with open(EMPLOYEE_FILE, 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row["Employee ID"] == emp_id:
                found = True
                now = datetime.now()
                date = now.strftime("%Y-%m-%d")
                time = now.strftime("%H:%M")
                status = "On Time" if now.time() <= OFFICE_START_TIME.time() else "Late"

                with open(ATTENDANCE_FILE, 'a', newline='') as att_file:
                    writer = csv.writer(att_file)
                    writer.writerow([emp_id, row["Name"], date, time, status])

                return jsonify({"status": "success", "message": f"{row['Name']} clocked in at {time} ({status})"})

    if not found:
        return jsonify({"status": "error", "message": "Employee ID not found."})




@app.route('/clock_out', methods=['POST'])
def clock_out():
    emp_id = request.form['emp_id']
    found = False

    with open(EMPLOYEE_FILE, 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row["Employee ID"] == emp_id:
                found = True
                now = datetime.now()
                date = now.strftime("%Y-%m-%d")
                time = now.strftime("%H:%M")

                with open(ATTENDANCE_FILE, 'a', newline='') as att_file:
                    writer = csv.writer(att_file)
                    writer.writerow([emp_id, row["Name"], date, time, "Clock Out"])

                return jsonify({"status": "success", "message": f"{row['Name']} clocked out at {time}"})

    if not found:
        return jsonify({"status": "error", "message": "Employee ID not found."})

if __name__ == '__main__':
    app.run(debug=True)
