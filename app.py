
from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import os
from functools import wraps

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-only-change-this")
DATABASE = "complaints.db"

# Change these before deployment
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")


def get_db():
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    return db


def initialize_db():
    with get_db() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS complaints (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                description TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Pending'
            )
        """)


def admin_required(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        if not session.get("admin_logged_in"):
            return redirect(url_for("admin_login"))
        return function(*args, **kwargs)
    return wrapper


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/submit", methods=["POST"])
def submit():
    name = request.form.get("name", "").strip()
    category = request.form.get("category", "").strip()
    description = request.form.get("description", "").strip()

    if not name or not category or not description:
        return "Please fill in all fields.", 400

    if len(name) > 100 or len(description) > 2000:
        return "Input is too long.", 400

    allowed_categories = [
        "Infrastructure", "Water Supply",
        "Electricity", "Sanitation", "Other"
    ]

    if category not in allowed_categories:
        return "Invalid category.", 400

    with get_db() as db:
        cursor = db.execute(
            """INSERT INTO complaints
               (name, category, description)
               VALUES (?, ?, ?)""",
            (name, category, description)
        )
        complaint_id = cursor.lastrowid

    return render_template(
        "success.html",
        complaint_id=complaint_id
    )


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    error = None

    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")

        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session.clear()
            session["admin_logged_in"] = True
            return redirect(url_for("admin_dashboard"))

        error = "Invalid username or password."

    return render_template("login.html", error=error)


@app.route("/admin")
@admin_required
def admin_dashboard():
    with get_db() as db:
        complaints = db.execute(
            "SELECT * FROM complaints ORDER BY id DESC"
        ).fetchall()

        total = db.execute(
            "SELECT COUNT(*) FROM complaints"
        ).fetchone()[0]

        pending = db.execute(
            "SELECT COUNT(*) FROM complaints WHERE status = 'Pending'"
        ).fetchone()[0]

        in_progress = db.execute(
            "SELECT COUNT(*) FROM complaints WHERE status = 'In Progress'"
        ).fetchone()[0]

        resolved = db.execute(
            "SELECT COUNT(*) FROM complaints WHERE status = 'Resolved'"
        ).fetchone()[0]

    return render_template(
        "admin.html",
        complaints=complaints,
        total=total,
        pending=pending,
        in_progress=in_progress,
        resolved=resolved
    )


@app.route("/update/<int:complaint_id>", methods=["POST"])
@admin_required
def update_status(complaint_id):
    status = request.form.get("status", "")
    allowed_statuses = ["Pending", "In Progress", "Resolved"]

    if status not in allowed_statuses:
        return "Invalid status.", 400

    with get_db() as db:
        db.execute(
            "UPDATE complaints SET status = ? WHERE id = ?",
            (status, complaint_id)
        )

    return redirect(url_for("admin_dashboard"))


@app.route("/admin/logout", methods=["POST"])
@admin_required
def admin_logout():
    session.clear()
    return redirect(url_for("admin_login"))


@app.route("/health")
def health():
    try:
        with get_db() as db:
            db.execute("SELECT 1")
        return {"status": "healthy"}, 200
    except sqlite3.Error:
        app.logger.exception("Health check failed")
        return {"status": "unhealthy"}, 500


initialize_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
