from flask import Flask, render_template, request, flash, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash

import sqlite3
app = Flask(__name__)
app.secret_key = "safevoice123"

@app.route("/")
def home():
    return render_template("home.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        fullname = request.form["fullname"]
        email = request.form["email"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        if password != confirm_password:
            flash("Passwords do not match!", "error")
            return redirect(url_for("register"))

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM users WHERE email=?", (email,))
        user = cursor.fetchone()

        if user:
            conn.close()
            flash("Email already registered!", "error")
            return redirect(url_for("register"))
        
        hashed_password = generate_password_hash(password)

        cursor.execute(
            "INSERT INTO users(fullname,email,password) VALUES(?,?,?)",
            (fullname, email, hashed_password)
        )

        conn.commit()
        conn.close()

        flash("Registration Successful!", "success")
        return redirect(url_for("register"))

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM users WHERE email=?", (email,))
        user = cursor.fetchone()

        conn.close()

        if user and check_password_hash(user[3], password):
            session["user"] = user[1]
            session["email"] = user[2]
            return redirect(url_for("dashboard"))

        flash("Invalid Email or Password!", "error")
        return redirect(url_for("login"))

    return render_template("login.html")

@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template("dashboard.html", name=session["user"])

@app.route("/report", methods=["GET", "POST"])
def report():
    if request.method == "POST":
        fullname = request.form["fullname"]
        phone = request.form["phone"]
        location = request.form["location"]
        incident_date = request.form["incident_date"]
        description = request.form["description"]

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        cursor.execute("INSERT INTO reports(fullname, phone, location, incident_date, description) VALUES (?, ?, ?, ?, ?)", (fullname, phone, location, incident_date, description))

        conn.commit()
        conn.close()

        flash("Report submitted successfully!", "success")

        return redirect(url_for("report"))

    return render_template("report.html")

@app.route("/myreports")
def myreports():

    if "user" not in session:
        return redirect(url_for("login"))

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM reports WHERE fullname=?",
        (session["user"],)
    )
    reports = cursor.fetchall()

    cursor.execute(
        "SELECT COUNT(*) FROM reports WHERE fullname=?",
        (session["user"],)
    )
    total_reports = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM reports WHERE fullname=? AND status='Pending'",
        (session["user"],)
    )
    pending = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM reports WHERE fullname=? AND status='Reviewed'",
        (session["user"],)
    )
    reviewed = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM reports WHERE fullname=? AND status='Resolved'",
        (session["user"],)
    )
    resolved = cursor.fetchone()[0]

    conn.close()

    return render_template(
        "myreports.html",
        reports=reports,
        total_reports=total_reports,
        pending=pending,
        reviewed=reviewed,
        resolved=resolved
    )


@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully!", "success")
    return redirect(url_for("login"))


@app.route("/admin", methods=["GET", "POST"])
def admin():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        if email == "admin@safevoice.com" and password == "admin123":
            session["admin"] = True
            return redirect(url_for("admin_dashboard"))
        else:
            flash("Invalid Admin Credentials!", "error")

    return render_template("admin.html")

@app.route("/admin_dashboard")
def admin_dashboard():
    if "admin" not in session:
        return redirect(url_for("admin"))

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM reports")
    total_reports = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM reports WHERE status='Pending'")
    pending = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM reports WHERE status='Resolved'")
    resolved = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM reports WHERE status='Reviewed'")
    reviewed = cursor.fetchone()[0]

    conn.close()

    return render_template(
        "admin_dashboard.html",
        total_reports=total_reports,
        total_users=total_users,
        pending=pending,
        resolved=resolved,
        reviewed=reviewed
    )

@app.route("/admin_reports")
def admin_reports():

    if "admin" not in session:
        return redirect(url_for("admin"))

    search = request.args.get("search", "")

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    if search:

        cursor.execute(
            """
            SELECT * FROM reports
            WHERE name LIKE ?
            OR location LIKE ?
            """,
            (f"%{search}%", f"%{search}%")
        )

    else:

        cursor.execute("SELECT * FROM reports")

    reports = cursor.fetchall()

    conn.close()

    return render_template(
        "admin_reports.html",
        reports=reports,
        search=search
    )

@app.route("/update_status/<int:id>", methods=["GET", "POST"])
def update_status(id):
    if "admin" not in session:
        return redirect(url_for("admin"))

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    if request.method == "POST":

        new_status = request.form["status"]

        cursor.execute(
            "UPDATE reports SET status=? WHERE id=?",
            (new_status, id)
        )

        conn.commit()
        conn.close()

        return redirect(url_for("admin_reports"))

    cursor.execute("SELECT * FROM reports WHERE id=?", (id,))
    report = cursor.fetchone()

    conn.close()

    return render_template("update_status.html", report=report)

@app.route("/admin_logout")
def admin_logout():
    session.pop("admin", None)
    flash("Admin logged out successfully!", "success")
    return redirect(url_for("admin"))

@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404

if __name__ == "__main__":
    app.run(debug=True)