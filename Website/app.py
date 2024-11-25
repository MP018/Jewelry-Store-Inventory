from flask import Flask, render_template, request, redirect, url_for, session, send_file, flash, jsonify, send_from_directory
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
import webbrowser
import threading
import time
import sys
import traceback
import hashlib
from pathlib import Path
from dotenv import load_dotenv

app = Flask(__name__, 
    static_url_path='/static',
    static_folder='static')

# Change this to your secret key (can be anything, it's for extra protection)
app.secret_key = ':)'

# Add upload folder configuration
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'images')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Create uploads directory if it doesn't exist
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Change this to your secret key (can be anything, it's for extra protection)
app.secret_key = ':)'

# Get the absolute path to the ca.pem file
current_dir = os.path.dirname(os.path.abspath(__file__))
ca_path = os.path.join(current_dir, 'Backend', 'ca.pem')

print(f"Looking for certificate at: {ca_path}")
if not os.path.exists(ca_path):
    print("Error: ca.pem not found!")
    sys.exit(1)
else:
    print("Certificate file found!")

# SSL Configuration
ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_REQUIRED
try:
    ssl_context.load_verify_locations(cafile=ca_path)
    print("SSL context created successfully")
except Exception as e:
    print(f"SSL context creation failed: {e}")
    traceback.print_exc()
    sys.exit(1)

# Load environment variables
load_dotenv()

# Update MySQL configuration
app.config.update(
    MYSQL_HOST=os.getenv('MYSQL_HOST', "palacejewelers-palacejewelers.j.aivencloud.com"),
    MYSQL_USER=os.getenv('MYSQL_USER', "avnadmin"),
    MYSQL_PASSWORD=os.getenv('MYSQL_PASSWORD', "AVNS_eTE1cr2Go3sTM_VZneL"),
    MYSQL_DB=os.getenv('MYSQL_DB', "PalaceDatabase"),
    MYSQL_PORT=int(os.getenv('MYSQL_PORT', 16246)),
    MYSQL_CURSORCLASS='DictCursor',
    MYSQL_SSL_CA=ca_path,
    MYSQL_SSL={
        'ca': ca_path,
        'check_hostname': False,
        'verify_mode': ssl.CERT_REQUIRED,
        'ssl_context': ssl_context
    }
)

# Initialize MySQL with custom SSL handling
try:
    mysql = MySQL(app)
    # Test connection immediately
    with app.app_context():
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT 1')
        cursor.close()
        print("Initial database connection test successful!")
except Exception as e:
    print(f"Error during MySQL initialization: {e}")

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def init_db():
    with app.app_context():
        try:
            print("Attempting database connection...")
            cursor = mysql.connection.cursor()
            cursor.execute('SELECT 1')
            result = cursor.fetchone()
            cursor.close()
            print(f"Database test query result: {result}")
            return True
        except Exception as e:
            print("\nDetailed connection error:")
            print("-" * 50)
            print(f"Error type: {type(e).__name__}")
            print(f"Error message: {str(e)}")
            print("\nTraceback:")
            traceback.print_exc()
            print("-" * 50)
            return False

# Allowed file extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Login route
@app.route('/', methods=['GET', 'POST'])
def login():
    msg = ''
    if request.method == 'POST' and 'Employee_Email' in request.form and 'Employee_Password' in request.form:
        try:
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            email = request.form['Employee_Email']
            password = request.form['Employee_Password']
            
            cursor.execute('SELECT * FROM EMPLOYEE WHERE Employee_Email = %s AND Employee_Password = %s', (email, password,))
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

# Dashboard page
@app.route('/dashboard')
def dashboard():
    if 'loggedin' in session:
        return render_template('dashboard.html', 
                               first_name=session['First_Name'], 
                               last_name=session['Last_Name'])
    return redirect(url_for('login'))

# Customer Profile page
@app.route('/customer_profile', methods=['GET', 'POST'])
def customer_profile():
    if 'loggedin' not in session:
        return redirect(url_for('login'))

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    if request.method == 'POST':
        action = request.form['action']
        
        if action == 'add':
            first_name = request.form['first_name']
            last_name = request.form['last_name']
            email = request.form['Customer_Email']
            phone_number = request.form['Customer_Phone']
            
            cursor.execute('SELECT * FROM CUSTOMER WHERE Customer_Email = %s', (email,))
            existing_customer = cursor.fetchone()

            if not existing_customer:
                cursor.execute('INSERT INTO CUSTOMER (First_Name, Last_Name, Customer_Email, Customer_Phone) VALUES (%s, %s, %s, %s)', 
                               (first_name, last_name, email, phone_number))
                mysql.connection.commit()
        
        elif action == 'remove':
            try:
                customer_id = request.form['customer_id']
                # First delete associated notes
                cursor.execute('DELETE FROM NOTES WHERE customer_id = %s', (customer_id,))
                # Then delete the customer
                cursor.execute('DELETE FROM CUSTOMER WHERE Customer_ID = %s', (customer_id,))
                mysql.connection.commit()
            except Exception as e:
                print(f"Error deleting customer: {e}")
                mysql.connection.rollback()

        elif action == 'select':
            customer_id = request.form['customer_id']
            session['Customer_ID'] = customer_id
            return redirect(url_for('notes'))

        return redirect(url_for('customer_profile'))

    cursor.execute('SELECT * FROM CUSTOMER')
    customers = cursor.fetchall()
    return render_template('customer_profile.html', customers=customers)

# Add this helper function to calculate file hash
def get_file_hash(file_data):
    """Calculate SHA-256 hash of file data"""
    return hashlib.sha256(file_data).hexdigest()

# Define the base directory for the project
BASE_DIR = Path(__file__).resolve().parent

def save_image(image_file):
    """
    Save image file and return filename. If image already exists, return existing filename.
    """
    if not image_file:
        return None
        
    try:
        # Secure the filename
        original_filename = secure_filename(image_file.filename)
        if not original_filename:
            return None
            
        # Read file data and get hash
        file_data = image_file.read()
        file_hash = hashlib.sha256(file_data).hexdigest()[:12]
        
        # Get file extension
        _, ext = os.path.splitext(original_filename)
        
        # Create new filename using hash
        filename = f"{file_hash}{ext}"
        
        # Create full path using BASE_DIR
        static_folder = os.path.join(BASE_DIR, 'static')
        images_folder = os.path.join(static_folder, 'images')
        file_path = os.path.join(images_folder, filename)
        
        # Ensure directories exist
        os.makedirs(images_folder, exist_ok=True)
        
        # Save file if it doesn't exist
        if not os.path.exists(file_path):
            image_file.seek(0)  # Reset file pointer
            image_file.save(file_path)
            print(f"Saved image to: {file_path}")
        else:
            print(f"Image already exists at: {file_path}")
            
        return filename
        
    except Exception as e:
        print(f"Error saving image: {e}")
        return None

# Update inventory route
@app.route('/inventory', methods=['GET', 'POST'])
def inventory():
    if 'loggedin' not in session:
        return redirect(url_for('login'))
        
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    if request.method == 'POST':
        try:
            # Get form data
            sku = request.form['sku']
            name = request.form['item_name']
            material = request.form['material']
            gemstone = request.form['gemstone']
            weight = request.form['weight']
            price = request.form['price']
            quantity = request.form['quantity']
            description = request.form['description']
            
            # Start transaction
            cursor.execute('START TRANSACTION')
            
            # Handle image upload first
            filename = None
            if 'picture' in request.files:
                image = request.files['picture']
                if image and image.filename:
                    filename = save_image(image)
                    print(f"Saved image filename: {filename}")
            
            # Insert into ITEM table
            cursor.execute('''
                INSERT INTO ITEM (SKU, Name, Price, Quantity, Picture, Sold)
                VALUES (%s, %s, %s, %s, %s, %s)
            ''', (sku, name, price, quantity, filename, 0))
            
            # Insert into ITEM_TAGS table
            cursor.execute('''
                INSERT INTO ITEM_TAGS (SKU, Material, Gemstone, Weight, Description)
                VALUES (%s, %s, %s, %s, %s)
            ''', (sku, material, gemstone, weight, description))
            
            # Commit transaction
            mysql.connection.commit()
            print(f"Successfully added item with SKU {sku}")
            flash('Item added successfully!')
            return redirect(url_for('inventory'))
            
        except Exception as e:
            mysql.connection.rollback()
            print(f"Error adding inventory item: {e}")
            flash(f'Error adding inventory item: {str(e)}')
            return redirect(url_for('inventory'))
    
    # GET request handling
    try:
        cursor.execute('''
            SELECT i.*, 
                   t.Material,
                   t.Gemstone,
                   t.Weight,
                   t.Description
            FROM ITEM i
            LEFT JOIN ITEM_TAGS t ON i.SKU = t.SKU
            WHERE i.Sold = 0
        ''')
        items = cursor.fetchall()
        
        # Process images for display - add debug prints
        for item in items:
            if item['Picture']:
                # Create the correct URL for the image
                image_url = url_for('static', filename=f'images/{item["Picture"]}')
                item['Picture'] = image_url
                print(f"SKU: {item['SKU']}, Image URL: {image_url}")  # Debug print
            else:
                print(f"SKU: {item['SKU']} has no image")  # Debug print
        
        cursor.close()
        return render_template('inventory.html', items=items)
    except Exception as e:
        print(f"Error fetching inventory: {e}")
        return str(e), 500

@app.route('/inventory/remove/<int:sku>', methods=['POST'])
def remove_inventory_item(sku):
    if 'loggedin' not in session:
        return jsonify({'error': 'Not logged in'}), 401
        
    try:
        cursor = mysql.connection.cursor()
        # Delete from ITEM_TAGS first (child table)
        cursor.execute('DELETE FROM `ITEM_TAGS` WHERE SKU = %s', (sku,))
        # Then delete from ITEM (parent table)
        cursor.execute('DELETE FROM `ITEM` WHERE SKU = %s', (sku,))
        mysql.connection.commit()
        cursor.close()
        return jsonify({'success': True})
    except Exception as e:
        mysql.connection.rollback()
        print(f"Error removing item: {e}")
        return jsonify({'error': str(e)}), 500

# Get image route
@app.route('/inventory/image/<sku>', methods=['GET'])
def get_image(sku):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT Picture FROM ITEM WHERE SKU = %s", (sku,))
    result = cursor.fetchone()
    cursor.close()

    if result and result['Picture']:
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], result['Picture'])
        if os.path.exists(image_path):
            return send_file(image_path, mimetype='image/jpeg')
    return '', 404

