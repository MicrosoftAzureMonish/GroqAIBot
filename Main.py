import requests
import time
import datetime

TELEGRAM_BOT_TOKEN = '7828677821:AAGfAyEuR0amyAkq1DQv8DMyP_0GkcSv5_Y'
TELEGRAM_CHAT_ID = '6963333384'
TWELVE_API_KEY = 'b01e66e1bae94fc49360e516bb13cc26'
GROQ_API_KEY = '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'

SYMBOLS = ['EUR/USD', 'GBP/USD', 'USD/JPY']
INTERVALS = ['1min', '5min', '15min']

def fetch_price_history(symbol, interval):
    url = f"https://api.twelvedata.com/time_series?symbol={symbol}&interval={interval}&apikey={TWELVE_API_KEY}&outputsize=100"
    response = requests.get(url)
    data = response.json()

    if 'values' not in data:
        print(f"[WARN] Failed to fetch {symbol}: {data}")
        return []

    closes = [float(item['close']) for item in reversed(data['values'])]
    return closes

def calculate_ema(prices, period=14):
    if len(prices) < period:
        return None
    ema = prices[0]
    multiplier = 2 / (period + 1)
    for price in prices[1:]:
        ema = (price - ema) * multiplier + ema
    return ema

def calculate_rsi(prices, period=14):
    if len(prices) < period + 1:
        return None
    gains, losses = 0, 0
    for i in range(1, period + 1):
        change = prices[i] - prices[i - 1]
        if change > 0:
            gains += change
        else:
            losses -= change
    avg_gain = gains / period
    avg_loss = losses / period
    if avg_loss == 0:
        return 100
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def send_telegram(message):
    url = f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage'
    payload = {'chat_id': TELEGRAM_CHAT_ID, 'text': message, 'parse_mode': 'Markdown'}
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print(f"[ERROR] Failed to send Telegram message: {e}")

def ask_groq(message):
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    json_data = {
        "messages": [{"role": "user", "content": message}],
        "model": "llama3-70b-8192"
    }
    try:
        res = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=json_data)
        return res.json()['choices'][0]['message']['content'].strip()
    except Exception as e:
        print(f"[ERROR] Groq failed: {e}")
        return "WAIT"

def run_bot():
    print(f"[INFO] Bot started at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    summary = "*📊 Currency Signals 📊*\n\n"
    ai_input = ""
    decisions = {}

    for symbol in SYMBOLS:
        symbol_key = symbol.replace("/", "")
        ai_input += f"\nSymbol: {symbol_key}"
        decisions[symbol_key] = []

        for interval in INTERVALS:
            prices = fetch_price_history(symbol, interval)
            if not prices:
                continue
            ema = calculate_ema(prices[-20:])
            rsi = calculate_rsi(prices[-20:])
            price = prices[-1]

            ai_input += f"\n{interval} - Price: {price:.5f}, EMA: {ema:.5f}, RSI: {rsi:.2f}"

    ai_input += "\n\nGive final decision for each symbol as only BUY, SELL or WAIT."

    ai_reply = ask_groq(ai_input)
    print(f"[GROQ] {ai_reply}")

    summary += f"{ai_reply}"
    send_telegram(summary)

# --- Run every 15 minutes ---
while True:
    run_bot()
    time.sleep(120)