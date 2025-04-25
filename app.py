from flask import Flask, request, redirect, url_for, render_template, send_from_directory,session,jsonify,flash
import mysql.connector
import requests
import os
import smtplib
from flask_mail import Mail, Message
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from werkzeug.utils import secure_filename
from math import ceil
import random
from decimal import Decimal
from datetime import datetime, timedelta
from app import app
from urllib.parse import urlparse
import stripe

app = Flask(__name__)

stripe.api_key = 'sk_test_51Qojj706HMl5AKyp97KfZVEqa2FEN8lY0rmAb2rJXbfceDd7ouFfQAsBufApTUOBVjiw1yEUPSc9HWMoTCsOAjD600sQ5LkIDQ'

@app.route('/create-checkout-session', methods=['POST'])
def create_checkout_session():
    try:
        booking_id = request.form.get('booking_id')  # Assuming booking_id is passed in the form
        print(f"Received booking_id: {booking_id}")  # Debugging statement
        if not booking_id:
            raise ValueError("Booking ID is required")

        # Fetch booking details from the database
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT ac.car_name, ac.price_per_day, b.car_number
            FROM Bookings b
            JOIN add_car ac ON b.car_number = ac.car_number
            WHERE b.booking_id = %s
        """, (booking_id,))
        booking = cursor.fetchone()
        cursor.close()
        connection.close()

        if not booking:
            raise ValueError("Booking not found")

        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': booking['car_name'],
                    },
                    'unit_amount': int(booking['price_per_day'] * 100),  # Amount in cents
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=url_for('booking_confirmation', booking_id=booking_id, _external=True) + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=url_for('booking', car_number=booking['car_number'], _external=True),
        )
        return redirect(checkout_session.url, code=303)
    except Exception as e:
        return str(e)

# Flask-Mail configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'carsharing52@gmail.com'  # Replace with your email
app.config['MAIL_PASSWORD'] = 'ueimkbvarolxvuio'  # Replace with your App Password
mail=Mail(app)

app.secret_key = 'your secret key'
try:
    def get_db_connection():
        # Option 1: Use individual environment variables
        db_config = {
            'host': os.getenv('gondola.proxy.rlwy.net'),
            'port': os.getenv('3306'),
            'user': os.getenv('root'),
            'password': os.getenv('zYXDJMrfYGjWEZhBUfcroeSSrYBKthyA'),
            'database': os.getenv('railway')
        }

        # Option 2: Use MYSQL_URL (uncomment if preferred)
        """
        mysql_url = os.getenv('MYSQL_URL')
        url = urlparse(mysql_url)
        db_config = {
            'host': url.hostname,
            'port': url.port,
            'user': url.username,
            'password': url.password,
            'database': url.path.lstrip('/')
        }
        """

        conn = mysql.connector.connect(**db_config)
        return conn

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    print("Connected to MySQL database!")
    print("--------------------------------------------------------------")
    print(conn)

except mysql.connector.Error as e:
    print("Error connecting to MySQL database:", e)

ITEMS_PER_PAGE =2

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form['name'] 
        email = request.form['email']
        subject = request.form['subject']
        message = request.form['message']

        # Create the email message
        msg = MIMEMultipart()
        msg['From'] = email
        msg['To'] = 'carsharing52@gmail.com'  # Replace with your email
        msg['Subject'] = subject
        body = f"Name: {name}\nEmail: {email}\n\nMessage:\n{message}"
        msg.attach(MIMEText(body, 'plain'))

        # Send the email
        try:
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login('carsharing52@gmail.com', 'ueimkbvarolxvuio')  # Replace with your email and App Password
            text = msg.as_string()
            server.sendmail(email, 'carsharing52@gmail.com', text)  # Replace with your email
            server.quit()
            flash('Message sent successfully', 'success')
        except Exception as e:
            flash(f'An error occurred while sending the message: {str(e)}', 'danger')
            return redirect(url_for('contact'))
    return render_template('contact.html')



@app.route('/') 
@app.route('/index')
def index():
    # Fetch the page number from the query string (default to 1 if not provided)
    page = request.args.get('page', 1, type=int)
    per_page = 3  # Number of cars per page
    
    # Calculate the offset
    offset = (page - 1) * per_page
    
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    # Fetch the total count of cars
    cursor.execute("""
        SELECT COUNT(*) AS total_cars FROM add_car;
    """)
    total_cars = cursor.fetchone()['total_cars']
    
    # Fetch paginated cars
    cursor.execute("""
    SELECT c.car_number, c.car_name, c.stock, c.price_per_day, c.car_img, 
           ct.type_name, cmp.company_name, u.username AS owner_name
    FROM add_car c
    LEFT JOIN CarTypes ct ON c.type_id = ct.type_id 
    LEFT JOIN Companies cmp ON c.company_id = cmp.company_id
    LEFT JOIN Users u ON c.car_owner_id = u.user_id
    LIMIT %s OFFSET %s;
