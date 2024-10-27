from flask import Flask, render_template, request, redirect, url_for, session, send_file
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re
import io



app = Flask(__name__)

# Change this to your secret key (can be anything, it's for extra protection)
app.secret_key = ':)'

# Enter your database connection details below
app.config['MYSQL_HOST'] = 'palacejewelers-palacejewelers.j.aivencloud.com'
app.config['MYSQL_USER'] = 'avnadmin'
app.config['MYSQL_PASSWORD'] = 'AVNS_eTE1cr2Go3sTM_VZneL'
app.config['MYSQL_DB'] = 'PalaceDatabase'
app.config['MYSQL_PORT'] = 16246

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
    # Ensure user is logged in before showing the customer profile
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
            
            # Check if the customer already exists
            cursor.execute('SELECT * FROM CUSTOMER WHERE Customer_Email = %s', (email,))
            existing_customer = cursor.fetchone()

            if not existing_customer:
                cursor.execute('INSERT INTO CUSTOMER (First_Name, Last_Name, Customer_Email, Customer_Phone) VALUES (%s, %s, %s, %s)', 
                               (first_name, last_name, email, phone_number))
                mysql.connection.commit()
            else:
                # Handle case where the customer already exists (e.g., flash a message)
                pass
        
        elif action == 'remove':
            customer_id = request.form['customer_id']
            cursor.execute('DELETE FROM CUSTOMER WHERE Customer_ID = %s', (customer_id,))
            mysql.connection.commit()

        # Redirect to avoid form resubmission
        return redirect(url_for('customer_profile'))

    cursor.execute('SELECT * FROM CUSTOMER')
    customers = cursor.fetchall()

    return render_template('customer_profile.html', 
                           first_name=session['First_Name'], 
                           last_name=session['Last_Name'],
                           customers=customers)


import uuid  # Import UUID for unique filenames

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
    
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute(
            'INSERT INTO ITEM (SKU, Picture, Price, Name, Quantity) VALUES (%s, %s, %s, %s, %s)',
            (sku, picture, price, item_name, quantity)
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

# Notes page
@app.route('/notes', methods=['GET', 'POST'])
def notes():
    # Ensure user is logged in before showing the notes
    if 'loggedin' not in session:
        return redirect(url_for('login'))

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    if request.method == 'POST':
        customer_id = request.form['customer_id']
        note_content = request.form['note_content']

        # Add the new note
        cursor.execute('INSERT INTO NOTES (Customer_ID, Note_Content) VALUES (%s, %s)', 
                       (customer_id, note_content))
        mysql.connection.commit()

        # Redirect to avoid form resubmission
        return redirect(url_for('notes'))

    cursor.execute('SELECT * FROM NOTES')
    notes = cursor.fetchall()

    return render_template('notes.html', 
                           first_name=session['First_Name'], 
                           last_name=session['Last_Name'],
                           notes=notes)

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
        if 'name' in request.form and 'Employee_Password' in request.form and 'Employee_Email' in request.form:
            name = request.form['name']
            firstName, lastName = name.split(" ", 1)
            password = request.form['Employee_Password']
            email = request.form['Employee_Email']

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
