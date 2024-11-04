from flask import Flask, render_template, request, redirect, url_for, session, send_file, flash
from flask_mysqldb import MySQL
import logging
import MySQLdb.cursors
import re
import io
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Change this to your secret key (can be anything, it's for extra protection)
app.secret_key = ':)'

# Enter your database connection details below
app.config['MYSQL_HOST'] = 'palacejewelers-palacejewelers.j.aivencloud.com'
app.config['MYSQL_USER'] = 'avnadmin'
app.config['MYSQL_PASSWORD'] = 'AVNS_eTE1cr2Go3sTM_VZneL'
app.config['MYSQL_DB'] = 'PalaceDatabase'
app.config['MYSQL_PORT'] = 16246

# Set the upload folder
UPLOAD_FOLDER = 'Website/static/images'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

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
            customer_id = request.form['customer_id']
            cursor.execute('DELETE FROM CUSTOMER WHERE Customer_ID = %s', (customer_id,))
            mysql.connection.commit()

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

    if request.method == 'POST':
        sku = request.form['sku']
        item_name = request.form['item_name']
        price = request.form['price']
        quantity = request.form['quantity']
        material = request.form['material']
        gemstone = request.form['gemstone']
        weight = request.form['weight']
        description = request.form['description']
        picture = request.files['picture']

        if picture and allowed_file(picture.filename):
            filename = secure_filename(picture.filename)
            picture_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            picture.save(picture_path)
        
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute(
                'INSERT INTO ITEM (SKU, Picture, Price, Name, Quantity) VALUES (%s, %s, %s, %s, %s)',
                (sku, filename, price, item_name, quantity)
            )
            cursor.execute(
                'INSERT INTO ITEM_TAGS (SKU, Material, Gemstone, Weight, Description) VALUES (%s, %s, %s, %s, %s)',
                (sku, material, gemstone, weight, description)
            )
            mysql.connection.commit()
            cursor.close()

        return redirect(url_for('inventory'))

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('''
        SELECT ITEM.SKU, ITEM.Picture, ITEM.Price, ITEM.Name, ITEM.Quantity, 
               ITEM_TAGS.Material, ITEM_TAGS.Gemstone, ITEM_TAGS.Weight, ITEM_TAGS.Description 
        FROM ITEM 
        LEFT JOIN ITEM_TAGS ON ITEM.SKU = ITEM_TAGS.SKU
    ''')
    items = cursor.fetchall()
    cursor.close()

    return render_template('inventory.html', items=items)

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
            # Check if the connection is alive
            mysql.connection.ping()

            # Retrieve form data
            repair_item_id = request.form['repair_item_id']
            item_name = request.form['item_name']
            condition = request.form['condition']
            repair_date = request.form['repair_date']
            repair_cost = request.form['repair_cost']
            notes = request.form['notes']
            picture = request.files['picture']
            customer_id = request.form['customer_id']
            employee_id = request.form['employee_id']
            subtotal = request.form['subtotal']
            tax = request.form['tax']
            total = request.form['total']

            if picture and allowed_file(picture.filename):
                filename = secure_filename(picture.filename)
                picture_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                picture.save(picture_path)

                cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                cursor.execute(
                    'INSERT INTO REPAIR_ITEM (Name, Condition, Repair_Date, Repair_Cost, Notes, Image, Customer_ID, Employee_ID, Subtotal, Tax, Total) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)',
                    (item_name, condition, repair_date, repair_cost, notes, filename, customer_id, employee_id, subtotal, tax, total)
                )
                mysql.connection.commit()
                cursor.close()
                print("Database insertion completed.")
                return redirect(url_for('repair_items'))
        except Exception as e:
            logging.error("Error during insertion: %s", e)
            print("Error during insertion:", e)
            return "Error during database operation", 500

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM REPAIR_ITEM')
    items = cursor.fetchall()
    cursor.close()

    return render_template('repair_items.html', repair_items=items)

# Get image route
@app.route('/repair_items/image/<repair_item_id>', methods=['GET'])
def get_repair_item_image(repair_item_id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT Image FROM REPAIR_ITEM WHERE Repair_Item_ID = %s", (repair_item_id,))
    result = cursor.fetchone()
    cursor.close()

    if result:
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], result['Image'])
        return send_file(image_path, mimetype='image/jpeg')
    else:
        return '', 404
    
@app.route('/orders_receipts')
def orders_receipts():
    # Add the logic for orders and receipts page here
    return render_template('orders_receipts.html')

if __name__ == '__main__':
    app.run(debug=True)