# Notes route
@app.route('/notes', methods=['GET', 'POST'])
def notes():
    if 'Customer_ID' not in session:
        return redirect(url_for('customer_profile'))

    customer_id = session['Customer_ID']
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    if request.method == 'POST':
        note_title = request.form['note_title']
        note_content = request.form['note_content']
        cursor.execute('INSERT INTO NOTES (title, content, customer_id) VALUES (%s, %s, %s)', 
                       (note_title, note_content, customer_id))
        mysql.connection.commit()

    cursor.execute('SELECT title, content FROM NOTES WHERE customer_id = %s', (customer_id,))
    notes = cursor.fetchall()
    return render_template('notes.html', notes=notes)

@app.route('/notes/delete/<title>', methods=['POST'])
def delete_note(title):
    cursor = mysql.connection.cursor()
    cursor.execute('DELETE FROM NOTES WHERE title = %s', (title,))
    mysql.connection.commit()
    cursor.close()
    return redirect(url_for('notes'))

# Logout route
@app.route('/logout')
def logout():
    # Clear the session data
    session.clear()
    # Redirect to login page with a message
    flash('You have been successfully logged out.')
    return redirect(url_for('login'))


@app.route('/repair_items', methods=['GET', 'POST'])
def repair_items():
    if 'loggedin' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        try:
            # Get form data
            repair_order_number = request.form['repair_order_number']
            item_name = request.form['item_name']
            description = request.form['description']
            repair_date = request.form['repair_date']
            repair_notes = request.form['repair_notes']
            customer_id = request.form['customer_id']
            employee_id = request.form['employee_id']
            subtotal = request.form['subtotal']
            tax = request.form['tax']
            total = request.form['total']

            cursor = mysql.connection.cursor()
            
            # Handle image upload
            if 'image' in request.files:
                image = request.files['image']
                if image and image.filename:
                    filename = save_image(image)
                    # Store only filename in database
                    cursor.execute(
                        'INSERT INTO REPAIR_ORDER (Repair_order_Number, Item_Name, Description, Employee_ID, Customer_ID, Image, Subtotal, Total, Tax, Repair_Date, Repair_Notes) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)',
                        (repair_order_number, item_name, description, employee_id,  customer_id, filename, subtotal, tax, total, repair_date, repair_notes)
                    )
            else:
                # No image provided
                cursor.execute(
                    'INSERT INTO REPAIR_ORDER (Repair_order_Number, Item_Name, Description, Employee_ID, Customer_ID, Subtotal, Total, Tax, Repair_Date, Repair_Notes) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)',
                    (repair_order_number, item_name, description, employee_id,  customer_id, subtotal, tax, total, repair_date, repair_notes)
                )
                
            
            mysql.connection.commit()
            cursor.close()
            
            return jsonify({'success': True}), 200
            
        except Exception as e:
            print(f"Error: {str(e)}")  # For debugging
            return jsonify({'error': str(e)}), 500
            
    # GET request - fetch existing repair orders
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM REPAIR_ORDER')
    repair_items = cursor.fetchall()
    
    # Process images for display
    for item in repair_items:
        if item['Image']:
            item['Image'] = url_for('static', filename=f"images/{item['Image']}")
    
    cursor.close()
    return render_template('repair_items.html', repair_items=repair_items)

