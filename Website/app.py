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

# Change this to your secret key (can be anything, it's for extra protection)
app.secret_key = ':)'

# Get the absolute path to the ca.pem file
current_dir = os.path.dirname(os.path.abspath(__file__))
ca_path = os.path.join(current_dir, 'Backend', 'ca.pem')

# Database configuration with SSL
app.config['MYSQL_HOST'] = 'palacejewelers-palacejewelers.j.aivencloud.com'
app.config['MYSQL_USER'] = 'avnadmin'
app.config['MYSQL_PASSWORD'] = 'AVNS_eTE1cr2Go3sTM_VZneL'
app.config['MYSQL_DB'] = 'PalaceDatabase'
app.config['MYSQL_PORT'] = 16246
app.config['MYSQL_SSL'] = {
    'ca': ca_path,
    'check_hostname': False,
    'verify_mode': ssl.CERT_NONE
}

# File upload configuration
UPLOAD_FOLDER = 'Website/static/images'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Create upload folder if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Ensure the upload folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Initialize MySQL
mysql = MySQL(app)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


# Allowed file extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Login route
@app.route('/', methods=['GET', 'POST'])
def login():
    msg = ''
    if request.method == 'POST' and 'Employee_Email' in request.form and 'Employee_Password' in request.form:
        email = request.form['Employee_Email']
        password = request.form['Employee_Password']
        
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM EMPLOYEE WHERE Employee_Email = %s AND Employee_Password = %s', (email, password,))
        account = cursor.fetchone()

        if account:
            session['loggedin'] = True
            session['Employee_ID'] = account['Employee_ID']
            session['First_Name'] = account['First_Name']
            session['Last_Name'] = account['Last_Name']
            session['Employee_Email'] = account['Employee_Email']
            return redirect(url_for('dashboard'))
        else:
            msg = 'Incorrect email/password!'

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

# Inventory route
@app.route('/inventory', methods=['GET', 'POST'])
def inventory():
    if 'loggedin' not in session:
        return redirect(url_for('login'))
        
    try:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        
        # Join ITEM and ITEM_TAGS tables
        cursor.execute('''
            SELECT i.SKU, i.Picture, i.Price, i.Name, i.Quantity, i.Sold_Date,
                   t.Tag, t.Material, t.Gemstone, t.Weight, t.Description
            FROM ITEM i
            LEFT JOIN ITEM_TAGS t ON i.SKU = t.SKU
        ''')
        
        items = cursor.fetchall()
        
        # Process each item
        for item in items:
            # Handle Picture data
            if item['Picture'] is not None:
                try:
                    # If Picture is stored as a path
                    if isinstance(item['Picture'], str):
                        item['Picture'] = item['Picture']
                    # If Picture is stored as bytes
                    else:
                        import base64
                        item['Picture'] = f"data:image/jpeg;base64,{base64.b64encode(item['Picture']).decode('utf-8')}"
                except Exception as e:
                    print(f"Error processing image for SKU {item['SKU']}: {e}")
                    item['Picture'] = None
            
            # Convert decimal to float for JSON serialization
            if item['Price']:
                item['Price'] = float(item['Price'])
                
            # Format datetime for display
            if item['Sold_Date']:
                item['Sold_Date'] = item['Sold_Date'].strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.close()
        return render_template('inventory.html', items=items)
        
    except Exception as e:
        print(f"Error in inventory: {e}")
        return str(e), 500

# Get image route
@app.route('/inventory/image/<sku>', methods=['GET'])
def get_image(sku):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT Picture FROM ITEM WHERE SKU = %s", (sku,))
    result = cursor.fetchone()
    cursor.close()

    if result:
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], result['Picture'])
        return send_file(image_path, mimetype='image/jpeg')
    else:
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
    session.clear()
    return redirect(url_for('login'))

# Registration route
@app.route('/register', methods=['GET', 'POST'])
def register():
    msg = ''
    if request.method == 'POST':
        if 'name' in request.form and 'Employee_Password' in request.form and 'Employee_Email' in request.form and 'confirm_password' in request.form:
            name = request.form['name']
            firstName, lastName = name.split(" ", 1)
            password = request.form['Employee_Password']
            confirm_password = request.form['confirm_password']
            email = request.form['Employee_Email']

            if password != confirm_password:
                msg = 'Passwords do not match!'
                return render_template('registration.html', msg=msg)

            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('SELECT * FROM EMPLOYEE WHERE Employee_Email = %s', (email,))
            account = cursor.fetchone()

            if account:
                msg = 'Account already exists!'
            elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
                msg = 'Invalid email address!'
            elif not re.match(r'[A-Za-z0-9 ]+', name):
                msg = 'Name must contain only characters and numbers!'
            elif not name or not password or not email:
                msg = 'Please fill out the form!'
            else:
                cursor.execute('INSERT INTO EMPLOYEE (First_Name, Last_Name, Employee_Email, Employee_Password) VALUES (%s, %s, %s, %s)', 
                               (firstName, lastName, email, password))
                mysql.connection.commit()
                msg = 'You have successfully registered!'
                return redirect(url_for('login'))
    return render_template('registration.html', msg=msg)

