import sqlite3
from datetime import datetime

from flask import Flask, flash, redirect, render_template, request, session, url_for

app = Flask(__name__)
app.config["SECRET_KEY"] = "your_secret_key"

DATABASE = "site.db"


def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        team_name = request.form["team_name"]
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]
        conn = get_db_connection()
        conn.execute("INSERT INTO teams (name) VALUES (?)", (team_name,))
        team_id = conn.execute(
            "SELECT id FROM teams WHERE name = ?", (team_name,)
        ).fetchone()["id"]
        conn.execute(
            "INSERT INTO users (username, email, password, team_id) VALUES (?, ?, ?, ?)",
            (username, email, password, team_id),
        )
        conn.commit()
        conn.close()
        flash("Account created!", "success")
        return redirect(url_for("login"))
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        conn = get_db_connection()
        user = conn.execute(
            "SELECT * FROM users WHERE email = ? AND password = ?", (email, password)
        ).fetchone()
        conn.close()
        if user:
            session["user_id"] = user["id"]
            flash("You have been logged in!", "success")
            return redirect(url_for("index"))
        else:
            flash("Login Unsuccessful. Please check email and password", "danger")
    return render_template("login.html")


@app.route("/challenge/<int:challenge_id>", methods=["GET", "POST"])
def challenge(challenge_id):
    conn = get_db_connection()
    challenge = conn.execute(
        "SELECT * FROM challenges WHERE id = ?", (challenge_id,)
    ).fetchone()
    if request.method == "POST":
        answer = request.form["answer"]
        conn.execute(
            "INSERT INTO submissions (user_id, challenge_id, answer, timestamp) VALUES (?, ?, ?, ?)",
            (session["user_id"], challenge_id, answer, datetime.now()),
        )
        conn.commit()
        conn.close()
        flash("Submission successful!", "success")
        return redirect(url_for("index"))
    return render_template("challenge.html", challenge=challenge)


@app.route("/leaderboard")
def leaderboard():
    conn = get_db_connection()
    submissions = conn.execute(
        """
        SELECT users.username, teams.name AS team_name, challenges.title, submissions.answer, submissions.timestamp
        FROM submissions
        JOIN users ON submissions.user_id = users.id
        JOIN teams ON users.team_id = teams.id
        JOIN challenges ON submissions.challenge_id = challenges.id
        ORDER BY submissions.timestamp
    """
    ).fetchall()
    conn.close()
    return render_template("leaderboard.html", submissions=submissions)


@app.route("/logout")
def logout():
    session.pop("user_id", None)
    flash("You have been logged out.", "success")
    return redirect(url_for("index"))


def init_db():
    conn = get_db_connection()
    conn.executescript(
        """
    CREATE TABLE IF NOT EXISTS teams (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE
    );

    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        email TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,
        team_id INTEGER,
        FOREIGN KEY (team_id) REFERENCES teams (id)
    );

    CREATE TABLE IF NOT EXISTS challenges (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT NOT NULL,
        date_posted TIMESTAMP NOT NULL,
        deadline TIMESTAMP NOT NULL
    );

    CREATE TABLE IF NOT EXISTS submissions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        challenge_id INTEGER,
        answer TEXT NOT NULL,
        timestamp TIMESTAMP NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users (id),
        FOREIGN KEY (challenge_id) REFERENCES challenges (id)
    );
    """
    )
    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
