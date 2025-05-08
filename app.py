from flask import Flask, render_template, request, redirect, flash, url_for , session, jsonify, send_file
import pyttsx3
from datetime import datetime
import csv
import os


app = Flask(__name__)
app.secret_key = 'your_secret_key'

tts_engine = pyttsx3.init()

def play_voice_message(message):
   
    tts_engine.say(message)
    tts_engine.runAndWait()


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
        writer.writerow(["Employee ID", "Name", "Date", "Time", "Status" ])

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

@app.route('/download')
def download_file():
    return send_file('attendance.csv', as_attachment=True)

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

@app.route('/preview_employees', methods=['GET'])
def preview_employees():
    try:
        data = []
        with open(EMPLOYEE_FILE, 'r') as file:
            reader = csv.reader(file)
            for row in reader:
                data.append(row)

        # Render the data in an HTML template
        return render_template('preview_employees.html', data=data)
    except FileNotFoundError:
        return render_template('error.html', message="Employee file not found.")
    except Exception as e:
        return render_template('error.html', message=str(e))
    

@app.route('/preview_attendance', methods=['GET'])
def preview_attendance():
    try:
        data = []
        with open(ATTENDANCE_FILE, 'r') as file:
            reader = csv.reader(file)
            for row in reader:
                data.append(row)

        # Render the data in an HTML template
        return render_template('preview_attendance.html', data=data)
    except FileNotFoundError:
        return render_template('error.html', message="Employee file not found.")
    except Exception as e:
        return render_template('error.html', message=str(e))
    

@app.route("/filter_attendance", methods=["GET", "POST"])
def filter_attendance():
    if request.method == "POST":
        # Get the form data for filtering
        employee_id = request.form.get("employee_id", "").strip()
        date = request.form.get("date", "").strip()
        late_attendance = request.form.get("late_attendance", "").strip()

        filtered_employees = []

        # Open the attendance file to filter data
        with open(ATTENDANCE_FILE, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Filter based on employee ID
                if employee_id and row["Employee ID"] != employee_id:
                    continue
                # Filter based on date
                if date and row["Date"] != date:
                    continue
                # Filter based on late attendance status
                if late_attendance and row["Status"].lower() != late_attendance.lower():
                    continue

                filtered_employees.append(row)
                print(filtered_employees)
        # Render the filtered data in the same attendance preview template
        return render_template("filter_attendance.html", data=filtered_employees)

    # If GET request, just render the page without any filters applied
    return render_template("filter_attendance.html")


@app.route('/add_employee', methods=['GET', 'POST'])
def add_employee():
    if request.method == 'POST':
        emp_id = request.form['emp_id']
        name = request.form['name']
        dept = request.form['dept']

        if emp_id and name and dept:
            if os.path.exists(EMPLOYEE_FILE):
                with open(EMPLOYEE_FILE, 'r') as file:
                    reader = csv.DictReader(file)
                    for row in reader:
                        if row.get("Employee ID") == emp_id:
                            return render_template('add_employee.html', message="Employee already exists.")
            
            # Add employee to file
            file_exists = os.path.exists(EMPLOYEE_FILE)
            with open(EMPLOYEE_FILE, 'a', newline='') as file:
                writer = csv.writer(file)
                if not file_exists:
                    writer.writerow(["Employee ID", "Name", "Department"])  # Write header if file is new
                writer.writerow([emp_id, name, dept])
            return render_template('add_employee.html', message="Employee added successfully.")
        
        else:
            return render_template('add_employee.html', message="Please fill all fields.")

    return render_template('add_employee.html')



@app.route('/delete_employee', methods=['GET', 'POST'])
def delete_employee():
    if request.method == 'POST':
        employee_id = request.form.get('employee_id')
        if not employee_id:
            return render_template('delete_employee.html', message="Please provide an Employee ID.")
        
        try:
            updated_data = []
            employee_found = False

            # Read and filter the data
            with open(EMPLOYEE_FILE, 'r') as file:
                reader = csv.reader(file)
                for row in reader:
                    if row[0] != employee_id:  # Assuming the first column is Employee ID
                        updated_data.append(row)
                    else:
                        employee_found = True

            if not employee_found:
                return render_template('delete_employee.html', message=f"Employee with ID {employee_id} not found.")

            # Write the updated data back to the file
            with open(EMPLOYEE_FILE, 'w', newline='') as file:
                writer = csv.writer(file)
                writer.writerows(updated_data)

            return render_template('delete_employee.html', message=f"Employee with ID {employee_id} deleted successfully.")

        except FileNotFoundError:
            return render_template('delete_employee.html', message="Employee file not found.")
        except Exception as e:
            return render_template('delete_employee.html', message=f"Error: {str(e)}")

    return render_template('delete_employee.html')


@app.route('/employee_details', methods=['GET', 'POST'])
def employee_details():
    if request.method == 'POST':
        employee_id = request.form.get('employee_id')
        if not employee_id:
            return render_template('employee_details.html', message="Please provide an Employee ID.")

        try:
            employee_data = None
            attendance_data = {}
            attendance_file = "attendance.csv"  # Update this file name

            # Fetch employee data
            with open(EMPLOYEE_FILE, 'r') as file:
                reader = csv.reader(file)
                for row in reader:
                    if row[0] == employee_id:  # Assuming first column is Employee ID
                        employee_data = row
                        break

            if not employee_data:
                return render_template('employee_details.html', message=f"Employee with ID {employee_id} not found.")

            # Fetch attendance data
            try:
                with open(attendance_file, 'r') as file:
                    reader = csv.reader(file)
                    for row in reader:
                        if row[0] == employee_id:  # Assuming first column is Employee ID
                            date = row[2]  # Assuming second column is Date
                            clock_in = row[3]  # Assuming third column is Clock In Time
                            clock_out = row[4] if len(row) > 4 else None  # Optional Clock Out Time

                            status = "Present" if clock_out else "Absent"

                            # Determine if the employee is late or on time
                            late_time = "10:00:00"

                            timing = "On Time"
                            
                            if clock_in and clock_in > late_time:
                                timing = "Late"
                                
                                
                            # Add or update the attendance summary for the date
                            if date not in attendance_data:
                                attendance_data[date] = {
                                    "status": status,
                                    "timing": timing,
                                    "time" : clock_in,
                                   
                                }

            except FileNotFoundError:
                attendance_data = {}

            return render_template(
                'employee_details.html',
                employee_data=employee_data,
                attendance_data=attendance_data,
                message=None
            )

        except Exception as e:
            return render_template('employee_details.html', message=f"Error: {str(e)}")

    return render_template('employee_details.html')


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
    app.run(debug=True, use_reloader=False)
