from flask import Flask, render_template_string, request, redirect
import json
import math
from pathlib import Path
import os

app = Flask(__name__)

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

TRANSACTION_FILE = DATA_DIR / "transactions.json"
SAVINGS_FILE = DATA_DIR / "savings.json"

def load_transactions():
    if not TRANSACTION_FILE.exists():
        return []
    return json.loads(TRANSACTION_FILE.read_text())

def save_transactions(transactions):
    savings = load_savings()
    for t in transactions:
        if not t.get("roundup_applied"):
            amount = float(t["amount"])
            roundup = calculate_roundup(amount)
            if roundup > 0:
                savings[t["person"]] += roundup
                t["roundup_applied"] = True
    save_savings(savings)
    TRANSACTION_FILE.write_text(json.dumps(transactions, indent=4))

def load_savings():
    if not SAVINGS_FILE.exists():
        return {"Luis": 0, "Janet": 0}
    return json.loads(SAVINGS_FILE.read_text())

def save_savings(data):
    SAVINGS_FILE.write_text(json.dumps(data, indent=4))

def calculate_roundup(amount):
    if amount >= 0:
        return 0
    return round(math.ceil(abs(amount)) - abs(amount), 2)

def bmo_message(amount):
    if amount < -50:
        return "⚠️ Whoa… big spend. I saved a little though."
    elif amount < 0:
        return "😊 I saved your round-up!"
    else:
        return "🌟 Income detected. Nice."

@app.route("/", methods=["GET", "POST"])
def home():
    bmo = "Hi! I'm BMO 🤖"

    if request.method == "POST":
        person = request.form["person"]
        amount = float(request.form["amount"])
        desc = request.form["desc"]

        transactions = load_transactions()
        transactions.append({
            "person": person,
            "amount": amount,
            "description": desc,
            "roundup_applied": False
        })

        save_transactions(transactions)
        bmo = bmo_message(amount)
        return redirect("/")

    transactions = load_transactions()
    savings = load_savings()

    balances = {"Luis": 0, "Janet": 0}
    for t in transactions:
        balances[t["person"]] += float(t["amount"])

    return render_template_string("""
    <h1>L&J Finance (BMO Edition)</h1>
    <h3>{{bmo}}</h3>

    <h2>Balances</h2>
    <p>Luis: ${{balances["Luis"]}}</p>
    <p>Janet: ${{balances["Janet"]}}</p>

    <h2>Savings</h2>
    <p>Luis: ${{savings["Luis"]}}</p>
    <p>Janet: ${{savings["Janet"]}}</p>

    <h2>Add Transaction</h2>
    <form method="POST">
        <select name="person">
            <option>Luis</option>
            <option>Janet</option>
        </select><br><br>

        <input name="amount" placeholder="Amount"><br><br>
        <input name="desc" placeholder="Description"><br><br>

        <button type="submit">Add</button>
    </form>
    """, balances=balances, savings=savings, bmo=bmo)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
