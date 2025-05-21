from flask import Flask, render_template, request, jsonify
import yfinance as yf
import pandas as pd
import os
import json
from datetime import datetime, timedelta

app = Flask(__name__)

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

TRACKED_FILE = "tracked_tickers.json"
if not os.path.exists(TRACKED_FILE):
    with open(TRACKED_FILE, 'w') as f:
        json.dump(["AAPL", "MSFT", "SPY", "QQQ"], f)

with open(TRACKED_FILE, 'r') as f:
    tracked_tickers = json.load(f)

def write_log(message):
    now = datetime.now()
    fname = f"log_{now.strftime('%Y-%m-%d')}.txt"
    with open(os.path.join(LOG_DIR, fname), "a", encoding="utf-8") as f:
        f.write(f"[{now.strftime('%H:%M:%S')}] {message}\n")

@app.route('/')
def home():
    write_log(">> Accès à /")

    try:
        end_str = request.args.get("end")
        start_str = request.args.get("start")

        if end_str:
            end_date = datetime.strptime(end_str, "%Y-%m-%d")
        else:
            end_date = datetime.now() - timedelta(days=1)

        if start_str:
            start_date = datetime.strptime(start_str, "%Y-%m-%d")
        else:
            start_date = end_date - timedelta(days=30)

    except Exception as e:
        write_log(f"[ERREUR PARSING DATES] : {e}")
        end_date = datetime.now() - timedelta(days=1)
        start_date = end_date - timedelta(days=30)

    performances = {}
    dates = []

    for ticker in tracked_tickers:
        write_log(f"Chargement {ticker}")
        try:
            data = yf.download(
                ticker,
                start=start_date.strftime('%Y-%m-%d'),
                end=end_date.strftime('%Y-%m-%d'),
                progress=False,
                auto_adjust=False
            )

            if data.empty:
                write_log(f"[ERREUR] {ticker} : données vides")
                continue

            close = data['Close']
            if isinstance(close, pd.DataFrame):
                close = close.squeeze()
            if isinstance(close, pd.Series):
                performances[ticker] = close.tolist()
                if not dates:
                    dates = [d.strftime('%Y-%m-%d') for d in data.index]

            write_log(f"{ticker} : OK ({len(close)} valeurs)")

        except Exception as e:
            write_log(f"[EXCEPTION] {ticker} : {e}")

    return render_template("home.html", performances=performances, dates=dates)

@app.route('/add_ticker')
def add_ticker():
    ticker = request.args.get('ticker', '').upper()
    write_log(f">> Tentative ajout {ticker}")

    if not ticker:
        write_log("[ERREUR] Aucun ticker fourni")
        return jsonify({"error": "Aucun ticker fourni"})

    if ticker not in tracked_tickers:
        tracked_tickers.append(ticker)
        with open(TRACKED_FILE, 'w') as f:
            json.dump(tracked_tickers, f)

    try:
        end_date = datetime.now() - timedelta(days=1)
        start_date = end_date - timedelta(days=30)

        data = yf.download(
            ticker,
            start=start_date.strftime('%Y-%m-%d'),
            end=end_date.strftime('%Y-%m-%d'),
            progress=False,
            auto_adjust=False
        )

        if data.empty:
            write_log(f"[ERREUR] {ticker} : vide")
            return jsonify({"error": "Pas de données pour ce ticker"})

        close = data['Close']
        if isinstance(close, pd.DataFrame):
            close = close.squeeze()

        closes = close.tolist() if isinstance(close, pd.Series) else []

        write_log(f"{ticker} ajouté avec {len(closes)} valeurs")
        return jsonify({
            "ticker": ticker,
            "closes": closes
        })

    except Exception as e:
        write_log(f"[EXCEPTION] {ticker} : {e}")
        return jsonify({"error": str(e)})

@app.route('/logs')
def logs():
    files = sorted(os.listdir(LOG_DIR), reverse=True)
    content = ""
    for fname in files:
        content += f"\n==== {fname} ====\n"
        with open(os.path.join(LOG_DIR, fname), encoding="utf-8") as f:
            content += f.read()
    return f"<pre>{content}</pre>"

if __name__ == '__main__':
    app.run(debug=True)