@app.route('/remove_repair_item/<repair_order_number>', methods=['POST'])
def remove_repair_item(repair_order_number):
    if 'loggedin' not in session:
        return jsonify({'error': 'Not logged in'}), 401

    try:
        # First get the image filename
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT Image FROM REPAIR_ORDER WHERE Repair_Order_Number = %s', (repair_order_number,))
        result = cursor.fetchone()
        
        if result and result['Image']:
            # Delete the image file
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], result['Image'])
            if os.path.exists(image_path):
                os.remove(image_path)
        
        # Delete the database record
        cursor.execute('DELETE FROM REPAIR_ORDER WHERE Repair_Order_Number = %s', (repair_order_number,))
        mysql.connection.commit()
        cursor.close()
        return jsonify({'success': True}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/repair_items/image/<repair_order_number>', methods=['GET'])
def get_repair_item_image(repair_order_number):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT Image FROM REPAIR_ORDER WHERE Repair_Order_Number = %s", (repair_order_number,))
    result = cursor.fetchone()
    cursor.close()

    if result and result['Image']:
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], result['Image'])
        if os.path.exists(image_path):
            return send_file(image_path, mimetype='image/jpeg')
    return '', 404

@app.route('/orders_receipts', methods=['GET', 'POST'])
def orders_receipts():
    if 'loggedin' not in session:
        return redirect(url_for('login'))

    try:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        
        if request.method == 'POST':
            data = request.get_json()
            action = data.get('action')

            if action == 'save_order':
                order = data.get('order')
                customer_id = order.get('customer_id')
                employee_id = order.get('employee_id')
                subtotal = order.get('subtotal')
                tax = order.get('tax')
                total = order.get('total')

                # Insert the new order into the database
                cursor.execute("""
                    INSERT INTO ORDERS (Customer_ID, Employee_ID, Subtotal, Tax, Total, Sold_Date)
                    VALUES (%s, %s, %s, %s, %s, NOW())
                """, (customer_id, employee_id, subtotal, tax, total))
                mysql.connection.commit()
                return jsonify({'success': True}), 200

            elif action == 'delete_order':
                order_number = data.get('order_number')
                cursor.execute('DELETE FROM ORDERS WHERE Order_Number = %s', (order_number,))
                mysql.connection.commit()
                return jsonify({'success': True}), 200

        # Fetch orders with JOINs for customer and employee names
        query = '''
            SELECT o.*, 
                   c.First_Name as customer_first_name,
                   c.Last_Name as customer_last_name,
                   e.First_Name as employee_first_name,
                   e.Last_Name as employee_last_name
            FROM ORDERS o
            LEFT JOIN CUSTOMER c ON o.Customer_ID = c.Customer_ID
            LEFT JOIN EMPLOYEE e ON o.Employee_ID = e.Employee_ID
        '''
        cursor.execute(query)
        orders = cursor.fetchall()
        
        # Fetch customers
        cursor.execute('SELECT Customer_ID, First_Name, Last_Name FROM CUSTOMER')
        customers = cursor.fetchall()
        
        # Fetch employees
        cursor.execute('SELECT Employee_ID, First_Name, Last_Name FROM EMPLOYEE')
        employees = cursor.fetchall()
        
        cursor.close()
        
        # Determine the next order number
        next_order_number = max([order['Order_Number'] for order in orders], default=0) + 1
        
        return render_template('orders_receipts.html', orders=orders, customers=customers, employees=employees, next_order_number=next_order_number)
    except Exception as e:
        print(f"Error in orders_receipts: {e}")
        return str(e), 500

