from flask import Flask, render_template
import sqlite3
import os
from collections import defaultdict
from datetime import datetime

app = Flask(__name__)
DB_FILE = "analytics.db"

# Головна сторінка зі статистикою
@app.route("/stats")
def stats():
    if not os.path.exists(DB_FILE):
        return "База ще не створена."

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Кількість повідомлень по юзерах
    cursor.execute("SELECT user_id, name, COUNT(*) FROM messages GROUP BY user_id")
    user_stats = cursor.fetchall()

    # Кількість повідомлень по датах
    cursor.execute("SELECT timestamp FROM messages")
    rows = cursor.fetchall()
    daily_stats = defaultdict(int)
    for row in rows:
        date = datetime.fromisoformat(row[0]).strftime("%Y-%m-%d")
        daily_stats[date] += 1

    sorted_dates = sorted(daily_stats.items())
    dates = [d for d, _ in sorted_dates]
    counts = [c for _, c in sorted_dates]

    conn.close()

    return render_template("stats.html", user_stats=user_stats, dates=dates, counts=counts)

if __name__ == "__main__":
    app.run(debug=True, port=5000)