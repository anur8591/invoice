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
            session['user_id'] = user[0]
            session['username'] = user[1]
            return redirect('/')
        else:
            return "Invalid username or password!"
    return render_template('login.html')

# Dashboard
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

# Create Invoice
@app.route('/create_invoice', methods=['GET', 'POST'])
def create_invoice():
    if request.method == 'POST':
        form_data = request.form.to_dict(flat=False)

        invoice_data = {
            "customer_name": request.form.get("customer_name"),
            "gst_invoice_no": request.form.get("gst_invoice_no"),
            "date": request.form.get("date"),
            "description": form_data.get("description[]", []),
            "hsn_code": form_data.get("hsn_code[]", []),
            "quantity": form_data.get("quantity[]", []),
            "rate": form_data.get("rate[]", []),
            "cgst_rate": request.form.get("cgst_rate") or "0",
            "sgst_rate": request.form.get("sgst_rate") or "0",
            "bank_name": request.form.get("bank_name"),
            "branch": request.form.get("branch"),
            "account_no": request.form.get("account_no"),
            "ifsc": request.form.get("ifsc"),
        }

        html = render_template("invoice_template.html", data=invoice_data)

        config = pdfkit.configuration(
            wkhtmltopdf=r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe"
        )

        pdf = pdfkit.from_string(html, False, configuration=config)

        return send_file(
            io.BytesIO(pdf),
            download_name=f"Invoice_{invoice_data['gst_invoice_no']}.pdf",
            mimetype="application/pdf"
        )

    return render_template("invoice_form.html")

# ---------------- RUN APP ---------------- #
if __name__ == '__main__':
    app.run(debug=True)
