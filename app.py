from flask import Flask, render_template, request, jsonify
import os
from dotenv import load_dotenv
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev_secret")

SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")
RECEIVER_EMAIL = os.getenv("RECEIVER_EMAIL") or SMTP_USER


def send_booking_email(subject: str, html_body: str, plain_body: str = ""):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = SMTP_USER
    msg["To"] = RECEIVER_EMAIL

    part1 = MIMEText(plain_body or html_body, "plain")
    part2 = MIMEText(html_body, "html")

    msg.attach(part1)
    msg.attach(part2)

    server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
    server.ehlo()
    if SMTP_PORT == 587:
        server.starttls()
        server.ehlo()
    server.login(SMTP_USER, SMTP_PASS)
    server.sendmail(SMTP_USER, RECEIVER_EMAIL, msg.as_string())
    server.quit()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/booking")
def booking_page():
    return render_template("booking.html")


@app.route("/send_email", methods=["POST"])
def send_email_route():
    data = request.get_json() or {}

    required = [
    "name", "phone", "pickup_address", "drop_address",
    "datetime", "package_type", "passengers",
    "distance_km", "fare"
]
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({"error": f"Missing: {', '.join(missing)}"}), 400

    subject = f"New Taxi Booking - {data.get('name')} - {data.get('datetime')}"
    html_body = f"""
    <h2>New Booking Request</h2>
    <ul>
      <li><strong>Name:</strong> {data.get('name')}</li>
      <li><strong>Phone:</strong> {data.get('phone')}</li>
      <li><strong>Pickup:</strong> {data.get('pickup_address')}</li>
      <li><strong>Drop:</strong> {data.get('drop_address')}</li>
      <li><strong>Date & Time:</strong> {data.get('datetime')}</li>
      <li><strong>Package:</strong> {data.get('package_type')}</li>
      <li><strong>Passengers:</strong> {data.get('passengers')}</li>
      <li><strong>Distance (km):</strong> {data.get('distance_km')}</li>
      <li><strong>Fare (est):</strong> Rs. {data.get('fare')}</li>
    </ul>
    """

    plain_body = f"""
New Booking Request

Name: {data.get('name')}
Phone: {data.get('phone')}
Pickup: {data.get('pickup_address')}
Drop: {data.get('drop_address')}
Date & Time: {data.get('datetime')}
Package: {data.get('package_type')}
Passengers: {data.get('passengers')}
Distance (km): {data.get('distance_km')}
Fare (est): Rs. {data.get('fare')}
"""

    
    try:
        send_booking_email(subject, html_body, plain_body)
        return jsonify({"ok": True})
    except Exception as e:
        print("EMAIL ERROR:", str(e))
        raise e                  


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
