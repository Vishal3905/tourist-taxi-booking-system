import requests
import pandas as pd
from flask import send_file
import sqlite3
from flask import Flask, render_template, request, jsonify, redirect, session
import os
from werkzeug.utils import secure_filename
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev_secret")
DRIVER_USERNAME = "vishal"
DRIVER_PASSWORD = "12345"

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "12345"

SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
FROM_EMAIL = os.getenv("SMTP_USER")   
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

def save_booking(data):

    conn = sqlite3.connect("bookings.db")

    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO bookings (
            name,
            phone,
            pickup,
            drop_location,
            datetime,
            package_type,
            passengers,
            distance,
            fare
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data.get("name"),
        data.get("phone"),
        data.get("pickup_address"),
        data.get("drop_address"),
        data.get("datetime"),
        data.get("package_type"),
        data.get("passengers"),
        data.get("distance_km"),
        data.get("fare")
    ))

    conn.commit()
    conn.close()    


@app.route("/")
def index():

    conn = sqlite3.connect("bookings.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            vehicles.*,
            drivers.name,
            drivers.phone
        FROM vehicles

        JOIN drivers
        ON vehicles.driver_id = drivers.id

        WHERE
            vehicles.status='Approved'
            AND drivers.status='Approved'
    """)

    vehicles = cursor.fetchall()

    conn.close()

    return render_template(
        "index.html",
        vehicles=vehicles
    )


@app.route("/booking")
def booking_page():
    return render_template("booking.html")

@app.route("/admin")
def admin():
    return render_template("admin.html")

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

        save_booking(data)

        send_booking_email(
        subject,
        html_body,
        plain_body
        )

        return jsonify({"ok": True})
    except Exception as e:
        print("FULL ERROR:")
        print(e)
        raise

@app.route("/driver-login", methods=["GET", "POST"])
def driver_login():

    if request.method == "POST":

        phone = request.form.get("phone")
        password = request.form.get("password")

        conn = sqlite3.connect("bookings.db")
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT *
            FROM drivers
            WHERE phone=?
            AND password=?
            AND status='Approved'
            """,
            (phone, password)
        )

        driver = cursor.fetchone()

        conn.close()

        if driver:

            session["driver_logged_in"] = True
            session["driver_id"] = driver[0]
            session["driver_name"] = driver[1]

            return redirect("/driver-dashboard")

    return render_template("driver_login.html")


@app.route("/driver-dashboard")
def driver_dashboard():

    if not session.get("driver_logged_in"):
        return redirect("/driver-login")

    conn = sqlite3.connect("bookings.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM bookings ORDER BY id DESC")

    bookings = cursor.fetchall()

    conn.close()

    pending_count = len(
        [b for b in bookings if b[10] == "Pending"]
    )

    completed_count = len(
        [b for b in bookings if b[10] == "Completed"]
    )

    return render_template(
        "driver_dashboard.html",
        bookings=bookings,
        pending_count=pending_count,
        completed_count=completed_count,
        driver_name=session.get("driver_name")
    )

@app.route("/logout")
def logout():

    session.pop("driver_logged_in", None)

    return redirect("/driver-login")

@app.route("/admin-logout")
def admin_logout():

    session.pop("admin_logged_in", None)

    return redirect("/admin-login")

@app.route("/accept-booking/<int:id>")
def accept_booking(id):

    conn = sqlite3.connect("bookings.db")
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE bookings SET status='Accepted' WHERE id=?",
        (id,)
    )

    conn.commit()
    conn.close()

    return redirect("/driver-dashboard")

@app.route("/complete-booking/<int:id>")
def complete_booking(id):

    conn = sqlite3.connect("bookings.db")
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE bookings SET status='Completed' WHERE id=?",
        (id,)
    )

    conn.commit()
    conn.close()

    return redirect("/driver-dashboard")

@app.route("/admin-login", methods=["GET", "POST"])
def admin_login():

    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")

        if (
            username == ADMIN_USERNAME and
            password == ADMIN_PASSWORD
        ):

            session["admin_logged_in"] = True

            return redirect("/admin-dashboard")

    return render_template("admin_login.html")

