from flask import Flask, render_template
from db import init_db, fetch_recent_balances

app = Flask(__name__)

# Initialize database on app startup
init_db()

@app.route("/")
def home():
    balances = fetch_recent_balances()
    return render_template("index.html", balances=balances)