""", (per_page, offset))

    
    cars = cursor.fetchall()
    cursor.close()
    connection.close()

    # Calculate the total number of pages
    total_pages = ceil(total_cars / per_page)

    return render_template('index.html', cars=cars, total_pages=total_pages, current_page=page)

# About page view function
@app.route('/about')
def about():
    return render_template('About.html')


@app.route("/car_sharing")
def car_sharing():
    return render_template("more_car_sharing.html")

@app.route("/user_registration")
def user_registration():
    return render_template("more_register.html")

@app.route("/multi_role")
def multi_role():
    return render_template("more_multirole.html")


# Login page View function
# @app.route('/login', methods=['GET', 'POST'])
# def login():
#     if request.method == 'POST':
#         username = request.form['username']
#         password = request.form['password']

#         # Validate user credentials
#         try:
#             conn = get_db_connection()
#             cursor = conn.cursor(dictionary=True)

#             # Query the database with case-sensitive username match
#             cursor.execute('SELECT * FROM users WHERE BINARY username = %s', (username,))
#             user = cursor.fetchone()
#             cursor.close()
#             conn.close()

#             if user and user['password'] == password:  # Check if password matches
#                 session['user_id'] = user['user_id']
#                 session['username'] = user['username']
#                 session['role'] = user['role']
#                 session['loggedin'] = True

#                 # Redirect based on the role
#                 if user['role'] == 'Admin':
#                     return redirect(url_for('admin_dashboard'))
#                 elif user['role'] == 'User':
#                     return redirect(url_for('user_dashboard'))  # Replace 'index' with the actual route for user's dashboard
#                 else:
#                     flash('Invalid role', 'danger')
#                     return redirect(url_for('login'))
#             else:
#                 flash('Incorrect Username/Password. Please try again.', 'danger')
#                 return redirect(url_for('login'))
#         except mysql.connector.Error as e:
#             print(f"Error fetching data from MySQL table: {e}")
#             flash('An error occurred while logging in.', 'danger')
#             return redirect(url_for('login'))

#     return render_template('login.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    msg = ''
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Validate user credentials
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)

            # Query the database with case-sensitive username match
            cursor.execute('SELECT * FROM users WHERE BINARY username = %s', (username,))
            user = cursor.fetchone()

            if user and user['password'] == password:  # Check if password matches
                session['temp_user_id'] = user['user_id']
                session['temp_username'] = user['username']
                session['temp_role'] = user['role']
                session['loggedin'] = True

                # Query to get user's email from 'user_info' table
                cursor.execute('SELECT email FROM user_info WHERE user_id = %s', (user['user_id'],))
                user_info = cursor.fetchone()

                if user_info:
                    email = user_info['email']

                    # Generate OTP (6 digits)
                    otp = str(random.randint(100000, 999999))

                    # Store OTP and generation time in session
                    session['otp'] = otp
                    session['otp_generated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                    # Send OTP to user's email (You need to implement this function)
                    send_otp(email, otp)

                    flash('OTP sent to your email address', 'info')
                    print("OTP sent to email:___________________________________________", otp)

                    # Redirect to OTP verification page
                    return redirect(url_for('verify_login_otp'))

                else:
                    flash('User email not found', 'danger')
                    return redirect(url_for('login'))

            else:
                flash('Incorrect Username/Password. Please try again.', 'danger')
                return redirect(url_for('login'))

        except mysql.connector.Error as e:
            print(f"Error fetching data from MySQL table: {e}")
            flash('An error occurred while logging in.', 'danger')
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/verify_login_otp', methods=['GET', 'POST'])
def verify_login_otp():
    if request.method == 'POST':
        entered_otp = request.form['otp']
        print(f"Entered OTP: {entered_otp}, Session OTP: {session.get('otp')}")  # Debugging

        # Check if OTP in session matches the entered OTP
        if 'otp' in session and int(entered_otp) == int(session['otp']):
            # Check if OTP is still valid (within 10 minutes)
            otp_generated_at = datetime.strptime(session['otp_generated_at'], '%Y-%m-%d %H:%M:%S')
            if datetime.now() - otp_generated_at <= timedelta(minutes=10):
                session.pop('otp', None)  # Remove OTP from session after successful verification
                session.pop('otp_generated_at', None)  # Remove OTP generation time from session

                session['loggedin'] = True
                session['user_id'] = session.pop('temp_user_id')
                session['username'] = session.pop('temp_username')
                session['role'] = session.pop('temp_role')

                # Redirect based on role (user or admin)
                if session.get('role') == 'Admin':
                    flash('Welcome Admin', 'success')
                    return redirect(url_for('admin_dashboard'))
                elif session.get('role') == 'User':
                    flash('Welcome User', 'success')
                    return redirect(url_for('user_dashboard'))
                else:
                    flash('Invalid role', 'danger')
                    return redirect(url_for('login'))
            else:
                flash('OTP has expired. Please login again.', 'danger')
                return redirect(url_for('login'))
        else:
            flash('Invalid OTP. Please try again.', 'danger')
            return redirect(url_for('verify_login_otp'))

    return render_template('verify_login_otp.html')


# Send OTP function
def send_otp(email, otp):
    msg = Message('Your OTP', sender='carsharing52@gmail.com', recipients=[email])
    msg.body = f'Your OTP is {otp}'
    mail.send(msg)
    return otp

# Forgot password view function
@app.route('/forgot_pswd', methods=['GET', 'POST'])
def forgot_pswd():
    if request.method == 'POST':
        email = request.form['email']

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        # Check if the email exists in the database
        cursor.execute('SELECT * FROM user_info WHERE email = %s', (email,))
        user = cursor.fetchone()
        cursor.fetchall()  # Ensure all results are read
        if user:
            otp = str(random.randint(100000, 999999))  # Generate a 6-digit OTP
            send_otp(email, otp)  # Pass both email and otp
            session['otp'] = otp
            session['email'] = email
            print("OTP sent to email:___________________________________________", otp)
            flash('OTP sent to your email address', 'info')
            return redirect(url_for('verify_otp'))
        else:
            flash('Email is not registered', 'danger')
            return redirect(url_for('forgot_pswd'))
    return render_template('Forgot_password.html')

@app.route('/verify_otp', methods=['GET', 'POST'])
def verify_otp():
    if request.method == 'POST':
        entered_otp = request.form['otp']
        if 'otp' in session and int(entered_otp) == int(session['otp']):
            flash('OTP verified successfully', 'success')
            return render_template('reset_password.html')
        else:
            flash('Invalid OTP', 'danger')
            return render_template('Verify_OTP.html')

    return render_template('Verify_OTP.html')

@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        new_password = request.form['newPassword']
        confirm_password = request.form['confirmPassword']
        email = session.get('email')

        if new_password != confirm_password:
            flash('Passwords do not match. Please try again.', 'danger')
            return redirect(url_for('reset_password'))
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET password = %s WHERE user_id = (SELECT user_id FROM user_info WHERE email = %s)', (new_password, email))
        conn.commit()
        cursor.close()
        conn.close()
        flash('Password reset successfully. Please log in with your new password.', 'success')
        return redirect(url_for('login'))
    return render_template('reset_password.html')


# Book ur car view function
@app.route('/book_ur_car', methods=['GET', 'POST'])
def book_ur_car():
    user_id = session.get('user_id')
    print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~",{user_id})


    # Redirect to login if user is not logged in
    # if not user_id:
    #     return redirect(url_for('login'))

    cars = None  
    from_locations = []
    to_locations = []

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Fetch locations for dropdowns
    cursor.execute("SELECT DISTINCT from_location FROM add_car")
    from_locations = [row['from_location'] for row in cursor.fetchall()]

    cursor.execute("SELECT DISTINCT to_location FROM add_car")
    to_locations = [row['to_location'] for row in cursor.fetchall()]

    if request.method == 'POST':
        from_location = request.form.get('From_Location')
        to_location = request.form.get('To_Location')
        from_date = request.form.get('from_date')
        to_date = request.form.get('to_date')

        if from_location and to_location and from_date and to_date:
            query = """
                SELECT 
                    ac.car_number, 
                    ac.car_name, 
                    ac.price_per_day, 
                    ac.car_img, 
                    ac.stock, 
                    ct.type_name, 
                    c.company_name, 
                    u.username AS owner_name
                FROM add_car ac
                JOIN CarTypes ct ON ac.type_id = ct.type_id 
                JOIN Companies c ON ac.company_id = c.company_id
                JOIN users u ON ac.car_owner_id = u.user_id  -- FIXED JOIN
                WHERE ac.from_location = %s 
                AND ac.to_location = %s 
                AND ac.car_number NOT IN (
                    SELECT b.car_number FROM Bookings b 
                    WHERE (b.pickup_date BETWEEN %s AND %s) 
                    OR (b.dropoff_date BETWEEN %s AND %s)
                );
            """
            cursor.execute(query, (from_location, to_location, from_date, to_date, from_date, to_date))
            cars = cursor.fetchall()

            # Convert Decimal values to float
            for car in cars:
                car['price_per_day'] = float(car['price_per_day'])

            print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!",{user_id})

    cursor.close()
    conn.close()

    return render_template(
        'Book_ur_car.html',
        user_id=user_id,
        from_locations=from_locations,
        to_locations=to_locations,
        cars=cars
    )



# API to fetch all available 'from' locations
@app.route('/api/from_locations', methods=['GET'])
def get_from_locations():
    # Connect to the database
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # MySQL query to fetch distinct from locations
    query = "SELECT DISTINCT from_location FROM add_car"
    cursor.execute(query)
    locations = cursor.fetchall()
    cursor.close()
    conn.close()

    # Return the list of 'from' locations
    return jsonify({'from_locations': [loc['from_location'] for loc in locations]})


# API to fetch all available 'to' locations
@app.route('/api/to_locations', methods=['GET'])
def get_to_locations():
    # Connect to the database
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # MySQL query to fetch distinct to locations
    query = "SELECT DISTINCT to_location FROM add_car"
    cursor.execute(query)
    locations = cursor.fetchall()
    cursor.close()
    conn.close()

    # Return the list of 'to' locations
    return jsonify({'to_locations': [loc['to_location'] for loc in locations]})


# View function for booking
@app.route('/booking/<int:car_number>', methods=['GET', 'POST'])
def booking(car_number):
    if 'user_id' not in session:
        flash('You must be logged in to make a booking.', 'error')
        return redirect(url_for('login'))  # Redirect to login if user is not logged in

    user_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM add_car WHERE car_number = %s", (car_number,))
    car = cursor.fetchone()

    if not car:
        flash('Car not found!', 'error')
        return redirect(url_for('index'))  # Redirect to available cars page

    if request.method == 'POST':
        pickup_date = request.form['pickup_date']
        dropoff_date = request.form['dropoff_date']
        pickup_address = request.form['pickup_address']
        dropoff_address = request.form['dropoff_address']

        cursor.execute("""
            INSERT INTO Bookings (user_id, car_number, pickup_date, dropoff_date, pickup_address, dropoff_address)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (user_id, car_number, pickup_date, dropoff_date, pickup_address, dropoff_address))

        conn.commit()
        booking_id = cursor.lastrowid

        # Fetch user details for email
        cursor.execute("""
            SELECT u.username, ui.email
            FROM users u
            JOIN user_info ui ON u.user_id = ui.user_id
            WHERE u.user_id = %s
        """, (user_id,))
        user_info = cursor.fetchone()

        # Prepare booking details for email
        booking = {
            'username': user_info['username'],
            'email': user_info['email'],
            'car_name': car['car_name'],
            'pickup_date': pickup_date,
            'dropoff_date': dropoff_date,
            'pickup_address': pickup_address,
            'dropoff_address': dropoff_address,
            'booking_id': booking_id
        }

        # Send booking confirmation email
        send_booking_confirmation_email(booking)

        flash('Booking successfully confirmed!', 'success')
        return redirect(url_for('booking_confirmation', booking_id=booking_id))

    return render_template('booking.html', car=car)