@app.route("/admin-dashboard", methods=["GET"])
def admin_dashboard():

    if not session.get("admin_logged_in"):
        return redirect("/admin-login")

    conn = sqlite3.connect("bookings.db")
    cursor = conn.cursor()

    search_phone = request.args.get("phone")
    status_filter = request.args.get("status")

    if search_phone:

        cursor.execute(
            "SELECT * FROM bookings WHERE phone LIKE ?",
            (f"%{search_phone}%",)
        )

    elif status_filter:

        cursor.execute(
            "SELECT * FROM bookings WHERE status=?",
            (status_filter,)
        )

    else:

        cursor.execute(
            "SELECT * FROM bookings"
        )

    bookings = cursor.fetchall()

    cursor.execute(
        "SELECT * FROM drivers WHERE status='Pending'"
    )

    pending_drivers = cursor.fetchall()

    cursor.execute(
        "SELECT * FROM vehicles WHERE status='Pending'"
    )

    pending_vehicles = cursor.fetchall()

    total_revenue = sum(
        booking[9]
        for booking in bookings
    )

    fares = [booking[9] for booking in bookings]

    average_fare = (
        round(sum(fares) / len(fares), 2)
        if fares else 0
    )

    highest_fare = max(fares) if fares else 0

    lowest_fare = min(fares) if fares else 0

    # ADD HERE ↓↓↓

    pending_count = len([
        b for b in bookings
        if b[10] == "Pending"
    ])

    accepted_count = len([
        b for b in bookings
        if b[10] == "Accepted"
    ])

    completed_count = len([
        b for b in bookings
        if b[10] == "Completed"
    ])

    # ADD HERE ↑↑↑

    conn.close()

    return render_template(
        "admin_dashboard.html",
        bookings=bookings,
        total_revenue=round(total_revenue, 2),

        pending_count=pending_count,
        accepted_count=accepted_count,
        completed_count=completed_count,

        average_fare=average_fare,
        highest_fare=highest_fare,
        lowest_fare=lowest_fare,

        pending_drivers=pending_drivers,
        pending_vehicles=pending_vehicles
    )

@app.route("/delete-booking/<int:id>")
def delete_booking(id):

    if not session.get("admin_logged_in"):
        return redirect("/admin-login")

    conn = sqlite3.connect("bookings.db")
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM bookings WHERE id=?",
        (id,)
    )

    conn.commit()
    conn.close()

    return redirect("/admin-dashboard")

@app.route("/approve-driver/<int:id>")
def approve_driver(id):

    conn = sqlite3.connect("bookings.db")
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE drivers SET status='Approved' WHERE id=?",
        (id,)
    )

    conn.commit()
    conn.close()

    return redirect("/admin-dashboard")

@app.route("/approve-vehicle/<int:id>")
def approve_vehicle(id):

    conn = sqlite3.connect("bookings.db")
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE vehicles SET status='Approved' WHERE id=?",
        (id,)
    )

    conn.commit()
    conn.close()

    return redirect("/admin-dashboard")

@app.route("/export-bookings")
def export_bookings():

    conn = sqlite3.connect("bookings.db")

    df = pd.read_sql_query(
        "SELECT * FROM bookings",
        conn
    )

    conn.close()

    file_name = "bookings.xlsx"

    df.to_excel(
        file_name,
        index=False
    )

    return send_file(
        file_name,
        as_attachment=True
    )

@app.route("/driver-register", methods=["GET", "POST"])
def driver_register():

    if request.method == "POST":

        name = request.form.get("name")
        phone = request.form.get("phone")
        email = request.form.get("email")
        address = request.form.get("address")
        license_no = request.form.get("license_no")
        password = request.form.get("password")

        conn = sqlite3.connect("bookings.db")
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO drivers
            (
                name,
                phone,
                email,
                address,
                license_no,
                password
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            name,
            phone,
            email,
            address,
            license_no,
            password
        ))

        conn.commit()
        conn.close()

        return redirect("/driver-login")

    return render_template("driver_register.html")

@app.route("/vehicle-register", methods=["GET", "POST"])
def vehicle_register():

    if not session.get("driver_logged_in"):
        return redirect("/driver-login")

    if request.method == "POST":

        vehicle_name = request.form.get("vehicle_name")
        vehicle_number = request.form.get("vehicle_number")
        vehicle_type = request.form.get("vehicle_type")
        seats = request.form.get("seats")

        photo = request.files["photo"]

        filename = secure_filename(
            photo.filename
        )

        photo.save(
            os.path.join(
                "static/uploads",
                filename
            )
        )

        conn = sqlite3.connect("bookings.db")
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO vehicles
            (
                driver_id,
                vehicle_name,
                vehicle_number,
                vehicle_type,
                seats,
                photo
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
                session.get("driver_id"),
                vehicle_name,
                vehicle_number,
                vehicle_type,
                seats,
                filename
            ))

        conn.commit()
        conn.close()

        return redirect("/driver-dashboard")

    return render_template("vehicle_register.html")

@app.route("/calculate-route", methods=["POST"])
def calculate_route():

    data = request.get_json()

    pickup_lat = data["pickup_lat"]
    pickup_lng = data["pickup_lng"]

    drop_lat = data["drop_lat"]
    drop_lng = data["drop_lng"]

    api_key = "eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6IjYwZTI5ZjdmNDc3ZjRiMDZiYTNkZGFjODI0ZTI4YTBhIiwiaCI6Im11cm11cjY0In0="

    url = "https://api.openrouteservice.org/v2/directions/driving-car"

    headers = {
        "Authorization": api_key,
        "Content-Type": "application/json"
    }

    body = {
        "coordinates": [
            [pickup_lng, pickup_lat],
            [drop_lng, drop_lat]
        ]
    }

    response = requests.post(
        url,
        headers=headers,
        json=body
    )

    return response.json()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)