from flask import Flask, request, render_template, redirect, url_for
import pyodbc

app = Flask(__name__)

conn_str = (
    "Driver = {SQL Server};"
    "Server = YOUR_SERVER_NAME;"
    "Database = AREngineering;"
    "Trusted_Connection = yes:"
)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO Users (username, email, password) VALUES (?, ?, ?)",(username, email, password))
        conn.commit()
        cursor.close()
        conn.close()

        return "Registration successful! You can now login."
    return render_template('register.html')

@app.route('/login', methods = ['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM Users Where username=? AND password=?', (username, password))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user:
            return f"welcome, {username}!"
        else:
            return "Invalid username or passowrd!"
    return render_template('login.html')

if __name__ == '__main__':
    app.run(debug=True)

    