@app.route('/edit_booking/<int:booking_id>', methods=['GET', 'POST'])
def edit_booking(booking_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Fetch booking details
    cursor.execute("""
        SELECT b.booking_id, b.car_number, b.pickup_date, b.dropoff_date, 
               b.pickup_address, b.dropoff_address, ac.car_name
        FROM Bookings b
        JOIN add_car ac ON b.car_number = ac.car_number
        WHERE b.booking_id = %s
    """, (booking_id,))
    
    booking = cursor.fetchone()
    cursor.fetchall()  # Clears any unread results

    if not booking:
        flash('Booking not found!', 'danger')
        cursor.close()
        conn.close()
        return redirect(url_for('booking_report'))

    if request.method == 'POST':
        pickup_date = request.form.get('pickup_date')
        dropoff_date = request.form.get('dropoff_date')
        pickup_address = request.form.get('pickup_address')
        dropoff_address = request.form.get('dropoff_address')

        if not pickup_date or not dropoff_date or not pickup_address or not dropoff_address:
            flash('All fields are required.', 'danger')
            return redirect(request.url)

        try:
            pickup_date_obj = datetime.strptime(pickup_date, '%Y-%m-%d')
            dropoff_date_obj = datetime.strptime(dropoff_date, '%Y-%m-%d')
        except ValueError:
            flash('Invalid date format.', 'danger')
            return redirect(request.url)

        today = datetime.today().date()
        if pickup_date_obj.date() < today or dropoff_date_obj.date() < today:
            flash('Dates cannot be in the past.', 'danger')
            return redirect(request.url)
        if pickup_date_obj.date() >= dropoff_date_obj.date():
            flash('Drop-off date must be after pickup date.', 'danger')
            return redirect(request.url)

        #  Update booking details **without changing car name**
        cursor.execute("""
            UPDATE Bookings 
            SET pickup_date = %s, dropoff_date = %s, pickup_address = %s, dropoff_address = %s
            WHERE booking_id = %s
        """, (pickup_date, dropoff_date, pickup_address, dropoff_address, booking_id))

        conn.commit()
        flash('Booking updated successfully!', 'success')

        cursor.close()
        conn.close()
        return redirect(url_for('booking_report'))

    cursor.close()
    conn.close()
    return render_template('edit_booking.html', booking=booking)

@app.route('/delete_booking/<int:booking_id>', methods=['POST'])
def delete_booking(booking_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Delete booking
    cursor.execute("DELETE FROM Bookings WHERE booking_id = %s", (booking_id,))
    conn.commit()

    flash('Booking deleted successfully!', 'success')
    return redirect(url_for('booking_report'))


# booking confirmation
@app.route('/booking_confirmation/<int:booking_id>')
def booking_confirmation(booking_id):
    # Create a connection to the database
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    # Execute the SQL query to fetch booking details along with user details
    cursor.execute("""
        SELECT 
            b.booking_id, 
            b.pickup_date, 
            b.dropoff_date, 
            b.pickup_address, 
            b.dropoff_address, 
            ac.car_name, 
            ac.car_img,
            u.username, 
            ui.email, 
            ui.phone_number,
            ac.price_per_day
        FROM Bookings b
        JOIN add_car ac ON b.car_number = ac.car_number
        JOIN users u ON b.user_id = u.user_id
        JOIN user_info ui ON b.user_id = ui.user_id
        WHERE b.booking_id = %s
    """, (booking_id,))

    # Fetch the booking data
    booking = cursor.fetchone()

    # Close the cursor and connection
    cursor.close()
    connection.close()

    # Send the confirmation email
    send_booking_confirmation_email(booking)

    # Flash a success message
    flash(f"Message sent to your email ({booking['email']})", "success")

    # Render the template with the fetched booking details
    return render_template('booking_confirmation.html', booking=booking)

def send_booking_confirmation_email(booking):
    msg = Message('Booking Confirmation', sender='your_email@gmail.com', recipients=[booking['email']])
    msg.body = f"""
    Dear {booking['username']},

    Your booking for the car {booking['car_name']} has been confirmed.

    Booking Details:
    - Pickup Date: {booking['pickup_date']}
    - Dropoff Date: {booking['dropoff_date']}
    - Pickup Address: {booking['pickup_address']}
    - Dropoff Address: {booking['dropoff_address']}
    - Booking ID: {booking['booking_id']}

    Thank you for choosing our service.

    Best regards,
    Team HITHA - Sharing Rides, Creating Smiles
    """
    mail.send(msg)
    print("##################################################Email sent to: ", booking['email'])
    print("##################################################Email sent to: ", msg.body)

# Cars view function
@app.route('/cars')
def cars():
    # Fetch the page number from the query string (default to 1 if not provided)
    page = request.args.get('page', 1, type=int)
    per_page = 3  # Number of cars per page
    
    # Calculate the offset
    offset = (page - 1) * per_page
    
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    # Fetch the total count of cars
    cursor.execute("""
        SELECT COUNT(*) AS total_cars FROM add_car;
    """)
    total_cars = cursor.fetchone()['total_cars']
    
    # Fetch paginated cars
    cursor.execute("""
        SELECT c.car_number, c.car_name, c.stock, c.price_per_day, c.car_img, 
               ct.type_name, cmp.company_name, u.username AS owner_name
        FROM add_car c
        LEFT JOIN CarTypes ct ON c.type_id = ct.type_id 
        LEFT JOIN Companies cmp ON c.company_id = cmp.company_id
        LEFT JOIN Users u ON c.car_owner_id = u.user_id
        LIMIT %s OFFSET %s;
    """, (per_page, offset))
    
    cars = cursor.fetchall()
    cursor.close()
    connection.close()

    # Calculate the total number of pages
    total_pages = ceil(total_cars / per_page)

    return render_template('Cars.html', cars=cars, total_pages=total_pages, current_page=page)



API_KEY = "WW83QWNQSVRjWHFXM1Z6VkhiN1kzWnZxSEFncXppdzhCMnZTM0RwMQ=="
BASE_URL = "https://api.countrystatecity.in/v1/countries"

@app.route('/countries', methods=['GET'])
def get_countries():
    url = "https://api.countrystatecity.in/v1/countries"
    headers = {"X-CSCAPI-KEY": API_KEY}
    response = requests.get(url, headers=headers)
    countries = [{"id": country["iso2"], "name": country["name"]} 
                 for country in response.json()]
    return jsonify(countries)


@app.route('/states', methods=['GET'])
def get_states():
    country_id = request.args.get('country_id')
    url = f"https://api.countrystatecity.in/v1/countries/{country_id}/states"
    headers = {"X-CSCAPI-KEY": API_KEY}
    response = requests.get(url, headers=headers)
    states = [{"id": state["iso2"], "name": state["name"]} 
              for state in response.json()]
    return jsonify(states)

@app.route('/cities', methods=['GET'])  
def get_cities():
    country_id = request.args.get('country_id')
    state_id = request.args.get('state_id')
    url = f"https://api.countrystatecity.in/v1/countries/{country_id}/states/{state_id}/cities"
    headers = {"X-CSCAPI-KEY": API_KEY}
    response = requests.get(url, headers=headers) 
    cities = [{"id": city["id"], "name": city["name"]} 
              for city in response.json()]
    return jsonify(cities)



UPLOAD_FOLDER = 'static/uploads/'  # Move this line here
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif','webp'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER  # Add this line

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['name']
        password = request.form['password']
        role = request.form.get('role')

        # Sanitize role value
        if role not in ['Admin', 'User']:
            role = 'User'  # Default to 'User' if invalid

        email = request.form['email']
        phone_number = request.form['phone']
        address_line1 = request.form['address_line1']
        address_line2 = request.form['address_line2']
        
        # Get city and check if it's provided, set to a default if not
        city = request.form.get('city')
        if not city:  # Check if city is not provided
            flash("City is required!", "error")
            return render_template('Register.html')

        state = request.form.get('state')
        country = request.form.get('country')
        gender = request.form.get('gender')
        birthday = request.form['dob']
        profile_picture = request.files.get('profile_picture')

        # Initialize image_filename to None if no picture is uploaded
        image_filename = None

        # Handle file upload
        if profile_picture and allowed_file(profile_picture.filename):
            filename = secure_filename(profile_picture.filename)
            image_upload_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            profile_picture.save(image_upload_path)
            image_filename = profile_picture.filename  # Set image filename only if an image is uploaded

        # Database connection and insert data
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Insert user details into users table
        cursor.execute('INSERT INTO users (username, password, role) VALUES (%s, %s, %s)', (username, password, role))

        user_id = cursor.lastrowid

        # Insert user info into user_info table
        cursor.execute('''INSERT INTO user_info (user_id, email, phone_number, address_line1, address_line2, city, state, country, gender, birthday, role, profile_picture) 
                          VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)''', 
                       (user_id, email, phone_number, address_line1, address_line2, city, state, country, gender, birthday, role, image_filename))

        conn.commit()
        cursor.close()
        conn.close()

        flash('Registration successful', 'success')
        return redirect(url_for('login'))

    return render_template('Register.html')




# view function for admin dashboard
# @app.route('/admin_dashboard')
# def admin_dashboard():
#     if 'role' in session and session['role'] == 'Admin':
#         return render_template('admin_dashboard.html')
#     else:
#         flash('Access denied! Admins only.', 'danger')
#         return redirect(url_for('index'))
@app.route('/admin_dashboard')
def admin_dashboard():
    if 'role' in session and session['role'] == 'Admin':
        # Admin does not need user_id, they see global counts
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        # Fetch the total count of cars, car types, companies, customers, and bookings
        cursor.execute("SELECT COUNT(*) AS car_count FROM add_car;")
        car_count = cursor.fetchone()['car_count']

        cursor.execute("SELECT COUNT(*) AS car_type_count FROM CarTypes;")
        car_type_count = cursor.fetchone()['car_type_count']

        cursor.execute("SELECT COUNT(*) AS company_count FROM Companies;")
        company_count = cursor.fetchone()['company_count']

        cursor.execute("SELECT COUNT(*) AS customer_count FROM Users;")
        customer_count = cursor.fetchone()['customer_count']

        cursor.execute("SELECT COUNT(*) AS booking_count FROM Bookings;")
        booking_count = cursor.fetchone()['booking_count']

        cursor.close()
        connection.close()

        # Render the admin dashboard template with the counts
        return render_template('Admin_Dashboard.html', 
                               car_count=car_count,
                               car_type_count=car_type_count,
                               company_count=company_count,
                               customer_count=customer_count,
                               booking_count=booking_count)
    else:
        flash('Access denied! Admins only.', 'danger')
        return redirect(url_for('index'))


    
# Car Report view function
@app.route('/car_report', methods=['GET'])
def car_report():
    if session.get('role') != 'Admin':
        flash('Access denied', 'danger')
        return redirect(url_for('login'))  # Redirect or show error page if not admin.
    
    # Get the logged-in user's user_id from the session
    user_id = session.get('user_id')
    if not user_id:
        flash('User not logged in', 'danger')
        return redirect(url_for('login'))  # Redirect to login if user_id is not found
    
    # Get page number from the query string, default to page 1
    page = request.args.get('page', 1, type=int)
    per_page = 5  # Items per page (Pagination limit)
    offset = (page - 1) * per_page  # Calculate the offset for the query

    # Get car data from the database, filtering by the logged-in user's user_id
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    # Fetch cars belonging to the logged-in user with LIMIT and OFFSET for pagination
    cursor.execute("""
        SELECT c.car_number, c.car_name, c.stock, c.price_per_day, c.car_img, 
               ct.type_name, cmp.company_name, u.username AS owner_name, ui.phone_number AS contact
        FROM add_car c
        LEFT JOIN CarTypes ct ON c.type_id = ct.type_id 
        LEFT JOIN Companies cmp ON c.company_id = cmp.company_id
        LEFT JOIN Users u ON c.car_owner_id = u.user_id
        LEFT JOIN user_info ui ON u.user_id = ui.user_id  -- Join user_info to fetch the phone number
        WHERE c.car_owner_id = %s  -- Filter by the logged-in user's user_id
        LIMIT %s OFFSET %s;
    """, (user_id, per_page, offset))
    cars = cursor.fetchall()

    # Fetch the total number of cars owned by the logged-in user to calculate total pages
    cursor.execute("""
        SELECT COUNT(*) AS total_cars FROM add_car WHERE car_owner_id = %s;
    """, (user_id,))
    total_cars = cursor.fetchone()['total_cars']
    total_pages = (total_cars + per_page - 1) // per_page  # Calculate total number of pages

    cursor.close()
    connection.close()

    # Render the template with the car data and pagination information
    return render_template('car_report.html', cars=cars, page=page, total_pages=total_pages)


# Edit function for car report
@app.route('/car_report/edit/<int:car_number>', methods=['GET', 'POST'])
def edit_car(car_number):
    if session.get('role') != 'Admin':
        flash('Access denied', 'danger')
        return redirect(url_for('some_other_route'))  # Redirect or show error if not admin.

    # Get the logged-in user's user_id from the session
    user_id = session.get('user_id')
    if not user_id:
        flash('User not logged in', 'danger')
        return redirect(url_for('login'))  # Redirect to login if user_id is not found

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    # Get car data to populate the edit form, ensuring it's the logged-in user's car
    cursor.execute("""SELECT * FROM add_car WHERE car_number = %s AND car_owner_id = %s;""", (car_number, user_id))
    car = cursor.fetchone()

    if car is None:
        flash('Car not found or you do not have permission to edit this car.', 'danger')
        return redirect(url_for('car_report'))  # If car not found or not owned by the user, redirect to the car report page.

    if request.method == 'POST':
        # Get updated values from the form
        car_name = request.form['car_name']
        stock = request.form['stock']
        price_per_day = request.form['price_per_day']
        
        # Check if a new image is uploaded
        car_img = car['car_img']  # Keep the current image by default

        if 'car_img' in request.files:  # If a new image is uploaded
            file = request.files['car_img']
            if file.filename != '':  # If there's a file
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))  # Save the new image
                car_img = filename  # Update the image filename
        
        # Update car data in the database
        cursor.execute(""" 
            UPDATE add_car
            SET car_name = %s, stock = %s, price_per_day = %s, car_img = %s
            WHERE car_number = %s AND car_owner_id = %s;
        """, (car_name, stock, price_per_day, car_img, car_number, user_id))
        connection.commit()

        flash('Car updated successfully', 'success')
        return redirect(url_for('car_report'))  # Redirect to the car report page after successful edit.

    cursor.close()
    connection.close()

    # Render edit form with existing car data
    return render_template('Edit_car_report.html', car=car)



