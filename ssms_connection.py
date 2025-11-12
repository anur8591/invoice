from flask import Flask, request, render_template, redirect, session, send_file
import pyodbc
import io
import pdfkit


app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# --- Database Connection ---
conn_str = (
    "Driver={ODBC Driver 18 for SQL Server};"
    "Server=localhost\\ANURAG_SQL;"
    "Database=AREngineering;"
    "Trusted_Connection=yes;"
    "Encrypt=no;"
)

# ---------------- ROUTES ---------------- #

# Home page
@app.route("/")
def home():
    # Always render index.html, navbar handles login/profile display dynamically
    return render_template("index.html")


# Registration
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO Users (username, email, password) VALUES (?, ?, ?)",
                       (username, email, password))
        conn.commit()
        cursor.close()
        conn.close()
        return "Registration successful! You can now login."
    return render_template('register.html')


# Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM Users WHERE username=? AND password=?', (username, password))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user:
            # Save user info in session
            session['user_id'] = user[0]
            session['username'] = user[1]
            # Redirect to homepage, index.html will show Profile now
            return redirect('/')
        else:
            return "Invalid username or password!"
    return render_template('login.html')


# Dashboard (only accessible if logged in)
@app.route('/dashboard')
def dashboard():
    if 'user_id' in session:
        return render_template('dashboard.html', username=session['username'])
    else:
        return redirect('/login')


# Logout
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')


# ---------- CREATE INVOICE ----------
@app.route('/create_invoice', methods=['GET', 'POST'])
def create_invoice():
    if request.method == 'POST':
        # Render invoice_template.html using the form data
        html = render_template('invoice_template.html', form_data=request.form)

        # Generate PDF from HTML (wkhtmltopdf must be installed)
        pdf = pdfkit.from_string(html, False)

        # Return the PDF as download
        return send_file(
            io.BytesIO(pdf),
            download_name="Invoice.pdf",
            mimetype="application/pdf"
        )

    # Show the invoice creation form if GET request
    return render_template('invoice.html')



# ---------------- RUN APP ---------------- #
if __name__ == '__main__':
    app.run(debug=True)
