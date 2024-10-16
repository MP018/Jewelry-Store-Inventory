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
app.config['MYSQL_DB'] = 'defaultdb'
app.config['MYSQL_PORT'] = 16246

# Intialize MySQL
mysql = MySQL(app)

# http://localhost:5000/pythonlogin/ - this will be the login page, we need to use both GET and POST requests

@app.route('/', methods=['GET', 'POST'])
def login():
    # Output message if something goes wrong...
    msg = ''
    # Check if "username" and "password" POST requests exist (user submitted form)
    if request.method == 'POST' and 'email' in request.form and 'password' in request.form:
        # Create variables for easy access
        email = request.form['email']
        password = request.form['password']
        # Check if account exists using MySQL
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM Customer WHERE email = %s AND password = %s', (email, password,))
        # Fetch one record and return result
        account = cursor.fetchone()
        # If account exists in the database
        if account:
            # Create session data, we can access this data in other routes
            session['loggedin'] = True
            session['id'] = account['id']
            session['First_Name'] = account['firstName']
            session['Last_Name'] = account['lastName']
            session['email'] = account['email']
            session['password'] = account['password']
            # Redirect to home page or other page
            return redirect(url_for('home'))  # Redirect after successful login
        else:
            # Account doesn't exist or incorrect username/password
            msg = 'Incorrect username/password!'
    # Show the login form with a message (if any)
    return render_template('login.html', msg=msg)


@app.route('/logout')
def logout():
    # Remove session data, this will log the user out
   session.pop('loggedin', None)
   session.pop('id', None)
   session.pop('email', None)
   # Redirect to login page
   return redirect(url_for('login'))


# http://localhost:5000/Falsk/register - this will be the registration page, we need to use both GET and POST requests
@app.route('/register', methods=['GET', 'POST'])
def register():
    msg = ''
    if request.method == 'POST' and 'name' in request.form and 'password' in request.form and 'email' in request.form:
        name = request.form['name']
        firstName, lastName = name.split(" ", 1)
        password = request.form['password']
        email = request.form['email']

        # Debugging output
        print(f"Name: {name}, First Name: {firstName}, Last Name: {lastName}, Email: {email}, Password: {password}")

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM Customer WHERE email = %s', (email,))
        account = cursor.fetchone()

        if account:
            msg = 'Account already exists!'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address!'
        elif not re.match(r'[A-Za-z0-9]+', name):
            msg = 'Username must contain only characters and numbers!'
        elif not name or not password or not email:
            msg = 'Please fill out the form!'
        else:
            try:
                # Attempt to insert into the database
                cursor.execute('INSERT INTO Customer (First_Name, Last_Name, password, email) VALUES (%s, %s, %s, %s)', (firstName, lastName, password, email,))
                mysql.connection.commit()
                msg = 'You have successfully registered!'
                print("Registration successful!")
            except MySQLdb.Error as err:
                print(f"Database error: {err}")
                msg = 'There was an issue with registration. Please try again.'
    
    elif request.method == 'POST':
        msg = 'Please fill out the form!'

    return render_template('registration.html', msg=msg)


if __name__ == '__main__':
    app.run()