@app.route('/car_report/delete/<int:car_number>', methods=['POST'])
def delete_car(car_number):
    if session.get('role') != 'Admin':
        flash('Access denied', 'danger')
        return redirect(url_for('login'))  # Redirect or show error if not admin.

    # Get the logged-in user's user_id from the session
    user_id = session.get('user_id')
    if not user_id:
        flash('User not logged in', 'danger')
        return redirect(url_for('login'))  # Redirect to login if user_id is not found

    # Get car data from the database to confirm it belongs to the logged-in user
    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute(""" 
        SELECT car_number FROM add_car WHERE car_number = %s AND car_owner_id = %s;
    """, (car_number, user_id))
    car = cursor.fetchone()

    if not car:
        flash('Car not found or you do not have permission to delete this car.', 'danger')
        return redirect(url_for('car_report'))  # Redirect if car doesn't exist or is not owned by the user.

    # Check if the car has associated bookings
    cursor.execute(""" 
        SELECT COUNT(*) FROM bookings WHERE car_number = %s;
    """, (car_number,))
    bookings_count = cursor.fetchone()[0]

    if bookings_count > 0:
        flash('Cannot delete this car because it has active bookings.', 'danger')
        return redirect(url_for('car_report'))  # Redirect if car has bookings.

    # Delete the car from the database
    cursor.execute(""" 
        DELETE FROM add_car WHERE car_number = %s AND car_owner_id = %s;
    """, (car_number, user_id))
    connection.commit()

    cursor.close()
    connection.close()

    flash('Car deleted successfully', 'success')
    return redirect(url_for('car_report'))  # Redirect to the car report page after successful delete.


