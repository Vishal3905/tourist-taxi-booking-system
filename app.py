from flask import Flask, render_template, request, jsonify
import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev_secret")

SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
FROM_EMAIL = os.getenv("SMTP_USER")   # must be verified in SendGrid
RECEIVER_EMAIL = os.getenv("RECEIVER_EMAIL")


def send_booking_email(subject, html_body, plain_body=""):
    message = Mail(
        from_email=FROM_EMAIL,
        to_emails=RECEIVER_EMAIL,
        subject=subject,
        plain_text_content=plain_body,
        html_content=html_body
    )

    sg = SendGridAPIClient(SENDGRID_API_KEY)
    sg.send(message)


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
      <li><strong>Distance:</strong> {data.get('distance_km')} km</li>
      <li><strong>Fare:</strong> Rs. {data.get('fare')}</li>
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
Distance: {data.get('distance_km')} km
Fare: Rs. {data.get('fare')}
"""

    try:
        send_booking_email(subject, html_body, plain_body)
        return jsonify({"ok": True})
    except Exception as e:
        print("SENDGRID ERROR:", str(e))
        return jsonify({"error": "Email failed"}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)