def open_browser():
    """Function to open the browser after a short delay"""
    time.sleep(1.5)  # Wait for server to start
    webbrowser.open('http://127.0.0.1:5000/')

# Update image serving route/logic
@app.route('/static/images/<path:filename>')
def serve_image(filename):
    try:
        # Clean the filename to prevent directory traversal
        filename = secure_filename(filename)
        return send_from_directory('static/images', filename)
    except Exception as e:
        app.logger.error(f"Error serving image {filename}: {e}")
        return "Image not found", 404

# Create directories when app starts
def create_upload_directories():
    """Create necessary upload directories"""
    static_folder = os.path.join(BASE_DIR, 'static')
    images_folder = os.path.join(static_folder, 'images')
    os.makedirs(images_folder, exist_ok=True)
    print(f"Ensuring upload directory exists: {images_folder}")

# Create directories when app starts
create_upload_directories()

@app.route('/debug/images')
def debug_images():
    """Debug route to list all images in the static/images directory"""
    images_dir = os.path.join(BASE_DIR, 'static', 'images')
    images = []
    try:
        for filename in os.listdir(images_dir):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                file_path = os.path.join(images_dir, filename)
                images.append({
                    'name': filename,
                    'path': file_path,
                    'exists': os.path.exists(file_path),
                    'size': os.path.getsize(file_path) if os.path.exists(file_path) else 0
                })
    except Exception as e:
        return f"Error: {str(e)}", 500
    
    return {'images': images}

if __name__ == '__main__':
    try:
        print("\nStarting JewelryNest Application...")
        print("Initializing database connection...")
        
        if init_db():
            print("\nDatabase connection successful!")
            print("Starting web server...")
            threading.Thread(target=open_browser, daemon=True).start()
            app.run(debug=False)
        else:
            print("\nFailed to initialize database connection.")
            print("Troubleshooting steps:")
            print("1. Verify ca.pem is in the Backend folder")
            print("2. Check internet connection")
            print("3. Verify database credentials")
            print("\nPress Enter to exit...")
            input()
            
    except Exception as e:
        print(f"\nApplication error: {e}")
        traceback.print_exc()
        input("\nPress Enter to exit...")