# Car Type Report View function
@app.route('/car_types_report')
def car_types_report():
    user_id = session.get('user_id')
    if not user_id:
        flash('User not logged in', 'danger')
        return redirect(url_for('login'))  # Redirect to login if user_id is not found

    page = request.args.get('page', 1, type=int)
    per_page = 5  # Adjust per page value here if needed

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)  # Ensure dictionary=True to return rows as dictionaries
    
    # Fetch car types associated with the logged-in user
    query = "SELECT * FROM carTypes WHERE user_id = %s LIMIT %s OFFSET %s"
    cursor.execute(query, (user_id, per_page, (page - 1) * per_page))
    car_types = cursor.fetchall()

    # Get total pages for pagination
    cursor.execute("SELECT COUNT(*) FROM carTypes WHERE user_id = %s", (user_id,))
    total_count = cursor.fetchone()['COUNT(*)']
    total_pages = (total_count + per_page - 1) // per_page
    
    cursor.close()
    connection.close()

    return render_template('car_type_report.html', car_types=car_types, total_pages=total_pages, current_page=page, per_page=per_page)


# Edit button function in Car Type Report
@app.route('/edit_car_type/edit/<int:type_id>', methods=['GET', 'POST'])
def edit_car_type(type_id):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    user_id = session.get('user_id')

    if request.method == 'GET':
        # Get the car type data to pre-fill the edit form
        cursor.execute("SELECT * FROM carTypes WHERE type_id = %s", (type_id,))
        car_type = cursor.fetchone()

        cursor.close()
        connection.close()

        if car_type:
            return render_template('Edit_type_report.html', car_type=car_type)  # Render edit form with current data
        else:
            flash('Car type not found', 'danger')
            return redirect(url_for('car_types_report'))

    if request.method == 'POST':
        new_name = request.form['type_name']
        new_description = request.form['type_description']
        
        # Handle file upload (new image)
        if 'type_img' in request.files and request.files['type_img'].filename:
            file = request.files['type_img']
            filename = secure_filename(file.filename)
            file.save(os.path.join('static/uploads', filename))  # Save the file to the desired location
        else:
            # Keep the existing filename if no new file is uploaded
            cursor.execute("SELECT image FROM carTypes WHERE type_id = %s", (type_id,))
            result = cursor.fetchone()
            filename = result['image'] if result else None

        # Update the car type record
        cursor.execute("""
            UPDATE carTypes 
            SET type_name = %s, type_description = %s, image = %s
            WHERE type_id = %s
        """, (new_name, new_description, filename, type_id))
        
        connection.commit()

        cursor.close()
        connection.close()

        flash('Car type updated successfully', 'success')
        return redirect(url_for('car_types_report'))

# Delete button function in Car Type Report
@app.route('/delete_car_type/delete/<int:type_id>', methods=['POST'])
def delete_car_type(type_id):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    # First, delete cars that are using this car type
    cursor.execute("DELETE FROM add_car WHERE type_id = %s", (type_id,))
    connection.commit()

    # Then, delete the car type itself
    cursor.execute("DELETE FROM carTypes WHERE type_id = %s", (type_id,))
    connection.commit()

    cursor.close()
    connection.close()

    flash('Car type and related cars deleted successfully', 'success')
    return redirect(url_for('car_types_report'))


 