@app.route('/repair_items', methods=['GET', 'POST'])
def repair_items():
    if 'loggedin' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        try:
            # Get form data
            repair_order_number = request.form['repair_order_number']
            item_name = request.form['item_name']
            condition = request.form['condition']
            repair_date = request.form['repair_date']
            notes = request.form['notes']
            customer_id = request.form['customer_id']
            employee_id = request.form['employee_id']
            subtotal = request.form['subtotal']
            tax = request.form['tax']
            total = request.form['total']
            
            # Handle file upload
            picture = request.files['picture']
            filename = None
            if picture and allowed_file(picture.filename):
                filename = secure_filename(picture.filename)
                picture.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            
            # Insert into database
            cursor = mysql.connection.cursor()
            cursor.execute("""
                INSERT INTO REPAIR_ORDER 
                (Repair_Order_Number, Item_Name, Description, Employee_ID, Customer_ID, 
                Image, Subtotal, Tax, Total, Repair_Date, Repair_Notes)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (repair_order_number, item_name, condition, employee_id, customer_id, 
                  filename, subtotal, tax, total, repair_date, notes))
            
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
    
    # Convert image data to string if it exists
    for item in repair_items:
        if item['Image'] and isinstance(item['Image'], bytes):
            item['Image'] = item['Image'].decode('utf-8')
    
    cursor.close()
    
    return render_template('repair_items.html', repair_items=repair_items)

@app.route('/remove_repair_item/<repair_order_number>', methods=['POST'])
def remove_repair_item(repair_order_number):
    if 'loggedin' not in session:
        return jsonify({'error': 'Not logged in'}), 401

    try:
        cursor = mysql.connection.cursor()
        cursor.execute('DELETE FROM REPAIR_ORDER WHERE Repair_Order_Number = %s', (repair_order_number,))
        mysql.connection.commit()
        cursor.close()
        return jsonify({'success': True}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Get image route
@app.route('/repair_items/image/<repair_item_id>', methods=['GET'])
def get_repair_item_image(repair_item_id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT Image FROM REPAIR_ORDER WHERE Repair_Item_ID = %s", (repair_item_id,))
    result = cursor.fetchone()
    cursor.close()

    if result:
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], result['Image'])
        return send_file(image_path, mimetype='image/jpeg')
    else:
        return '', 404
    
@app.route('/orders_receipts', methods=['GET', 'POST'])
def orders_receipts():
    if 'loggedin' not in session:
        return redirect(url_for('login'))

    try:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        
        if request.method == 'POST':
            if request.is_json:
                data = request.get_json()
                
                if data.get('action') == 'delete_order':
                    order_number = data.get('order_number')
                    cursor.execute('DELETE FROM `ORDER` WHERE Order_Number = %s', (order_number,))
                    mysql.connection.commit()
                    return jsonify({'success': True, 'message': 'Order deleted successfully'})
                
                elif data.get('action') == 'save_order':
                    order_data = data.get('order')
                    
                    # Generate a new order number
                    cursor.execute('SELECT MAX(Order_Number) as max_order FROM `ORDER`')
                    result = cursor.fetchone()
                    next_order_number = 1
                    if result['max_order']:
                        next_order_number = result['max_order'] + 1
                    
                    # Insert the order
                    cursor.execute('''
                        INSERT INTO `ORDER` (Order_Number, Customer_ID, Employee_ID, Subtotal, Tax, Total)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    ''', (
                        next_order_number,
                        order_data['customer_id'],
                        order_data['employee_id'],
                        order_data['subtotal'],
                        order_data['tax'],
                        order_data['total']
                    ))
                    mysql.connection.commit()
                    return jsonify({'success': True, 'message': 'Order saved successfully'})

        # Fetch all orders with customer and employee names
        cursor.execute('''
            SELECT o.*, 
                   c.First_Name as Customer_First_Name, 
                   c.Last_Name as Customer_Last_Name,
                   e.First_Name as Employee_First_Name, 
                   e.Last_Name as Employee_Last_Name
            FROM `ORDER` o
            JOIN CUSTOMER c ON o.Customer_ID = c.Customer_ID
            JOIN EMPLOYEE e ON o.Employee_ID = e.Employee_ID
            ORDER BY o.Order_Number DESC
        ''')
        orders = cursor.fetchall()
        
        # Fetch employees and customers for the dropdowns
        cursor.execute('SELECT Employee_ID, First_Name, Last_Name FROM EMPLOYEE')
        employees = cursor.fetchall()
        
        cursor.execute('SELECT Customer_ID, First_Name, Last_Name FROM CUSTOMER')
        customers = cursor.fetchall()
        
        return render_template('orders_receipts.html', 
                             orders=orders,
                             employees=employees,
                             customers=customers)
                             
    except Exception as e:
        print(f"Error in orders_receipts: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
