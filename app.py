"""ledgerly-api: a small expense tracker."""

from decimal import Decimal, InvalidOperation
from functools import wraps

from flask import Flask, g, jsonify, request

import auth
import db


def create_app(db_path: str = "ledgerly.db") -> Flask:
    app = Flask(__name__)
    conn = db.connect(db_path)

    def login_required(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            header = request.headers.get("Authorization", "")
            token = header.removeprefix("Bearer ").strip()
            row = conn.execute(
                "SELECT user_id FROM sessions WHERE token = ?", (token,)
            ).fetchone()
            if not token or row is None:
                return jsonify(error="login required"), 401
            g.user_id = row["user_id"]
            return fn(*args, **kwargs)

        return wrapper

    @app.post("/signup")
    def signup():
        data = request.get_json(force=True)
        username = str(data.get("username", "")).strip()
        password = str(data.get("password", ""))
        if not username or len(password) < 8:
            return jsonify(error="username and 8+ char password required"), 400
        try:
            conn.execute(
                "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                (username, auth.hash_password(password)),
            )
            conn.commit()
        except Exception:
            return jsonify(error="username taken"), 409
        return jsonify(ok=True), 201

    @app.post("/login")
    def login():
        data = request.get_json(force=True)
        row = conn.execute(
            "SELECT id, password_hash FROM users WHERE username = ?",
            (str(data.get("username", "")),),
        ).fetchone()
        if row is None or not auth.verify_password(
            str(data.get("password", "")), row["password_hash"]
        ):
            return jsonify(error="bad credentials"), 401
        token = auth.new_token()
        conn.execute(
            "INSERT INTO sessions (token, user_id) VALUES (?, ?)", (token, row["id"])
        )
        conn.commit()
        return jsonify(token=token)

    @app.post("/expenses")
    @login_required
    def add_expense():
        data = request.get_json(force=True)
        # Money is parsed with Decimal, never float: float() cannot hold amounts
        # like 0.285 or 1.005 exactly, so round() silently picked the wrong cent
        # and monthly totals drifted. Keep it Decimal.
        try:
            amount_cents = int(Decimal(str(data["amount"])) * 100)
        except (KeyError, TypeError, ValueError, OverflowError, InvalidOperation):
            return jsonify(error="amount must be a number"), 400
        if Decimal(str(data["amount"])) * 100 != amount_cents:
            return jsonify(error="amount can have at most 2 decimal places"), 400
        if amount_cents <= 0:
            return jsonify(error="amount must be positive"), 400
        expense_id = db.add_expense(conn, g.user_id, amount_cents, str(data.get("note", "")))
        return jsonify(id=expense_id), 201

    @app.get("/expenses")
    @login_required
    def list_expenses():
        return jsonify(expenses=db.list_expenses(conn, g.user_id))

    return app