#  Company Report View function
@app.route('/company_report', methods=['GET'])
def company_report():
    user_id = session.get('user_id')
    if not user_id:
        flash('User not logged in', 'danger')
        return redirect(url_for('login'))  # Redirect to login if user_id is not found

    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 5, type=int)

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Fetch companies associated with the logged-in user
    cursor.execute('SELECT COUNT(*) FROM Companies WHERE user_id = %s', (user_id,))
    total_companies = cursor.fetchone()['COUNT(*)']
    total_pages = (total_companies + per_page - 1) // per_page

    cursor.execute('SELECT * FROM Companies WHERE user_id = %s LIMIT %s OFFSET %s', (user_id, per_page, (page - 1) * per_page))
    companies = cursor.fetchall()
    cursor.close()
    conn.close()
    print(companies)


    return render_template('company_report.html', companies=companies, total_pages=total_pages, current_page=page, per_page=per_page)

# View function for view button
# @app.route('/view_company/<int:company_id>', methods=['GET'])
# def view_company(company_id):
#     # Check if the user is authorized
#     if session.get('role') != 'Admin':
#         flash('Access denied', 'danger')
#         return redirect(url_for('company_report'))

#     # Get company details from the database
#     conn = get_db_connection()
#     cursor = conn.cursor(dictionary=True)
#     cursor.execute('SELECT * FROM Companies WHERE company_id = %s', (company_id,))
#     company = cursor.fetchone()

#     if not company:
#         flash('Company not found', 'danger')
#         return redirect(url_for('company_report'))

#     cursor.close()
#     conn.close()

#     # Render the company details page
#     return render_template('view_company.html', company=company)



# View function for Edit in Company Report
@app.route('/edit_company/<int:company_id>', methods=['GET', 'POST'])
def edit_company(company_id):
    if session.get('role') != 'Admin':
        flash('Access denied', 'danger')
        return redirect(url_for('company_report'))
    
    user_id = session.get('user_id')
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Fetch company details from the database
    cursor.execute('SELECT * FROM Companies WHERE company_id = %s', (company_id,))
    company = cursor.fetchone()

    if not company:
        flash('Company not found', 'danger')
        return redirect(url_for('company_report'))

    if request.method == 'POST':
        company_name = request.form['company_name']
        company_description = request.form['company_description']
        company_img = company['image']  # Keep the existing image by default

        # Check if a new image is uploaded
        if 'profile_picture' in request.files:
            file = request.files['profile_picture']
            if file and allowed_file(file.filename):
                # Secure the filename and save it
                filename = secure_filename(file.filename)
                image_path = os.path.join(UPLOAD_FOLDER, filename)
                file.save(image_path)
                company_img = filename  # Update company image with the new image

        # Update company details in the database
        cursor.execute(''' 
            UPDATE Companies SET 
            company_name = %s,
            company_description = %s,
            image = %s
            WHERE company_id = %s
        ''', (company_name, company_description, company_img, company_id))

        conn.commit()

        # Debugging: check if the commit was successful
        if cursor.rowcount == 0:
            print("No rows updated.")
        else:
            print(f"Updated {cursor.rowcount} row(s).")

        cursor.close()
        conn.close()

        flash('Company updated successfully!', 'success')
        return redirect(url_for('company_report'))

    cursor.close()
    conn.close()

    # Render the edit form with the existing company data
    return render_template('Edit_company_report.html', company=company)

@app.route('/delete_company/<int:company_id>', methods=['POST'])
def delete_company(company_id):
    if session.get('role') != 'Admin':
        flash('Access denied', 'danger')
        return redirect(url_for('company_report'))
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # First, check for dependent records in the add_car table
    cursor.execute("SELECT COUNT(*) FROM add_car WHERE company_id = %s", (company_id,))
    result = cursor.fetchone()

    if result['COUNT(*)'] > 0:
        # Option 1: Delete dependent records in add_car and bookings first
        cursor.execute("DELETE FROM bookings WHERE car_number IN (SELECT car_number FROM add_car WHERE company_id = %s)", (company_id,))
        cursor.execute("DELETE FROM add_car WHERE company_id = %s", (company_id,))
        conn.commit()

        # Option 2: Or, just disassociate cars from the company using SET NULL
        # cursor.execute("UPDATE add_car SET company_id = NULL WHERE company_id = %s", (company_id,))
        # conn.commit()

    # Now delete the company
    cursor.execute("DELETE FROM Companies WHERE company_id = %s", (company_id,))
    conn.commit()

    cursor.close()
    conn.close()

    flash('Company deleted successfully!', 'success')
    return redirect(url_for('company_report'))



# customer report view function
@app.route('/customer_report', methods=['GET'])
def customer_report():
    # Check if admin is logged in (admin user should have role 'Admin' in the session)
    if session.get('role') != 'Admin':
        flash('Access denied', 'danger')
        return redirect(url_for('login'))  # Redirect or show error page if not admin.

    # Get the current page from query parameters
    page = request.args.get('page', 1, type=int)
    per_page = 3  # Items per page

    # Get the user_id of the logged-in admin
    admin_user_id = session.get('user_id')

    # Database connection
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Get the total number of users who have bookings for cars managed by this admin
    cursor.execute('''
        SELECT COUNT(DISTINCT u.user_id) 
        FROM Users u
        JOIN Bookings b ON u.user_id = b.user_id
        JOIN add_car ac ON b.car_number = ac.car_number
        WHERE ac.car_owner_id = %s
    ''', (admin_user_id,))
    total_users = cursor.fetchone()['COUNT(DISTINCT u.user_id)']
    total_pages = (total_users + per_page - 1) // per_page

    # Fetch users who have bookings for cars managed by this admin (pagination)
    cursor.execute('''
        SELECT u.user_id, u.username, ui.profile_picture, ui.phone_number, ui.email, ui.gender, ui.birthday 
        FROM Users u
        JOIN User_info ui ON u.user_id = ui.user_id
        JOIN Bookings b ON u.user_id = b.user_id
        JOIN add_car ac ON b.car_number = ac.car_number
        WHERE ac.car_owner_id = %s
        LIMIT %s OFFSET %s
    ''', (admin_user_id, per_page, (page - 1) * per_page))

    users = cursor.fetchall()

    # Close the database connection
    cursor.close()
    conn.close()

    # Render template with users and pagination info
    return render_template('Customer_report.html', users=users, total_pages=total_pages, current_page=page)

