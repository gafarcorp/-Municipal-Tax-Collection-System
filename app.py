import hashlib
import math
from datetime import date, datetime
from functools import wraps

from flask import Flask, jsonify, redirect, render_template, request, session, url_for
from mysql.connector import Error, errorcode
from werkzeug.security import check_password_hash, generate_password_hash

from config import Config
from db import call_procedure, execute_query, fetch_all, fetch_one, get_connection


app = Flask(__name__)
app.config.from_object(Config)


# This helper keeps API error responses consistent across the project.
def json_error(message, status_code=400):
    return jsonify({"success": False, "message": message}), status_code


def login_required(role=None):
    def decorator(function):
        @wraps(function)
        def wrapper(*args, **kwargs):
            user_role = session.get("role")

            if not session.get("user_id"):
                if request.path.startswith("/api/"):
                    return json_error("Please login to continue.", 401)
                return redirect(url_for("login_page"))

            if role and user_role != role:
                return json_error("You are not allowed to access this feature.", 403)

            return function(*args, **kwargs)

        return wrapper

    return decorator


def to_float(value):
    return float(value) if value is not None else 0.0


def hash_password(password):
    return generate_password_hash(password)


def verify_password(stored_hash, password):
    # The fallback allows the sample SQL data to use SHA-256 values.
    if not stored_hash:
        return False

    if stored_hash.startswith(("pbkdf2:", "scrypt:")):
        return check_password_hash(stored_hash, password)

    if len(stored_hash) == 64:
        return stored_hash == hashlib.sha256(password.encode()).hexdigest()

    return stored_hash == password


def calculate_tax_amount(property_value, area_sqft, property_type):
    # The tax formula is intentionally simple for a college mini project.
    base_tax = (to_float(property_value) * 0.01) + (to_float(area_sqft) * 2)
    type_multipliers = {
        "Residential": 1.0,
        "Commercial": 1.2,
        "Industrial": 1.35,
    }
    return round(base_tax * type_multipliers.get(property_type, 1.0), 2)


def calculate_penalty(base_tax, due_date_value, status):
    if not due_date_value or status == "PAID":
        return 0.0

    today = date.today()
    due_date_obj = due_date_value if isinstance(due_date_value, date) else datetime.strptime(str(due_date_value), "%Y-%m-%d").date()
    days_late = (today - due_date_obj).days

    if days_late <= 0:
        return 0.0

    late_months = math.ceil(days_late / 30)
    return round(to_float(base_tax) * 0.02 * late_months, 2)


def serialize_date(value):
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value


def current_user():
    return {
        "user_id": session.get("user_id"),
        "role": session.get("role"),
        "name": session.get("name"),
        "email": session.get("email"),
    }


def hydrate_tax_row(row):
    base_tax = to_float(row.get("base_tax"))
    penalty = calculate_penalty(base_tax, row.get("due_date"), row.get("status"))
    amount_paid = to_float(row.get("amount_paid"))
    total_due = round(base_tax + penalty, 2)

    row["base_tax"] = base_tax
    row["penalty_amount"] = penalty
    row["total_due"] = total_due
    row["amount_paid"] = amount_paid
    row["balance_due"] = round(max(total_due - amount_paid, 0), 2)
    row["due_date"] = serialize_date(row.get("due_date"))
    row["generated_at"] = serialize_date(row.get("generated_at"))
    return row


def refresh_tax_record(property_id, tax_year=None):
    year = tax_year or date.today().year

    try:
        # The stored procedure handles the official yearly tax generation.
        call_procedure("sp_generate_property_tax", [property_id, year])
    except Error:
        # The fallback keeps the application usable even if procedures are not available yet.
        property_row = fetch_one(
            """
            SELECT property_value, area_sqft, property_type
            FROM properties
            WHERE id = %s
            """,
            (property_id,),
        )

        if not property_row:
            return

        base_tax = calculate_tax_amount(
            property_row["property_value"],
            property_row["area_sqft"],
            property_row["property_type"],
        )

        execute_query(
            """
            INSERT INTO taxes (property_id, tax_year, base_tax, penalty_amount, total_due, due_date, status)
            VALUES (%s, %s, %s, 0, %s, %s, 'UNPAID')
            ON DUPLICATE KEY UPDATE
                base_tax = VALUES(base_tax),
                total_due = VALUES(total_due),
                due_date = VALUES(due_date),
                status = IF(status = 'PAID', status, 'UNPAID')
            """,
            (property_id, year, base_tax, base_tax, f"{year}-09-30"),
        )


