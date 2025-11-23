from flask import Flask, request, render_template, redirect, session, send_file
import pyodbc
import io
import pdfkit
import json
import random
import string
from datetime import datetime
import smtplib
from email.mime.text import MIMEText 

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# ---------------------------------------
# EMAIL FUNCTION
# ---------------------------------------
def send_contact_email(name, email, message):
    sender_email = "palanurag595@gmail.com"       #"arengineering7387@gmail.com"
    app_password = "qjxrwxidreqwdlzu"  # 16-digit Gmail app password

    body = f"""
    New Contact Form A.R. Engineering:

    Name: {name}
    Email: {email}
    Message:
    {message}
    """

    msg = MIMEText(body)
    msg["Subject"] = "New Contact Message from A.R. Engineering"
    msg["From"] = sender_email
    msg["To"] = sender_email

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender_email, app_password)
        server.sendmail(sender_email, sender_email, msg.as_string())


# ---------------------------------------
# SQL CONNECTION
# ---------------------------------------
conn_str = (
    "Driver={ODBC Driver 18 for SQL Server};"
    "Server=localhost\\ANURAG_SQL;"
    "Database=AREngineering;"
    "Trusted_Connection=yes;"
    "Encrypt=no;"
)

def get_db():
    return pyodbc.connect(conn_str)

# ---------------------------------------
# GENERATE UNIQUE INVOICE NUMBER
# Example: INV-20250121-5824
# ---------------------------------------
def generate_invoice_no():
    date_part = datetime.now().strftime("%Y%m%d")
    rand_part = ''.join(random.choices(string.digits, k=4))
    return f"INV-{date_part}-{rand_part}"

# ---------------------------------------
# HOME PAGE
# ---------------------------------------
@app.route("/")
def home():
    success_message = None

    if request.args.get("success") == "1":
        success_message = "Your message was sent successfully!"

    return render_template("index.html", success_message=success_message)


# ---------------------------------------
# REGISTER
# ---------------------------------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == 'POST':
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]

        conn = get_db()
        cur = conn.cursor()
        cur.execute("INSERT INTO Users (username, email, password) VALUES (?, ?, ?)",
                    (username, email, password))
        conn.commit()
        conn.close()
        return "Registration successful! You can now login."

    return render_template("register.html")

# ---------------------------------------
# LOGIN
# ---------------------------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM Users WHERE username=? AND password=?",
                    (username, password))
        user = cur.fetchone()
        conn.close()

        if user:
            session["user_id"] = user[0]
            session["username"] = user[1]
            return redirect("/dashboard")
        else:
            return "Invalid username or password!"

    return render_template("login.html")

# ---------------------------------------
# DASHBOARD
# ---------------------------------------
@app.route("/dashboard")
def dashboard():
    if 'user_id' not in session:
        return redirect("/login")
    return render_template("dashboard.html", username=session["username"])

# ---------------------------------------
# LOGOUT
# ---------------------------------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# ---------------------------------------
# EXTRA PAGES FROM FEATURES SECTION
# ---------------------------------------
@app.route("/analytics")
def analytics_page():
    return "<h2>Analytics Page Coming Soon...</h2>"

@app.route("/security")
def security_page():
    return "<h2>Security & Data Protection Info Coming Soon...</h2>"


# ---------------------------------------
# CONTACT FORM SUBMISSION
# ---------------------------------------
@app.route("/contact_submit", methods=["POST"])
def contact_submit():
    name = request.form.get("name")
    email = request.form.get("email")
    message = request.form.get("message")

    send_contact_email(name, email, message)

    # REDIRECT - prevents re-submission on refresh
    return redirect("/?success=1#contact")



