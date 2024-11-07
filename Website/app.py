from flask import Flask, render_template, request, redirect, url_for, session, send_file, flash, jsonify
from flask_mysqldb import MySQL
import logging
import MySQLdb.cursors
import re
import io
import os
from werkzeug.utils import secure_filename
import ssl
import mysql.connector
import base64

app = Flask(__name__)

# Change this to your secret key
app.secret_key = ':)'

# Get the absolute path to the ca.pem file
current_dir = os.path.dirname(os.path.abspath(__file__))
ca_path = os.path.join(current_dir, 'Backend', 'ca.pem')

# Ensure the ca.pem file exists
if not os.path.exists(ca_path):
    raise FileNotFoundError(f"SSL Certificate not found at {ca_path}")

# Database configuration
app.config['MYSQL_HOST'] = 'palacejewelers-palacejewelers.j.aivencloud.com'
app.config['MYSQL_USER'] = 'avnadmin'
app.config['MYSQL_PASSWORD'] = 'AVNS_eTE1cr2Go3sTM_VZneL'
app.config['MYSQL_DB'] = 'PalaceDatabase'
app.config['MYSQL_PORT'] = 16246
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

# SSL Configuration
ssl_config = {
    'ssl': {
        'ca': ca_path
    }
}

try:
    # Initialize MySQL with SSL
    mysql = MySQL(app)
    
    # Test connection
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT 1')
    cursor.close()
    print("Database connection successful!")
    
except Exception as e:
    print(f"Error connecting to database: {e}")
    raise

# File upload configuration
UPLOAD_FOLDER = 'Website/static/images'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Allowed file extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_db_cursor():
    try:
        return mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    except Exception as e:
        print(f"Error getting cursor: {e}")
        # Try to reconnect
        mysql.connection.ping(reconnect=True)
        return mysql.connection.cursor(MySQLdb.cursors.DictCursor)

@app.route('/', methods=['GET', 'POST'])
def login():
    msg = ''
    if request.method == 'POST' and 'Employee_Email' in request.form and 'Employee_Password' in request.form:
        try:
            cursor = get_db_cursor()
            email = request.form['Employee_Email']
            password = request.form['Employee_Password']
            
            cursor.execute('SELECT * FROM EMPLOYEE WHERE Employee_Email = %s AND Employee_Password = %s', (email, password))
            account = cursor.fetchone()
            cursor.close()

            if account:
                session['loggedin'] = True
                session['Employee_ID'] = account['Employee_ID']
                session['First_Name'] = account['First_Name']
                session['Last_Name'] = account['Last_Name']
                session['Employee_Email'] = account['Employee_Email']
                return redirect(url_for('dashboard'))
            else:
                msg = 'Incorrect email/password!'
        except Exception as e:
            print(f"Login error: {e}")
            msg = 'Database connection error. Please try again.'

    return render_template('login.html', msg=msg)
