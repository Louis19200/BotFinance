import yfinance as yf
from datetime import datetime, timedelta
import pandas as pd
import holidays
import os

# Liste d'actions/ETF à suivre
tickers = [
    "AAPL", "MSFT", "AMZN", "TSLA", "SPY", "QQQ"
]

def log(message):
    """Écrit un message dans un fichier logs."""
    if not os.path.exists("logs"):
        os.makedirs("logs")

    today_str = datetime.now().strftime("%Y-%m-%d")
    log_filename = f"logs/log_{today_str}.txt"

    time_str = datetime.now().strftime("%H:%M:%S")
    with open(log_filename, "a", encoding="utf-8") as f:
        f.write(f"[{time_str}] {message}\n")

    print(message)  # Affiche aussi en console

def is_market_closed_today():
    today = datetime.now().date()
    us_holidays = holidays.US()

    if today.weekday() >= 5 or today in us_holidays:
        return True
    return False

def was_market_closed_yesterday():
    today = datetime.now().date()
    yesterday = today - timedelta(days=1)
    us_holidays = holidays.US()

    if today.weekday() == 0:  # lundi
        friday = today - timedelta(days=3)
        return friday in us_holidays
    return yesterday.weekday() >= 5 or yesterday in us_holidays

def get_daily_changes(tickers):
    data = yf.download(tickers, period="5d", interval="1d", group_by='ticker', auto_adjust=True)
    results = []

    for ticker in tickers:
        try:
            if len(tickers) == 1:
                df = data
            else:
                df = data[ticker]

            df = df.dropna(subset=['Close'])

            if len(df) < 2:
                log(f"Pas assez de données pour {ticker}.")
                continue

            today_close = df['Close'].iloc[-1]
            yesterday_close = df['Close'].iloc[-2]

            daily_change = ((today_close - yesterday_close) / yesterday_close) * 100

            results.append({
                "Ticker": ticker,
                "Yesterday Close": round(yesterday_close, 2),
                "Today Close": round(today_close, 2),
                "Change (%)": round(daily_change, 2)
            })

        except Exception as e:
            log(f"Erreur pour {ticker}: {e}")

    sorted_results = sorted(results, key=lambda x: x["Change (%)"], reverse=True)
    return sorted_results

def print_results(results):
    log(f"--- Performances du {datetime.now().strftime('%d/%m/%Y')} ---")
    if not results:
        log("Pas de résultats disponibles aujourd'hui.")
    for res in results:
        log(f"{res['Ticker']}: {res['Change (%)']}% (Clôture hier: {res['Yesterday Close']} -> aujourd'hui: {res['Today Close']})")

def save_to_csv(results):
    if not results:
        log("Pas de sauvegarde CSV car aucun résultat.")
        return

    if not os.path.exists("exports"):
        os.makedirs("exports")

    today_str = datetime.now().strftime("%Y-%m-%d")
    filename = f"exports/performances_{today_str}.csv"

    df = pd.DataFrame(results)
    df.to_csv(filename, index=False, encoding='utf-8-sig')
    log(f"Résultats sauvegardés dans {filename}")

if __name__ == "__main__":
    if is_market_closed_today():
        log("La bourse est fermée aujourd'hui (week-end ou jour férié).")
    elif was_market_closed_yesterday():
        log("La bourse était fermée hier (week-end ou jour férié). Résultats incomplets possibles.")
        results = get_daily_changes(tickers)
        print_results(results)
        save_to_csv(results)
    else:
        results = get_daily_changes(tickers)
        print_results(results)
        save_to_csv(results)
