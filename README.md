# 🚀 Binance Futures Testnet Trading Bot

**A professional-grade, Streamlit-powered trading bot for Binance Futures Testnet.**  
Test strategies, manage positions, and monitor risk – all without risking real capital.

---

[![Python 3.8+](https://img.shields.io/badge/python-3.8%2B-blue?logo=python)](https://www.python.org/downloads/)
[![Streamlit 1.38+](https://img.shields.io/badge/streamlit-1.38%2B-ff4b4b?logo=streamlit)](https://streamlit.io/)
[![Binance API](https://img.shields.io/badge/binance-api-orange?logo=binance)](https://binance-docs.github.io/apidocs/futures/en/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Testnet](https://img.shields.io/badge/environment-testnet-lightgrey)](#-quick-start)

---

## ✨ Features

| ✅ | Description |
|---|-------------|
| **📊 Real-time Market Data** | Live tickers, order-book depth, candlestick charts (1m–1M) |
| **🛎️ Advanced Order Types** | MARKET, LIMIT, STOP, STOP-MARKET, TAKE-PROFIT, TAKE-PROFIT-MARKET, TRAILING-STOP-MARKET + built-in TP/SL |
| **📈 Interactive UI** | Clean Streamlit dashboard – responsive on desktop & mobile |
| **💰 Account Management** | Balance, equity, margin utilization, isolated & crossed margin |
| **📜 Order History** | Real-time updates, export to CSV/Excel, status tracking |
| **🛑 Risk Controls** | One-click “Close All Positions”, position-size calculator, margin-call alerts |
| **🔐 Secure API Wrapper** | HMAC-SHA256 signing, auto-reconnect, rate-limit & retry handling |
| **⚙️ Configurable** | Environment-based (testnet/mainnet), custom log level, Docker ready |
| **🧪 Test-driven** | Unit tests for core client & order logic (`pytest`) |
| **🤝 Contribute** | Clear contribution guide, CI badge, pre-commit hooks |

---

## 📂 Project Structure
binance-futures-bot/
├─ bot/                        # Core trading logic
│  ├─ client.py                # Binance REST & WebSocket wrapper
│  ├─ orders.py                # Order execution (TP/SL, trailing)
│  ├─ validators.py            # Input safety checks
│  ├─ logging_config.py        # Centralised logger
│  └─ cli.py                   # CLI entry-point
├─ utils/
│  ├─ helpers.py               # Re-usable helpers
│  └─ calculations.py          # P&L, risk, leverage utils
├─ tests/
│  ├─ test_client.py
│  └─ test_orders.py
├─ streamlit_app.py            # Streamlit dashboard (main)
├─ .env.example                # Template for secrets
├─ requirements.txt            # Python dependencies
├─ Dockerfile                  # Container image
├─ docker-compose.yml
└─ README.md




---

## 🛠️ Quick Start

> **All commands assume you are in the project root.**  
> Windows → `PowerShell` (or `cmd`), macOS/Linux → `bash`/`zsh`.

### 1️⃣ Clone the repository

```bash
git clone https://github.com/Ansh7473/Trading-Bot-on-Binance-Futures-Testnet
cd Trading-Bot-on-Binance-Futures-Testnet

### 2️⃣ Create a virtual environment & install deps

```bash
Bash# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate

# Install required packages
pip install -r requirements.txt

### 3️⃣ Generate your Testnet API credentials

Visit Binance Futures Testnet and log in.
Navigate to API Management → Create API.
Enable Futures permission (no withdrawals needed).
Copy the API Key and Secret.

### 4️⃣ Configure environment variables
Bash# Copy the template and edit in your favorite editor
cp .env.example .env
Edit .env:
textBINANCE_API_KEY=your_testnet_api_key
BINANCE_API_SECRET=your_testnet_api_secret
TESTNET_MODE=true                # set false for mainnet
LOG_LEVEL=INFO                  # DEBUG, INFO, WARNING, ERROR
Never commit .env – it is ignored via .gitignore.
### 5️⃣ Run the dashboard (recommended)
Bashstreamlit run streamlit_app.py
Open the URL shown in the console (usually http://localhost:8501).
All market data, order entry, positions & logs update in real-time.
### 6️⃣ Or use the CLI
Bashpython -m bot.cli place-order \
    --symbol BTCUSDT \
    --side BUY \
    --type MARKET \
    --quantity 0.001
Other CLI commands (--help shows the full list):
Bashpython -m bot.cli get-balance
python -m bot.cli get-positions
python -m bot.cli cancel-all
python -m bot.cli set-leverage --symbol BTCUSDT --leverage 25
### 7️⃣ (Optional) Run via Docker
Bashdocker compose up -d   # builds image and starts the Streamlit service
Access the UI at http://localhost:8501.

🖥️ Dashboard Walk-through

Section,What you’ll see
Market,"Ticker, depth chart, selected-pair candlesticks"
Order Panel,"Symbol, side, type, qty, price, TP/SL fields, submit button"
Portfolio,"Wallet balance, margin ratio, isolated-margin toggle"
Open Positions,"Qty, entry price, mark price, unrealised P&L, close button"
Order History,"Recent fills, status, fees, CSV export"
Alerts,"Margin-call warning, order-rejection details, connection health"

⌨️ CLI Quick Reference
Bash# Place any order
python -m bot.cli place-order \
    --symbol ETHUSDT \
    --side SELL \
    --type LIMIT \
    --price 1850 \
    --quantity 0.5 \
    --take_profit 1800 \
    --stop_loss 1900

# View live balance
python -m bot.cli get-balance

# List open positions
python -m bot.cli get-positions

# Cancel a single order
python -m bot.cli cancel-order --order-id 12345678

# Cancel *all* open orders for a symbol
python -m bot.cli cancel-all --symbol BTCUSDT

# Set isolated margin mode (per-symbol)
python -m bot.cli set-margin-type --symbol BTCUSDT --type ISOLATED

# Adjust leverage
python -m bot.cli set-leverage --symbol BTCUSDT --leverage 30
All commands perform input validation and report friendly error messages.

🛡️ Safety & Risk Management

Input validation against Binance’s PRICE_FILTER, LOT_SIZE, and PERCENT_PRICE rules.
Leverage caps respect the exchange-provided maximum for each symbol.
Margin-call detection (real-time via WebSocket) – UI shows a red banner and emits a system beep.
Close-All button instantly sends market orders to liquidate every open position.
Rate-limit awareness – wrapper automatically backs off on HTTP 429/418 responses and retries with exponential delay.
Logging – every request/response, including timestamps, signatures (hashed), and error traces, are written to logs/trading_bot.log.
Testnet-only mode – the TESTNET_MODE flag forces the client to use Binance’s sandbox endpoints; you cannot accidentally trade real funds.


⚠️ Important Notes

Educational/Testing Use Only – Real-world crypto futures are high-risk. Even on Testnet, practice disciplined risk management.
Do not share your .env or API secrets.
Enable IP Whitelisting on Binance for added security.
Never enable withdrawal permission on a Testnet key (the sandbox does not support withdrawals, but it’s a good habit).
API keys are case-sensitive – copy them exactly.
Network latency can cause order rejections; the bot retries idempotently where safe.
Backtest strategies before live deployment – the bot is merely an execution layer.


🤝 Contributing

Fork the repo & create a feature branch.
Follow PEP-8 styling (black, flake8).
Write unit tests for any new logic (pytest).
Submit a PR with a clear description and screenshots (if UI changes).

All contributions are welcome! See CONTRIBUTING.md for detailed guidelines.

📜 License
This project is licensed under the MIT License – see the LICENSE file for details.
