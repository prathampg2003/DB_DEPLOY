from flask import Flask, request, jsonify
import qrcode
import io
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import mysql.connector
from datetime import datetime

app = Flask(__name__)

# Database Configuration
db_config = {
    'host': 'sql12.freesqldatabase.com',
    'user': 'sql12759159',
    'password': 'v5SaGkWwNS',
    'database': 'sql12759159'
}

# Email Configuration
SMTP_SERVER = 'smtp-relay.sendinblue.com'
SMTP_PORT = 587
SMTP_USER = 'prathampg2003@gmail.com'
SMTP_PASS = 'aQbv7CZdDrckyxw8'

# Utility Functions
def send_email(to_address, subject, body, qr_image, filename="qr-code.jpeg"):
    msg = MIMEMultipart()
    msg['From'] = SMTP_USER
    msg['To'] = to_address
    msg['Subject'] = subject

    # Email Body
    msg.attach(MIMEText(body, 'plain'))

    # Attach QR Code
    part = MIMEBase('application', 'octet-stream')
    part.set_payload(qr_image)
    encoders.encode_base64(part)
    part.add_header('Content-Disposition', f'attachment; filename={filename}')
    msg.attach(part)

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.sendmail(SMTP_USER, to_address, msg.as_string())
        server.quit()
        print(f"Email sent to {to_address} successfully.")
    except Exception as e:
        print(f"Error sending email to {to_address}: {e}")

# Initialize Database
def init_db():
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS testing (
            opportunity_id VARCHAR(255) PRIMARY KEY,
            user_name VARCHAR(255),
            user_email VARCHAR(255),
            user_preferred_lang VARCHAR(255),
            u_date DATE,
            u_time TIME,
            manager VARCHAR(255),
            u_scan BOOLEAN DEFAULT FALSE
        )
    ''')
    conn.commit()
    cursor.close()
    conn.close()

@app.route('/submit', methods=['POST'])
def submit():
    data = request.json
    try:
        # Extracting data
        opportunity_id = data['opportunity_id']
        user_name = data['user_name']
        user_email = data['user_email']
        user_preferred_lang = data['user_preferred_lang']
        u_date = data['u_date']
        u_time = data['u_time']

        # Insert into database
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO testing (opportunity_id, user_name, user_email, user_preferred_lang, u_date, u_time)
            VALUES (%s, %s, %s, %s, %s, %s)
        ''', (opportunity_id, user_name, user_email, user_preferred_lang, u_date, u_time))
        conn.commit()

        # Generate QR Code
        server_url = request.host_url.strip('/')
        qr_code_data = f"{server_url}/verify/{opportunity_id}"
        qr = qrcode.make(qr_code_data)
        buffered = io.BytesIO()
        qr.save(buffered, format="JPEG")
        qr_image = buffered.getvalue()

        # Send Email
        email_subject = 'Your QR Code for Visit'
        email_body = f"Hello {user_name},\n\nThank you for submitting your details! Please find your QR code attached."
        send_email(user_email, email_subject, email_body, qr_image)

        cursor.close()
        conn.close()

        return jsonify({"message": "Form submitted successfully, QR code sent to email."}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/assign', methods=['POST'])
def assign():
    data = request.json
    try:
        opportunity_id = data['opportunity_id']
        manager = data['manager']

        # Update manager in database
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE testing
            SET manager = %s
            WHERE opportunity_id = %s
        ''', (manager, opportunity_id))
        conn.commit()

        cursor.close()
        conn.close()
        return jsonify({"message": "Manager assigned successfully."}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/verify/<opportunity_id>', methods=['GET'])
def verify(opportunity_id):
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)

        # Mark as scanned
        cursor.execute('''
            UPDATE testing
            SET u_scan = TRUE
            WHERE opportunity_id = %s
        ''', (opportunity_id,))
        conn.commit()

       

        cursor.close()
        conn.close()

        return jsonify({"message": "WELCOME, QR IS SCANNED AND VERIFIED."}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)
