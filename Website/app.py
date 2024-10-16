from flask import Flask, render_template, request, redirect, url_for, session
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re

app = Flask(__name__)

# Change this to your secret key (can be anything, it's for extra protection)
app.secret_key = ':)'

# Enter your database connection details below
app.config['MYSQL_HOST'] = 'palacejewelers-palacejewelers.j.aivencloud.com'
app.config['MYSQL_USER'] = 'avnadmin'
app.config['MYSQL_PASSWORD'] = 'AVNS_eTE1cr2Go3sTM_VZneL'
app.config['MYSQL_DB'] = 'PalaceDatabase'
app.config['MYSQL_PORT'] = 16246

# Intialize MySQL
mysql = MySQL(app)

# http://localhost:5000/pythonlogin/ - this will be the login page, we need to use both GET and POST requests

@app.route('/', methods=['GET', 'POST'])
def login():
    msg = ''
    if request.method == 'POST' and 'Customer_Email' in request.form and 'Customer_Password' in request.form:
        email = request.form['Customer_Email']
        password = request.form['Customer_Password']
        
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM CUSTOMER WHERE Customer_Email = %s AND Customer_Password = %s', (email, password,))
        account = cursor.fetchone()

        if account:
            session['loggedin'] = True
            session['Customer_ID'] = account['Customer_ID']
            session['First_Name'] = account['First_Name']
            session['Last_Name'] = account['Last_Name']
            session['Customer_Email'] = account['Customer_Email']
            return redirect(url_for('home'))
        else:
            msg = 'Incorrect email/password!'

    return render_template('login.html', msg=msg)



@app.route('/logout')
def logout():
    # Remove session data, this will log the user out
   session.pop('loggedin', None)
   session.pop('Customer_ID', None)
   session.pop('Customer_Email', None)
   # Redirect to login page
   return redirect(url_for('login'))


# http://localhost:5000/Falsk/register - this will be the registration page, we need to use both GET and POST requests
@app.route('/register', methods=['GET', 'POST'])
def register():
    msg = ''
    if request.method == 'POST':
        print("Form submitted!")  # Debugging statement
        if 'name' in request.form and 'Customer_Password' in request.form and 'Customer_Email' in request.form:
            name = request.form['name']
            firstName, lastName = name.split(" ", 1)
            password = request.form['Customer_Password']
            email = request.form['Customer_Email']

            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('SELECT * FROM CUSTOMER WHERE Customer_Email = %s', (email,))
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
                    cursor.execute('INSERT INTO CUSTOMER (First_Name, Last_Name, Customer_Phone, Customer_Email, Customer_Password) VALUES (%s, %s, %s, %s, %s)', 
                                   (firstName, lastName, None, email, password,))
                    mysql.connection.commit()
                    msg = 'You have successfully registered!'
                    print("Registration successful!")
                except MySQLdb.Error as err:
                    print(f"Database error: {err}")
                    msg = 'There was an issue with registration. Please try again.'

    return render_template('registration.html', msg=msg)




if __name__ == '__main__':
    app.run()
