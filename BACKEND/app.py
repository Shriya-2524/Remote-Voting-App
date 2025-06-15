from flask import Flask, render_template, request, redirect, url_for, flash
import mysql.connector
import os
from config import DB_CONFIG
from datetime import date
import random
import string

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # You can make this anything random
app.config['UPLOAD_FOLDER'] = 'uploads'

# Database connection
def get_db_connection():
    return mysql.connector.connect(
        host=DB_CONFIG['host'],
        user=DB_CONFIG['user'],
        password=DB_CONFIG['password'],
        database=DB_CONFIG['database']
    )

# Route for voter registration
@app.route('/', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        voter_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
        conn = None
        cursor = None
        try:
            print("Form submitted!")
            print("Data received:", request.form)

            full_name = request.form['full_name']
            parent_name = request.form['parent_name']
            dob = request.form['dob']
            gender = request.form['gender']
            aadhar_number = request.form['aadhar_number']
            phone = request.form['phone']
            email = request.form.get('email', '')
            full_address = request.form['address']
            state_name = request.form['state']
            district_name = request.form['district']
            pincode = request.form['pincode']

            photo_file = request.files.get('photo')
            photo_filename = ""
            if photo_file:
                photo_filename = voter_id + "_" + photo_file.filename
                photo_path = os.path.join(app.config['UPLOAD_FOLDER'], photo_filename)
                photo_file.save(photo_path)

            conn = get_db_connection()
            cursor = conn.cursor()

            # Insert or get state
            cursor.execute("SELECT state_id FROM state WHERE state_name = %s", (state_name,))
            state = cursor.fetchone()
            if not state:
                cursor.execute("INSERT INTO state (state_name) VALUES (%s)", (state_name,))
                conn.commit()
                state_id = cursor.lastrowid
            else:
                state_id = state[0]

            # Insert or get district
            cursor.execute("SELECT district_id FROM district WHERE district_name = %s AND state_id = %s", (district_name, state_id))
            district = cursor.fetchone()
            if not district:
                cursor.execute("INSERT INTO district (district_name, state_id) VALUES (%s, %s)", (district_name, state_id))
                conn.commit()
                district_id = cursor.lastrowid
            else:
                district_id = district[0]

            # Insert address
            cursor.execute("INSERT INTO address (full_address, pincode, district_id) VALUES (%s, %s, %s)", (full_address, pincode, district_id))
            conn.commit()
            address_id = cursor.lastrowid

            # Insert voter
            cursor.execute("""
                INSERT INTO voter (
                    voter_id, full_name, parent_name, dob, gender, aadhar_number, phone, email, photo, address_id
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (voter_id, full_name, parent_name, dob, gender, aadhar_number, phone, email, photo_filename, address_id))
            conn.commit()

            flash(f"Registration successful! Your Voter ID is {voter_id}", "success")
            return redirect(url_for('register'))

        except mysql.connector.Error as err:
            print("DB Error:", err)
            flash(f"Database error: {err}", "danger")

        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    return render_template("register.html")

if __name__ == '__main__':
    app.run(debug=True)
