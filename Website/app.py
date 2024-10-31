from flask import Flask, render_template, request, redirect, url_for, session, send_file
from flask_mysqldb import MySQL
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
UPLOAD_FOLDER = 'static/images'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure the upload folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Initialize MySQL
mysql = MySQL(app)

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
    # Ensure user is logged in before showing the dashboard
    if 'loggedin' in session:
        return render_template('dashboard.html', 
                               first_name=session['First_Name'], 
                               last_name=session['Last_Name'])
    # If not logged in, redirect to login page
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
            # Add a new customer
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
            # Remove a customer
            customer_id = request.form['customer_id']
            cursor.execute('DELETE FROM CUSTOMER WHERE Customer_ID = %s', (customer_id,))
            mysql.connection.commit()

        elif action == 'select':
            # Select a customer and store their ID in session
            customer_id = request.form['customer_id']
            session['Customer_ID'] = customer_id  # Store customer ID in session
            return redirect(url_for('notes'))  # Redirect to notes after selecting customer

    cursor.execute('SELECT * FROM CUSTOMER')
    customers = cursor.fetchall()
    return render_template('customer_profile.html', customers=customers)

# Inventory route
@app.route('/inventory', methods=['GET', 'POST'])
def inventory():
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

    # For GET request, fetch the inventory items with tags
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

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/inventory/remove/<sku>', methods=['POST'])
def remove_item(sku):
    cursor = mysql.connection.cursor()
    
    # First, delete any related entries in ITEM_TAGS
    cursor.execute("DELETE FROM ITEM_TAGS WHERE SKU = %s", (sku,))
    
    # Now delete the item from the ITEM table
    cursor.execute("DELETE FROM ITEM WHERE SKU = %s", (sku,))
    
    mysql.connection.commit()
    cursor.close()
    return '', 204  # No content

@app.route('/inventory/image/<sku>', methods=['GET'])
def get_image(sku):
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT Picture FROM ITEM WHERE SKU = %s", (sku,))
    result = cursor.fetchone()
    cursor.close()

    if result and result[0]:
        return send_file(io.BytesIO(result[0]), mimetype='image/jpeg')
    else:
        return '', 404  # Not found

#notes route
@app.route('/notes', methods=['GET', 'POST'])
def notes():
    # Check if 'Customer_ID' is in session; if not, redirect to customer_profile
    if 'Customer_ID' not in session:
        return redirect(url_for('customer_profile'))

    customer_id = session['Customer_ID']
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    if request.method == 'POST':
        note_title = request.form['note_title']
        note_content = request.form['note_content']

        # Add a new note
        cursor.execute('INSERT INTO NOTES (title, content, customer_id) VALUES (%s, %s, %s)', 
                       (note_title, note_content, customer_id))
        mysql.connection.commit()
        return redirect(url_for('notes'))

    # Fetch notes for the selected customer
    cursor.execute('SELECT title, content FROM NOTES WHERE customer_id = %s', (customer_id,))
    notes = cursor.fetchall()
    return render_template('notes.html', notes=notes)

@app.route('/notes/delete/<title>', methods=['POST'])
def delete_note(title):
    cursor = mysql.connection.cursor()
    cursor.execute('DELETE FROM NOTES WHERE title = %s', (title,))
    mysql.connection.commit()
    cursor.close()
    return redirect(url_for('notes'))  # Redirect back to notes after deletion

# Logout route
@app.route('/logout')
def logout():
    # Remove user session data
    session.pop('loggedin', None)
    session.pop('Employee_ID', None)
    session.pop('Employee_Email', None)
    session.pop('First_Name', None)
    session.pop('Last_Name', None)
    # Redirect to login page
    return redirect(url_for('login'))

# Registration route
@app.route('/register', methods=['GET', 'POST'])
def register():
    msg = ''
    if request.method == 'POST':
        print("Form submitted!")  # Debugging statement
        if 'name' in request.form and 'Employee_Password' in request.form and 'Employee_Email' in request.form and 'confirm_password' in request.form:
            name = request.form['name']
            firstName, lastName = name.split(" ", 1)
            password = request.form['Employee_Password']
            confirm_password = request.form['confirm_password']
            email = request.form['Employee_Email']

            # Check if passwords match
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
                try:
                    # Add password for employee
                    cursor.execute('INSERT INTO EMPLOYEE (First_Name, Last_Name, Employee_Email, Employee_Password) VALUES (%s, %s, %s, %s)', 
                                   (firstName, lastName, email, password))
                    mysql.connection.commit()
                    msg = 'You have successfully registered!'
                    print("Registration successful!")
                    return redirect(url_for('login'))
                except MySQLdb.Error as err:
                    print(f"Database error: {err}")
                    msg = 'There was an issue with registration. Please try again.'
    return render_template('registration.html', msg=msg)

if __name__ == '__main__':
    app.run()