# ---------------------------------------
# CREATE INVOICE
# ---------------------------------------
@app.route("/create_invoice", methods=["GET", "POST"])
def create_invoice():
    if request.method == "POST":

        # auto invoice no
        gst_invoice_no = generate_invoice_no()

        # collect form fields
        form_data = request.form.to_dict(flat=False)

        descriptions = form_data.get("description[]", [])
        hsn_codes = form_data.get("hsn_code[]", [])
        quantities = form_data.get("quantity[]", [])
        rates = form_data.get("rate[]", [])

        items = []
        total_value = 0

        for i in range(len(descriptions)):
            qty = float(quantities[i])
            rate = float(rates[i])
            amount = qty * rate
            total_value += amount

            items.append({
                "description": descriptions[i],
                "hsn": hsn_codes[i],
                "qty": qty,
                "rate": rate,
                "amount": amount
            })

        # TAX
        cgst_rate = float(request.form.get("cgst_rate", 0))
        sgst_rate = float(request.form.get("sgst_rate", 0))

        cgst_amount = total_value * cgst_rate / 100
        sgst_amount = total_value * sgst_rate / 100

        grand_total = total_value + cgst_amount + sgst_amount

        # SAVE INTO DATABASE (correct columns)
        conn = get_db()
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO Invoices
            (customer_name, gst_invoice_no, date,
             items_json,
             total_value, cgst_rate, cgst_amount,
             sgst_rate, sgst_amount, grand_total,
             bank_name, branch, account_no, ifsc)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            request.form.get("customer_name"),
            gst_invoice_no,
            request.form.get("date"),

            json.dumps(items),  # items stored as JSON

            total_value,
            cgst_rate,
            cgst_amount,
            sgst_rate,
            sgst_amount,
            grand_total,

            request.form.get("bank_name"),
            request.form.get("branch"),
            request.form.get("account_no"),
            request.form.get("ifsc")
        ))

        conn.commit()
        conn.close()

        # render pdf
        invoice_data = {
            "customer_name": request.form.get("customer_name"),
            "gst_invoice_no": gst_invoice_no,
            "date": request.form.get("date"),
            "items": items,
            "total_value": total_value,
            "cgst_rate": cgst_rate,
            "cgst_amount": cgst_amount,
            "sgst_rate": sgst_rate,
            "sgst_amount": sgst_amount,
            "grand_total": grand_total,
            "bank_name": request.form.get("bank_name"),
            "branch": request.form.get("branch"),
            "account_no": request.form.get("account_no"),
            "ifsc": request.form.get("ifsc")
        }

        html = render_template("invoice_template.html", data=invoice_data)

        config = pdfkit.configuration(
            wkhtmltopdf=r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe"
        )

        pdf = pdfkit.from_string(html, False, configuration=config)

        return send_file(
            io.BytesIO(pdf),
            download_name=f"Invoice_{gst_invoice_no}.pdf",
            mimetype="application/pdf"
        )

    return render_template("invoice_form.html")

# ---------------------------------------
# VIEW ALL INVOICES
# ---------------------------------------
@app.route("/invoices")
def view_invoices():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT id, customer_name, gst_invoice_no, date, grand_total FROM Invoices ORDER BY id DESC")
    data = cur.fetchall()

    conn.close()
    return render_template("invoice_list.html", invoices=data)

# ---------------------------------------
# DOWNLOAD OLD INVOICE
# ---------------------------------------
@app.route("/invoice/<int:id>/download")
def download_invoice(id):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM Invoices WHERE id=?", (id,))
    inv = cur.fetchone()
    conn.close()

    if not inv:
        return "Invoice not found!"

    # correct mapping
    items = json.loads(inv[4])   # items_json

    invoice_data = {
        "customer_name": inv[1],
        "gst_invoice_no": inv[2],
        "date": str(inv[3]),
        "items": items,
        "total_value": inv[5],
        "cgst_rate": inv[6],
        "cgst_amount": inv[7],
        "sgst_rate": inv[8],
        "sgst_amount": inv[9],
        "grand_total": inv[10],
        "bank_name": inv[11],
        "branch": inv[12],
        "account_no": inv[13],
        "ifsc": inv[14],
    }

    html = render_template("invoice_template.html", data=invoice_data)

    config = pdfkit.configuration(
        wkhtmltopdf=r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe"
    )

    pdf = pdfkit.from_string(html, False, configuration=config)

    return send_file(
        io.BytesIO(pdf),
        download_name=f"{inv[2]}.pdf",
        mimetype="application/pdf"
    )

# ---------------------------------------
# RUN APP
# ---------------------------------------
if __name__ == '__main__':
    app.run(debug=True)