# Edit functionality view function for Customer Report
@app.route('/edit_user/<int:user_id>', methods=['GET', 'POST'])
def edit_user(user_id):
    # Connect to the database
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Fetch the user details by user_id
    cursor.execute('''SELECT u.user_id, u.username, ui.profile_picture, ui.phone_number, ui.email, ui.gender, ui.birthday
                      FROM Users u
                      JOIN User_info ui ON u.user_id = ui.user_id
                      WHERE u.user_id = %s''', (user_id,))
    user = cursor.fetchone()

    if request.method == 'POST':
        # Get form data
        username = request.form['username']
        phone_number = request.form['phone_number']
        email = request.form['email']
        gender = request.form['gender']
        birthday = request.form['birthday']
        profile_picture = request.files.get('profile_picture')

        # Check if the email is already in use by another user (excluding the current user)
        cursor.execute('''SELECT COUNT(*) FROM User_info WHERE email = %s AND user_id != %s''', (email, user_id))
        email_exists = cursor.fetchone()['COUNT(*)']

        if email_exists > 0:
            flash('This email is already taken by another user. Please choose a different one.', 'danger')
            return redirect(url_for('edit_user', user_id=user_id))  # Redirect back to the edit form

        # Handle file upload (optional)
        if profile_picture:
            profile_picture_path = f"static/uploads/{profile_picture.filename}"
            profile_picture.save(profile_picture_path)
        else:
            profile_picture_path = user['profile_picture']

        # Update the user details in the database
        cursor.execute('''UPDATE Users u
                          JOIN User_info ui ON u.user_id = ui.user_id
                          SET u.username = %s, ui.phone_number = %s, ui.email = %s, ui.gender = %s, ui.birthday = %s, ui.profile_picture = %s
                          WHERE u.user_id = %s''',
                       (username, phone_number, email, gender, birthday, profile_picture_path, user_id))
        conn.commit()

        flash('User details updated successfully!', 'success')
        cursor.close()
        conn.close()

        return redirect(url_for('customer_report'))  # Redirect back to user report page

    # Render the edit form with existing user data
    cursor.close()
    conn.close()
    return render_template('Edit_customer_report.html', user=user)
 # Redirect back to user report page

    # Render the edit form with existing user data
    cursor.close()
    conn.close()
    return render_template('Edit_customer_report.html', user=user)

# Delete view function for customer_report 
@app.route('/delete_user/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor = conn.cursor(dictionary=True)  # Make sure this is set for the cursor

    # Check if the user is referenced in the 'add_car' table (or other related tables)
    cursor.execute('SELECT COUNT(*) AS car_count FROM add_car WHERE car_owner_id = %s', (user_id,))
    result = cursor.fetchone()
    
    # Check if there are any cars related to the user
    if result['car_count'] > 0:
        flash('Cannot delete this user because they own cars in the add_car table.', 'danger')
        return redirect(url_for('customer_report'))

    # If no cars are associated, proceed to delete the user from user_info and Users tables
    try:
        # First, delete the child record(s) from user_info
        cursor.execute('DELETE FROM user_info WHERE user_id = %s', (user_id,))
        
        # Then, delete the parent record from Users
        cursor.execute('DELETE FROM Users WHERE user_id = %s', (user_id,))
        
        conn.commit()  # Commit the changes to the database
        flash('User deleted successfully!', 'success')
    except Exception as e:
        conn.rollback()  # Rollback in case of any error
        flash(f'Error deleting user: {str(e)}', 'danger')
    
    cursor.close()
    conn.close()

    return redirect(url_for('customer_report'))  # Redirect to the customer report page


@app.route('/booking_report', methods=['GET'])
def booking_report():
    # Ensure the logged-in user is an Admin
    # if session.get('role') != 'Admin':
    #     flash('Access denied', 'danger')
    #     return redirect(url_for('booking_report'))  # Redirect or show error page if not admin.

    # Get the current page and per_page (items per page)
    page = request.args.get('page', 1, type=int)  # Default to page 1 if not provided
    per_page = 5  # Number of bookings per page
    offset = (page - 1) * per_page

    # Get the user_id of the logged-in admin from the session
    admin_user_id = session.get('user_id')

    # SQL query to fetch bookings for the current admin along with car info (including car image path)
    query = """
        SELECT b.booking_id, u.username, ui.email, ui.phone_number, b.created_at, 
               ac.car_name, ac.car_img, ac.price_per_day, 
               b.pickup_date, b.dropoff_date, b.pickup_address, b.dropoff_address
        FROM Bookings b
        JOIN users u ON b.user_id = u.user_id
        JOIN user_info ui ON u.user_id = ui.user_id
        JOIN add_car ac ON ac.car_number = b.car_number  # Assuming car_number links to the car
        WHERE b.user_id = %s  # Filter by logged-in admin's user_id
        LIMIT %s OFFSET %s;
    """
    
    # Database connection
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(query, (admin_user_id, per_page, offset))  # Fetch bookings for the admin
    bookings = cursor.fetchall()

    # Get total count of bookings for pagination (count only bookings for the logged-in admin)
    cursor.execute("""
        SELECT COUNT(*) FROM Bookings b
        WHERE b.user_id = %s;
    """, (admin_user_id,))
    total_bookings = cursor.fetchone()['COUNT(*)']
    cursor.close()

    # Calculate total pages for pagination
    total_pages = (total_bookings // per_page) + (1 if total_bookings % per_page else 0)

    # Render the template with bookings and pagination info
    return render_template('booking_report.html', bookings=bookings, total_pages=total_pages, current_page=page)





    
# Add car view function
@app.route('/add_car', methods=['GET', 'POST'])
def add_car():
    # if session.get('role') != 'Admin':
    #     flash('Access denied', 'danger')
    #     return redirect(url_for('index'))

    # Fetch car types and companies
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute('SELECT * FROM CarTypes')
    car_types = cursor.fetchall()

    cursor.execute('SELECT * FROM Companies')
    companies = cursor.fetchall()

    cursor.close()
    conn.close()

    if request.method == 'POST':
        car_name = request.form['car_name']
        car_type_id = request.form['car_type']  # This should correspond to the selected car type ID
        company_id = request.form['company_name']  # This should correspond to the selected company ID
        price_per_day = request.form['price_per_day']
        stock = request.form['stock']
        image_file = request.files.get('car_image')
        from_location = request.form['from_location']
        to_location = request.form['to_location']
        description = request.form['description']

        car_owner_id = session.get('user_id')  # Get the logged-in user's ID

        # Handle the file upload
        if image_file and allowed_file(image_file.filename):
            filename = secure_filename(image_file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

            # Save the file
            image_file.save(file_path)
            image_url = f"{filename}"
        else:
            image_url = None  # If no image is uploaded, store None

        # Fetch the actual car type and company names using the selected IDs to ensure consistency
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute('SELECT type_name FROM CarTypes WHERE type_id = %s', (car_type_id,))
        car_type = cursor.fetchone()

        cursor.execute('SELECT company_name FROM Companies WHERE company_id = %s', (company_id,))
        company = cursor.fetchone()

        cursor.close()
        conn.close()

        if not car_type or not company:
            flash('Invalid car type or company selected', 'danger')
            return redirect(url_for('add_car'))

        # Connect to the database again for the final insert operation
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO add_car (car_owner_id, car_name, from_location, to_location, type_id, company_id, car_type, company_name, price_per_day, stock, car_img, description) '
                       'VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)',
                       (car_owner_id, car_name, from_location, to_location, car_type_id, company_id, car_type['type_name'], company['company_name'], price_per_day, stock, image_url, description))
        conn.commit()
        cursor.close()
        conn.close()
        # flash('Car added successfully', 'success')
        return jsonify({'success': True, 'message': 'Car added successfully!'})

    return render_template('Add_car.html', car_types=car_types, companies=companies)

# Add company view function
@app.route('/add_company', methods=['GET', 'POST'])
def add_company():
    if session.get('role') != 'Admin':
        flash('Access denied', 'danger')
        # return redirect(url_for('index'))
        return render_template('add_company.html')
    user_id = session.get('user_id')  # Get the user_id from session
    
    if request.method == 'POST':
        company_name = request.form['company_name']
        description = request.form['company_description']
        image= request.files['company_image']
        upload_folder = os.path.join('static', 'Uploads')
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)

        image_filename = image.filename
        image.save(os.path.join(upload_folder, image_filename))

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('INSERT INTO Companies (company_name, company_description,image,user_id) VALUES (%s, %s,%s,%s)',
                       (company_name, description,image_filename, user_id))
        conn.commit()
        cursor.close()
        conn.close()

        # flash('Company added successfully', 'success')
        flash(f"Company '{company_name}' added successfully!", "success")
        # return redirect(url_for('admin_dashboard'))
        return redirect(url_for('company_report'))  # Redirect to clear the form and avoid re-submission
    
    return render_template('Add_company.html')

@app.route('/Add_type')
def Add_type():
    return render_template('Add_company.html')

# Add Car Type View function
@app.route('/add_car_type', methods=['GET', 'POST'])
def add_car_type():
    if session.get('role') != 'Admin':
        flash('Access denied', 'danger')
        # return redirect(url_for('index'))
        return render_template('Add_type.html')

    user_id = session.get('user_id')
    if request.method == 'POST':
        # Get the data sent via the fetch request
        car_type = request.form.get('carType')
        type_description = request.form.get('typeDescription')
        image = request.files['company_image']

        upload_folder = os.path.join('static', 'Uploads')
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)

        image_filename = image.filename
        image.save(os.path.join(upload_folder, image_filename))

        # Check if all fields are provided
        if not car_type or not type_description or not image:
            flash("All fields are required, including the company image.", 'danger')
            return render_template('add_car_type.html')
        
        # Connect to the database
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # try
            # Insert the car type and description into the database
        cursor.execute('INSERT INTO CarTypes (type_name, type_description,image, user_id) VALUES (%s, %s, %s, %s)', (car_type, type_description,image_filename, user_id))
        conn.commit()
        cursor.close()
        conn.close()

            # Return success response
        return redirect(url_for('car_types_report'))
        return jsonify({"message": "Car type added successfully!"}), 200

        # except Exception as e:
        #     conn.rollback()  # In case of an error, rollback
        #     cursor.close()
        #     conn.close()
        #     return jsonify({"message": "Error adding car type: " + str(e)}), 500

    # For GET request, render the form
    return render_template('Add_type.html')