def ensure_tax_access(tax_id):
    tax_row = fetch_one(
        """
        SELECT t.id, t.property_id, p.taxpayer_id
        FROM taxes t
        INNER JOIN properties p ON p.id = t.property_id
        WHERE t.id = %s
        """,
        (tax_id,),
    )

    if not tax_row:
        return None

    if session.get("role") == "taxpayer" and tax_row["taxpayer_id"] != session.get("user_id"):
        return None

    return tax_row


@app.route("/")
def home():
    if session.get("user_id"):
        return redirect(url_for("dashboard_page"))
    return redirect(url_for("login_page"))


@app.route("/login")
def login_page():
    return render_template("login.html")


@app.route("/register")
def register_page():
    return render_template("register.html")


@app.route("/dashboard")
@login_required()
def dashboard_page():
    return render_template("dashboard.html")


@app.route("/properties")
@login_required()
def properties_page():
    return render_template("properties.html")


@app.route("/payment")
@login_required()
def payment_page():
    return render_template("payment.html")


@app.route("/history")
@login_required()
def history_page():
    return render_template("history.html")


@app.post("/api/auth/register")
def register():
    data = request.get_json() or {}
    full_name = (data.get("full_name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    phone = (data.get("phone") or "").strip()
    address = (data.get("address") or "").strip()
    password = data.get("password") or ""

    if not all([full_name, email, phone, address, password]):
        return json_error("All registration fields are required.")

    try:
        user_id = execute_query(
            """
            INSERT INTO taxpayers (full_name, email, phone, address, password_hash)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (full_name, email, phone, address, hash_password(password)),
        )
        return jsonify({"success": True, "message": "Registration completed successfully.", "user_id": user_id})
    except Error as exc:
        if exc.errno == errorcode.ER_DUP_ENTRY:
            return json_error("Email already exists. Please use a different email.")
        return json_error("Unable to register taxpayer right now.", 500)


@app.post("/api/auth/login")
def login():
    data = request.get_json() or {}
    email_or_username = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    role = data.get("role") or "taxpayer"

    if not email_or_username or not password:
        return json_error("Email/username and password are required.")

    if role == "admin":
        user = fetch_one(
            """
            SELECT id, username, full_name, password_hash
            FROM admins
            WHERE username = %s
            """,
            (email_or_username,),
        )

        if not user or not verify_password(user["password_hash"], password):
            return json_error("Invalid admin credentials.", 401)

        session.update(
            {
                "user_id": user["id"],
                "role": "admin",
                "name": user["full_name"],
                "email": user["username"],
            }
        )
    else:
        user = fetch_one(
            """
            SELECT id, full_name, email, password_hash
            FROM taxpayers
            WHERE email = %s
            """,
            (email_or_username,),
        )

        if not user or not verify_password(user["password_hash"], password):
            return json_error("Invalid taxpayer credentials.", 401)

        session.update(
            {
                "user_id": user["id"],
                "role": "taxpayer",
                "name": user["full_name"],
                "email": user["email"],
            }
        )

    return jsonify({"success": True, "message": "Login successful.", "user": current_user()})


@app.post("/api/auth/logout")
def logout():
    session.clear()
    return jsonify({"success": True, "message": "Logout successful."})


@app.get("/api/auth/session")
def auth_session():
    if not session.get("user_id"):
        return jsonify({"success": True, "authenticated": False})

    return jsonify({"success": True, "authenticated": True, "user": current_user()})


@app.get("/api/dashboard/summary")
@login_required()
def dashboard_summary():
    if session.get("role") == "admin":
        summary = fetch_one(
            """
            SELECT
                (SELECT COUNT(*) FROM taxpayers) AS taxpayer_count,
                (SELECT COUNT(*) FROM properties) AS property_count,
                (SELECT COALESCE(SUM(amount_paid), 0) FROM payments WHERE payment_status = 'SUCCESS') AS total_collection,
                (SELECT COUNT(*) FROM taxes WHERE status <> 'PAID') AS pending_tax_count
            """
        )

        recent_collections = fetch_all(
            """
            SELECT payment_reference, amount_paid, payment_method, paid_at, payment_status
            FROM payments
            ORDER BY paid_at DESC
            LIMIT 5
            """
        )
    else:
        summary = fetch_one(
            """
            SELECT
                (SELECT COUNT(*) FROM properties WHERE taxpayer_id = %s) AS property_count,
                (
                    SELECT COUNT(*)
                    FROM taxes t
                    INNER JOIN properties p ON p.id = t.property_id
                    WHERE p.taxpayer_id = %s
                ) AS tax_count,
                (
                    SELECT COUNT(*)
                    FROM taxes t
                    INNER JOIN properties p ON p.id = t.property_id
                    WHERE p.taxpayer_id = %s AND t.status <> 'PAID'
                ) AS pending_tax_count,
                (SELECT COALESCE(SUM(amount_paid), 0) FROM payments WHERE taxpayer_id = %s AND payment_status = 'SUCCESS') AS total_paid
            """,
            (
                session.get("user_id"),
                session.get("user_id"),
                session.get("user_id"),
                session.get("user_id"),
            ),
        )

        recent_collections = fetch_all(
            """
            SELECT payment_reference, amount_paid, payment_method, paid_at, payment_status
            FROM payments
            WHERE taxpayer_id = %s
            ORDER BY paid_at DESC
            LIMIT 5
            """,
            (session.get("user_id"),),
        )

    for field in ["total_collection", "total_paid"]:
        if field in summary:
            summary[field] = to_float(summary.get(field))

    for item in recent_collections:
        item["amount_paid"] = to_float(item.get("amount_paid"))
        item["paid_at"] = serialize_date(item.get("paid_at"))

    return jsonify({"success": True, "summary": summary, "recent_payments": recent_collections, "user": current_user()})


@app.get("/api/properties")
@login_required()
def properties():
    if session.get("role") == "admin":
        rows = fetch_all(
            """
            SELECT p.*, tp.full_name AS taxpayer_name, tp.email AS taxpayer_email
            FROM properties p
            INNER JOIN taxpayers tp ON tp.id = p.taxpayer_id
            ORDER BY p.created_at DESC
            """
        )
    else:
        rows = fetch_all(
            """
            SELECT p.*, tp.full_name AS taxpayer_name, tp.email AS taxpayer_email
            FROM properties p
            INNER JOIN taxpayers tp ON tp.id = p.taxpayer_id
            WHERE p.taxpayer_id = %s
            ORDER BY p.created_at DESC
            """,
            (session.get("user_id"),),
        )

    for row in rows:
        row["property_value"] = to_float(row.get("property_value"))
        row["area_sqft"] = to_float(row.get("area_sqft"))
        row["created_at"] = serialize_date(row.get("created_at"))

    taxpayers = []
    if session.get("role") == "admin":
        taxpayers = fetch_all("SELECT id, full_name, email FROM taxpayers ORDER BY full_name")

    return jsonify({"success": True, "properties": rows, "taxpayers": taxpayers})


@app.post("/api/properties")
@login_required(role="admin")
def add_property():
    data = request.get_json() or {}
    property_code = (data.get("property_code") or "").strip().upper()
    taxpayer_id = data.get("taxpayer_id")
    property_type = data.get("property_type") or "Residential"
    address = (data.get("address") or "").strip()
    area_sqft = data.get("area_sqft")
    property_value = data.get("property_value")

    if not all([property_code, taxpayer_id, property_type, address, area_sqft, property_value]):
        return json_error("All property fields are required.")

    try:
        property_id = execute_query(
            """
            INSERT INTO properties (taxpayer_id, property_code, property_type, address, area_sqft, property_value)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (taxpayer_id, property_code, property_type, address, area_sqft, property_value),
        )
        refresh_tax_record(property_id)
        return jsonify({"success": True, "message": "Property created successfully.", "property_id": property_id})
    except Error as exc:
        if exc.errno == errorcode.ER_DUP_ENTRY:
            return json_error("Duplicate property code detected. Please use a unique property code.")
        return json_error("Unable to save property right now.", 500)


@app.put("/api/properties/<int:property_id>")
@login_required(role="admin")
def update_property(property_id):
    data = request.get_json() or {}
    property_code = (data.get("property_code") or "").strip().upper()
    taxpayer_id = data.get("taxpayer_id")
    property_type = data.get("property_type") or "Residential"
    address = (data.get("address") or "").strip()
    area_sqft = data.get("area_sqft")
    property_value = data.get("property_value")

    if not all([property_code, taxpayer_id, property_type, address, area_sqft, property_value]):
        return json_error("All property fields are required.")

    try:
        execute_query(
            """
            UPDATE properties
            SET taxpayer_id = %s, property_code = %s, property_type = %s, address = %s, area_sqft = %s, property_value = %s
            WHERE id = %s
            """,
            (taxpayer_id, property_code, property_type, address, area_sqft, property_value, property_id),
        )
        refresh_tax_record(property_id)
        return jsonify({"success": True, "message": "Property updated successfully."})
    except Error as exc:
        if exc.errno == errorcode.ER_DUP_ENTRY:
            return json_error("Duplicate property code detected. Please use a unique property code.")
        return json_error("Unable to update property right now.", 500)


@app.delete("/api/properties/<int:property_id>")
@login_required(role="admin")
def delete_property(property_id):
    execute_query("DELETE FROM properties WHERE id = %s", (property_id,))
    return jsonify({"success": True, "message": "Property deleted successfully."})


@app.get("/api/taxes")
@login_required()
def tax_list():
    base_query = """
        SELECT
            t.id,
            t.property_id,
            t.tax_year,
            t.base_tax,
            t.penalty_amount,
            t.total_due,
            t.due_date,
            t.status,
            t.generated_at,
            p.property_code,
            p.address,
            p.taxpayer_id,
            tp.full_name AS taxpayer_name,
            COALESCE(SUM(pay.amount_paid), 0) AS amount_paid
        FROM taxes t
        INNER JOIN properties p ON p.id = t.property_id
        INNER JOIN taxpayers tp ON tp.id = p.taxpayer_id
        LEFT JOIN payments pay ON pay.tax_id = t.id AND pay.payment_status = 'SUCCESS'
    """

    params = ()
    if session.get("role") == "taxpayer":
        base_query += " WHERE p.taxpayer_id = %s"
        params = (session.get("user_id"),)

    base_query += """
        GROUP BY t.id, t.property_id, t.tax_year, t.base_tax, t.penalty_amount, t.total_due, t.due_date, t.status, t.generated_at,
                 p.property_code, p.address, p.taxpayer_id, tp.full_name
        ORDER BY t.tax_year DESC, t.generated_at DESC
    """

    rows = fetch_all(base_query, params)
    hydrated_rows = [hydrate_tax_row(row) for row in rows]
    return jsonify({"success": True, "taxes": hydrated_rows})


@app.post("/api/payments")
@login_required()
def add_payment():
    data = request.get_json() or {}
    tax_id = data.get("tax_id")
    amount_paid = to_float(data.get("amount_paid"))
    payment_method = (data.get("payment_method") or "Online").strip()

    if not tax_id or amount_paid <= 0:
        return json_error("Valid tax and payment amount are required.")

    if not ensure_tax_access(tax_id):
        return json_error("You cannot access this tax record.", 403)

    tax_row = fetch_one(
        """
        SELECT
            t.id,
            t.base_tax,
            t.due_date,
            t.status,
            p.taxpayer_id,
            COALESCE(SUM(pay.amount_paid), 0) AS amount_paid
        FROM taxes t
        INNER JOIN properties p ON p.id = t.property_id
        LEFT JOIN payments pay ON pay.tax_id = t.id AND pay.payment_status = 'SUCCESS'
        WHERE t.id = %s
        GROUP BY t.id, t.base_tax, t.due_date, t.status, p.taxpayer_id
        """,
        (tax_id,),
    )

    if not tax_row:
        return json_error("Tax record not found.", 404)

    penalty = calculate_penalty(tax_row["base_tax"], tax_row["due_date"], tax_row["status"])
    total_due = round(to_float(tax_row["base_tax"]) + penalty, 2)
    balance_due = round(total_due - to_float(tax_row["amount_paid"]), 2)

    if balance_due <= 0:
        return json_error("This tax is already fully paid.")

    if amount_paid > balance_due:
        return json_error(f"Payment amount cannot exceed current balance of {balance_due:.2f}.")

    payment_reference = f"PAY-{datetime.now().strftime('%Y%m%d%H%M%S')}-{int(tax_id)}"
    execute_query(
        """
        UPDATE taxes
        SET penalty_amount = %s, total_due = %s
        WHERE id = %s
        """,
        (penalty, total_due, tax_id),
    )

    payer_id = tax_row["taxpayer_id"] if session.get("role") == "admin" else session.get("user_id")

    payment_id = execute_query(
        """
        INSERT INTO payments (tax_id, taxpayer_id, amount_paid, payment_method, payment_reference, payment_status)
        VALUES (%s, %s, %s, %s, %s, 'SUCCESS')
        """,
        (tax_id, payer_id, amount_paid, payment_method, payment_reference),
    )

    return jsonify(
        {
            "success": True,
            "message": "Payment recorded successfully.",
            "payment_id": payment_id,
            "payment_reference": payment_reference,
        }
    )


@app.get("/api/payments/history")
@login_required()
def payment_history():
    query = """
        SELECT
            pay.id,
            pay.payment_reference,
            pay.amount_paid,
            pay.payment_method,
            pay.payment_status,
            pay.paid_at,
            t.tax_year,
            p.property_code,
            p.address,
            tp.full_name AS taxpayer_name
        FROM payments pay
        INNER JOIN taxes t ON t.id = pay.tax_id
        INNER JOIN properties p ON p.id = t.property_id
        INNER JOIN taxpayers tp ON tp.id = pay.taxpayer_id
    """

    params = ()
    if session.get("role") == "taxpayer":
        query += " WHERE pay.taxpayer_id = %s"
        params = (session.get("user_id"),)

    query += " ORDER BY pay.paid_at DESC"

    rows = fetch_all(query, params)
    for row in rows:
        row["amount_paid"] = to_float(row.get("amount_paid"))
        row["paid_at"] = serialize_date(row.get("paid_at"))

    return jsonify({"success": True, "payments": rows})


@app.get("/api/reports/collection")
@login_required(role="admin")
def collection_report():
    report_rows = fetch_all(
        """
        SELECT
            taxpayer_name,
            property_code,
            address,
            tax_year,
            base_tax,
            penalty_amount,
            total_due,
            total_paid,
            balance_due,
            tax_status
        FROM vw_tax_collection_report
        ORDER BY tax_year DESC, taxpayer_name ASC
        """
    )

    monthly_rows = fetch_all(
        """
        SELECT
            DATE_FORMAT(paid_at, '%Y-%m') AS collection_month,
            COUNT(*) AS payment_count,
            COALESCE(SUM(amount_paid), 0) AS total_amount
        FROM payments
        WHERE payment_status = 'SUCCESS'
        GROUP BY DATE_FORMAT(paid_at, '%Y-%m')
        ORDER BY collection_month DESC
        """
    )

    for row in report_rows:
        for field in ["base_tax", "penalty_amount", "total_due", "total_paid", "balance_due"]:
            row[field] = to_float(row.get(field))

    for row in monthly_rows:
        row["total_amount"] = to_float(row.get("total_amount"))

    return jsonify({"success": True, "report": report_rows, "monthly_summary": monthly_rows})


@app.get("/api/system/health")
def health_check():
    try:
        connection = get_connection()
        connection.close()
        return jsonify({"success": True, "message": "Database connection successful."})
    except Error as exc:
        return jsonify({"success": False, "message": str(exc)}), 500


if __name__ == "__main__":
    app.run(debug=True)
