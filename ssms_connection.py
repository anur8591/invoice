from flask import Flask, request, render_template, redirect, session, send_file
import pyodbc
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import io

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

@app.route("/")
def home():
    if 'user_id' in session:
        return redirect('/dashboard')
    return render_template("index.html")


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
            return redirect('/dashboard')
        else:
            return "Invalid username or password!"
    return render_template('login.html')


@app.route('/dashboard')
def dashboard():
    if 'user_id' in session:
        return render_template('dashboard.html', username=session['username'])
    else:
        return redirect('/login')


@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')


# ---------- CREATE INVOICE ----------
@app.route('/create_invoice', methods=['GET', 'POST'])
def create_invoice():
    if request.method == 'POST':
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()

        customer_name = request.form['customer_name']
        gst_invoice_no = request.form['gst_invoice_no']
        date = request.form['date']
        description = request.form['description']
        hsn_code = request.form['hsn_code']
        quantity = int(request.form['quantity'])
        rate = float(request.form['rate'])
        cgst_rate = float(request.form['cgst_rate'])
        sgst_rate = float(request.form['sgst_rate'])
        bank_name = request.form['bank_name']
        branch = request.form['branch']
        account_no = request.form['account_no']
        ifsc = request.form['ifsc']

        amount = quantity * rate
        cgst_amount = (amount * cgst_rate) / 100
        sgst_amount = (amount * sgst_rate) / 100
        grand_total = round(amount + cgst_amount + sgst_amount, 2)
        total_value = amount

        cursor.execute("""
            INSERT INTO Invoices (customer_name, gst_invoice_no, date, description, hsn_code,
            quantity, rate, amount, total_value, cgst_rate, cgst_amount, sgst_rate, sgst_amount,
            round_off, grand_total, amount_in_words, bank_name, branch, account_no, ifsc)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (customer_name, gst_invoice_no, date, description, hsn_code, quantity, rate, amount,
              total_value, cgst_rate, cgst_amount, sgst_rate, sgst_amount, 0, grand_total,
              'Seven Thousand Seven Hundred Ninety Three Only', bank_name, branch, account_no, ifsc))
        conn.commit()
        cursor.close()
        conn.close()

        # --- Generate PDF ---
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=A4)
        p.setFont("Helvetica-Bold", 16)
        p.drawString(200, 800, "A.R. ENGINEERING")
        p.setFont("Helvetica", 10)
        p.drawString(180, 785, "WE UNDERTAKE ALL TYPE OF ENGINEERING WORKS")

        p.drawString(50, 750, f"Customer: {customer_name}")
        p.drawString(50, 735, f"Invoice No: {gst_invoice_no}   Date: {date}")
        p.drawString(50, 720, f"Description: {description}")
        p.drawString(50, 705, f"Amount: ₹{amount}")
        p.drawString(50, 690, f"CGST: ₹{cgst_amount}")
        p.drawString(50, 675, f"SGST: ₹{sgst_amount}")
        p.drawString(50, 660, f"Grand Total: ₹{grand_total}")
        p.showPage()
        p.save()
        buffer.seek(0)

        return send_file(buffer, as_attachment=True,
                         download_name=f"Invoice_{gst_invoice_no}.pdf",
                         mimetype='application/pdf')

    return render_template('invoice.html')


# ---------------- RUN APP ---------------- #
if __name__ == '__main__':
    app.run(debug=True)