# Profile page view function
@app.route('/Account', methods=['GET', 'POST'])
def Account():
    user_id = session.get('user_id')  # Get the user_id from session
    
    if not user_id:
        flash('User not logged in', 'danger')
        return redirect(url_for('login'))

    # Fetch the current user data from the database (using JOIN)
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT u.user_id, u.username, u.role, ui.email, ui.phone_number, ui.address_line1, ui.address_line2, 
               ui.city, ui.state, ui.country, ui.gender, ui.birthday, ui.profile_picture
        FROM users u
        JOIN user_info ui ON u.user_id = ui.user_id
        WHERE u.user_id = %s
    """, (user_id,))
    user = cursor.fetchone()

    # Fetch countries, states, and cities for dropdowns
    cursor.execute('SELECT DISTINCT country FROM user_info')
    countries = cursor.fetchall()
    cursor.execute('SELECT DISTINCT state FROM user_info')
    states = cursor.fetchall()
    cursor.execute('SELECT DISTINCT city FROM user_info')
    cities = cursor.fetchall()

    if request.method == 'POST':
        # Get form data
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        country = request.form['country']
        state = request.form['state']
        city = request.form['city']
        address1 = request.form['address1']
        address2 = request.form['address2']
        # gender = request.form['gender']
        gender = request.form.get('gender')  # Use .get() to avoid KeyError
        birthday = request.form['dob']

        # Handle file upload (profile picture)
        file = request.files.get('profile_picture')
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            profile_picture = filename
        else:
            profile_picture = user['profile_picture']  # Keep the old profile picture if no new one is uploaded

        try:
            # Update user_info table
            cursor.execute("""
                UPDATE user_info
                SET email = %s, phone_number = %s, address_line1 = %s, address_line2 = %s, 
                    city = %s, state = %s, country = %s, gender = %s, birthday = %s, profile_picture = %s
                WHERE user_id = %s
            """, (email, phone, address1, address2, city, state, country, gender, birthday, profile_picture, user_id))

            # Update users table
            cursor.execute("""
                UPDATE users
                SET username = %s, role = %s
                WHERE user_id = %s
            """, (name, request.form['role'], user_id))

            conn.commit()
            flash('Account details updated successfully!', 'success')
            return redirect(url_for('Account'))
        except Exception as e:
            flash(f'Error occurred: {str(e)}', 'danger')
            return redirect(url_for('Account'))

    cursor.close()
    conn.close()

    return render_template('account.html', user=user, countries=countries, states=states, cities=cities)
# Ensure you have the allowed_file function and save_user_profile function as needed.

# Url for change password
@app.route('/change_password', methods=['GET', 'POST'])
def change_password():
    if 'loggedin' not in session:
        return redirect(url_for('login'))
    
    msg = ''
    user_id = session['user_id']
    error = None
    success = None


    if request.method == 'POST':
        conn = get_db_connection()
        old_password = request.form['user_password']
        new_password = request.form['newPassword']
        confirm_password = request.form['confirmPassword']
        cursor = conn.cursor(dictionary=True)

        # Check if old password matches
        cursor.execute('SELECT password FROM users WHERE User_id = %s', (user_id,))
        user = cursor.fetchone()
        print(f"User retrieved from DB: {user}")

        if conn is None:
            print("Database connection is not established!") 
        if not user:
            error = 'User not found.'
        elif user['password'] != old_password:
            error = 'Old password is incorrect!'
        elif new_password != confirm_password:
            error = 'New password and confirm password do not match!'
        elif len(new_password) < 8 or not any(char.isdigit() for char in new_password) or not any(char.isalpha() for char in new_password):
            error = 'New password must be at least 8 characters long and include letters and numbers.'
        else:
            # Update the password in the database
            cursor.execute("UPDATE users SET password = %s WHERE user_id = %s", (new_password, user_id))
            conn.commit()
            success = 'Password updated successfully!' 
            cursor.close()
    return render_template('Change_password.html', msg=msg,error=error, success=success)


# Url for logout
# @app.route('/logout')
# def logout():
#     session.pop('role', None)
#     session.pop('username', None)
#     flash('You have been logged out', 'success')
#     return redirect(url_for('index'))
@app.route('/logout')
def logout():
    session.clear()  # Clear all session data
    flash('You have been logged out', 'success')
    return redirect(url_for('index'))


# @app.route('/user_dashboard')
# def user_dashboard():
#     return render_template('User_Dashboard.html')

@app.route('/user_dashboard')
def user_dashboard():
    # Assuming you have a session with the logged-in user (e.g., stored in `session['user_id']`)
    user_id = session.get('user_id')  # Adjust based on how you're storing user sessions

    # Establish the database connection
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    # Query to get the count of bookings for the logged-in user
    cursor.execute("""
        SELECT COUNT(*) AS booking_count
        FROM Bookings
        WHERE user_id = %s
    """, (user_id,))

    # Fetch the result
    booking_count = cursor.fetchone()['booking_count']

    # Close the cursor and connection
    cursor.close()
    connection.close()

    # Pass the booking_count to the template
    return render_template('User_Dashboard.html', booking_count=booking_count)



    
if __name__ == '__main__':
    app.run(debug=True)
